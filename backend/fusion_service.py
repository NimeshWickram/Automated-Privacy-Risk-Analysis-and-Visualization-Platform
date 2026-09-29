"""Persist deterministic Phase 2 results without rewriting legacy runs or evidence."""
import json
import hashlib
from sqlalchemy import inspect, select
from models import AppAnalysis
from models_provenance import AnalysisRun, EvidenceProvenance
from models_fusion import AnalysisConfiguration, FusionRun, NormalizedEvidence, FindingAssessment, FUSION_TABLES
from privacy_ontology import configuration, canonical_json, digest, ANALYSIS_VERSION, ONTOLOGY_VERSION, RULE_VERSION
from normalization import normalize_sources
from fusion_engine import fuse
import provenance


def schema_ready(db):
    inspector = inspect(db.connection())
    return provenance.schema_ready(db) and all(inspector.has_table(table.name) for table in FUSION_TABLES)


def make_bundle(app, records, source_status):
    return {'apk_sha256': app.apk_hash, 'application_version': app.version_name or 'unknown',
            'records': sorted(records, key=canonical_json), 'source_status': dict(source_status)}


def ensure_outer_transaction(db):
    # Python sqlite's legacy transaction mode does not BEGIN on SELECT. Without
    # an explicit outer transaction RELEASE of a first savepoint commits writes,
    # making a later caller rollback ineffective.
    connection = db.connection()
    if connection.dialect.name == 'sqlite' and not connection.connection.driver_connection.in_transaction:
        connection.exec_driver_sql('BEGIN')


def analyze_bundle(db, app, bundle, preset='E', replay_of_run_id=None):
    if not schema_ready(db):
        raise ValueError('Phase 2 migration is required.')
    if bundle.get('apk_sha256') != app.apk_hash or bundle.get('application_version') != (app.version_name or 'unknown'):
        raise ValueError('Evidence bundle APK hash/version does not match this application analysis.')
    config = configuration(preset)
    records = bundle['records']
    if not isinstance(records, list) or not isinstance(bundle.get('source_status'), dict):
        raise ValueError('Records and source status must be explicit.')
    canonical_bundle = make_bundle(app, records, bundle['source_status'])
    if replay_of_run_id is not None and saved_bundle(db, app, replay_of_run_id) != canonical_bundle:
        raise ValueError('Replay must use the unchanged source bundle.')
    normalized = normalize_sources(records, config['enabled_sources'])
    findings = fuse(normalized, config)
    ensure_outer_transaction(db)
    # Validation happens before any new rows. A savepoint makes a failed write
    # atomic even if a caller catches the exception without rolling back.
    with db.begin_nested():
        stored = db.get(AnalysisConfiguration, config['id'])
        if stored is None:
            stored = AnalysisConfiguration(id=config['id'], preset=preset, definition_json=canonical_json(config))
            db.add(stored)
        elif stored.definition_json != canonical_json(config):
            raise ValueError('Analysis configuration integrity failure.')
        aliases = {'MANIFEST': 'manifest', 'CODE': 'decompiled_code', 'SDK': 'sdk', 'NETWORK': 'network_traffic', 'POLICY': 'privacy_policy', 'DATA_SAFETY': 'data_safety'}
        raw_records = [{'source_type': aliases[item['source']], 'evidence_category': item['behavior'] or item['claim'],
                        'analyzer': 'phase2-normalization-v1:' + item['source'].lower(),
                        'data_type': item['data_category'], 'description': item['description'],
                        'raw_evidence': item['raw_evidence'], 'file_reference': item['file_reference']} for item in normalized]
        coverage = {source.lower(): (bundle['source_status'].get(source, 'not_provided') if source in config['enabled_sources'] else 'disabled') for source in aliases}
        # Preserve API-compatible status keys from Phase 1 while recording admission.
        coverage['enabled_sources'] = config['enabled_sources']
        run = provenance.persist_observations(db, app, raw_records, coverage, create_initial_findings=False, analysis_version=ANALYSIS_VERSION)
        db.add(FusionRun(run_id=run.id, analysis_configuration_id=config['id'], ontology_version=ONTOLOGY_VERSION,
                          rule_version=RULE_VERSION, bundle_json=canonical_json(canonical_bundle), bundle_sha256=digest(canonical_bundle),
                          normalized_input_sha256=digest(normalized), semantic_output_sha256=digest(findings), replay_of_run_id=replay_of_run_id))
        db.flush()
        rows = db.scalars(select(EvidenceProvenance).where(EvidenceProvenance.run_id == run.id).order_by(EvidenceProvenance.evidence_source_id)).all()
        identities = {}
        for item, row in zip(normalized, rows, strict=True):
            identities[item['id']] = row.evidence_source_id
            db.add(NormalizedEvidence(run_id=run.id, evidence_source_id=row.evidence_source_id, semantic_id=item['id'], normalized_json=canonical_json(item)))
        for item in findings:
            rationale = {'SUPPORTS': 'Supports only the limited interpretation stated in this versioned rule.',
                         'CORROBORATES': 'Corroborates permission capability, not execution or runtime collection.',
                         'CONTRADICTS': 'Explicit collection claim conflicts with the other retained evidence; applicability still requires review.'}
            finding = provenance.create_finding(db, run.id, item['category'], item['data_category'], item['interpretation'], item['rule_id'],
                [(identities[key], relation, rationale[relation]) for key, relation in item['links']])
            db.add(FindingAssessment(finding_id=finding.id, run_id=run.id, semantic_id=item['semantic_id'],
                                     evidence_strength_score=item['evidence_strength_score'], severity=item['severity'], semantic_json=canonical_json(item)))
        db.flush()
    return run


