import os
import shutil
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import engine, Base, get_db
import models
from analyzer import analyze_apk

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Privacy Risk Analysis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/api/analyze")
async def upload_and_analyze(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith('.apk'):
        raise HTTPException(status_code=400, detail="File must be an APK")
        
    filepath = os.path.join(UPLOAD_DIR, file.filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Run Androguard analysis
        result = analyze_apk(filepath)
        
        # Save to DB
        db_app = models.AppAnalysis(
            app_name=result['app_name'],
            package_name=result['package_name'],
            developer=result['developer'],
            category=result['category'],
            version_name=result['version_name'],
            apk_size=result['apk_size'],
            target_sdk=result['target_sdk'],
            apk_hash=result['apk_hash'],
            analyzed_at=result['analyzed_at'],
            risk_score=result['risk_score'],
            risk_grade=result['risk_grade'],
            risk_level=result['risk_level']
        )
        db.add(db_app)
        db.commit()
        db.refresh(db_app)
        
        for perm in result['permissions']:
            db_perm = models.AppPermission(
                app_id=db_app.id,
                name=perm['name'],
                status=perm['status'],
                description=perm['description'],
                justified=perm['justified']
            )
            db.add(db_perm)
            
        db.commit()
        
        # Clean up file
        os.remove(filepath)
        
        return {"message": "Analysis complete", "app_id": db_app.id}
        
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/apps")
def get_apps(db: Session = Depends(get_db)):
    apps = db.query(models.AppAnalysis).order_by(models.AppAnalysis.id.desc()).all()
    
    total = len(apps)
    avg_score = sum(a.risk_score for a in apps) // total if total > 0 else 0
    
    low_risk = sum(1 for a in apps if a.risk_level == "Low")
    med_risk = sum(1 for a in apps if a.risk_level == "Medium")
    high_risk = sum(1 for a in apps if a.risk_level == "High")
    
    recent = []
    for a in apps:
        recent.append({
            "id": a.id,
            "name": a.app_name,
            "developer": a.developer,
            "category": a.category,
            "riskScore": a.risk_score,
            "riskGrade": a.risk_grade,
            "riskLevel": a.risk_level,
            "analyzedAt": a.analyzed_at
        })
        
    return {
        "totalAppsAnalyzed": total,
        "averageRiskScore": avg_score,
        "riskDistribution": [
            {"name": "Low Risk", "value": low_risk, "color": "#10b981"},
            {"name": "Medium Risk", "value": med_risk, "color": "#f59e0b"},
            {"name": "High Risk", "value": high_risk, "color": "#ef4444"}
        ],
        "recentApps": recent
    }

@app.get("/api/apps/{app_id}")
def get_app_details(app_id: int, db: Session = Depends(get_db)):
    app_record = db.query(models.AppAnalysis).filter(models.AppAnalysis.id == app_id).first()
    if not app_record:
        raise HTTPException(status_code=404, detail="Application not found")
        
    permissions = db.query(models.AppPermission).filter(models.AppPermission.app_id == app_id).all()
    
    dangerous_perms = [p for p in permissions if p.status == "dangerous"]
    
    return {
        "id": app_record.id,
        "name": app_record.app_name,
        "developer": app_record.developer,
        "category": app_record.category,
        "analyzedAt": app_record.analyzed_at,
        "riskScore": app_record.risk_score,
        "riskGrade": app_record.risk_grade,
        "riskLevel": app_record.risk_level,
        "version": app_record.version_name,
        "analysisMetadata": {
            "apkSize": app_record.apk_size,
            "targetSdkVersion": app_record.target_sdk,
            "apkHash": app_record.apk_hash,
            "staticAnalysisComplete": True,
            "dynamicAnalysisComplete": False
        },
        "permissions": {
            "total": len(permissions),
            "dangerous": len(dangerous_perms),
            "list": [{"name": p.name, "status": p.status, "description": p.description, "justified": p.justified} for p in permissions]
        },
        "trackers": {"total": 0, "list": []},
        "network": {"domains": [], "unencryptedEndpoints": 0},
        "disclosureMismatch": [],
        "riskFactors": []
    }

@app.get("/api/compare")
def get_compare_apps(db: Session = Depends(get_db)):
    apps = db.query(models.AppAnalysis).order_by(models.AppAnalysis.id.desc()).all()
    result = []
    for app_record in apps:
        permissions = db.query(models.AppPermission).filter(models.AppPermission.app_id == app_record.id).all()
        dangerous_perms = sum(1 for p in permissions if p.status == "dangerous")
        
        # Calculate a mock dimension score based on dangerous perms for now
        perm_score = min(100, dangerous_perms * 15)
        
        result.append({
            "id": app_record.id,
            "name": app_record.app_name,
            "developer": app_record.developer,
            "riskScore": app_record.risk_score,
            "riskGrade": app_record.risk_grade,
            "permissions": {"total": len(permissions), "dangerous": dangerous_perms},
            "trackers": 0,
            "encryptedEndpoints": "100%",
            "disclosureMatch": "100%",
            "childSafety": "Partial",
            "dimensions": {
                "Permissions": perm_score,
                "Trackers": 20,
                "Network": 20,
                "Storage": 30,
                "Child Safety": 50
            }
        })
    return result

@app.get("/api/compare")
def get_compare_apps(db: Session = Depends(get_db)):
    apps = db.query(models.AppAnalysis).order_by(models.AppAnalysis.id.desc()).all()
    result = []
    for app_record in apps:
        permissions = db.query(models.AppPermission).filter(models.AppPermission.app_id == app_record.id).all()
        dangerous_perms = sum(1 for p in permissions if p.status == "dangerous")
        
        # Calculate a mock dimension score based on dangerous perms for now
        perm_score = min(100, dangerous_perms * 15)
        
        result.append({
            "id": app_record.id,
            "name": app_record.app_name,
            "developer": app_record.developer,
            "riskScore": app_record.risk_score,
            "riskGrade": app_record.risk_grade,
            "permissions": {"total": len(permissions), "dangerous": dangerous_perms},
            "trackers": 0,
            "encryptedEndpoints": "100%",
            "disclosureMatch": "100%",
            "childSafety": "Partial",
            "dimensions": {
                "Permissions": perm_score,
                "Trackers": 20,
                "Network": 20,
                "Storage": 30,
                "Child Safety": 50
            }
        })
    return result
