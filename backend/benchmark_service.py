"""Independent review lifecycle and reproducible evaluation; never auto-label truth."""
from functools import wraps
from itertools import product
from pathlib import Path
import csv
import hashlib
import io
import json
import secrets
from sqlalchemy import inspect, select
from models_benchmark import *
from models import AppAnalysis
from models_provenance import AnalysisRun
from privacy_ontology import canonical_json, digest, DataCategory, Finding, configuration
from evaluation import LABELS, EVALUATION_VERSION, evaluate_units, cohen_kappa
import fusion_service
import provenance


def ready(db):
    inspector = inspect(db.connection())
    return all(inspector.has_table(table.name) for table in BENCHMARK_TABLES)


def require_schema(db):
    if not ready(db): raise ValueError('Phase 4 migration is required.')


def atomic(function):
    @wraps(function)
    def wrapped(db, *args, **kwargs):
        require_schema(db)
        fusion_service.ensure_outer_transaction(db)
        with db.begin_nested():
            result = function(db, *args, **kwargs)
            db.flush()
        return result
    return wrapped


def get(db, model, identity):
    value = db.get(model, identity)
    if value is None: raise LookupError('Benchmark record not found.')
    return value


def save(db, value):
    db.add(value); db.flush(); return value


def audit(db, event, actor, **detail):
    db.add(BenchmarkAuditEvent(event=event, actor=actor, detail_json=canonical_json(detail), created_at=provenance.utc_now()))


def universe(dataset):
    protocol = json.loads(dataset.protocol_json)
    return sorted(product(protocol['finding_categories'], protocol['data_categories']))


@atomic
def create_dataset(db, request):
    if (not set(request.finding_categories) <= set(LABELS) or
        not set(request.data_categories) <= {item.value for item in DataCategory if item.value != 'UNKNOWN'}):
        raise ValueError('Unknown evaluation label/category.')
    protocol = {'finding_categories':sorted(set(request.finding_categories)), 'data_categories':sorted(set(request.data_categories)),
        'rationale':request.protocol_rationale, 'evaluation_version':EVALUATION_VERSION,
        'unit':'benchmark version × finding category × data category, evaluated per configuration',
        'negative_policy':'Only explicit reviewed NEGATIVE decisions; UNCERTAIN is excluded.'}
    row=save(db,BenchmarkDataset(name=request.name,version=request.version,dataset_type=request.dataset_type,
        protocol_json=canonical_json(protocol),created_at=provenance.utc_now()))
    audit(db,'DATASET_CREATED',request.actor,dataset_id=row.id,protocol=protocol)
    return {'id':row.id,'dataset_type':row.dataset_type,'protocol':protocol}


def verify_apk(request):
    """REAL_WORLD admission requires local APK bytes plus human eligibility review."""
    if not request.artifact_path or not request.free_educational_verified:
        raise ValueError('REAL_WORLD requires a retained APK and verified free educational eligibility.')
    path=Path(request.artifact_path).resolve(strict=True)
    roots=[Path(__file__).resolve().parent/name for name in ('uploads','benchmark_artifacts')]
    if not any(path.is_relative_to(root.resolve()) for root in roots) or path.suffix.lower() != '.apk':
        raise ValueError('APK must be retained under backend/uploads or backend/benchmark_artifacts.')
    if hashlib.sha256(path.read_bytes()).hexdigest()!=request.apk_sha256:
        raise ValueError('Retained APK hash mismatch.')
    from androguard.core.apk import APK
    apk=APK(str(path))
    if not apk.is_valid_APK() or apk.get_package()!=request.package_name or (apk.get_androidversion_name() or 'unknown')!=request.application_version:
        raise ValueError('APK package/version verification failed.')
    return str(path)


@atomic
def create_version(db, dataset_id, request):
    dataset=get(db,BenchmarkDataset,dataset_id)
    if dataset.frozen_at: raise ValueError('Dataset is frozen; create a new dataset version.')
    artifact=verify_apk(request) if dataset.dataset_type=='REAL_WORLD' else request.artifact_path
    application=save(db,BenchmarkApplication(name=request.name,package_name=request.package_name))
    verification={'artifact_path':artifact,'eligibility_source':request.eligibility_source,'eligibility_notes':request.eligibility_notes,
        'android_tooling_version':request.android_tooling_version,
        'free_educational_verified':request.free_educational_verified,'verified_by':request.actor,'verified_at':provenance.utc_now(),
        'apk_bytes_verified':dataset.dataset_type=='REAL_WORLD'}
    row=save(db,BenchmarkVersion(dataset_id=dataset_id,application_id=application.id,dataset_type=dataset.dataset_type,
        apk_sha256=request.apk_sha256,application_version=request.application_version,verification_json=canonical_json(verification),created_at=provenance.utc_now()))
    audit(db,'VERSION_REGISTERED',request.actor,version_id=row.id,dataset_id=dataset_id)
    return {'id':row.id,'dataset_type':row.dataset_type,'apk_sha256':row.apk_sha256}


