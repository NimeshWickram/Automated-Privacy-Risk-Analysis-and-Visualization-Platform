"""Validated, immutable graph snapshots scoped by app, version AND analysis run."""
import json
from sqlalchemy import select, inspect, null
from models_provenance import AnalysisRun
from models_evidence import AppVersion
from models_fusion import FusionRun, FindingAssessment
from models_graph import GraphRun, GraphNode, GraphEdge, GRAPH_TABLES
from privacy_ontology import canonical_json, digest
from graph_engine import GRAPH_VERSION, build_graph, validate_graph, explain_graph
import provenance
import fusion_service


def schema_ready(db):
    inspector = inspect(db.connection())
    return fusion_service.schema_ready(db) and all(inspector.has_table(table.name) for table in GRAPH_TABLES)


def require_schema(db):
    if not schema_ready(db):
        raise ValueError('Phase 3 graph migration is required.')


def verified_inputs(db, app_id, run_id):
    run = db.get(AnalysisRun, run_id)
    if run is None or run.app_id != app_id:
        raise LookupError('Analysis run not found for this application.')
    if db.get(FusionRun, run_id) is None:
        raise ValueError('Graph requires a verified Phase 2 run; legacy results cannot be promoted.')
    payload = provenance.app_provenance(db, app_id, run_id=run_id)
    metadata = payload['runs'][0]
    evidence = [{key: value for key, value in item.items() if key != 'evidenceSourceId'} for item in metadata['normalizedEvidence']]
    source_ids = {item['id']: item['evidenceSourceId'] for item in metadata['normalizedEvidence']}
    rows = db.scalars(select(FindingAssessment).where(FindingAssessment.run_id == run_id).order_by(FindingAssessment.semantic_id)).all()
    findings = [json.loads(row.semantic_json) for row in rows]
    finding_ids = {row.semantic_id: row.finding_id for row in rows}
    return run, metadata, evidence, findings, source_ids, finding_ids


def check_scope(db, app_id, app_version_id, run_id):
    version = db.get(AppVersion, app_version_id)
    run = db.get(AnalysisRun, run_id)
    graph = db.get(GraphRun, run_id)
    if (version is None or version.app_id != app_id or run is None or run.app_id != app_id or
        graph is None or graph.app_version_id != app_version_id):
        raise LookupError('Graph not found in this application/version/run scope.')
    if version.apk_hash != run.apk_sha256 or version.version_name != run.application_version:
        raise ValueError('Version identity disagrees with the analysis run.')
    return graph, version


def read_graph(db, app_id, app_version_id, run_id):
    require_schema(db)
    stored, version = check_scope(db, app_id, app_version_id, run_id)
    run, metadata, evidence, findings, source_ids, finding_ids = verified_inputs(db, app_id, run_id)
    nodes = db.scalars(select(GraphNode).where(GraphNode.run_id == run_id, GraphNode.app_version_id == app_version_id).order_by(GraphNode.node_id)).all()
    edges = db.scalars(select(GraphEdge).where(GraphEdge.run_id == run_id, GraphEdge.app_version_id == app_version_id).order_by(GraphEdge.edge_id)).all()
    graph = {'graph_version': stored.graph_version, 'nodes': [json.loads(row.data_json) for row in nodes],
             'edges': [json.loads(row.data_json) for row in edges], 'omitted_evidence': json.loads(stored.omitted_evidence_json)}
    validate_graph(graph, evidence, findings)
    if digest(graph) != stored.graph_sha256:
        raise ValueError('Graph snapshot hash integrity failure.')
    for row, node in zip(nodes, graph['nodes'], strict=True):
        expected_source = source_ids.get(node['data'].get('id')) if node['type'] == 'EVIDENCE_SOURCE' else None
        expected_finding = finding_ids.get(node['data'].get('semantic_id')) if node['type'] == 'RISK_FINDING' else None
        if (row.node_id != node['id'] or row.node_type != node['type'] or row.layer != node['layer'] or
            row.evidence_source_id != expected_source or row.finding_id != expected_finding):
            raise ValueError('Graph node provenance integrity failure.')
    for row, edge in zip(edges, graph['edges'], strict=True):
        if (row.edge_id != edge['id'] or row.source_node_id != edge['source'] or row.target_node_id != edge['target'] or
            row.relation != edge['relation'] or row.evidence_source_id != source_ids[edge['evidence_id']]):
            raise ValueError('Graph edge provenance integrity failure.')
    return {**graph, 'app_id': app_id, 'app_version_id': version.id, 'run_id': run.id,
            'apk_sha256': run.apk_sha256, 'application_version': run.application_version,
            'analysis_configuration_id': metadata['analysisConfigurationId'], 'configuration': metadata['configuration'],
            'enabled_sources': metadata['enabledSources'], 'source_status': metadata['sourceStatus'],
            'graph_sha256': stored.graph_sha256, 'created_at': stored.created_at,
            'evidence_source_ids': source_ids, 'finding_ids': finding_ids,
            'explanations': explain_graph(graph),
            'limitations': 'Static API references do not prove access. Payload category annotations require review. Shared categories do not prove code-to-network data flow.'}


