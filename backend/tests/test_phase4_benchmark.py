"""SYNTHETIC implementation fixtures. No real-world accuracy claims."""
from contextlib import closing
from copy import deepcopy
import csv
import io
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sqlalchemy import create_engine,event,select,func
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import IntegrityError
from fastapi.testclient import TestClient
from pydantic import ValidationError
from database import Base,get_db
from models import AppAnalysis
from models_provenance import AnalysisRun
from models_benchmark import *
from benchmark_schemas import *
from evaluation import evaluate_units,ratios,cohen_kappa
from privacy_ontology import canonical_json
import benchmark_service as service
import fusion_service
import main
import reviewer_api
import research_auth
from migrations.phase1_provenance import table_snapshot
from migrations.phase4_benchmark import migrate
from test_phase2_fusion import manifest,code

KEY='synthetic-test-research-key-not-production-123'


def dataset_request(kind='SYNTHETIC',name='Fixture'):
    return DatasetInput(name=name,version='1',dataset_type=kind,finding_categories=['CAPABILITY','POTENTIAL_ACCESS'],
        data_categories=['LOCATION'],protocol_rationale='Synthetic implementation validation protocol',actor='fixture-curator')


def version_request(**changes):
    return VersionInput(**{'name':'Synthetic application','package_name':'test.fixture','application_version':'1','apk_sha256':'a'*64,
        'eligibility_source':'SYNTHETIC','eligibility_notes':'Synthetic fixture, not a real application','free_educational_verified':False,'actor':'fixture-curator',**changes})


def review_units(evidence_ids,second='POSITIVE'):
    common={'data_category':'LOCATION','observation':'Inspected synthetic raw evidence.','interpretation':'Manual fixture conclusion for software validation.',
        'observation_status':'OBSERVED','transmission_status':'NOT_APPLICABLE','disclosure_status':'NOT_APPLICABLE','evidence_ids':evidence_ids}
    return [dict(common,finding_category='CAPABILITY',decision='POSITIVE',access_status='CAPABILITY_ONLY'),
            dict(common,finding_category='POTENTIAL_ACCESS',decision=second,access_status='STATIC_REFERENCE' if second=='POSITIVE' else 'NOT_OBSERVED' if second=='NEGATIVE' else 'UNKNOWN')]


class MetricsTests(unittest.TestCase):
    def unit(self,version,truth,predicted,label='CAPABILITY'):
        return dict(version_id=version,finding_category=label,data_category='LOCATION',truth=truth,predicted=predicted)

    def test_tp_fp_fn_tn_and_rates(self):
        result=evaluate_units([self.unit(1,'POSITIVE',True),self.unit(2,'NEGATIVE',True),self.unit(3,'POSITIVE',False),self.unit(4,'NEGATIVE',False)])
        self.assertEqual([row['classification'] for row in result['units']],['TP','FP','FN','TN'])
        self.assertEqual({key:result['micro'][key] for key in ('TP','FP','FN','TN')},dict(TP=1,FP=1,FN=1,TN=1))
        for key in ('precision','recall','f1','false_positive_rate','false_negative_rate'):self.assertEqual(result['micro'][key],0.5)

    def test_macro_is_mean_per_label_not_mean_counts(self):
        rows=[self.unit(i,'POSITIVE',True) for i in range(3)]+[self.unit(4,'POSITIVE',False,'POTENTIAL_ACCESS')]
        result=evaluate_units(rows)
        self.assertEqual(result['micro']['recall'],0.75)
        self.assertEqual(result['macro']['recall']['value'],0.5)
        self.assertEqual(result['macro']['f1']['value'],0.5)
        self.assertAlmostEqual(result['micro']['f1'],6/7)

    def test_tn_only_has_undefined_precision_recall_and_f1(self):
        result=evaluate_units([self.unit(1,'NEGATIVE',False)])
        for metric in ('precision','recall','f1'):self.assertIsNone(result['micro'][metric])
        self.assertEqual(result['micro']['false_positive_rate'],0)

    def test_fn_only_recall_and_f1_zero_precision_undefined(self):
        metrics=evaluate_units([self.unit(1,'POSITIVE',False)])['micro']
        self.assertIsNone(metrics['precision']);self.assertEqual(metrics['recall'],0);self.assertEqual(metrics['f1'],0)

    def test_uncertain_is_excluded_not_negative(self):
        result=evaluate_units([self.unit(1,'UNCERTAIN',True),self.unit(2,'NEGATIVE',False)])
        self.assertEqual(result['uncertain_units'],1);self.assertEqual(result['micro']['FP'],0)
        self.assertEqual(result['units'][0]['classification'],'EXCLUDED_UNCERTAIN')

    def test_no_ground_truth_stops(self):
        for units in ([],[self.unit(1,'UNCERTAIN',False)]):
            with self.assertRaisesRegex(ValueError,'insufficient'):evaluate_units(units)

    def test_duplicate_units_rejected(self):
        with self.assertRaisesRegex(ValueError,'Duplicate'):evaluate_units([self.unit(1,'POSITIVE',True)]*2)

    def test_kappa_known_fixture(self):
        result=cohen_kappa(['POSITIVE','POSITIVE','NEGATIVE','NEGATIVE'],['POSITIVE','NEGATIVE','NEGATIVE','NEGATIVE'])
        self.assertEqual(result['kappa'],0.5)

    def test_kappa_degenerate_and_small_samples_are_na(self):
        self.assertIsNone(cohen_kappa(['POSITIVE'],['POSITIVE'])['kappa'])
        self.assertIsNone(cohen_kappa(['POSITIVE']*3,['POSITIVE']*3)['kappa'])

    def test_kappa_uses_uncertain_as_explicit_third_category(self):
        self.assertEqual(cohen_kappa(['POSITIVE','NEGATIVE','UNCERTAIN'],['POSITIVE','NEGATIVE','UNCERTAIN'])['kappa'],1)