def version_open(db, version):
    if version.sealed_at or get(db,BenchmarkDataset,version.dataset_id).frozen_at: raise ValueError('Ground truth/dataset is sealed.')


@atomic
def add_evidence(db, version_id, request):
    version=get(db,BenchmarkVersion,version_id);version_open(db,version)
    if db.scalar(select(ReviewAssignment.id).where(ReviewAssignment.version_id==version_id)) is not None:
        raise ValueError('Review packet is locked after assignment; create a new benchmark version/dataset for corrections.')
    row=save(db,GroundTruthEvidence(version_id=version_id,source=request.source,raw_evidence=request.raw_evidence,
        file_reference=request.file_reference,artifact_sha256=request.artifact_sha256,curator=request.actor,created_at=provenance.utc_now()))
    audit(db,'INDEPENDENT_EVIDENCE_ADDED',request.actor,version_id=version_id,evidence_id=row.id)
    return {'id':row.id}


@atomic
def create_reviewer(db, request):
    row=save(db,GroundTruthReviewer(identity=request.identity,metadata_json=canonical_json(request.metadata),created_at=provenance.utc_now()))
    audit(db,'REVIEWER_REGISTERED',request.actor,reviewer_id=row.id)
    return {'id':row.id}


def packet(db, version):
    application=get(db,BenchmarkApplication,version.application_id)
    dataset=get(db,BenchmarkDataset,version.dataset_id)
    evidence=db.scalars(select(GroundTruthEvidence).where(GroundTruthEvidence.version_id==version.id).order_by(GroundTruthEvidence.id)).all()
    # Allowlist from independent benchmark tables ONLY. No analysis IDs, findings,
    # normalized annotations, scores, severity, reviewer answers or classifications.
    return {'application':{'name':application.name,'package_name':application.package_name,
        'application_version':version.application_version,'apk_sha256':version.apk_sha256},
        'units':[{'finding_category':label,'data_category':category} for label,category in universe(dataset)],
        'evidence':[{'id':row.id,'source':row.source,'raw_evidence':row.raw_evidence,
                     'file_reference':row.file_reference,'artifact_sha256':row.artifact_sha256} for row in evidence]}


@atomic
def assign_review(db, version_id, request):
    version=get(db,BenchmarkVersion,version_id);version_open(db,version)
    reviewer=get(db,GroundTruthReviewer,request.reviewer_id)
    payload=packet(db,version)
    if not payload['evidence']: raise ValueError('Independent evidence is required before review.')
    token=secrets.token_urlsafe(32)
    row=save(db,ReviewAssignment(version_id=version_id,reviewer_id=reviewer.id,token_sha256=hashlib.sha256(token.encode()).hexdigest(),
        packet_sha256=digest(payload),created_at=provenance.utc_now()))
    audit(db,'BLINDED_REVIEW_ASSIGNED',request.actor,assignment_id=row.id,reviewer_id=reviewer.id,version_id=version_id)
    return {'assignment_id':row.id,'review_token':token,'blinded':True}


def assignment_for_token(db, token):
    require_schema(db)
    row=db.scalar(select(ReviewAssignment).where(ReviewAssignment.token_sha256==hashlib.sha256(token.encode()).hexdigest()))
    if row is None: raise LookupError('Review credential is invalid.')
    if digest(packet(db,get(db,BenchmarkVersion,row.version_id)))!=row.packet_sha256:
        raise ValueError('Review packet integrity failure.')
    return row


def reviewer_payload(db, token):
    row=assignment_for_token(db,token)
    submitted=db.scalar(select(ReviewerReview.id).where(ReviewerReview.assignment_id==row.id)) is not None
    return {**packet(db,get(db,BenchmarkVersion,row.version_id)), 'blinded':True,'submitted':submitted,
            'reviewer':get(db,GroundTruthReviewer,row.reviewer_id).identity}


