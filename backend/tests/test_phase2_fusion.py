"""SYNTHETIC implementation validation, never empirical benchmark accuracy."""
from contextlib import closing
from copy import deepcopy
import json
import os
from pathlib import Path
import random
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from sqlalchemy import create_engine, event, select, func
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import IntegrityError
from fastapi.testclient import TestClient
from database import Base, get_db
import models
import models_evidence
from models_provenance import AnalysisRun, EvidenceProvenance, RiskFinding, FindingEvidence, PROVENANCE_TABLES
from models_fusion import AnalysisConfiguration, FusionRun, NormalizedEvidence, FindingAssessment, FUSION_TABLES
from privacy_ontology import configuration, canonical_json, digest, Finding, PRESETS
from normalization import normalize, normalize_sources
from fusion_engine import fuse
from adapter import adapt_legacy_records
import fusion_service
import provenance
import main
from migrations.phase1_provenance import table_snapshot, migrate as phase1_migrate
from migrations.phase2_fusion import migrate


def manifest(permission='ACCESS_FINE_LOCATION'):
    return {'source': 'MANIFEST', 'kind': 'permission', 'raw_evidence': f'<uses-permission android:name="android.permission.{permission}"/>',
            'file_reference': 'AndroidManifest.xml', 'description': 'Declared permission'}


def code(indicator='LocationManager'):
    return {'source': 'CODE', 'kind': 'api_reference', 'indicator': indicator, 'raw_evidence': f'Landroid/{indicator};',
            'file_reference': 'classes.dex', 'description': 'Static reference'}


def sdk():
    return {'source': 'SDK', 'kind': 'sdk_presence', 'sdk_name': 'Example Analytics', 'signature': 'com.example.analytics',
            'raw_evidence': 'com.example.analytics.Init', 'file_reference': 'AndroidManifest.xml', 'description': 'SDK signature'}


def network(payload=True):
    item = {'source': 'NETWORK', 'kind': 'payload_observation' if payload else 'domain_observation',
            'raw_evidence': json.dumps({'domain': 'analytics.example.com', 'direction': 'outbound', 'payload': {'location': {'latitude': 6.9, 'longitude': 79.8}}}),
            'file_reference': 'synthetic_capture.json#request-1', 'description': 'Synthetic request observation'}
    if payload:
        item.update(data_category='LOCATION', payload_pointer='/location', category_basis='Synthetic fixture has known coordinate pair',
                    annotated_by='synthetic-test', captured_at='2026-09-28T12:00:00Z', capture_sha256='c'*64)
    return item


def claim(source='POLICY', state='denies'):
    text = 'We do not collect location.' if state == 'denies' else 'We collect location.'
    return {'source': source, 'kind': 'claim', 'data_category': 'LOCATION', 'scope': 'collection', 'claim_state': state,
            'quote': text, 'raw_evidence': text, 'file_reference': 'https://example.com/privacy', 'description': 'Retained claim',
            'annotation_method': 'manual_evidence_review', 'annotated_by': 'synthetic-reviewer'}


def all_sources():
    return [manifest(), code(), sdk(), network(), claim(), claim('DATA_SAFETY', 'collects')]


def result(records, preset='E'):
    config = configuration(preset)
    return fuse(normalize_sources(records, config['enabled_sources']), config)


