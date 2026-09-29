"""SYNTHETIC graph implementation tests; not empirical privacy accuracy."""
from contextlib import closing
from copy import deepcopy
import json
from pathlib import Path
import random
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import create_engine, event, select, func, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from database import Base, get_db
from models import AppAnalysis
from models_evidence import AppVersion
from models_provenance import AnalysisRun
from models_fusion import FUSION_TABLES
from models_graph import GraphRun, GraphNode, GraphEdge, GRAPH_TABLES
from models_benchmark import BENCHMARK_TABLES
from privacy_ontology import configuration, digest, canonical_json
from normalization import normalize_sources
from fusion_engine import fuse
from graph_engine import build_graph, validate_graph, explain_graph
import graph_service
import fusion_service
import main
from migrations.phase1_provenance import table_snapshot
from migrations.phase3_graph import migrate
from test_phase2_fusion import manifest, code, sdk, network, claim, all_sources


def project(records, preset='E'):
    config = configuration(preset)
    evidence = normalize_sources(records, config['enabled_sources'])
    findings = fuse(evidence, config)
    return build_graph(evidence, findings), evidence, findings


class GraphSemanticTests(unittest.TestCase):
    def setUp(self):
        self.graph, self.evidence, self.findings = project(all_sources())

    def invalid(self, graph, message):
        with self.assertRaisesRegex(ValueError, message): validate_graph(graph, self.evidence, self.findings)

    def test_manifest_indicates_capability_only(self):
        graph, _, _ = project([manifest()])
        relations = {edge['relation'] for edge in graph['edges']}
        self.assertEqual(relations, {'INDICATES_CAPABILITY','SUPPORTED_BY'})

    def test_static_code_never_becomes_runtime_access(self):
        graph, _, _ = project([code()])
        self.assertIn('REFERENCES_API_FOR', {edge['relation'] for edge in graph['edges']})
        self.assertNotIn('ACCESSES_DATA', canonical_json(graph))
        self.assertIn('runtime access unverified', canonical_json(graph))

    def test_sdk_signature_is_attribution_not_access(self):
        graph, _, _ = project([sdk()])
        self.assertEqual({edge['relation'] for edge in graph['edges']},{'ATTRIBUTED_TO','SUPPORTED_BY'})

    def test_domain_alone_has_no_sensitive_transmission(self):
        graph, _, _ = project([network(False)])
        self.assertEqual([edge['relation'] for edge in graph['edges']], ['CONTACTS'])
        self.assertEqual({node['type'] for node in graph['nodes']},{'EVIDENCE_SOURCE','DOMAIN'})

    def test_payload_transmission_terminates_at_domain_and_shares_anchor(self):
        graph, _, _ = project([network()])
        nodes={node['id']:node for node in graph['nodes']}
        transmission=next(edge for edge in graph['edges'] if edge['relation']=='TRANSMITTED_TO')
        payload=next(edge for edge in graph['edges'] if edge['relation']=='HAS_PAYLOAD_CATEGORY')
        self.assertEqual(nodes[transmission['source']]['type'],'DATA_CATEGORY')
        self.assertEqual(nodes[transmission['target']]['type'],'DOMAIN')
        self.assertEqual(transmission['evidence_id'],payload['evidence_id'])
        self.assertEqual(transmission['source'],payload['target'])

    def test_explanations_preserve_payload_path_without_code_flow_claim(self):
        paths=explain_graph(self.graph)
        path=next(path for path in paths if len(path['edge_ids'])==2)
        self.assertIn('HAS_PAYLOAD_CATEGORY',path['text'])
        self.assertIn('TRANSMITTED_TO',path['text'])
        self.assertIn('not a proven code-to-network data flow',path['text'])
        self.assertEqual(len(path['evidence_ids']),1)
        self.assertEqual(paths,explain_graph(self.graph))

    def test_policy_claim_is_not_behavior(self):
        graph, _, _ = project([claim(state='collects')])
        self.assertEqual([edge['relation'] for edge in graph['edges']],['CLAIMS_COLLECTION'])

    def test_contradiction_and_corroboration_roles_preserved(self):
        self.assertIn('CONTRADICTED_BY',{edge['relation'] for edge in self.graph['edges']})
        self.assertTrue(any(edge['relation']=='SUPPORTED_BY' and edge['qualification'].startswith('CORROBORATES;') for edge in self.graph['edges']))

    def test_unknown_documents_retained_outside_graph_without_orphans(self):
        records=[{'source':'POLICY','kind':'document','raw_evidence':'Document only','file_reference':'policy.txt','description':'No claim annotation'}]
        graph, evidence, _=project(records)
        self.assertEqual(graph['nodes'],[]);self.assertEqual(graph['edges'],[])
        self.assertEqual(graph['omitted_evidence'][0]['evidence_id'],evidence[0]['id'])

    def test_reordering_and_duplicates_keep_semantic_hash(self):
        records=all_sources()
        for seed in range(5):
            random.Random(seed).shuffle(records)
            self.assertEqual(digest(project(records+records)[0]),digest(self.graph))

    def test_invalid_node_layer_rejected(self):
        graph=deepcopy(self.graph);graph['nodes'][0]['layer']='INVENTED'
        self.invalid(graph,'type/layer')

    def test_invalid_node_type_rejected(self):
        graph=deepcopy(self.graph);graph['nodes'][0]['type']='PERSON'
        self.invalid(graph,'type/layer')

    def test_duplicate_node_rejected(self):
        graph=deepcopy(self.graph);graph['nodes'].append(graph['nodes'][0])
        self.invalid(graph,'Duplicate graph node')

    def test_orphan_rejected(self):
        graph=deepcopy(self.graph);node=deepcopy(graph['nodes'][0]);node['id']='orphan';graph['nodes'].append(node)
        self.invalid(graph,'Orphan')

    def test_dangling_edge_rejected(self):
        graph=deepcopy(self.graph);graph['edges'][0]['target']='missing'
        self.invalid(graph,'Dangling')

    def test_reversed_transmission_rejected(self):
        graph=deepcopy(self.graph);edge=next(edge for edge in graph['edges'] if edge['relation']=='TRANSMITTED_TO')
        edge['source'],edge['target']=edge['target'],edge['source']
        self.invalid(graph,'endpoints')

    def test_source_to_category_transmission_rejected(self):
        graph=deepcopy(self.graph);edge=next(edge for edge in graph['edges'] if edge['relation']=='HAS_PAYLOAD_CATEGORY')
        edge['relation']='TRANSMITTED_TO'
        self.invalid(graph,'endpoints')

    def test_manifest_actual_access_rejected(self):
        graph=deepcopy(self.graph);edge=next(edge for edge in graph['edges'] if edge['relation']=='INDICATES_CAPABILITY')
        edge['relation']='ACCESSES_DATA'
        self.invalid(graph,'runtime adapter')

    def test_valid_shape_with_invented_domain_rejected(self):
        graph=deepcopy(self.graph);next(node for node in graph['nodes'] if node['type']=='DOMAIN')['label']='invented.example'
        self.invalid(graph,'deterministic projection')

    def test_edge_without_source_evidence_rejected(self):
        graph=deepcopy(self.graph);graph['edges'][0]['evidence_id']='missing'
        self.invalid(graph,'supporting evidence')


class GraphPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine('sqlite://',poolclass=StaticPool,connect_args={'check_same_thread':False})
        event.listen(self.engine,'connect',lambda db,_:db.execute('PRAGMA foreign_keys=ON'))
        Base.metadata.create_all(self.engine)
        self.db=Session(self.engine)
        self.addCleanup(self.engine.dispose);self.addCleanup(self.db.close)
        self.app=AppAnalysis(app_name='Synthetic graph',apk_hash='a'*64,version_name='1')
        self.db.add(self.app);self.db.flush()
        self.run=self.analyze(self.app)

    def analyze(self, app, preset='E'):
        return fusion_service.analyze_bundle(self.db,app,fusion_service.make_bundle(app,all_sources(),{}),preset)

    def count(self, model):return self.db.scalar(select(func.count()).select_from(model))

    def build(self, run=None):return graph_service.materialize_graph(self.db,self.app.id,(run or self.run).id)

    def test_round_trip_all_layers_edges_and_hashes(self):
        graph=self.build()
        self.assertEqual({node['layer'] for node in graph['nodes']},{'OBSERVED','DERIVED'})
        self.assertEqual(graph,graph_service.read_graph(self.db,self.app.id,graph['app_version_id'],self.run.id))
        self.assertEqual(len(graph['edges']),self.count(GraphEdge))
        self.assertTrue(all(edge.evidence_source_id for edge in self.db.scalars(select(GraphEdge))))

    def test_repeat_build_is_idempotent(self):
        first=self.build();counts=(self.count(GraphNode),self.count(GraphEdge))
        self.assertEqual(first,self.build())
        self.assertEqual(counts,(self.count(GraphNode),self.count(GraphEdge)))
        self.assertEqual(self.count(AppVersion),1)

    def test_new_version_does_not_fabricate_uncomputed_counts(self):
        graph=self.build();version=self.db.get(AppVersion,graph['app_version_id'])
        self.assertIsNone(version.risk_score)
        self.assertIsNone(version.data_flow_count)
        self.assertIsNone(version.policy_changed)

    def test_existing_version_metadata_is_preserved(self):
        version=AppVersion(app_id=self.app.id,apk_hash='a'*64,version_name='1',risk_score=37,permission_count=12)
        self.db.add(version);self.db.flush()
        graph=self.build()
        self.assertEqual(graph['app_version_id'],version.id)
        self.assertEqual((version.risk_score,version.permission_count),(37,12))

    def test_repeated_analysis_reuses_version_but_isolates_runs(self):
        first=self.build();second=self.build(self.analyze(self.app))
        self.assertEqual(first['app_version_id'],second['app_version_id'])
        self.assertNotEqual(first['run_id'],second['run_id'])
        self.assertEqual(first['graph_sha256'],second['graph_sha256'])
        self.assertTrue(set(first['evidence_source_ids'].values()).isdisjoint(second['evidence_source_ids'].values()))

    def test_same_version_label_different_apk_is_isolated(self):
        first=self.build();self.app.apk_hash='b'*64;self.db.flush()
        second=self.build(self.analyze(self.app))
        self.assertNotEqual(first['app_version_id'],second['app_version_id'])
        with self.assertRaises(LookupError):graph_service.read_graph(self.db,self.app.id,first['app_version_id'],second['run_id'])
        self.assertEqual(graph_service.read_graph(self.db,self.app.id,first['app_version_id'],first['run_id'])['apk_sha256'],'a'*64)

    def test_different_version_labels_same_apk_are_isolated(self):
        first=self.build();self.app.version_name='2';self.db.flush()
        second=self.build(self.analyze(self.app))
        self.assertNotEqual(first['app_version_id'],second['app_version_id'])

    def test_other_app_cannot_read_or_build_run(self):
        first=self.build();other=AppAnalysis(app_name='Other',apk_hash='a'*64,version_name='1');self.db.add(other);self.db.flush()
        with self.assertRaises(LookupError):graph_service.read_graph(self.db,other.id,first['app_version_id'],self.run.id)
        with self.assertRaises(LookupError):graph_service.materialize_graph(self.db,other.id,self.run.id)
        self.assertEqual(graph_service.list_graphs(self.db,other.id),[])

    def test_ablation_graph_cannot_include_excluded_sources(self):
        first=self.build(self.analyze(self.app,'A'))
        sources=[node['data']['source'] for node in first['nodes'] if node['type']=='EVIDENCE_SOURCE']
        self.assertEqual(set(sources),{'MANIFEST'})
        self.assertNotIn('TRANSMITTED_TO',{edge['relation'] for edge in first['edges']})

    def test_version_tampering_fails_closed(self):
        first=self.build();self.db.get(AppVersion,first['app_version_id']).apk_hash='c'*64;self.db.flush()
        with self.assertRaisesRegex(ValueError,'Version identity'):graph_service.read_graph(self.db,self.app.id,first['app_version_id'],self.run.id)

    def test_changed_stored_graph_is_rejected(self):
        first=self.build();row=self.db.scalar(select(GraphNode).where(GraphNode.node_type=='DOMAIN'));data=json.loads(row.data_json);data['label']='invented';row.data_json=canonical_json(data);self.db.flush()
        with self.assertRaisesRegex(ValueError,'projection'):graph_service.read_graph(self.db,self.app.id,first['app_version_id'],self.run.id)

    def test_missing_persisted_edge_is_rejected(self):
        first=self.build();self.db.delete(self.db.scalar(select(GraphEdge)));self.db.flush()
        with self.assertRaises(ValueError):graph_service.read_graph(self.db,self.app.id,first['app_version_id'],self.run.id)

    def test_sql_foreign_key_rejects_version_mixing(self):
        self.build();other=AppVersion(app_id=self.app.id,apk_hash='b'*64,version_name='2');self.db.add(other);self.db.flush()
        with self.assertRaises(IntegrityError),self.db.begin_nested():
            self.db.execute(update(GraphEdge).values(app_version_id=other.id));self.db.flush()

    def test_sql_foreign_key_rejects_cross_run_evidence(self):
        first=self.build();second=self.build(self.analyze(self.app))
        foreign_id=next(iter(second['evidence_source_ids'].values()))
        with self.assertRaises(IntegrityError),self.db.begin_nested():
            self.db.execute(update(GraphEdge).where(GraphEdge.run_id==first['run_id']).values(evidence_source_id=foreign_id));self.db.flush()

    def test_ambiguous_legacy_versions_stop_without_writes(self):
        for _ in range(2):self.db.add(AppVersion(app_id=self.app.id,apk_hash=self.run.apk_sha256,version_name='1'))
        self.db.flush()
        with self.assertRaisesRegex(ValueError,'Ambiguous'):self.build()
        self.assertEqual(self.count(GraphRun),0)
        self.assertEqual(self.count(AppVersion),2)

    def test_invalid_graph_rejected_before_version_creation(self):
        with patch.object(graph_service,'build_graph',side_effect=ValueError('invalid graph')):
            with self.assertRaises(ValueError):self.build()
        self.assertEqual(self.count(GraphRun),0);self.assertEqual(self.count(AppVersion),0)

    def test_final_validation_failure_rolls_back_all_graph_rows(self):
        with patch.object(graph_service,'read_graph',side_effect=ValueError('invalid persisted graph')):
            with self.assertRaises(ValueError):self.build()
        for model in (AppVersion,GraphRun,GraphNode,GraphEdge):self.assertEqual(self.count(model),0)

    def test_caller_rollback_preserves_only_phase2(self):
        self.db.commit();self.build();self.db.rollback()
        self.assertEqual(self.count(AnalysisRun),1)
        self.assertEqual(self.count(GraphRun),0);self.assertEqual(self.count(AppVersion),0)

    def test_api_build_read_index_and_wrong_version(self):
        main.app.dependency_overrides[get_db]=lambda:self.db
        self.addCleanup(main.app.dependency_overrides.clear)
        with TestClient(main.app) as client:
            response=client.post(f'/api/apps/{self.app.id}/runs/{self.run.id}/graph')
            self.assertEqual(response.status_code,200,response.text)
            graph=response.json();prefix=f'/api/apps/{self.app.id}/versions'
            self.assertEqual(client.get(f"{prefix}/{graph['app_version_id']}/runs/{self.run.id}/graph").json(),graph)
            self.assertEqual(client.get(f'{prefix}/999/runs/{self.run.id}/graph').status_code,404)
            self.assertEqual(len(client.get(f'/api/apps/{self.app.id}/graph-runs').json()['graphs']),1)


class GraphMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.database=self.root/'phase2.db'
        engine=create_engine('sqlite:///'+self.database.as_posix())
        Base.metadata.create_all(engine,tables=[table for table in Base.metadata.sorted_tables if table not in GRAPH_TABLES and table not in BENCHMARK_TABLES])
        with Session(engine) as db:
            app=AppAnalysis(app_name='Preserve populated Phase 2',apk_hash='a'*64,version_name='1');db.add(app);db.flush()
            fusion_service.analyze_bundle(db,app,fusion_service.make_bundle(app,all_sources(),{}))
            db.add(AppVersion(app_id=app.id,apk_hash='old-hash',version_name='old',risk_score=37))
            db.commit()
        engine.dispose()

    def snapshot(self):
        with closing(sqlite3.connect(self.database)) as db:return table_snapshot(db)

    def test_migration_backup_preserves_phase2_and_existing_versions(self):
        before=self.snapshot();result=migrate(self.database,self.root/'backups');after=self.snapshot()
        self.assertEqual({name:after[name] for name in before},before)
        self.assertEqual(len(after),len(before)+3)
        with closing(sqlite3.connect(result['backup'])) as db:self.assertEqual(table_snapshot(db),before)
        self.assertEqual(migrate(self.database,self.root/'backups')['status'],'already_applied')

    def test_conflicting_graph_schema_stops_without_mutation(self):
        with closing(sqlite3.connect(self.database)) as db:db.execute('CREATE TABLE privacy_graph_runs (wrong TEXT)');db.commit()
        before=self.database.read_bytes()
        with self.assertRaisesRegex(ValueError,'conflicting'):migrate(self.database,self.root/'backups')
        self.assertEqual(self.database.read_bytes(),before)

    def test_missing_phase2_prerequisite_stops_without_mutation(self):
        with closing(sqlite3.connect(self.database)) as db:db.execute('ALTER TABLE fusion_runs ADD COLUMN unexpected TEXT');db.commit()
        before=self.database.read_bytes()
        with self.assertRaisesRegex(ValueError,'Prerequisite'):migrate(self.database,self.root/'backups')
        self.assertEqual(self.database.read_bytes(),before)


if __name__=='__main__':unittest.main()
