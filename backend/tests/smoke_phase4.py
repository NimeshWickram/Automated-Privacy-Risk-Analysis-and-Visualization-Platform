"""Exercise both HTTP services using SYNTHETIC records in a disposable DB copy.

Never writes to the source database. This is implementation validation only.
"""
import argparse
from contextlib import closing, ExitStack
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

BACKEND=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BACKEND))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import AppAnalysis
import fusion_service
from test_phase2_fusion import manifest,code
from test_phase4_benchmark import dataset_request,version_request,review_units


def request(base,path,headers=None,data=None,expected=200,raw=False):
    body=json.dumps(data).encode() if data is not None else None
    req=urllib.request.Request(base+path,data=body,headers={**(headers or {}),'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=15) as response:
            assert response.status==expected
            value=response.read().decode()
            return value if raw else json.loads(value)
    except urllib.error.HTTPError as exc:
        if exc.code!=expected:raise AssertionError(f'{path}: {exc.code}: {exc.read().decode()}') from exc
        return None


def run(source):
    source=Path(source).resolve(strict=True);before_hash=hashlib.sha256(source.read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix='privacyguard-phase4-http-') as directory,ExitStack() as stack:
        copied=Path(directory)/'isolated.db'
        with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as src,closing(sqlite3.connect(copied)) as dst:src.backup(dst)
        engine=create_engine('sqlite:///'+copied.as_posix())
        with Session(engine) as db:
            app=AppAnalysis(app_name='SYNTHETIC HTTP fixture',package_name='test.fixture',apk_hash='a'*64,version_name='1',risk_score=0)
            db.add(app);db.flush()
            analysis=fusion_service.analyze_bundle(db,app,fusion_service.make_bundle(app,[manifest(),code()],{'MANIFEST':'synthetic_fixture','CODE':'synthetic_fixture'}))
            analysis_id=analysis.id;db.commit()
        engine.dispose()
        secret=secrets.token_urlsafe(40);headers={'X-Research-Key':secret};bases=[];processes=[]
        try:
            for module in ('main','reviewer_api'):
                with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
                log=stack.enter_context((Path(directory)/(module+'.log')).open('w'))
                process=subprocess.Popen([sys.executable,'-B','-m','uvicorn',module+':app','--host','127.0.0.1','--port',str(port)],
                    cwd=BACKEND,env={**os.environ,'PRIVACYGUARD_DATABASE_PATH':str(copied),'PRIVACYGUARD_RESEARCH_KEY':secret},
                    stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                processes.append(process);bases.append(f'http://127.0.0.1:{port}')
            admin,reviewer=bases
            for base in bases:
                for _ in range(120):
                    try:
                        request(base,'/api/benchmark' if base==admin else '/api/review',headers if base==admin else {},expected=200 if base==admin else 401)
                        break
                    except urllib.error.URLError:
                        if any(process.poll() is not None for process in processes):raise RuntimeError('HTTP service exited during startup.')
                        time.sleep(.25)
                else:raise RuntimeError('HTTP service startup timeout.')
            nonce=secrets.token_hex(5)
            dataset=request(admin,'/api/benchmark/datasets',headers,dataset_request(name='HTTP-SYNTHETIC-'+nonce).model_dump())['id']
            version=request(admin,f'/api/benchmark/datasets/{dataset}/versions',headers,version_request().model_dump())['id']
            evidence=[]
            for source_type,raw in (('MANIFEST',manifest()['raw_evidence']),('CODE',code()['raw_evidence'])):
                evidence.append(request(admin,f'/api/benchmark/versions/{version}/evidence',headers,
                    {'source':source_type,'raw_evidence':raw,'file_reference':'synthetic-http-fixture','artifact_sha256':'b'*64,
                     'independent_and_prediction_free':True,'actor':'synthetic-curator'})['id'])
            for index in range(2):
                identity=request(admin,'/api/benchmark/reviewers',headers,{'identity':f'synthetic-{nonce}-{index}','metadata':{'purpose':'HTTP implementation fixture'},'actor':'synthetic-curator'})['id']
                assignment=request(admin,f'/api/benchmark/versions/{version}/assignments',headers,{'reviewer_id':identity,'actor':'synthetic-curator'})
                review_headers={'Authorization':'Bearer '+assignment['review_token']}
                packet=request(reviewer,'/api/review?blinded=false',review_headers)
                assert packet['blinded'] and set(packet)=={'application','units','evidence','blinded','submitted','reviewer'}
                request(admin,'/api/apps',review_headers,expected=403)
                request(reviewer,'/api/apps/1',review_headers,expected=404)
                request(reviewer,'/api/review',review_headers,{'independent_review':True,'predictions_not_seen':True,'units':review_units(evidence)})
            catalog=request(admin,'/api/benchmark',headers)
            reviews=[row['id'] for row in catalog['reviews'] if row['version_id']==version]
            request(admin,f'/api/benchmark/versions/{version}/seal',headers,{'review_ids':reviews,'approval_reason':'Explicit approval of independent SYNTHETIC fixture reviews','actor':'synthetic-curator'})
            request(admin,f'/api/benchmark/datasets/{dataset}/freeze',headers,{'actor':'synthetic-curator'})
            result=request(admin,f'/api/benchmark/datasets/{dataset}/evaluate',headers,{'dataset_type':'SYNTHETIC','selections':[{'benchmark_version_id':version,'analysis_run_id':analysis_id}],'actor':'synthetic-curator'})
            assert result['validation_type']=='IMPLEMENTATION_VALIDATION' and result['results']['micro']['TP']==2
            exported=request(admin,f"/api/benchmark/evaluations/{result['id']}/export?format=json",headers)
            assert exported==result
            csv=request(admin,f"/api/benchmark/evaluations/{result['id']}/export?format=csv",headers,raw=True)
            assert 'SYNTHETIC' in csv and 'reproducibility_json' in csv
            request(admin,'/api/apps',expected=403)
        finally:
            for process in processes:process.terminate()
            for process in processes:
                try:process.wait(timeout=10)
                except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
        with closing(sqlite3.connect(copied)) as con:
            assert con.execute('PRAGMA integrity_check').fetchall()==[('ok',)]
            assert not con.execute('PRAGMA foreign_key_check').fetchall()
    assert hashlib.sha256(source.read_bytes()).hexdigest()==before_hash
    return {'dataset_type':'SYNTHETIC','validation':'IMPLEMENTATION_ONLY','two_service_http_workflow':'passed',
            'blinded_payload':'passed','prediction_access_denied':'passed','independent_reviews_and_approval':'passed',
            'evaluation_and_exports':'passed','source_database_unchanged':True,'source_sha256':before_hash}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--database',required=True);parser.add_argument('--report')
    args=parser.parse_args();result=run(args.database)
    if args.report:Path(args.report).write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