def validate_decisions(db, version, units):
    expected=universe(get(db,BenchmarkDataset,version.dataset_id))
    actual=[(unit['finding_category'],unit['data_category']) for unit in units]
    if sorted(actual)!=expected: raise ValueError('Submit exactly one independent decision for every protocol unit.')
    evidence={row.id:row for row in db.scalars(select(GroundTruthEvidence).where(GroundTruthEvidence.version_id==version.id))}
    for unit in units:
        ids=unit['evidence_ids']
        if not ids or len(set(ids))!=len(ids) or not set(ids)<=set(evidence):
            raise ValueError('Every decision needs independent evidence from this benchmark version.')
        label=unit['finding_category'];sources={evidence[key].source for key in ids}
        if unit['decision']=='UNCERTAIN': continue
        if unit['decision']=='NEGATIVE':
            status = unit['access_status'] if label in {'CAPABILITY','POTENTIAL_ACCESS','ACTUAL_ACCESS'} else unit['transmission_status'] if label=='POTENTIAL_TRANSMISSION' else unit['disclosure_status'] if label=='DISCLOSURE_INCONSISTENCY' else 'NOT_OBSERVED'
            if status != ('CONSISTENT' if label=='DISCLOSURE_INCONSISTENCY' else 'NOT_OBSERVED'):
                raise ValueError('Negative labels require an explicit reviewed absence/consistency status; unknown is not negative.')
            continue
        if unit['observation_status']!='OBSERVED': raise ValueError('Positive decision requires an explicit observation.')
        if label=='CAPABILITY' and (unit['access_status']!='CAPABILITY_ONLY' or 'MANIFEST' not in sources):
            raise ValueError('Capability requires reviewed manifest evidence, not collection.')
        if label=='POTENTIAL_ACCESS' and (unit['access_status'] not in {'STATIC_REFERENCE','OBSERVED'} or not sources & {'CODE','RUNTIME'}):
            raise ValueError('Potential access needs code/runtime evidence.')
        if label=='ACTUAL_ACCESS' and (unit['access_status']!='OBSERVED' or 'RUNTIME' not in sources):
            raise ValueError('Actual access requires runtime evidence; static references are insufficient.')
        if label=='POTENTIAL_TRANSMISSION' and (unit['transmission_status']!='OBSERVED' or 'NETWORK' not in sources):
            raise ValueError('Transmission requires reviewed network evidence.')
        if label=='DISCLOSURE_INCONSISTENCY' and (unit['disclosure_status']!='INCONSISTENT' or not (
            {'POLICY','DATA_SAFETY'}<=sources or (sources & {'POLICY','DATA_SAFETY'} and sources & {'NETWORK','RUNTIME'}))):
            raise ValueError('Disclosure inconsistency needs explicit claim and supporting behavioral/contradictory claim evidence.')
        if label=='UNNECESSARY_PERMISSION' and 'MANIFEST' not in sources:
            raise ValueError('Permission necessity review requires manifest evidence and contextual interpretation.')


@atomic
def submit_review(db, token, request):
    assignment=assignment_for_token(db,token);version=get(db,BenchmarkVersion,assignment.version_id);version_open(db,version)
    if db.scalar(select(ReviewerReview.id).where(ReviewerReview.assignment_id==assignment.id)) is not None:
        raise ValueError('Review is already submitted and immutable.')
    units=sorted([unit.model_dump() for unit in request.units],key=lambda unit:(unit['finding_category'],unit['data_category']))
    validate_decisions(db,version,units)
    payload={'units':units,'packet_sha256':assignment.packet_sha256,'reviewer_id':assignment.reviewer_id,
             'independent_review':request.independent_review,'predictions_not_seen':request.predictions_not_seen}
    row=save(db,ReviewerReview(assignment_id=assignment.id,version_id=version.id,decisions_json=canonical_json(payload),
        submission_sha256=digest(payload),submitted_at=provenance.utc_now()))
    audit(db,'INDEPENDENT_REVIEW_SUBMITTED',get(db,GroundTruthReviewer,assignment.reviewer_id).identity,review_id=row.id,assignment_id=assignment.id)
    return {'submitted':True,'blinded':True}


