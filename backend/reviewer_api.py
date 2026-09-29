"""Run separately: uvicorn reviewer_api:app --app-dir backend --port 8001.

There are deliberately no analysis, graph, evaluation, admin or unblinding routes.
"""
from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import get_db
from research_auth import configured_key
from benchmark_schemas import ReviewInput
import benchmark_service as service

app=FastAPI(title='PrivacyGuard Independent Review',docs_url=None,redoc_url=None,openapi_url=None)
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_methods=['GET','POST'],allow_headers=['Authorization','Content-Type'])


def credential(authorization:str|None=Header(default=None)):
    if configured_key() is None: raise HTTPException(503,'Research authentication must be configured before review.')
    if not authorization or not authorization.startswith('Bearer '): raise HTTPException(401,'Assignment credential required.')
    return authorization[7:]


@app.get('/api/review')
def packet(token:str=Depends(credential),db:Session=Depends(get_db)):
    try:return service.reviewer_payload(db,token)
    except LookupError:raise HTTPException(401,'Invalid assignment credential.')
    except ValueError as exc:raise HTTPException(409,str(exc))


@app.post('/api/review')
def submit(request:ReviewInput,token:str=Depends(credential),db:Session=Depends(get_db)):
    try:
        result=service.submit_review(db,token,request);db.commit();return result
    except (ValueError,LookupError) as exc:
        db.rollback();raise HTTPException(409,str(exc))
    except IntegrityError:
        db.rollback();raise HTTPException(409,'Review is already submitted or its references are inconsistent.')
