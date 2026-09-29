from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from database import get_db
from research_auth import require_admin
from benchmark_schemas import *
from models_benchmark import BenchmarkAuditEvent
import benchmark_service as service
from privacy_ontology import canonical_json

router=APIRouter(prefix='/api/benchmark',dependencies=[Depends(require_admin)])


def invoke(db, function, *args):
    try:
        service.require_schema(db)
        result=function(db,*args);db.commit();return result
    except (ValueError,LookupError,IntegrityError,OSError) as exc:
        db.rollback()
        if isinstance(exc,IntegrityError): raise HTTPException(409,'Duplicate or inconsistent benchmark record.')
        raise HTTPException(404 if isinstance(exc,LookupError) else 409,str(exc))


@router.get('')
def catalog(db:Session=Depends(get_db)): return invoke(db,service.catalog)


@router.post('/datasets')
def dataset(request:DatasetInput,db:Session=Depends(get_db)): return invoke(db,service.create_dataset,request)


@router.post('/datasets/{dataset_id}/versions')
def version(dataset_id:int,request:VersionInput,db:Session=Depends(get_db)): return invoke(db,service.create_version,dataset_id,request)


@router.post('/versions/{version_id}/evidence')
def evidence(version_id:int,request:EvidenceInput,db:Session=Depends(get_db)): return invoke(db,service.add_evidence,version_id,request)


@router.post('/reviewers')
def reviewer(request:ReviewerInput,db:Session=Depends(get_db)): return invoke(db,service.create_reviewer,request)


@router.post('/versions/{version_id}/assignments')
def assign(version_id:int,request:AssignmentInput,db:Session=Depends(get_db)): return invoke(db,service.assign_review,version_id,request)


@router.get('/versions/{version_id}/agreement')
def agreement(version_id:int,first_review_id:int,second_review_id:int,db:Session=Depends(get_db)):
    return invoke(db,service.agreement,version_id,[first_review_id,second_review_id])


@router.post('/versions/{version_id}/seal')
def seal(version_id:int,request:SealInput,db:Session=Depends(get_db)): return invoke(db,service.seal_truth,version_id,request)


@router.post('/datasets/{dataset_id}/freeze')
def freeze(dataset_id:int,request:ActorInput,db:Session=Depends(get_db)): return invoke(db,service.freeze_dataset,dataset_id,request)


@router.post('/datasets/{dataset_id}/evaluate')
def evaluate(dataset_id:int,request:EvaluationInput,db:Session=Depends(get_db)): return invoke(db,service.evaluate,dataset_id,request)


@router.post('/datasets/{dataset_id}/ablation')
def ablate(dataset_id:int,request:AblationInput,db:Session=Depends(get_db)): return invoke(db,service.ablation,dataset_id,request)


@router.get('/evaluations/{evaluation_id}')
def result(evaluation_id:int,db:Session=Depends(get_db)): return invoke(db,service.read_evaluation,evaluation_id)


@router.get('/ablations/{experiment_id}')
def experiment(experiment_id:int,db:Session=Depends(get_db)): return invoke(db,service.read_ablation,experiment_id)


@router.post('/evaluations/{evaluation_id}/error-notes')
def error_note(evaluation_id:int,request:ErrorNoteInput,db:Session=Depends(get_db)):
    return invoke(db,service.add_error_note,evaluation_id,request)


@router.get('/evaluations/{evaluation_id}/export')
def export(evaluation_id:int,format:Literal['json','csv'],db:Session=Depends(get_db)):
    snapshot=invoke(db,service.read_evaluation,evaluation_id)
    content=service.export_csv(snapshot) if format=='csv' else canonical_json(snapshot)
    return Response(content,media_type='text/csv' if format=='csv' else 'application/json',
                    headers={'Content-Disposition':f'attachment; filename="privacyguard-evaluation-{evaluation_id}.{format}"'})


@router.get('/audit')
def audit(db:Session=Depends(get_db)):
    service.require_schema(db)
    return [{'id':row.id,'event':row.event,'actor':row.actor,'detail':__import__('json').loads(row.detail_json),'timestamp':row.created_at}
            for row in db.scalars(select(BenchmarkAuditEvent).order_by(BenchmarkAuditEvent.id))]
