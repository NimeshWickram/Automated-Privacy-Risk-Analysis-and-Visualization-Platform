"""Synthetic implementation tests; these do not estimate real-world accuracy."""

from contextlib import closing
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from sqlalchemy import create_engine, event, select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from database import Base, get_db
import models
import models_evidence
from models_provenance import AnalysisRun, EvidenceProvenance, RiskFinding, FindingEvidence, PROVENANCE_TABLES
import provenance
import main
import evidence_engine
from llm_report_generator import generate_report

spec = importlib.util.spec_from_file_location("phase1_migration", BACKEND / "migrations/phase1_provenance.py")
migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration)


def observation(source="manifest", raw=None):
    return {"source_type": source, "evidence_category": "location_collection", "data_type": "Location",
            "description": "Permission declared" if source == "manifest" else "Static API reference",
            "raw_evidence": raw or ('<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>' if source == "manifest" else "LocationManager.getLastKnownLocation"),
            "file_reference": "AndroidManifest.xml" if source == "manifest" else "classes2.dex", "line_number": None}


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
        event.listen(self.engine, "connect", lambda db, _: db.execute("PRAGMA foreign_keys=ON"))
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.addCleanup(self.engine.dispose)
        self.addCleanup(self.db.close)
        self.app = models.AppAnalysis(app_name="Synthetic fixture", apk_hash="a" * 64, version_name="1", analyzed_at="2026-09-28")
        self.db.add(self.app)
        self.db.flush()
        self.run = provenance.persist_observations(self.db, self.app, [observation()], {"code": "complete", "network": "not_performed"})
        self.db.commit()

    def count(self, model):
        return self.db.scalar(select(func.count()).select_from(model))

    def test_manifest_finding_has_exact_source_not_collection(self):
        data = provenance.app_provenance(self.db, self.app.id)
        finding = data["findings"][0]
        self.assertEqual(finding["category"], "Sensitive Permission Capability")
        self.assertEqual(finding["evidence"][0]["observation"]["observation_kind"], "PERMISSION_REQUESTED")
        self.assertEqual(finding["evidence"][0]["observation"]["raw_evidence"], observation()["raw_evidence"])
        self.assertIn("does not establish", finding["interpretation"])
        self.assertEqual(self.count(models.PersonalDataCollection), 0)
        self.assertIsNone(finding["evidenceStrengthScore"])

    def test_code_reference_does_not_claim_runtime_access(self):
        provenance.persist_observations(self.db, self.app, [observation("decompiled_code")], {})
        finding = provenance.app_provenance(self.db, self.app.id)["findings"][-1]
        self.assertEqual(finding["category"], "Potential Sensitive Data Access")
        self.assertIn("does not establish invocation", finding["interpretation"])
        self.assertEqual(finding["evidence"][0]["observation"]["file_reference"], "classes2.dex")

    def test_sdk_and_network_presence_do_not_assert_transmission(self):
        for source in ("sdk", "network_traffic", "privacy_policy", "data_safety", "app_ui"):
            provenance.persist_observations(self.db, self.app, [observation(source, "Observed source content")], {})
        categories = [f["category"] for f in provenance.app_provenance(self.db, self.app.id)["findings"]]
        self.assertEqual(categories, ["Sensitive Permission Capability", "Third-Party SDK Presence"])

    def test_source_snapshot_hash_and_metadata(self):
        row = self.db.scalars(select(EvidenceProvenance)).one()
        self.assertEqual(row.snapshot_sha256, hashlib.sha256(row.snapshot_json.encode()).hexdigest())
        self.assertTrue(row.captured_at)
        self.assertEqual(self.run.apk_sha256, self.app.apk_hash)
        self.assertEqual(self.run.application_version, "1")
        self.assertIn("python", json.loads(self.run.environment_json))

    def test_finding_without_evidence_is_rejected(self):
        before = self.count(RiskFinding)
        with self.assertRaisesRegex(ValueError, "SUPPORTS"):
            provenance.create_finding(self.db, self.run.id, "potential", "Location", "Limited inference", "test", [])
        self.assertEqual(self.count(RiskFinding), before)

    def test_missing_and_cross_run_links_are_rejected(self):
        other = models.AppAnalysis(app_name="Other version", apk_hash="b" * 64, version_name="2")
        self.db.add(other)
        self.db.flush()
        run = provenance.persist_observations(self.db, other, [observation()], {})
        ev = self.db.scalar(select(EvidenceProvenance).where(EvidenceProvenance.run_id == run.id))
        for evidence_id in (999999, ev.evidence_source_id):
            with self.subTest(evidence_id=evidence_id), self.assertRaisesRegex(ValueError, "same analysis run"):
                provenance.create_finding(self.db, self.run.id, "potential", "Location", "Limited inference", "test", [(evidence_id, "SUPPORTS", "reason")])

    def test_all_relationship_types_round_trip(self):
        ev = self.db.scalars(select(EvidenceProvenance)).one()
        provenance.create_finding(self.db, self.run.id, "Review fixture", "Location", "Synthetic relationship validation", "test",
            [(ev.evidence_source_id, relation, "Synthetic test relation") for relation in ("SUPPORTS", "CORROBORATES", "CONTRADICTS")])
        relations = [link["relationship"] for link in provenance.app_provenance(self.db, self.app.id)["findings"][-1]["evidence"]]
        self.assertEqual(relations, ["SUPPORTS", "CORROBORATES", "CONTRADICTS"])

    def test_invalid_relationship_rejected(self):
        ev = self.db.scalars(select(EvidenceProvenance)).one()
        with self.assertRaises(ValueError):
            provenance.create_finding(self.db, self.run.id, "potential", "Location", "test", "test", [(ev.evidence_source_id, "SUPPORTS", "reason"), (ev.evidence_source_id, "PROVES", "reason")])

    def test_database_rejects_cross_run_relationship(self):
        second = provenance.persist_observations(self.db, self.app, [observation()], {})
        finding = self.db.scalars(select(RiskFinding).where(RiskFinding.run_id == second.id)).one()
        first_ev = self.db.scalars(select(EvidenceProvenance).where(EvidenceProvenance.run_id == self.run.id)).one()
        with self.assertRaises(IntegrityError), self.db.begin_nested():
            self.db.add(FindingEvidence(run_id=second.id, finding_id=finding.id, evidence_source_id=first_ev.evidence_source_id, relationship="SUPPORTS", rationale="invalid"))
            self.db.flush()

    def test_missing_raw_evidence_does_not_create_run(self):
        before = self.count(AnalysisRun)
        record = observation()
        record["raw_evidence"] = ""
        with self.assertRaisesRegex(ValueError, "raw evidence"):
            provenance.persist_observations(self.db, self.app, [record], {})
        self.assertEqual(self.count(AnalysisRun), before)

    def test_corrupted_snapshot_fails_closed(self):
        record = self.db.scalars(select(EvidenceProvenance)).one()
        record.snapshot_json = '{}'
        self.db.flush()
        with self.assertRaisesRegex(ValueError, "integrity"):
            provenance.app_provenance(self.db, self.app.id)

    def test_legacy_records_are_not_automatically_grounded(self):
        legacy = models.AppAnalysis(app_name="Legacy")
        self.db.add(legacy)
        self.db.flush()
        self.assertEqual(provenance.app_provenance(self.db, legacy.id), {"status": "legacy_unverified", "runs": [], "findings": []})

    def test_app_payload_is_isolated(self):
        other = models.AppAnalysis(app_name="Other", apk_hash="b"*64, version_name="2")
        self.db.add(other)
        self.db.flush()
        run = provenance.persist_observations(self.db, other, [observation("decompiled_code", "OTHER_APP_ONLY")], {})
        data = provenance.app_provenance(self.db, self.app.id)
        self.assertNotIn(run.id, [r["id"] for r in data["runs"]])
        self.assertNotIn("OTHER_APP_ONLY", json.dumps(data))

    def test_report_uses_only_linked_findings_no_llm_or_mock(self):
        with patch('llm_report_generator.genai.GenerativeModel', side_effect=AssertionError("LLM must not run")):
            report = generate_report(self.app.id, self.db)
        self.assertEqual(report["provider"], "deterministic-evidence-template-v2")
        self.assertIn("evidence #", report["markdown"])
        self.assertNotIn("Firebase", report["markdown"])
        self.assertNotIn("0.45", report["markdown"])

    def client(self):
        main.app.dependency_overrides[get_db] = lambda: self.db
        self.addCleanup(main.app.dependency_overrides.clear)
        return TestClient(main.app)

    def test_provenance_endpoint_and_missing_app(self):
        with self.client() as client:
            response = client.get(f"/api/apps/{self.app.id}/provenance")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["findings"][0]["evidence"][0]["relationship"], "SUPPORTS")
            self.assertEqual(client.get('/api/apps/999999/provenance').status_code, 404)

    def test_upload_does_not_create_fabricated_claims(self):
        class FakeAPK:
            def __init__(self, path): pass
            def get_app_name(self): return "Synthetic APK fixture"
            def get_package(self): return "test.synthetic"
            def get_androidversion_name(self): return "1.2"
            def get_target_sdk_version(self): return "34"
            def get_permissions(self): return ["android.permission.ACCESS_FINE_LOCATION", "android.permission.CAMERA"]
            def get_activities(self): return []
            def get_services(self): return []
            def get_receivers(self): return []
            def get_providers(self): return []
            def get_all_dex(self): return []
        with tempfile.TemporaryDirectory() as folder, patch.object(main, "UPLOAD_DIR", folder), patch.object(main, "APK", FakeAPK), patch.object(main.policy_extractor, "extract_policy_claims", side_effect=AssertionError("Do not use mock claims")), patch.object(main.data_safety_scraper, "fetch_data_safety", side_effect=AssertionError("Do not use mock Data Safety")), self.client() as client:
            response = client.post('/api/analyze', files={"file": ("sample.apk", b"SYNTHETIC IMPLEMENTATION FIXTURE", "application/octet-stream")})
            self.assertEqual(response.status_code, 200, response.text)
            app_id = response.json()["app_id"]
            detail = client.get(f"/api/apps/{app_id}").json()
            self.assertEqual(detail["personalData"]["total"], 0)
            self.assertEqual(detail["trackers"]["total"], 0)
            self.assertEqual(detail["riskPredictions"]["total"], 0)
            self.assertEqual(detail["securityIncidents"]["total"], 0)
            self.assertEqual(detail["securityMechanisms"]["total"], 0)
            self.assertFalse(detail["analysisMetadata"]["dynamicAnalysisComplete"])
            self.assertEqual(detail["disclosureMismatches"]["total"], 0)
            self.assertEqual(detail["provenance"]["runs"][0]["apkSha256"], hashlib.sha256(b"SYNTHETIC IMPLEMENTATION FIXTURE").hexdigest())
            self.assertTrue(detail["provenance"]["findings"])

    def test_code_scan_failure_is_not_success(self):
        class BrokenAPK:
            def get_all_dex(self): raise ValueError("fixture failure")
        diagnostics = {}
        self.assertEqual(evidence_engine.scan_code_patterns(BrokenAPK(), diagnostics), [])
        self.assertEqual(diagnostics["status"], "failed")

    def test_code_snapshot_preserves_full_context_and_dex_file(self):
        context = "X" * 300 + "LocationManager.getLastKnownLocation"
        class APK:
            def get_all_dex(self): return [b"first", b"second"]
        class DEX:
            def __init__(self, raw): pass
            def get_strings(self): return [context]
        with patch('androguard.core.dex.DEX', DEX):
            records = evidence_engine.scan_code_patterns(APK())
        self.assertTrue(records)
        self.assertEqual({record['file'] for record in records}, {'classes.dex', 'classes2.dex'})
        self.assertTrue(all(record['context'] == context for record in records))

    def test_readiness_check_does_not_rollback_pending_provenance(self):
        run = provenance.persist_observations(self.db, self.app, [observation('decompiled_code')], {})
        self.assertTrue(provenance.schema_ready(self.db))
        self.assertIsNotNone(self.db.get(AnalysisRun, run.id))
        self.assertEqual(self.count(RiskFinding), 2)

    def test_upload_is_blocked_until_migration(self):
        with patch.object(provenance, 'schema_ready', return_value=False), self.client() as client:
            response = client.post('/api/analyze', files={'file': ('fixture.apk', b'fixture')})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.count(models.AppAnalysis), 1)


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.database = self.root / 'legacy.db'
        engine = create_engine('sqlite:///' + self.database.as_posix())
        legacy_names = {value.__tablename__ for module in (models, models_evidence)
                        for value in vars(module).values() if isinstance(value, type) and hasattr(value, '__tablename__')}
        legacy_tables = [table for table in Base.metadata.sorted_tables if table.name in legacy_names]
        Base.metadata.create_all(engine, tables=legacy_tables)
        with Session(engine) as session:
            app = models.AppAnalysis(app_name="Preserved legacy", apk_hash="a" * 64, version_name="1")
            session.add(app)
            session.commit()
        engine.dispose()

    def snapshot(self):
        with closing(sqlite3.connect(self.database)) as db:
            return migration.table_snapshot(db)

    def test_migration_backs_up_preserves_rows_and_is_idempotent(self):
        before = self.snapshot()
        result = migration.migrate(self.database, self.root / 'backups')
        self.assertEqual(result["status"], "applied")
        after = self.snapshot()
        self.assertEqual({name: after[name] for name in before}, before)
        with closing(sqlite3.connect(result["backup"])) as backup:
            self.assertEqual(migration.table_snapshot(backup), before)
        self.assertEqual(len(after), len(before) + 4)
        self.assertTrue(all(after[t.name]['count'] == 0 for t in PROVENANCE_TABLES))
        self.assertEqual(migration.migrate(self.database, self.root / 'backups')["status"], "already_applied")

    def test_conflicting_schema_stops_without_mutation(self):
        with closing(sqlite3.connect(self.database)) as db:
            db.execute('CREATE TABLE risk_findings (wrong_column TEXT)')
            db.commit()
        before = self.database.read_bytes()
        with self.assertRaisesRegex(ValueError, 'conflicting'):
            migration.migrate(self.database, self.root / 'backups')
        self.assertEqual(self.database.read_bytes(), before)
        self.assertFalse((self.root / 'backups').exists())

    def test_failure_after_backup_rolls_back_ddl(self):
        before = self.snapshot()
        real_snapshot = migration.table_snapshot
        calls = 0
        def fail_post_ddl(db):
            nonlocal calls
            calls += 1
            if calls == 4:
                raise RuntimeError('injected post-DDL failure')
            return real_snapshot(db)
        with patch.object(migration, 'table_snapshot', side_effect=fail_post_ddl):
            with self.assertRaisesRegex(RuntimeError, 'injected'):
                migration.migrate(self.database, self.root / 'backups')
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(len(list((self.root / 'backups').glob('*.db'))), 1)


if __name__ == '__main__':
    unittest.main()