def review_document(db, review):
    data=json.loads(review.decisions_json)
    assignment=get(db,ReviewAssignment,review.assignment_id)
    if (digest(data)!=review.submission_sha256 or data['packet_sha256']!=assignment.packet_sha256 or
        data['reviewer_id']!=assignment.reviewer_id or digest(packet(db,get(db,BenchmarkVersion,review.version_id)))!=assignment.packet_sha256):
        raise ValueError('Review integrity failure.')
    return data


def agreement(db, version_id, review_ids):
    if len(set(review_ids))!=2: raise ValueError('Choose two distinct independent reviews.')
    rows=[get(db,ReviewerReview,key) for key in review_ids]
    if any(row.version_id!=version_id for row in rows): raise ValueError('Reviews must belong to this version.')
    data=[review_document(db,row) for row in rows]
    if data[0]['reviewer_id']==data[1]['reviewer_id']: raise ValueError('Two different reviewers are required.')
    return {**cohen_kappa(*[[unit['decision'] for unit in item['units']] for item in data]),
            'dataset_type':get(db,BenchmarkVersion,version_id).dataset_type,
            'review_ids':review_ids,'categories':['POSITIVE','NEGATIVE','UNCERTAIN']}


@atomic
def seal_truth(db, version_id, request):
    version=get(db,BenchmarkVersion,version_id);version_open(db,version)
    concordance=agreement(db,version_id,request.review_ids)
    rows=[get(db,ReviewerReview,key) for key in request.review_ids]
    documents=[review_document(db,row) for row in rows]
    chosen=rows[0]
    conflicts=any(a['decision']!=b['decision'] for a,b in zip(documents[0]['units'],documents[1]['units']))
    if conflicts:
        if request.adjudicator_review_id is None: raise ValueError('Disagreement requires an explicit third independent adjudicator review.')
        chosen=get(db,ReviewerReview,request.adjudicator_review_id)
        adjudication=review_document(db,chosen)
        if chosen.version_id!=version_id or adjudication['reviewer_id'] in {item['reviewer_id'] for item in documents}:
            raise ValueError('Adjudication requires a different reviewer on the same version.')
    units=review_document(db,chosen)['units'];validate_decisions(db,version,units)
    for unit in units:
        save(db,GroundTruthFinding(version_id=version_id,review_id=chosen.id,first_evidence_id=unit['evidence_ids'][0],
            finding_category=unit['finding_category'],data_category=unit['data_category'],decision_json=canonical_json(unit),
            approved_by=request.actor,approval_reason=request.approval_reason,approved_at=provenance.utc_now()))
    version.sealed_at=provenance.utc_now();version.truth_sha256=digest(units)
    audit(db,'GROUND_TRUTH_APPROVED',request.actor,version_id=version_id,review_ids=request.review_ids,
        adjudicator_review_id=request.adjudicator_review_id,agreement=concordance,reason=request.approval_reason)
    return {'version_id':version_id,'sealed':True,'truth_sha256':version.truth_sha256,'agreement':concordance}


@atomic
def freeze_dataset(db, dataset_id, request):
    dataset=get(db,BenchmarkDataset,dataset_id)
    versions=db.scalars(select(BenchmarkVersion).where(BenchmarkVersion.dataset_id==dataset_id)).all()
    if not versions or not all(row.sealed_at for row in versions): raise ValueError('Every dataset version needs sealed independent ground truth.')
    if not dataset.frozen_at:
        dataset.frozen_at=provenance.utc_now();audit(db,'DATASET_FROZEN',request.actor,dataset_id=dataset_id)
    return {'dataset_id':dataset_id,'frozen_at':dataset.frozen_at}


def truth_document(db, version):
    rows=db.scalars(select(GroundTruthFinding).where(GroundTruthFinding.version_id==version.id)
        .order_by(GroundTruthFinding.finding_category,GroundTruthFinding.data_category)).all()
    units=[json.loads(row.decision_json) for row in rows]
    if not version.sealed_at or digest(units)!=version.truth_sha256: raise ValueError('Ground truth missing or integrity failure.')
    validate_decisions(db,version,units)
    for row,unit in zip(rows,units):
        original=review_document(db,get(db,ReviewerReview,row.review_id))['units']
        if unit not in original or row.first_evidence_id!=unit['evidence_ids'][0]: raise ValueError('Ground truth disagrees with independent review.')
    return units