class NormalizationTests(unittest.TestCase):
    def test_all_six_source_families(self):
        rows = normalize_sources(all_sources(), configuration('E')['enabled_sources'])
        self.assertEqual({row['source'] for row in rows}, set(configuration('E')['enabled_sources']))
        self.assertTrue(all(row['raw_evidence'] and row['file_reference'] for row in rows))

    def test_manifest_capability_not_collection(self):
        item = normalize(manifest())
        self.assertEqual(item['behavior'], 'PERMISSION_REQUESTED')
        self.assertIsNone(item['claim'])
        self.assertEqual(item['data_category'], 'LOCATION')

    def test_advertising_identifier_is_not_device_identifier(self):
        permission=manifest('AD_ID')
        permission['raw_evidence']=permission['raw_evidence'].replace('android.permission.AD_ID','com.google.android.gms.permission.AD_ID')
        self.assertEqual(normalize(permission)['data_category'], 'ADVERTISING_IDENTIFIER')
        self.assertEqual(normalize(manifest('AD_ID'))['data_category'], 'UNKNOWN')
        self.assertEqual(normalize(code('AdvertisingIdClient'))['data_category'], 'ADVERTISING_IDENTIFIER')
        self.assertEqual(normalize(code('getDeviceId'))['data_category'], 'DEVICE_IDENTIFIER')

    def test_unknown_permission_does_not_match_substring(self):
        self.assertEqual(normalize(manifest('FAKE_ACCESS_FINE_LOCATION'))['data_category'], 'UNKNOWN')

    def test_existing_photo_access_is_not_camera_capability(self):
        self.assertEqual(normalize(manifest('READ_MEDIA_IMAGES'))['data_category'],'UNKNOWN')
        self.assertEqual(normalize(code('MediaStore.Images'))['data_category'],'UNKNOWN')

    def test_malformed_record_rejected_explicitly(self):
        with self.assertRaisesRegex(ValueError,'object'):normalize_sources([None],['MANIFEST'])

    def test_adapter_does_not_promote_legacy_interpretations(self):
        record={'source_type':'manifest','evidence_category':'permission','raw_evidence':manifest()['raw_evidence'],
                'file_reference':'AndroidManifest.xml','description':'Declared permission',
                'educational_justification':'excessive','confidence':0.99,'data_type':'INVENTED'}
        item=normalize(adapt_legacy_records([record])[0])
        self.assertEqual(item['attributes']['necessity'],'unknown')
        self.assertEqual(item['data_category'],'LOCATION')

    def test_ambiguous_reference_stays_unknown(self):
        self.assertEqual(normalize(code('age'))['data_category'], 'UNKNOWN')
        self.assertEqual(result([code('age')]), [])

    def test_api_reference_cannot_be_promoted_to_access(self):
        item = code()
        item['kind'] = 'API_ACCESS'
        with self.assertRaises(ValueError): normalize(item)

    def test_absent_indicator_rejected(self):
        item = code(); item['raw_evidence'] = 'unrelated'
        with self.assertRaisesRegex(ValueError, 'absent'): normalize(item)

    def test_sdk_presence_never_becomes_third_party_access(self):
        self.assertEqual(normalize(sdk())['behavior'], 'SDK_PRESENT')
        item = sdk(); item['kind'] = 'THIRD_PARTY_ACCESS'
        with self.assertRaises(ValueError): normalize(item)

    def test_domain_alone_is_not_transmission(self):
        item = network(False)
        item['data_category'] = 'LOCATION'
        row = normalize(item)
        self.assertEqual(row['behavior'], 'CONTACTS_DOMAIN')
        self.assertEqual(row['data_category'], 'UNKNOWN')
        self.assertEqual(result([item]), [])

    def test_payload_requires_capture_and_bound_value(self):
        for key in ('category_basis', 'annotated_by', 'payload_pointer', 'capture_sha256', 'captured_at'):
            item = network(); del item[key]
            with self.subTest(key=key), self.assertRaises(ValueError): normalize(item)
        for pointer in ('/absent', ''):
            item = network(); item['payload_pointer'] = pointer
            with self.subTest(pointer=pointer), self.assertRaises(ValueError): normalize(item)

    def test_inbound_payload_is_not_outbound_transmission(self):
        item = network(); raw=json.loads(item['raw_evidence']); raw['direction']='inbound'; item['raw_evidence']=json.dumps(raw)
        with self.assertRaisesRegex(ValueError, 'outbound'): normalize(item)

    def test_claim_requires_verbatim_quote_and_manual_annotation(self):
        item = claim(); item['quote'] = 'Not in document'
        with self.assertRaisesRegex(ValueError, 'exactly'): normalize(item)
        item = claim(); item['annotation_method']='llm_generated'
        with self.assertRaisesRegex(ValueError, 'manual'): normalize(item)

    def test_unknown_and_not_mentioned_are_not_denials(self):
        for state in ('unknown', 'not_mentioned'):
            item = claim(state=state)
            self.assertIn(normalize(item)['claim'], ('UNKNOWN', 'NOT_MENTIONED'))
            self.assertFalse(any(f['category'] == Finding.DISCLOSURE.value for f in result([network(), item])))

    def test_document_alone_is_not_a_claim(self):
        item = claim(); item['kind'] = 'document'
        self.assertEqual(normalize(item)['claim'], 'UNKNOWN')

    def test_excluded_source_is_filtered_before_semantic_normalization(self):
        bad = network(); bad['payload_pointer']='/missing'
        self.assertEqual(result([manifest(), bad], 'A'), result([manifest()], 'A'))
        with self.assertRaises(ValueError): result([manifest(), bad], 'D')

    def test_legacy_sdk_is_normalized_as_separate_source(self):
        legacy={'source_type':'manifest','evidence_category':'sdk_presence','data_type':'Example SDK','raw_evidence':'com.example.Init','file_reference':'AndroidManifest.xml','description':'SDK signature'}
        self.assertEqual(adapt_legacy_records([legacy])[0]['source'], 'SDK')
        self.assertEqual(result(adapt_legacy_records([legacy]), 'A'), [])

    def test_legacy_mock_claims_are_rejected(self):
        with self.assertRaises(ValueError): adapt_legacy_records([{'source_type':'data_safety','evidence_category':'location_data_safety'}])