def materialize_graph(db, app_id, run_id):
    require_schema(db)
    run, _, evidence, findings, source_ids, finding_ids = verified_inputs(db, app_id, run_id)
    existing = db.get(GraphRun, run_id)
    if existing is not None:
        return read_graph(db, app_id, existing.app_version_id, run_id)
    graph = build_graph(evidence, findings)  # Validate before any persistence, including version creation.
    fusion_service.ensure_outer_transaction(db)
    with db.begin_nested():
        versions = db.scalars(select(AppVersion).where(AppVersion.app_id == app_id,
            AppVersion.apk_hash == run.apk_sha256, AppVersion.version_name == run.application_version)).all()
        if len(versions) > 1:
            raise ValueError('Ambiguous existing version identity; researcher review required.')
        if versions:
            version = versions[0]
        else:
            identity_fields = {'id', 'app_id', 'apk_hash', 'version_name', 'analyzed_at'}
            # Legacy version counters default to zero/false. Graph materialization
            # does not compute them; write SQL NULL rather than fictitious results.
            uncomputed = {column.name: null() for column in AppVersion.__table__.columns if column.name not in identity_fields}
            version = AppVersion(app_id=app_id, apk_hash=run.apk_sha256, version_name=run.application_version,
                                 analyzed_at=run.started_at, **uncomputed)
            db.add(version)
            db.flush()
        scope = {'run_id': run_id, 'app_version_id': version.id}
        db.add(GraphRun(**scope, graph_version=GRAPH_VERSION, graph_sha256=digest(graph), created_at=provenance.utc_now(),
                        omitted_evidence_json=canonical_json(graph['omitted_evidence'])))
        db.flush()
        for node in graph['nodes']:
            db.add(GraphNode(**scope, node_id=node['id'], node_type=node['type'], layer=node['layer'], data_json=canonical_json(node),
                evidence_source_id=source_ids[node['data']['id']] if node['type'] == 'EVIDENCE_SOURCE' else None,
                finding_id=finding_ids[node['data']['semantic_id']] if node['type'] == 'RISK_FINDING' else None))
        db.flush()
        for edge in graph['edges']:
            db.add(GraphEdge(**scope, edge_id=edge['id'], source_node_id=edge['source'], target_node_id=edge['target'],
                relation=edge['relation'], evidence_source_id=source_ids[edge['evidence_id']], data_json=canonical_json(edge)))
        db.flush()
        result = read_graph(db, app_id, version.id, run_id)
    return result


def list_graphs(db, app_id):
    require_schema(db)
    # Require matching app ownership on BOTH version and analysis, even for the index.
    rows = db.execute(select(GraphRun, AppVersion, AnalysisRun).join(AppVersion, GraphRun.app_version_id == AppVersion.id)
        .join(AnalysisRun, GraphRun.run_id == AnalysisRun.id)
        .where(AppVersion.app_id == app_id, AnalysisRun.app_id == app_id).order_by(GraphRun.run_id)).all()
    result = []
    for graph, version, run in rows:
        check_scope(db, app_id, version.id, run.id)
        result.append({'app_version_id': version.id, 'run_id': run.id, 'application_version': version.version_name,
                       'apk_sha256': version.apk_hash, 'graph_sha256': graph.graph_sha256})
    return result