class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine('sqlite://',poolclass=StaticPool,connect_args={'check_same_thread':False})
        event.listen(self.engine,'connect',lambda db,_:db.execute('PRAGMA foreign_keys=ON'))
        Base.metadata.create_all(self.engine);self.db=Session(self.engine)
        self.addCleanup(self.engine.dispose);self.addCleanup(self.db.close)
        self.dataset=service.create_dataset(self.db,dataset_request())['id']
        self.version=service.create_version(self.db,self.dataset,version_request())['id']
        self.evidence=[]
        for source,raw in [('MANIFEST','<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>'),('CODE','Landroid/location/LocationManager;')]:
            self.evidence.append(service.add_evidence(self.db,self.version,EvidenceInput(source=source,raw_evidence=raw,file_reference='synthetic-artifact',artifact_sha256='b'*64,independent_and_prediction_free=True,actor='fixture-curator'))['id'])
        self.app=AppAnalysis(app_name='Synthetic analysis',package_name='test.fixture',apk_hash='a'*64,version_name='1',risk_score=0)
        self.db.add(self.app);self.db.flush()
        self.run=fusion_service.analyze_bundle(self.db,self.app,fusion_service.make_bundle(self.app,[manifest(),code()],{'MANIFEST':'synthetic','CODE':'synthetic'}))

    def count(self,model):return self.db.scalar(select(func.count()).select_from(model))

    def assign(self,name):
        reviewer=service.create_reviewer(self.db,ReviewerInput(identity=name,metadata={'qualification':'synthetic fixture'},actor='fixture-curator'))['id']
        return service.assign_review(self.db,self.version,AssignmentInput(reviewer_id=reviewer,actor='fixture-curator'))

    def reviewed(self,name,second='POSITIVE'):
        assigned=self.assign(name)
        service.submit_review(self.db,assigned['review_token'],ReviewInput(independent_review=True,predictions_not_seen=True,units=review_units(self.evidence,second)))
        return self.db.scalar(select(ReviewerReview.id).where(ReviewerReview.assignment_id==assigned['assignment_id']))

    def seal(self):
        reviews=[self.reviewed(name) for name in ('reviewer-1','reviewer-2')]
        service.seal_truth(self.db,self.version,SealInput(review_ids=reviews,approval_reason='Independent researcher approval of fixture reviews',actor='fixture-curator'))
        service.freeze_dataset(self.db,self.dataset,ActorInput(actor='fixture-curator'))
        return reviews

    def evaluation_request(self,**changes):
        return EvaluationInput(**{'dataset_type':'SYNTHETIC','selections':[{'benchmark_version_id':self.version,'analysis_run_id':self.run.id}],'actor':'fixture-curator',**changes})

    def test_automated_findings_do_not_become_truth(self):
        self.assertEqual(self.count(GroundTruthFinding),0)
        with self.assertRaisesRegex(ValueError,'Freeze'):service.evaluate(self.db,self.dataset,self.evaluation_request())

    def test_actual_access_cannot_be_grounded_in_manifest_or_code(self):
        dataset=self.db.get(BenchmarkDataset,self.dataset)
        protocol=json.loads(dataset.protocol_json);protocol['finding_categories']=['ACTUAL_ACCESS'];dataset.protocol_json=canonical_json(protocol);self.db.flush()
        token=self.assign('runtime-check')['review_token']
        unit=review_units(self.evidence)[1];unit.update(finding_category='ACTUAL_ACCESS',access_status='OBSERVED')
        with self.assertRaisesRegex(ValueError,'runtime evidence'):service.submit_review(self.db,token,ReviewInput(independent_review=True,predictions_not_seen=True,units=[unit]))
        self.assertEqual(self.count(ReviewerReview),0)

    def test_all_uncertain_ground_truth_blocks_evaluation(self):
        reviews=[]
        for name in ('uncertain-one','uncertain-two'):
            assigned=self.assign(name);units=review_units(self.evidence)
            for unit in units:unit.update(decision='UNCERTAIN',observation_status='UNKNOWN',access_status='UNKNOWN')
            service.submit_review(self.db,assigned['review_token'],ReviewInput(independent_review=True,predictions_not_seen=True,units=units))
            reviews.append(self.db.scalar(select(ReviewerReview.id).where(ReviewerReview.assignment_id==assigned['assignment_id'])))
        service.seal_truth(self.db,self.version,SealInput(review_ids=reviews,approval_reason='Both independent reviewers report uncertainty',actor='fixture'))
        service.freeze_dataset(self.db,self.dataset,ActorInput(actor='fixture'))
        with self.assertRaisesRegex(ValueError,'insufficient'):service.evaluate(self.db,self.dataset,self.evaluation_request())
        self.assertEqual(self.count(EvaluationRun),0)

    def test_error_analysis_notes_do_not_mutate_metrics_or_truth(self):
        self.seal()
        manifest_run=fusion_service.analyze_bundle(self.db,self.app,fusion_service.make_bundle(self.app,[manifest(),code()],{}),'A')
        result=service.evaluate(self.db,self.dataset,self.evaluation_request(selections=[{'benchmark_version_id':self.version,'analysis_run_id':manifest_run.id}]))
        note=ErrorNoteInput(version_id=self.version,finding_category='POTENTIAL_ACCESS',data_category='LOCATION',cause_analysis='Code source excluded by configuration A in this fixture.',actor='fixture')
        self.assertEqual(service.add_error_note(self.db,result['id'],note)['classification'],'FN')
        self.assertEqual(service.read_evaluation(self.db,result['id']),result)
        with self.assertRaisesRegex(ValueError,'actual FP/FN'):service.add_error_note(self.db,result['id'],note.model_copy(update={'finding_category':'CAPABILITY'}))

    def test_extra_automated_fields_are_rejected_by_review_schema(self):
        with self.assertRaises(ValidationError):ReviewInput(independent_review=True,predictions_not_seen=True,units=review_units(self.evidence),predicted_severity='high')

    def test_reviewer_attestation_cannot_be_skipped(self):
        with self.assertRaises(ValidationError):ReviewInput(independent_review=True,predictions_not_seen=False,units=review_units(self.evidence))

    def test_ground_truth_cannot_be_inserted_without_evidence(self):
        reviews=self.seal()
        with self.assertRaises(IntegrityError),self.db.begin_nested():
            self.db.add(GroundTruthFinding(version_id=self.version,review_id=reviews[0],first_evidence_id=None,finding_category='OTHER',data_category='LOCATION',decision_json='{}',approved_by='fixture',approval_reason='fixture reason',approved_at='now'));self.db.flush()

    def test_review_requires_supporting_evidence(self):
        token=self.assign('r')['review_token'];units=review_units(self.evidence);units[0]['evidence_ids']=[999]
        with self.assertRaisesRegex(ValueError,'independent evidence'):service.submit_review(self.db,token,ReviewInput(independent_review=True,predictions_not_seen=True,units=units))
        self.assertEqual(self.count(ReviewerReview),0)

    def test_all_protocol_units_required(self):
        token=self.assign('r')['review_token']
        with self.assertRaisesRegex(ValueError,'every protocol unit'):service.submit_review(self.db,token,ReviewInput(independent_review=True,predictions_not_seen=True,units=review_units(self.evidence)[:1]))

    def test_unknown_cannot_be_negative(self):
        token=self.assign('r')['review_token'];units=review_units(self.evidence,'NEGATIVE');units[1]['access_status']='UNKNOWN'
        with self.assertRaisesRegex(ValueError,'unknown is not negative'):service.submit_review(self.db,token,ReviewInput(independent_review=True,predictions_not_seen=True,units=units))

    def test_packet_has_no_automated_prediction_fields(self):
        assigned=self.assign('r');payload=service.reviewer_payload(self.db,assigned['review_token'])
        self.assertEqual(set(payload),{'application','units','evidence','blinded','submitted','reviewer'})
        serialized=canonical_json(payload)
        for field in ('severity','confidence','risk_score','evidenceStrengthScore','analysis_run_id','classification','predictions','TP','FP','FN'):
            self.assertNotIn('"'+field+'"',serialized)
        self.assertEqual(set(payload['evidence'][0]),{'id','source','raw_evidence','file_reference','artifact_sha256'})

    def test_token_is_only_stored_as_hash(self):
        assigned=self.assign('r');row=self.db.get(ReviewAssignment,assigned['assignment_id'])
        self.assertNotEqual(row.token_sha256,assigned['review_token']);self.assertEqual(len(row.token_sha256),64)

    def test_evidence_locks_at_assignment(self):
        self.assign('r')
        with self.assertRaisesRegex(ValueError,'locked'):service.add_evidence(self.db,self.version,EvidenceInput(source='CODE',raw_evidence='different',file_reference='x',artifact_sha256='b'*64,independent_and_prediction_free=True,actor='fixture'))

    def test_tampered_review_packet_fails_closed(self):
        token=self.assign('r')['review_token'];self.db.get(GroundTruthEvidence,self.evidence[0]).raw_evidence='changed';self.db.flush()
        with self.assertRaisesRegex(ValueError,'integrity'):service.reviewer_payload(self.db,token)

    def test_review_is_immutable(self):
        assigned=self.assign('r');request=ReviewInput(independent_review=True,predictions_not_seen=True,units=review_units(self.evidence))
        service.submit_review(self.db,assigned['review_token'],request)
        with self.assertRaisesRegex(ValueError,'immutable'):service.submit_review(self.db,assigned['review_token'],request)

    def test_agreement_requires_distinct_reviewers(self):
        review=self.reviewed('r')
        with self.assertRaisesRegex(ValueError,'distinct'):service.agreement(self.db,self.version,[review,review])

    def test_disagreement_requires_third_review(self):
        reviews=[self.reviewed('one'),self.reviewed('two','NEGATIVE')]
        request=SealInput(review_ids=reviews,approval_reason='Independent disagreement requires adjudication',actor='fixture')
        with self.assertRaisesRegex(ValueError,'adjudicator'):service.seal_truth(self.db,self.version,request)
        self.assertEqual(self.count(GroundTruthFinding),0)
        third=self.reviewed('three')
        result=service.seal_truth(self.db,self.version,request.model_copy(update={'adjudicator_review_id':third}))
        self.assertTrue(result['sealed'])

    def test_complete_evaluation_contains_reproducibility_and_review_metadata(self):
        self.seal();result=service.evaluate(self.db,self.dataset,self.evaluation_request())
        self.assertEqual(result['validation_type'],'IMPLEMENTATION_VALIDATION')
        self.assertEqual(result['results']['micro']['TP'],2)
        version=result['versions'][0]
        for key in ('apkSha256','applicationVersion','analysisVersion','analysisConfigurationId','enabledSources','ruleVersion','ontologyVersion','environment','startedAt'):
            self.assertIn(key,version['analysis'])
        self.assertIn('reviewer_identity',version['reviews'][0]);self.assertIn('submitted_at',version['reviews'][0])
        self.assertEqual(result,service.read_evaluation(self.db,result['id']))

    def test_synthetic_cannot_be_selected_as_real_world(self):
        self.seal()
        with self.assertRaisesRegex(ValueError,'cannot mix'):service.evaluate(self.db,self.dataset,self.evaluation_request(dataset_type='REAL_WORLD'))
        self.assertEqual(self.count(EvaluationRun),0)

    def test_dataset_type_is_mandatory(self):
        with self.assertRaises(ValidationError):EvaluationInput(selections=[{'benchmark_version_id':1,'analysis_run_id':1}],actor='fixture')

    def test_contaminated_version_type_rejected(self):
        self.seal();self.db.get(BenchmarkVersion,self.version).dataset_type='REAL_WORLD';self.db.flush()
        with self.assertRaisesRegex(ValueError,'contamination'):service.evaluate(self.db,self.dataset,self.evaluation_request())

    def test_wrong_apk_version_or_package_rejected(self):
        self.seal();self.run.apk_sha256='c'*64;self.db.flush()
        with self.assertRaisesRegex(ValueError,'does not match'):service.evaluate(self.db,self.dataset,self.evaluation_request())

    def test_cross_dataset_selection_rejected(self):
        self.seal()
        with self.assertRaisesRegex(ValueError,'every version'):service.evaluate(self.db,self.dataset,self.evaluation_request(selections=[{'benchmark_version_id':999,'analysis_run_id':self.run.id}]))

    def test_dataset_freeze_requires_independent_truth(self):
        with self.assertRaisesRegex(ValueError,'sealed independent'):service.freeze_dataset(self.db,self.dataset,ActorInput(actor='fixture'))

    def test_frozen_dataset_cannot_gain_versions(self):
        self.seal()
        with self.assertRaisesRegex(ValueError,'frozen'):service.create_version(self.db,self.dataset,version_request(apk_sha256='c'*64))

    def test_real_world_registration_requires_actual_apk(self):
        dataset=service.create_dataset(self.db,dataset_request('REAL_WORLD','Real admission test'))['id']
        with self.assertRaisesRegex(ValueError,'retained APK'):service.create_version(self.db,dataset,version_request())

    def test_csv_and_json_export_preserve_units_metrics_and_provenance(self):
        self.seal();result=service.evaluate(self.db,self.dataset,self.evaluation_request())
        rows=list(csv.DictReader(io.StringIO(service.export_csv(result))))
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]['dataset_type'],'SYNTHETIC')
        self.assertEqual(json.loads(rows[0]['metrics_json'])['micro']['TP'],2)
        self.assertIn('version_snapshot',json.loads(rows[0]['reproducibility_json']))

    def test_csv_formula_cells_are_neutralized(self):
        self.seal();self.db.get(BenchmarkDataset,self.dataset).version='=1+1';self.db.flush()
        result=service.evaluate(self.db,self.dataset,self.evaluation_request())
        row=next(csv.DictReader(io.StringIO(service.export_csv(result))))
        self.assertEqual(row['dataset_version'],"'=1+1")

    def test_evaluation_snapshot_corruption_is_rejected(self):
        self.seal();result=service.evaluate(self.db,self.dataset,self.evaluation_request())
        self.db.get(EvaluationRun,result['id']).snapshot_json='{}';self.db.flush()
        with self.assertRaisesRegex(ValueError,'integrity'):service.read_evaluation(self.db,result['id'])

    def test_audit_trail_records_reviewer_and_approval(self):
        self.seal();events=self.db.scalars(select(BenchmarkAuditEvent)).all()
        self.assertEqual(sum(row.event=='INDEPENDENT_REVIEW_SUBMITTED' for row in events),2)
        self.assertTrue(any(row.event=='GROUND_TRUTH_APPROVED' and row.created_at and row.actor for row in events))

    def test_ablation_preserves_truth_and_has_separate_evaluations(self):
        self.seal();truth_hash=self.db.get(BenchmarkVersion,self.version).truth_sha256
        result=service.ablation(self.db,self.dataset,AblationInput(**self.evaluation_request().model_dump()))
        loaded=service.read_ablation(self.db,result['id'])
        self.assertEqual(set(loaded['evaluations']),set('ABCDE'))
        self.assertEqual(set(result['evaluation_ids']),set('ABCDE'));self.assertEqual(self.count(EvaluationRun),5)
        self.assertEqual(self.db.get(BenchmarkVersion,self.version).truth_sha256,truth_hash)
        a=service.read_evaluation(self.db,result['evaluation_ids']['A']);b=service.read_evaluation(self.db,result['evaluation_ids']['B'])
        self.assertEqual(a['results']['micro']['FN'],1);self.assertEqual(b['results']['micro']['FN'],0)

    def test_failed_ablation_rolls_back_all_new_runs_and_results(self):
        self.seal();before=self.count(AnalysisRun)
        with patch.object(service,'evaluate',side_effect=ValueError('injected')):
            with self.assertRaises(ValueError):service.ablation(self.db,self.dataset,AblationInput(**self.evaluation_request().model_dump()))
        self.assertEqual(self.count(AnalysisRun),before);self.assertEqual(self.count(AblationExperiment),0)

    def test_reviewer_api_stays_blinded_and_has_no_prediction_routes(self):
        token=self.assign('api-reviewer')['review_token']
        reviewer_api.app.dependency_overrides[get_db]=lambda:self.db;self.addCleanup(reviewer_api.app.dependency_overrides.clear)
        with patch.dict(os.environ,{'PRIVACYGUARD_RESEARCH_KEY':KEY}),TestClient(reviewer_api.app) as client:
            headers={'Authorization':'Bearer '+token}
            response=client.get('/api/review?blinded=false',headers=headers)
            self.assertEqual(response.status_code,200);self.assertTrue(response.json()['blinded'])
            for path in ('/api/apps/1','/api/benchmark','/api/apps/1/provenance','/openapi.json'):
                self.assertEqual(client.get(path,headers=headers).status_code,404)
            self.assertEqual(client.get('/api/review').status_code,401)

    def test_main_predictions_require_admin_even_with_reviewer_token(self):
        token=self.assign('r')['review_token']
        with patch.dict(os.environ,{'PRIVACYGUARD_RESEARCH_KEY':KEY}),TestClient(main.app) as client:
            for path in ('/api/apps','/api/apps/1','/api/apps/1/provenance','/api/compare','/api/benchmark'):
                self.assertEqual(client.get(path).status_code,403)
                self.assertEqual(client.get(path,headers={'Authorization':'Bearer '+token}).status_code,403)

    def test_main_fails_closed_when_key_removed_after_assignment(self):
        with patch.dict(os.environ,{'PRIVACYGUARD_RESEARCH_KEY':''}),patch.object(research_auth,'assignments_exist',return_value=True),TestClient(main.app) as client:
            self.assertEqual(client.get('/api/apps').status_code,503)

    def test_reviewer_service_requires_research_configuration(self):
        with patch.dict(os.environ,{'PRIVACYGUARD_RESEARCH_KEY':''}),TestClient(reviewer_api.app) as client:
            self.assertEqual(client.get('/api/review',headers={'Authorization':'Bearer x'}).status_code,503)

    def test_admin_api_dynamic_results_and_export(self):
        self.seal();self.db.commit()
        main.app.dependency_overrides[get_db]=lambda:self.db;self.addCleanup(main.app.dependency_overrides.clear)
        with patch.dict(os.environ,{'PRIVACYGUARD_RESEARCH_KEY':KEY}),TestClient(main.app) as client:
            headers={'X-Research-Key':KEY}
            response=client.post(f'/api/benchmark/datasets/{self.dataset}/evaluate',headers=headers,json=self.evaluation_request().model_dump())
            self.assertEqual(response.status_code,200,response.text)
            result=response.json()
            export=client.get(f"/api/benchmark/evaluations/{result['id']}/export?format=json",headers=headers)
            self.assertEqual(export.json(),result)
            self.assertIn('N/A',client.get('/api/benchmark',headers=headers).json()['empirical_status'])


class BenchmarkMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.database=self.root/'phase3.db'
        engine=create_engine('sqlite:///'+self.database.as_posix())
        Base.metadata.create_all(engine,tables=[table for table in Base.metadata.sorted_tables if table not in BENCHMARK_TABLES])
        with Session(engine) as db:
            app=AppAnalysis(app_name='Preserve graph',package_name='test.fixture',apk_hash='a'*64,version_name='1');db.add(app);db.flush()
            run=fusion_service.analyze_bundle(db,app,fusion_service.make_bundle(app,[manifest(),code()],{}))
            import graph_service
            graph_service.materialize_graph(db,app.id,run.id);db.commit()
        engine.dispose()

    def snapshot(self):
        with closing(sqlite3.connect(self.database)) as db:return table_snapshot(db)

    def test_backup_and_migration_preserve_populated_graphs(self):
        before=self.snapshot();result=migrate(self.database,self.root/'backups');after=self.snapshot()
        self.assertEqual({name:after[name] for name in before},before)
        self.assertEqual(len(after),len(before)+11)
        with closing(sqlite3.connect(result['backup'])) as db:self.assertEqual(table_snapshot(db),before)
        self.assertEqual(migrate(self.database,self.root/'backups')['status'],'already_applied')

    def test_conflicting_schema_stops_without_mutation(self):
        with closing(sqlite3.connect(self.database)) as db:db.execute('CREATE TABLE benchmark_datasets (wrong TEXT)');db.commit()
        before=self.database.read_bytes()
        with self.assertRaisesRegex(ValueError,'conflicting'):migrate(self.database,self.root/'backups')
        self.assertEqual(self.database.read_bytes(),before)


if __name__=='__main__':unittest.main()