def selected_versions(db, dataset_id, request):
    dataset=get(db,BenchmarkDataset,dataset_id)
    if request.dataset_type!=dataset.dataset_type: raise ValueError('Explicit dataset type does not match; synthetic and real-world data cannot mix.')
    if not dataset.frozen_at: raise ValueError('Freeze the independently reviewed dataset before evaluation.')
    versions=db.scalars(select(BenchmarkVersion).where(BenchmarkVersion.dataset_id==dataset_id).order_by(BenchmarkVersion.id)).all()
    mapping={item.benchmark_version_id:item.analysis_run_id for item in request.selections}
    if len(mapping)!=len(request.selections) or set(mapping)!={row.id for row in versions}:
        raise ValueError('Select exactly one analysis for every version of this frozen dataset.')
    for version in versions:
        if version.dataset_type!=dataset.dataset_type: raise ValueError('Dataset contamination detected.')
        run=get(db,AnalysisRun,mapping[version.id])
        app=get(db,AppAnalysis,run.app_id);benchmark_app=get(db,BenchmarkApplication,version.application_id)
        if run.apk_sha256!=version.apk_sha256 or run.application_version!=version.application_version or app.package_name!=benchmark_app.package_name:
            raise ValueError('Prediction APK/package/version does not match benchmark version.')
        if dataset.dataset_type=='REAL_WORLD':
            verification=json.loads(version.verification_json)
            from types import SimpleNamespace
            verify_apk(SimpleNamespace(**verification,apk_sha256=version.apk_sha256,package_name=benchmark_app.package_name,application_version=version.application_version))
        truth_document(db,version)
    return dataset,versions,mapping


def predictions(data):
    pairs=set();mapped=[]
    for item in data['runs'][0]['normalizedEvidence']:
        if item['behavior']=='PERMISSION_REQUESTED' and item['data_category']!='UNKNOWN': pairs.add(('CAPABILITY',item['data_category']))
    labels={Finding.ACCESS.value:'POTENTIAL_ACCESS',Finding.TRANSMISSION.value:'POTENTIAL_TRANSMISSION',
            Finding.DISCLOSURE.value:'DISCLOSURE_INCONSISTENCY',Finding.UNNECESSARY_PERMISSION.value:'UNNECESSARY_PERMISSION'}
    for finding in data['findings']:
        label=labels.get(finding['category'])
        if label: pairs.add((label,finding['dataCategory']))
        mapped.append({'evaluation_label':label,**finding})
    return pairs,mapped