class FusionRuleTests(unittest.TestCase):
    def test_manifest_only_needs_context_before_unnecessary_label(self):
        self.assertEqual(result([manifest()])[0]['category'], Finding.CAPABILITY.value)
        item=manifest(); item.update(necessity='excessive', necessity_basis='Not expected by category profile', necessity_analyzer='fixture-profile-v1')
        finding=result([item])[0]
        self.assertEqual(finding['category'], Finding.UNNECESSARY_PERMISSION.value)
        self.assertEqual(finding['evidence_strength_score'], .4)
        self.assertIn('does not establish collection', finding['interpretation'])

    def test_static_reference_plus_denial_is_not_collection_contradiction(self):
        for records in ([manifest(), claim()], [code(), claim()], [sdk(), claim()]):
            with self.subTest(records=records):
                self.assertFalse(any(f['category']==Finding.DISCLOSURE.value for f in result(records)))

    def test_corroboration_is_bounded_and_not_probability(self):
        single=result([code()])[0]
        combined=result([manifest(), code()])[0]
        self.assertEqual(single['evidence_strength_score'], .6)
        self.assertEqual(combined['evidence_strength_score'], .7)
        self.assertIn('runtime collection are not established',combined['interpretation'])
        self.assertIn('CORROBORATES', [rel for _,rel in combined['links']])
        self.assertNotIn('probability',combined)

    def test_duplicate_evidence_never_increases_strength(self):
        records=all_sources()
        self.assertEqual(result(records), result(records * 5))

    def test_payload_transmission_requires_domain_and_category(self):
        finding=result([network()])[0]
        self.assertEqual(finding['category'], Finding.TRANSMISSION.value)
        self.assertEqual(finding['domain'],'analytics.example.com')
        self.assertEqual(finding['data_category'],'LOCATION')
        self.assertEqual(finding['evidence_strength_score'],.9)

    def test_explicit_denial_and_payload_yield_potential_inconsistency(self):
        findings=result([network(),claim()])
        disclosure=next(f for f in findings if f['category']==Finding.DISCLOSURE.value)
        self.assertEqual(disclosure['evidence_strength_score'],.7)
        self.assertIn('CONTRADICTS',[rel for _,rel in disclosure['links']])
        self.assertIn('no legal violation',disclosure['interpretation'])

    def test_claims_can_conflict_without_proving_behavior(self):
        findings=result([claim(),claim('DATA_SAFETY','collects')])
        self.assertEqual(len(findings),1)
        self.assertIn('not proof of collection',findings[0]['interpretation'])

    def test_no_detection_is_not_over_disclosure(self):
        self.assertEqual(result([claim(state='collects')]),[])

    def test_reordered_inputs_give_byte_identical_semantic_output(self):
        records=all_sources(); expected=canonical_json(result(records))
        for seed in range(10):
            random.Random(seed).shuffle(records)
            self.assertEqual(canonical_json(result(records)),expected)

    def test_different_python_hash_seeds_have_same_output(self):
        script="import sys,json;sys.path.insert(0,sys.argv[1]);from normalization import normalize_sources;from privacy_ontology import configuration,canonical_json;from fusion_engine import fuse;c=configuration('E');print(canonical_json(fuse(normalize_sources(json.loads(sys.stdin.read()),c['enabled_sources']),c)))"
        outputs=[]
        for seed in ('1','123'):
            completed=subprocess.run([sys.executable,'-B','-c',script,str(BACKEND)],input=json.dumps(all_sources()),text=True,capture_output=True,env={**os.environ,'PYTHONHASHSEED':seed},timeout=15)
            self.assertEqual(completed.returncode,0,completed.stderr); outputs.append(completed.stdout)
        self.assertEqual(*outputs)

    def test_configuration_tampering_is_rejected(self):
        config=configuration('E'); config['base_strength_points']['NETWORK']=99
        with self.assertRaises(ValueError): fuse([],config)


class FusionPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine('sqlite://',poolclass=StaticPool,connect_args={'check_same_thread':False})
        event.listen(self.engine,'connect',lambda db,_:db.execute('PRAGMA foreign_keys=ON'))
        Base.metadata.create_all(self.engine)
        self.db=Session(self.engine)
        self.addCleanup(self.engine.dispose);self.addCleanup(self.db.close)
        self.app=models.AppAnalysis(app_name='Synthetic',apk_hash='a'*64,version_name='1')
        self.db.add(self.app);self.db.flush()
        self.bundle=fusion_service.make_bundle(self.app,all_sources(),{source:'synthetic_fixture' for source in configuration('E')['enabled_sources']})

    def count(self,model):return self.db.scalar(select(func.count()).select_from(model))

    def client(self):
        main.app.dependency_overrides[get_db]=lambda:self.db
        self.addCleanup(main.app.dependency_overrides.clear)
        return TestClient(main.app)

    def test_same_bundle_configuration_same_semantics_distinct_runs(self):
        one=fusion_service.analyze_bundle(self.db,self.app,self.bundle)
        two=fusion_service.analyze_bundle(self.db,self.app,self.bundle)
        rows=[self.db.get(FusionRun,run.id) for run in (one,two)]
        self.assertNotEqual(one.id,two.id)
        self.assertEqual(rows[0].semantic_output_sha256,rows[1].semantic_output_sha256)
        self.assertEqual(rows[0].normalized_input_sha256,rows[1].normalized_input_sha256)
        self.assertEqual(self.count(AnalysisConfiguration),1)
        payload=provenance.app_provenance(self.db,self.app.id)
        self.assertEqual(len(payload['runs']),2)
        self.assertTrue(all(f['evidenceStrengthScore'] is not None for f in payload['findings']))

    def test_ablation_source_isolation_and_traceability(self):
        baseline=fusion_service.analyze_bundle(self.db,self.app,self.bundle)
        runs=fusion_service.ablate(self.db,self.app,baseline.id,list(PRESETS))
        outputs={}
        for preset,run in zip(PRESETS,runs):
            metadata=self.db.get(FusionRun,run.id)
            self.assertEqual(metadata.replay_of_run_id,baseline.id)
            self.assertEqual(metadata.analysis_configuration_id,configuration(preset)['id'])
            self.assertEqual(run.apk_sha256,self.app.apk_hash)
            self.assertEqual(run.application_version,'1')
            normalized=[json.loads(row.normalized_json) for row in self.db.scalars(select(NormalizedEvidence).where(NormalizedEvidence.run_id==run.id))]
            self.assertEqual({item['source'] for item in normalized},set(configuration(preset)['enabled_sources']))
            outputs[preset]=[row.finding_category for row in self.db.scalars(select(RiskFinding).where(RiskFinding.run_id==run.id))]
        self.assertNotIn(Finding.TRANSMISSION.value,outputs['C'])
        self.assertIn(Finding.TRANSMISSION.value,outputs['D'])
        self.assertNotIn(Finding.DISCLOSURE.value,outputs['D'])
        self.assertIn(Finding.DISCLOSURE.value,outputs['E'])
        self.assertEqual(self.db.get(FusionRun,runs[-1].id).semantic_output_sha256,self.db.get(FusionRun,baseline.id).semantic_output_sha256)

    def test_wrong_hash_or_version_rejected_before_any_run(self):
        for key,value in (('apk_sha256','b'*64),('application_version','2')):
            bundle=deepcopy(self.bundle);bundle[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):fusion_service.analyze_bundle(self.db,self.app,bundle)
        self.assertEqual(self.count(AnalysisRun),0)

    def test_other_app_run_cannot_be_replayed(self):
        baseline=fusion_service.analyze_bundle(self.db,self.app,self.bundle)
        other=models.AppAnalysis(app_name='Other',apk_hash='a'*64,version_name='1');self.db.add(other);self.db.flush()
        with self.assertRaises(ValueError):fusion_service.ablate(self.db,other,baseline.id,['A'])

    def test_corrupted_bundle_blocks_replay(self):
        run=fusion_service.analyze_bundle(self.db,self.app,self.bundle)
        self.db.get(FusionRun,run.id).bundle_json='{}';self.db.flush()
        with self.assertRaisesRegex(ValueError,'integrity'):fusion_service.ablate(self.db,self.app,run.id,['A'])

    def test_corrupted_normalization_blocks_read(self):
        run=fusion_service.analyze_bundle(self.db,self.app,self.bundle)
        row=self.db.scalar(select(NormalizedEvidence));row.normalized_json='{}';self.db.flush()
        with self.assertRaisesRegex(ValueError,'integrity'):provenance.app_provenance(self.db,self.app.id)

    def test_modified_unlinked_observation_blocks_read(self):
        bundle=fusion_service.make_bundle(self.app,[network(False)],{})
        fusion_service.analyze_bundle(self.db,self.app,bundle)
        row=self.db.scalar(select(EvidenceProvenance))
        snapshot=json.loads(row.snapshot_json);snapshot['raw_evidence']='different'
        row.snapshot_json=canonical_json(snapshot);row.snapshot_sha256=digest(snapshot);self.db.flush()
        with self.assertRaisesRegex(ValueError,'snapshot integrity'):provenance.app_provenance(self.db,self.app.id)

    def test_changed_rule_version_blocks_read(self):
        run=fusion_service.analyze_bundle(self.db,self.app,self.bundle)
        self.db.get(FusionRun,run.id).rule_version='unknown';self.db.flush()
        with self.assertRaisesRegex(ValueError,'integrity'):provenance.app_provenance(self.db,self.app.id)

    def test_caller_rollback_removes_released_savepoint_writes(self):
        self.db.commit()
        fusion_service.analyze_bundle(self.db,self.app,self.bundle)
        self.db.rollback()
        self.assertEqual(self.count(FusionRun),0)
        self.assertEqual(self.count(AnalysisRun),0)
        self.assertEqual(self.count(models_evidence.EvidenceSource),0)

    def test_replay_cannot_change_bundle(self):
        baseline=fusion_service.analyze_bundle(self.db,self.app,self.bundle)
        changed=deepcopy(self.bundle);changed['records']=[manifest()]
        with self.assertRaisesRegex(ValueError,'unchanged'):fusion_service.analyze_bundle(self.db,self.app,changed,'A',baseline.id)

    def test_api_validation_failure_rolls_back_new_run(self):
        self.db.commit()
        with self.client() as client, patch.object(provenance,'app_provenance',side_effect=ValueError('integrity failure')):
            response=client.post(f'/api/apps/{self.app.id}/fusion',json=self.bundle)
        self.assertEqual(response.status_code,422)
        self.assertEqual(self.count(AnalysisRun),0)

    def test_report_separates_configurations_and_labels_scores(self):
        from llm_report_generator import generate_report
        fusion_service.analyze_bundle(self.db,self.app,self.bundle,'A')
        fusion_service.analyze_bundle(self.db,self.app,self.bundle,'E')
        report=generate_report(self.app.id,self.db)['markdown']
        self.assertIn('configuration A',report)
        self.assertIn('configuration E',report)
        self.assertIn('Evidence Strength Score: 0.90',report)
        self.assertIn('not a probability',report)

    def test_failed_persistence_leaves_no_partial_run(self):
        with patch.object(provenance,'create_finding',side_effect=RuntimeError('injected failure')):
            with self.assertRaises(RuntimeError):fusion_service.analyze_bundle(self.db,self.app,self.bundle)
        self.assertEqual(self.count(AnalysisRun),0)
        self.assertEqual(self.count(models_evidence.EvidenceSource),0)
        self.assertEqual(self.count(AnalysisConfiguration),0)

    def test_invalid_later_ablation_rolls_back_all_new_runs(self):
        bundle=deepcopy(self.bundle); next(item for item in bundle['records'] if item['source']=='NETWORK')['payload_pointer']='/missing'
        baseline=fusion_service.analyze_bundle(self.db,self.app,bundle,'A')
        before=self.count(AnalysisRun)
        with self.assertRaises(ValueError):fusion_service.ablate(self.db,self.app,baseline.id,['B','D'])
        self.assertEqual(self.count(AnalysisRun),before)

    def test_api_import_and_ablation(self):
        self.db.commit()
        with self.client() as client:
            configs=client.get('/api/analysis-configurations');self.assertEqual(configs.status_code,200)
            self.assertEqual(len(configs.json()['configurations']),5)
            response=client.post(f'/api/apps/{self.app.id}/fusion',json={**self.bundle,'configuration':'E'})
            self.assertEqual(response.status_code,200,response.text)
            run=response.json()['run_id']
            response=client.post(f'/api/apps/{self.app.id}/ablation',json={'source_run_id':run,'configurations':['A','B','C','D','E']})
            self.assertEqual(response.status_code,200,response.text)
            self.assertEqual(len(response.json()['run_ids']),5)

    def test_api_rejects_unanchored_claim_without_writing(self):
        bundle=deepcopy(self.bundle);next(item for item in bundle['records'] if item['source']=='POLICY')['quote']='invented'
        self.db.commit()
        with self.client() as client:
            response=client.post(f'/api/apps/{self.app.id}/fusion',json=bundle)
            self.assertEqual(response.status_code,422,response.text)
        self.assertEqual(self.count(AnalysisRun),0)


