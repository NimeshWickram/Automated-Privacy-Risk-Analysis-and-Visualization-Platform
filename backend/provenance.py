"""Conservative adapter from legacy analyzer observations to persistent provenance.

This is not Phase 2 fusion. Each initial finding has a single explicit support;
no runtime access, transmission, or contradiction is inferred from static data.
"""

import hashlib
import json
import platform
from datetime import datetime, timezone
from importlib.metadata import version, PackageNotFoundError

from sqlalchemy import inspect, select
from models import AppAnalysis
from models_evidence import EvidenceSource
from models_provenance import AnalysisRun, EvidenceProvenance, RiskFinding, FindingEvidence, PROVENANCE_TABLES

ANALYSIS_VERSION = "phase1-provenance-v1"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def canonical_json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def schema_ready(db):
    # Reuse the session connection: a second connection can roll back an active
    # transaction when a test or application uses a single-connection SQLite pool.
    inspector = inspect(db.connection())
    return all(inspector.has_table(table.name) for table in PROVENANCE_TABLES)


def environment_metadata():
    packages = {}
    for name in ("androguard", "SQLAlchemy", "fastapi"):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = "unavailable"
    return {"python": platform.python_version(), "os": platform.platform(), "analyzers": packages}


def create_finding(db, run_id, category, data_category, interpretation, rule_id, links):
    """Validate the complete provenance before writing any finding.

Each link is (evidence_source_id, relationship, rationale). Stronger behavioral
semantics belong to versioned Phase 2 rules, not arbitrary client payloads.
    """
    if not links or not any(link[1] == "SUPPORTS" for link in links):
        raise ValueError("A finding requires at least one SUPPORTS evidence relationship.")
    if not all(isinstance(text, str) and text.strip() for text in (category, data_category, interpretation, rule_id)):
        raise ValueError("Finding fields must be non-empty.")
    seen = set()
    for evidence_id, relation, rationale in links:
        if relation not in {"SUPPORTS", "CORROBORATES", "CONTRADICTS"} or not rationale.strip():
            raise ValueError("Invalid evidence relationship or missing rationale.")
        if (evidence_id, relation) in seen:
            raise ValueError("Duplicate evidence relationship.")
        seen.add((evidence_id, relation))
        evidence = db.get(EvidenceProvenance, evidence_id)
        if evidence is None or evidence.run_id != run_id:
            raise ValueError("Evidence must belong to the same analysis run as the finding.")
    finding = RiskFinding(run_id=run_id, finding_category=category, data_category=data_category,
                          interpretation=interpretation, rule_id=rule_id, created_at=utc_now())
    db.add(finding)
    db.flush()
    for evidence_id, relation, rationale in links:
        db.add(FindingEvidence(run_id=run_id, finding_id=finding.id,
                               evidence_source_id=evidence_id, relationship=relation, rationale=rationale))
    db.flush()
    return finding