@atomic
def evaluate(db, dataset_id, request):
    dataset,versions,mapping=selected_versions(db,dataset_id,request)
    units=[];snapshots=[];configurations=set()
    for version in versions:
        run=get(db,AnalysisRun,mapping[version.id]);data=provenance.app_provenance(db,run.app_id,run_id=run.id)
        metadata=data['runs'][0]
        if 'analysisConfigurationId' not in metadata: raise ValueError('Verified Phase 2 predictions are required.')
        configurations.add(metadata['analysisConfigurationId'])
        predicted,findings=predictions(data);truth=truth_document(db,version)
        for unit in truth:
            units.append({'version_id':version.id,'finding_category':unit['finding_category'],'data_category':unit['data_category'],
                'truth':unit['decision'],'predicted':(unit['finding_category'],unit['data_category']) in predicted,
                'ground_truth':unit,'analysis_run_id':run.id,'apk_sha256':run.apk_sha256,'application_version':run.application_version})
        snapshots.append({'benchmark_version_id':version.id,'dataset_type':version.dataset_type,'truth_sha256':version.truth_sha256,
            'configuration_definition':configuration(metadata['configuration']),
            'ground_truth_approval':[{'review_id':row.review_id,'finding_category':row.finding_category,'data_category':row.data_category,
                'approved_by':row.approved_by,'approval_reason':row.approval_reason,'approved_at':row.approved_at}
                for row in db.scalars(select(GroundTruthFinding).where(GroundTruthFinding.version_id==version.id))],
            'verification':json.loads(version.verification_json),'analysis':metadata,'predictions':findings,
            'independent_evidence':packet(db,version)['evidence'],
            'reviews':[{'id':row.id,'submitted_at':row.submitted_at,
                'reviewer_identity':get(db,GroundTruthReviewer,get(db,ReviewAssignment,row.assignment_id).reviewer_id).identity,
                'reviewer_metadata':json.loads(get(db,GroundTruthReviewer,get(db,ReviewAssignment,row.assignment_id).reviewer_id).metadata_json),
                **review_document(db,row)} for row in db.scalars(select(ReviewerReview).where(ReviewerReview.version_id==version.id))]})
    if len(configurations)!=1: raise ValueError('One evaluation must use a single analysis configuration; evaluate ablations separately.')
    result=evaluate_units(units)
    snapshot={'dataset_id':dataset.id,'dataset_name':dataset.name,'dataset_version':dataset.version,'dataset_type':dataset.dataset_type,
        'validation_type':'EMPIRICAL_EVALUATION' if dataset.dataset_type=='REAL_WORLD' else 'IMPLEMENTATION_VALIDATION',
        'protocol':json.loads(dataset.protocol_json),'protocol_sha256':digest(json.loads(dataset.protocol_json)),
        'evaluation_version':EVALUATION_VERSION,'environment':provenance.environment_metadata(),
        'android_tooling_version':{str(version.id):json.loads(version.verification_json).get('android_tooling_version') or 'not recorded; static/import workflow' for version in versions},
        'dataset_sha256':digest({'protocol':json.loads(dataset.protocol_json),'versions':[{'id':row.id,'apk':row.apk_sha256,'truth':row.truth_sha256} for row in versions]}),
        'evaluated_at':provenance.utc_now(),'actor':request.actor,
        'configuration_id':next(iter(configurations)),'versions':snapshots,'results':result,
        'limitations':['Unit-level results on this frozen reviewed dataset only; no general accuracy claim.',
            'ACTUAL_ACCESS is unsupported by the current static analyzer and is never inferred from potential access.',
            'Absence of prediction is scored only against explicit reviewed labels; source coverage remains in each run.']}
    row=save(db,EvaluationRun(dataset_id=dataset_id,dataset_type=dataset.dataset_type,snapshot_json=canonical_json(snapshot),
        snapshot_sha256=digest(snapshot),created_at=provenance.utc_now()))
    audit(db,'EVALUATION_RECORDED',request.actor,evaluation_id=row.id,dataset_id=dataset_id,snapshot_sha256=row.snapshot_sha256)
    return {'id':row.id,'snapshot_sha256':row.snapshot_sha256,**snapshot}


def read_evaluation(db, identity):
    row=get(db,EvaluationRun,identity);data=json.loads(row.snapshot_json)
    if digest(data)!=row.snapshot_sha256 or data['dataset_type']!=row.dataset_type or data['dataset_id']!=row.dataset_id:
        raise ValueError('Evaluation snapshot integrity failure.')
    return {'id':row.id,'snapshot_sha256':row.snapshot_sha256,**data}


@atomic
def add_error_note(db, evaluation_id, request):
    snapshot=read_evaluation(db,evaluation_id)
    matching=[unit for unit in snapshot['results']['units'] if (unit['version_id'],unit['finding_category'],unit['data_category']) ==
              (request.version_id,request.finding_category,request.data_category)]
    if not matching or matching[0]['classification'] not in {'FP','FN'}:
        raise ValueError('Error analysis must reference an actual FP/FN in this evaluation snapshot.')
    audit(db,'ERROR_ANALYSIS_NOTE',request.actor,evaluation_id=evaluation_id,classification=matching[0]['classification'],
          version_id=request.version_id,finding_category=request.finding_category,data_category=request.data_category,cause_analysis=request.cause_analysis)
    return {'recorded':True,'classification':matching[0]['classification'],'evaluation_snapshot_unchanged':True}


@atomic
def ablation(db, dataset_id, request):
    dataset,versions,mapping=selected_versions(db,dataset_id,request)
    if len(set(request.configurations))!=len(request.configurations): raise ValueError('Ablation configurations must be distinct.')
    from benchmark_schemas import EvaluationInput
    selections={preset:[] for preset in request.configurations}
    for version in versions:
        source=get(db,AnalysisRun,mapping[version.id]);app=get(db,AppAnalysis,source.app_id)
        for preset,run in zip(request.configurations,fusion_service.ablate(db,app,source.id,request.configurations),strict=True):
            selections[preset].append({'benchmark_version_id':version.id,'analysis_run_id':run.id})
    evaluations={preset:evaluate(db,dataset_id,EvaluationInput(dataset_type=dataset.dataset_type,selections=selection,actor=request.actor))['id']
                 for preset,selection in selections.items()}
    document={'dataset_id':dataset_id,'dataset_type':dataset.dataset_type,'source_selections':[item.model_dump() for item in request.selections],
        'evaluation_ids':evaluations,'scope':'Evidence-admission ablation over retained bundles; fixed independent ground truth, not acquisition-time benchmarking.'}
    row=save(db,AblationExperiment(dataset_id=dataset_id,experiment_json=canonical_json(document),experiment_sha256=digest(document),created_at=provenance.utc_now()))
    audit(db,'ABLATION_RECORDED',request.actor,experiment_id=row.id,evaluation_ids=evaluations)
    return {'id':row.id,**document}