class Phase2MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.database=self.root/'phase1.db'
        engine=create_engine('sqlite:///'+self.database.as_posix())
        legacy_names = {value.__tablename__ for module in (models, models_evidence)
                        for value in vars(module).values() if isinstance(value, type) and hasattr(value, '__tablename__')}
        Base.metadata.create_all(engine,tables=[table for table in Base.metadata.sorted_tables if table.name in legacy_names or table in PROVENANCE_TABLES])
        with Session(engine) as db:
            app=models.AppAnalysis(app_name='Preserve Phase 1',apk_hash='a'*64,version_name='1');db.add(app);db.flush()
            provenance.persist_observations(db,app,[{'source_type':'manifest','evidence_category':'permission','data_type':'Location','description':'Declared','raw_evidence':'permission','file_reference':'AndroidManifest.xml'}],{})
            db.commit()
        engine.dispose()

    def snapshot(self):
        with closing(sqlite3.connect(self.database)) as db:return table_snapshot(db)

    def test_preserves_populated_phase1_and_backup(self):
        before=self.snapshot();result=migrate(self.database,self.root/'backups');after=self.snapshot()
        self.assertEqual({name:after[name] for name in before},before)
        self.assertEqual(len(after),len(before)+4)
        with closing(sqlite3.connect(result['backup'])) as db:self.assertEqual(table_snapshot(db),before)
        self.assertEqual(migrate(self.database,self.root/'backups')['status'],'already_applied')

    def test_conflicting_phase2_table_stops_without_writing(self):
        with closing(sqlite3.connect(self.database)) as db:db.execute('CREATE TABLE analysis_configurations (wrong TEXT)');db.commit()
        before=self.database.read_bytes()
        with self.assertRaisesRegex(ValueError,'conflicting'):migrate(self.database,self.root/'backups')
        self.assertEqual(self.database.read_bytes(),before)

    def test_missing_phase1_prerequisite_is_refused(self):
        with closing(sqlite3.connect(self.database)) as db:
            db.execute('ALTER TABLE evidence_provenance ADD COLUMN unexpected TEXT');db.commit()
        before=self.database.read_bytes()
        with self.assertRaisesRegex(ValueError,'Prerequisite'):migrate(self.database,self.root/'backups')
        self.assertEqual(self.database.read_bytes(),before)


if __name__=='__main__':unittest.main()