def persist_observations(db, app, records, source_status, *, create_initial_findings=True, analysis_version=ANALYSIS_VERSION):
    if not app.id or db.get(AppAnalysis, app.id) is not app:
        raise ValueError("Application must be persisted in this session first.")
    if len(app.apk_hash or "") != 64 or any(c not in "0123456789abcdef" for c in app.apk_hash.lower()):
        raise ValueError("A new analysis requires the APK SHA-256.")
    # Validate everything before creating partial provenance. Caller owns commit/rollback.
    accepted = {"manifest", "decompiled_code", "privacy_policy", "sdk", "network_traffic", "data_safety", "app_ui"}
    for record in records:
        if record.get("source_type") not in accepted:
            raise ValueError("This Phase 1 adapter does not validate that source yet.")
        if not all(isinstance(record.get(key), str) and record[key].strip() for key in ("raw_evidence", "file_reference", "description")):
            raise ValueError("Exact raw evidence and source reference are required.")
    now = utc_now()
    run = AnalysisRun(app_id=app.id, apk_sha256=app.apk_hash, application_version=app.version_name or "unknown",
                      analysis_version=analysis_version, started_at=now,
                      source_status_json=canonical_json(source_status), environment_json=canonical_json(environment_metadata()))
    db.add(run)
    db.flush()
    for original in records:
        record = dict(original)
        source = record["source_type"]
        sdk = record.get("evidence_category") == "sdk_presence"
        if source == "manifest":
            kind = "SDK_PRESENT" if sdk else "PERMISSION_REQUESTED"
            analyzer = "manifest-component-v1" if sdk else "manifest-permission-v1"
        elif source == "decompiled_code":
            kind, analyzer = "API_REFERENCE", "dex-string-v1"
        elif source == "privacy_policy":
            kind, analyzer = "POLICY_DOCUMENT", "html-text-v1"
        else:
            kind = {"sdk": "SDK_PRESENT", "network_traffic": "NETWORK_OBSERVATION", "data_safety": "DATA_SAFETY_DOCUMENT", "app_ui": "UI_OBSERVATION"}[source]
            analyzer = record.get("analyzer", "manual-evidence-import-v1")
        analyzer = record.get('analyzer', analyzer)
        evidence = EvidenceSource(app_id=app.id, source_type=source, evidence_category=kind,
                                  data_type=record.get("data_type", "Unknown"), description=record["description"],
                                  raw_evidence=record["raw_evidence"], file_reference=record["file_reference"],
                                  line_number=record.get("line_number"), timestamp=now,
                                  confidence=None, severity="info", is_confirmed=False)
        db.add(evidence)
        db.flush()
        snapshot = canonical_json({"source_type": source, "observation_kind": kind,
                                   "description": evidence.description, "data_category": evidence.data_type,
                                   "raw_evidence": evidence.raw_evidence, "file_reference": evidence.file_reference,
                                   "line_number": evidence.line_number})
        db.add(EvidenceProvenance(evidence_source_id=evidence.id, run_id=run.id, observation_kind=kind,
                                  analyzer=analyzer, captured_at=now, snapshot_json=snapshot,
                                  snapshot_sha256=hashlib.sha256(snapshot.encode("utf-8")).hexdigest()))
        db.flush()
        if not create_initial_findings:
            continue
        if kind == "PERMISSION_REQUESTED":
            category = "Sensitive Permission Capability"
            interpretation = "The declared permission indicates a capability. It does not establish access, collection, or transmission. Necessity has not been established."
        elif kind == "API_REFERENCE":
            category = "Potential Sensitive Data Access"
            interpretation = "A DEX string references a sensitive API indicator. This suggests potential access but does not establish invocation or runtime collection."
        elif kind == "SDK_PRESENT":
            category = "Third-Party SDK Presence"
            interpretation = "A manifest component matches an SDK signature. SDK data access and transmission have not been observed."
        else:
            continue  # A policy document alone establishes no privacy risk or claim.
        create_finding(db, run.id, category, evidence.data_type, interpretation, ANALYSIS_VERSION + ":" + kind,
                       [(evidence.id, "SUPPORTS", "This exact observation supports only the limited interpretation stated above.")])
    return run


def app_provenance(db, app_id, run_id=None):
    if not schema_ready(db):
        return {"status": "migration_required", "runs": [], "findings": []}
    query = select(AnalysisRun).where(AnalysisRun.app_id == app_id)
    if run_id is not None:
        query = query.where(AnalysisRun.id == run_id)
    runs = db.scalars(query.order_by(AnalysisRun.id)).all()
    payload = {"status": "available" if runs else "legacy_unverified", "runs": [], "findings": []}
    for run in runs:
        payload["runs"].append({"id": run.id, "apkSha256": run.apk_sha256, "applicationVersion": run.application_version,
                                 "analysisVersion": run.analysis_version, "startedAt": run.started_at,
                                 "sourceStatus": json.loads(run.source_status_json), "environment": json.loads(run.environment_json)})
        for finding in db.scalars(select(RiskFinding).where(RiskFinding.run_id == run.id).order_by(RiskFinding.id)):
            links = []
            for link in db.scalars(select(FindingEvidence).where(FindingEvidence.finding_id == finding.id).order_by(FindingEvidence.id)):
                record = db.get(EvidenceProvenance, link.evidence_source_id)
                source = db.get(EvidenceSource, link.evidence_source_id)
                if record is None or source is None or source.app_id != run.app_id or record.run_id != run.id or hashlib.sha256(record.snapshot_json.encode("utf-8")).hexdigest() != record.snapshot_sha256:
                    raise ValueError("Evidence provenance integrity check failed.")
                links.append({"relationship": link.relationship, "rationale": link.rationale,
                              "evidenceSourceId": record.evidence_source_id, "observation": json.loads(record.snapshot_json),
                              "capturedAt": record.captured_at, "analyzer": record.analyzer, "snapshotSha256": record.snapshot_sha256})
            if not any(link["relationship"] == "SUPPORTS" for link in links):
                raise ValueError("Finding has no supporting evidence.")
            payload["findings"].append({"id": finding.id, "runId": run.id, "category": finding.finding_category,
                                        "dataCategory": finding.data_category, "interpretation": finding.interpretation,
                                        "ruleId": finding.rule_id, "evidenceStrengthScore": None, "evidence": links})
    # Local import keeps the Phase 1 write path independent of Phase 2 services.
    from fusion_service import enrich_provenance
    return enrich_provenance(db, payload)