def read_ablation(db, identity):
    row=get(db,AblationExperiment,identity);document=json.loads(row.experiment_json)
    if digest(document)!=row.experiment_sha256 or document['dataset_id']!=row.dataset_id:
        raise ValueError('Ablation manifest integrity failure.')
    evaluations={preset:read_evaluation(db,key) for preset,key in document['evaluation_ids'].items()}
    if (len({item['dataset_sha256'] for item in evaluations.values()})!=1 or
        any(item['dataset_id']!=row.dataset_id or item['dataset_type']!=document['dataset_type'] or
            item['versions'][0]['analysis']['configuration']!=preset for preset,item in evaluations.items())):
        raise ValueError('Ablation evaluations do not share the fixed dataset/protocol.')
    return {'id':row.id,'manifest_sha256':row.experiment_sha256,**document,'evaluations':evaluations}


def export_csv(snapshot):
    stream=io.StringIO(newline='')
    fields=['dataset_type','dataset_version','dataset_sha256','snapshot_sha256','evaluation_id','version_id','apk_sha256','application_version','analysis_run_id',
            'configuration_id','finding_category','data_category','truth','predicted','classification','ground_truth_json','metrics_json','reproducibility_json']
    writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
    for unit in snapshot['results']['units']:
        version=next(item for item in snapshot['versions'] if item['benchmark_version_id']==unit['version_id'])
        row={key:unit.get(key) for key in fields}
        row.update(dataset_type=snapshot['dataset_type'],dataset_version=snapshot['dataset_version'],evaluation_id=snapshot['id'],
            dataset_sha256=snapshot['dataset_sha256'],snapshot_sha256=snapshot['snapshot_sha256'],
            configuration_id=snapshot['configuration_id'],ground_truth_json=canonical_json(unit['ground_truth']),
            metrics_json=canonical_json({key:value for key,value in snapshot['results'].items() if key!='units'}),
            reproducibility_json=canonical_json({'evaluation_version':snapshot['evaluation_version'],'environment':snapshot['environment'],
                'android_tooling_version':snapshot['android_tooling_version'],'evaluated_at':snapshot['evaluated_at'],'version_snapshot':version}))
        writer.writerow({key: "'"+value if isinstance(value,str) and value.startswith(('=','+','-','@','\t','\r','\n')) else value for key,value in row.items()})
    return stream.getvalue()


def catalog(db):
    require_schema(db)
    datasets=[{'id':row.id,'name':row.name,'version':row.version,'dataset_type':row.dataset_type,'protocol':json.loads(row.protocol_json),'frozen_at':row.frozen_at} for row in db.scalars(select(BenchmarkDataset))]
    versions=[{'id':row.id,'dataset_id':row.dataset_id,'dataset_type':row.dataset_type,'application_version':row.application_version,'apk_sha256':row.apk_sha256,'sealed_at':row.sealed_at} for row in db.scalars(select(BenchmarkVersion))]
    evaluations=[{'id':row.id,'dataset_id':row.dataset_id,'dataset_type':row.dataset_type,'created_at':row.created_at} for row in db.scalars(select(EvaluationRun))]
    return {'datasets':datasets,'versions':versions,'evaluations':evaluations,
        'ablations':[{'id':row.id,'dataset_id':row.dataset_id,'created_at':row.created_at} for row in db.scalars(select(AblationExperiment))],
        'reviewers':[{'id':row.id,'identity':row.identity} for row in db.scalars(select(GroundTruthReviewer))],
        'reviews':[{'id':row.id,'version_id':row.version_id,'assignment_id':row.assignment_id,'submitted_at':row.submitted_at} for row in db.scalars(select(ReviewerReview))],
        'empirical_status':'REAL_WORLD evaluations available' if any(row['dataset_type']=='REAL_WORLD' for row in evaluations) else 'N/A — benchmark dataset not yet evaluated'}