def saved_bundle(db, app, source_run_id):
    source = db.get(AnalysisRun, source_run_id)
    run = db.get(FusionRun, source_run_id)
    if source is None or run is None or source.app_id != app.id:
        raise ValueError('Source run must be a Phase 2 run of this application analysis.')
    bundle = json.loads(run.bundle_json)
    if digest(bundle) != run.bundle_sha256 or source.apk_sha256 != bundle['apk_sha256'] or source.application_version != bundle['application_version']:
        raise ValueError('Source bundle integrity failure.')
    return bundle


def ablate(db, app, source_run_id, presets):
    if not presets or len(presets) != len(set(presets)) or len(presets) > 5:
        raise ValueError('Select one to five distinct ablation configurations.')
    for preset in presets:
        configuration(preset)
    bundle = saved_bundle(db, app, source_run_id)
    ensure_outer_transaction(db)
    with db.begin_nested():
        runs = [analyze_bundle(db, app, bundle, preset, source_run_id) for preset in presets]
    return runs


def enrich_provenance(db, payload):
    if not schema_ready(db):
        return payload
    for run_data in payload['runs']:
        run = db.get(FusionRun, run_data['id'])
        if run is None:
            continue
        bundle = json.loads(run.bundle_json)
        if (digest(bundle) != run.bundle_sha256 or bundle.get('apk_sha256') != run_data['apkSha256'] or
            bundle.get('application_version') != run_data['applicationVersion']):
            raise ValueError('Source bundle integrity failure.')
        config_row = db.get(AnalysisConfiguration, run.analysis_configuration_id)
        if config_row is None:
            raise ValueError('Configuration integrity failure.')
        config = json.loads(config_row.definition_json)
        if (config != configuration(config_row.preset) or config['id'] != run.analysis_configuration_id or
            run.ontology_version != ONTOLOGY_VERSION or run.rule_version != RULE_VERSION or run_data['analysisVersion'] != ANALYSIS_VERSION):
            raise ValueError('Configuration integrity failure.')
        rows = db.scalars(select(NormalizedEvidence).where(NormalizedEvidence.run_id == run.run_id).order_by(NormalizedEvidence.semantic_id)).all()
        normalized = [json.loads(row.normalized_json) for row in rows]
        if (digest(normalized) != run.normalized_input_sha256 or
            normalized != normalize_sources(bundle['records'], config['enabled_sources'])):
            raise ValueError('Normalized evidence integrity failure.')
        for row, item in zip(rows, normalized, strict=True):
            observation = db.get(EvidenceProvenance, row.evidence_source_id)
            if observation is None or observation.run_id != run.run_id or row.semantic_id != item['id']:
                raise ValueError('Normalized evidence provenance integrity failure.')
            snapshot = json.loads(observation.snapshot_json)
            if (hashlib.sha256(observation.snapshot_json.encode('utf-8')).hexdigest() != observation.snapshot_sha256 or
                any(snapshot[key] != item[key] for key in ('raw_evidence', 'file_reference', 'description', 'data_category'))):
                raise ValueError('Normalized evidence snapshot integrity failure.')
        expected = fuse(normalized, config)
        assessments = db.scalars(select(FindingAssessment).where(FindingAssessment.run_id == run.run_id).order_by(FindingAssessment.semantic_id)).all()
        saved = [json.loads(row.semantic_json) for row in assessments]
        if saved != json.loads(canonical_json(expected)) or digest(saved) != run.semantic_output_sha256:
            raise ValueError('Fusion output integrity failure.')
        run_data.update(analysisConfigurationId=config['id'], configuration=preset_label(config),
                        enabledSources=config['enabled_sources'], ontologyVersion=run.ontology_version, ruleVersion=run.rule_version,
                        bundleSha256=run.bundle_sha256, normalizedInputSha256=run.normalized_input_sha256,
                        semanticOutputSha256=run.semantic_output_sha256, replayOfRunId=run.replay_of_run_id,
                        normalizedEvidence=[{'evidenceSourceId': row.evidence_source_id, **item} for row, item in zip(rows, normalized, strict=True)])
        evidence_keys = {row.evidence_source_id: row.semantic_id for row in rows}
        run_findings = [item for item in payload['findings'] if item['runId'] == run.run_id]
        if {item['id'] for item in run_findings} != {item.finding_id for item in assessments}:
            raise ValueError('Finding assessment coverage integrity failure.')
        for finding in run_findings:
            assessment = db.get(FindingAssessment, finding['id'])
            if assessment is None:
                raise ValueError('Finding assessment missing.')
            semantic = json.loads(assessment.semantic_json)
            links = sorted([evidence_keys.get(link['evidenceSourceId']), link['relationship']] for link in finding['evidence'])
            if (links != semantic['links'] or finding['category'] != semantic['category'] or
                finding['interpretation'] != semantic['interpretation'] or finding['dataCategory'] != semantic['data_category'] or
                finding['ruleId'] != semantic['rule_id'] or assessment.evidence_strength_score != semantic['evidence_strength_score'] or
                assessment.semantic_id != semantic['semantic_id'] or assessment.severity != semantic['severity']):
                raise ValueError('Finding provenance disagrees with deterministic fusion output.')
            finding.update(evidenceStrengthScore=assessment.evidence_strength_score, severity=assessment.severity,
                           semanticId=assessment.semantic_id, domain=semantic['domain'])
    return payload


def preset_label(config):
    return config['preset']
