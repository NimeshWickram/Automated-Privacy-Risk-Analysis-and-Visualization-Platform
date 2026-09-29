import os
import shutil
from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

from database import engine, Base, get_db
import models
import models_evidence
from chatbot_engine import get_chatbot_response
import permission_analyzer
import sdk_analyzer
import evidence_engine
import policy_extractor
import data_safety_scraper
import llm_report_generator
import provenance
import fusion_service
import graph_service
from adapter import adapt_legacy_records
from privacy_ontology import configuration, PRESETS

# Schema changes are performed only by explicit, backed-up migrations.

app = FastAPI(title="Privacy Risk Analysis API")

from benchmark_api import router as benchmark_router
import research_auth
from fastapi.responses import JSONResponse
import hmac
app.include_router(benchmark_router)


@app.middleware('http')
async def protect_research(request, call_next):
    if request.url.path.startswith('/api/') and request.method != 'OPTIONS':
        secret = research_auth.configured_key()
        if secret is not None:
            supplied = request.headers.get('X-Research-Key', '')
            if not hmac.compare_digest(secret, supplied):
                return JSONResponse({'detail': 'Researcher credential required. Reviewers must use the isolated review service.'}, status_code=403)
        elif research_auth.assignments_exist():
            return JSONResponse({'detail': 'Research authentication is missing; analysis access is locked while review records exist.'}, status_code=503)
    return await call_next(request)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = str(Path(__file__).resolve().parent / "uploads")


# ─── Pydantic models ───────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    message: str
    app_id: int | None = None


# ─── File Upload / Analysis ────────────────────────────────────────────────────

import time
import hashlib
from androguard.core.apk import APK
from datetime import datetime

@app.post("/api/analyze")
async def analyze_apk(file: UploadFile = File(...), policy_url: str = Form(None), analysis_configuration: str = Form('E'), db: Session = Depends(get_db)):
    if not fusion_service.schema_ready(db):
        raise HTTPException(status_code=503, detail="Apply the Phase 1 and Phase 2 migrations before analysis.")
    try:
        configuration(analysis_configuration)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if not (file.filename or "").lower().endswith(".apk"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only APK files are supported.")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, uuid4().hex + ".apk")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # 1. Parse APK with Androguard
        apk = APK(file_path)
        app_name = apk.get_app_name() or file.filename
        package_name = apk.get_package()
        version_name = apk.get_androidversion_name() or "unknown"
        target_sdk = apk.get_target_sdk_version()
        
        # Hash
        with open(file_path, "rb") as f:
            apk_hash = hashlib.sha256(f.read()).hexdigest()
            
        file_size_mb = f"{os.path.getsize(file_path) / (1024 * 1024):.1f} MB"
        
        # Retain a fetched policy document, not unverified LLM or mock claims.
        policy_text = policy_extractor.fetch_and_clean_policy(policy_url) if policy_url else ""
        evidence_results = evidence_engine.run_evidence_pipeline(apk_obj=apk)
        declared_permissions = evidence_results["manifest_data"]["permissions"]
        detected_sdks = evidence_results["detected_sdks"]
        source_status = {
            "manifest": "observed", "sdk": "manifest_signature_scan",
            "code": evidence_results.get("code_scan_status", "unknown"),
            "network": "not_performed", "data_safety": "unavailable",
            "policy": "document_fetched_claims_not_validated" if policy_text else "unavailable",
        }
        if policy_text:
            evidence_results["evidence_records"].append({
                "source_type": "privacy_policy", "evidence_category": "policy_document",
                "data_type": "Privacy policy", "description": "Text fetched from the supplied policy URL; claims not validated.",
                "raw_evidence": policy_text, "file_reference": policy_url,
            })

        raw_perms = [{"name": p.split('.')[-1], "description": f"Permission {p} requested"} for p in declared_permissions]
        
        # Perform context-aware permission analysis
        perm_analysis = permission_analyzer.analyze_all_permissions(
            permissions=raw_perms,
            app_category="Education",
            detected_sdks=detected_sdks,
            target_age="Unknown"
        )
        
        dangerous_count = perm_analysis["summary"]["dangerous_count"]
        
        # 4. Basic Risk Scoring (Will be updated with ML later)
        risk_score = min(100, 30 + (dangerous_count * 5) + (perm_analysis["summary"]["excessive_count"] * 10))
        
        risk_grade = "A" if risk_score < 40 else "B" if risk_score < 60 else "C" if risk_score < 80 else "D"
        risk_level = "Low" if risk_score < 50 else "Medium" if risk_score < 75 else "High"
        
        # 5. Create AppRecord
        app_record = models.AppAnalysis(
            app_name=app_name,
            package_name=package_name,
            developer="Unknown (Uploaded APK)",
            category="Education (Auto-assigned)",
            version_name=version_name,
            apk_size=file_size_mb,
            target_sdk=int(target_sdk) if str(target_sdk).isdigit() else None,
            apk_hash=apk_hash,
            analyzed_at=provenance.utc_now(),
            description=f"Static evidence analysis for {app_name}. Risk score is a heuristic, not an empirical probability. Runtime collection and disclosures have not been verified.",
            play_store_rating=0.0,
            installs="N/A",
            target_age="Unknown",
            risk_score=risk_score,
            risk_grade=risk_grade,
            risk_level=risk_level,
            encryption_protocol="Not observed",
            authentication_method="Not statically determinable",
            data_storage_type="Unknown",
            has_2fa=False,
            compliance_standards="Pending Review",
        )
        db.add(app_record)
        db.flush()
        
        # Admission is controlled by the selected configuration. Raw acquisition
        # is retained once for replay; excluded sources never enter fusion.
        canonical_records = adapt_legacy_records(evidence_results['evidence_records'])
        statuses = {key.upper(): value for key, value in source_status.items()}
        run = fusion_service.analyze_bundle(db, app_record, fusion_service.make_bundle(app_record, canonical_records, statuses), analysis_configuration)

        import json
        for perm in perm_analysis["permissions"]:
            alt_json = json.dumps(perm["alternative_permission"]) if perm.get("alternative_permission") else ""
            db.add(models.AppPermission(
                app_id=app_record.id,
                name=perm["name"],
                status="dangerous" if perm["is_dangerous"] else "normal",
                description=perm["description"],
                justified=perm["educational_justification"] == "justified",
                necessity_score=perm["necessity_score"],
                educational_justification=perm["educational_justification"],
                sdk_attribution=perm["sdk_attribution"],
                risk_category=perm["risk_category"],
                privacy_risk_level=perm["privacy_risk_level"],
                is_actually_used=perm.get("is_actually_used"),
                alternative_permission=alt_json,
                explanation=perm["explanation"],
                child_risk_multiplier=perm["child_risk_multiplier"],
                base_risk_weight=perm["base_risk_weight"],
                adjusted_risk_weight=perm["adjusted_risk_weight"]
            ))

        # 8. Generate Rich Data Based on Analysis
        
        # Trackers — basic SDK detection for uploaded APKs
        default_sdks = sorted(set(detected_sdks))
        perm_names = [p.split('.')[-1] for p in declared_permissions]
        sdk_analysis = sdk_analyzer.analyze_all_sdks(
            sdk_names=default_sdks,
            target_age="Unknown",
            disclosed_sdks=[],
            detected_permissions=perm_names,
        )
        for sdk in sdk_analysis["sdks"]:
            db.add(models.AppTracker(
                app_id=app_record.id,
                name=sdk["name"],
                risk=sdk["privacy_impact"],
                description="SDK manifest signature matched. Access and transmission are not established.",
                category=sdk["category"],
                provider=sdk["provider"],
                privacy_impact=sdk["privacy_impact"],
                data_accessed="[]",  # Catalog capabilities are not observed access.
                permissions_connected=json.dumps(sdk["permissions_connected"]),
                network_domains="[]",  # Catalog domains are not observed communications.
                child_appropriate=sdk["child_appropriate"],
                coppa_mode_available=sdk["coppa_mode_available"],
                gdpr_compliant=sdk["gdpr_compliant"],
                is_disclosed=None,
                disclosure_status="unknown",
                risk_score=sdk["risk_score"],
                child_risk_multiplier=sdk["child_risk_multiplier"],
                privacy_config_issues="[]",
                recommendation="Review SDK behavior and disclosures; presence alone does not establish data access.",
            ))

        # Do not fabricate collection, transmission, payment security, incidents,
        # probabilities or TLS observations from manifest/SDK presence.

        db.commit()

        # Clean up
        try:
            os.remove(file_path)
        except Exception:
            pass

        return {"status": "success", "app_id": app_record.id, "run_id": run.id, "analysis_configuration_id": configuration(analysis_configuration)['id']}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ─── Dashboard / App listing ───────────────────────────────────────────────────

@app.get("/api/apps")
def get_apps(db: Session = Depends(get_db)):
    apps = db.query(models.AppAnalysis).order_by(models.AppAnalysis.id.asc()).all()

    total = len(apps)
    avg_score = sum(a.risk_score for a in apps) // total if total > 0 else 0

    low_risk = sum(1 for a in apps if a.risk_level == "Low")
    med_risk = sum(1 for a in apps if a.risk_level == "Medium")
    high_risk = sum(1 for a in apps if a.risk_level == "High")

    # Compute summary stats
    total_personal_data = 0
    total_incidents = 0
    total_payment_methods = 0
    for a in apps:
        total_personal_data += db.query(models.PersonalDataCollection).filter(
            models.PersonalDataCollection.app_id == a.id,
            models.PersonalDataCollection.is_collected == True
        ).count()
        total_incidents += db.query(models.SecurityIncident).filter(
            models.SecurityIncident.app_id == a.id
        ).count()
        total_payment_methods += db.query(models.PaymentGateway).filter(
            models.PaymentGateway.app_id == a.id
        ).count()

    recent = []
    for a in apps:
        pd_count = db.query(models.PersonalDataCollection).filter(
            models.PersonalDataCollection.app_id == a.id,
            models.PersonalDataCollection.is_collected == True
        ).count()
        inc_count = db.query(models.SecurityIncident).filter(
            models.SecurityIncident.app_id == a.id
        ).count()

        recent.append({
            "id": a.id,
            "name": a.app_name,
            "developer": a.developer,
            "category": a.category,
            "riskScore": a.risk_score,
            "riskGrade": a.risk_grade,
            "riskLevel": a.risk_level,
            "analyzedAt": a.analyzed_at,
            "personalDataItems": pd_count,
            "incidentCount": inc_count,
            "targetAge": a.target_age,
            "installs": a.installs,
        })

    return {
        "totalAppsAnalyzed": total,
        "averageRiskScore": avg_score,
        "totalPersonalDataItems": total_personal_data,
        "totalIncidents": total_incidents,
        "totalPaymentMethods": total_payment_methods,
        "riskDistribution": [
            {"name": "Low Risk", "value": low_risk, "color": "#10b981"},
            {"name": "Medium Risk", "value": med_risk, "color": "#f59e0b"},
            {"name": "High Risk", "value": high_risk, "color": "#ef4444"}
        ],
        "recentApps": recent
    }


# ─── App Detail ─────────────────────────────────────────────────────────────────

@app.get("/api/apps/{app_id}")
def get_app_details(app_id: int, db: Session = Depends(get_db)):
    app_record = db.query(models.AppAnalysis).filter(models.AppAnalysis.id == app_id).first()
    if not app_record:
        raise HTTPException(status_code=404, detail="Application not found")

    permissions = db.query(models.AppPermission).filter(models.AppPermission.app_id == app_id).all()
    trackers = db.query(models.AppTracker).filter(models.AppTracker.app_id == app_id).all()
    personal_data = db.query(models.PersonalDataCollection).filter(models.PersonalDataCollection.app_id == app_id).all()
    payment_gateways = db.query(models.PaymentGateway).filter(models.PaymentGateway.app_id == app_id).all()
    security_incidents = db.query(models.SecurityIncident).filter(
        models.SecurityIncident.app_id == app_id
    ).order_by(models.SecurityIncident.incident_date.desc()).all()
    security_mechanisms = db.query(models.SecurityMechanism).filter(models.SecurityMechanism.app_id == app_id).all()
    risk_predictions = db.query(models.RiskPrediction).filter(
        models.RiskPrediction.app_id == app_id
    ).order_by(models.RiskPrediction.probability.desc()).all()

    evidence_sources = db.query(models_evidence.EvidenceSource).filter(
        models_evidence.EvidenceSource.app_id == app_id
    ).all()
    
    disclosure_mismatches = db.query(models_evidence.DisclosureMismatch).filter(
        models_evidence.DisclosureMismatch.app_id == app_id
    ).all()
    
    llm_report = db.query(models_evidence.LLMReport).filter(
        models_evidence.LLMReport.app_id == app_id
    ).first()

    provenance_data = provenance.app_provenance(db, app_id)
    dangerous_perms = [p for p in permissions if p.status == "dangerous"]

    # Compute dimension scores for radar chart
    perm_score = min(100, len(dangerous_perms) * 15)
    tracker_score = min(100, len(trackers) * 15)
    shared_data = [d for d in personal_data if d.shared_with_third_parties]
    data_score = min(100, len(shared_data) * 20)
    payment_risk_items = [p for p in payment_gateways if p.risk_level in ("Medium", "High")]
    payment_score = min(100, len(payment_risk_items) * 30)
    incident_score = min(100, len(security_incidents) * 25)

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
        "description": app_record.description,
        "playStoreRating": app_record.play_store_rating,
        "installs": app_record.installs,
        "targetAge": app_record.target_age,
        "complianceStandards": app_record.compliance_standards,
        "has2fa": app_record.has_2fa,
        "encryptionProtocol": app_record.encryption_protocol,
        "authenticationMethod": app_record.authentication_method,

        "dimensions": {
            "Permissions": perm_score,
            "Trackers": tracker_score,
            "Data Sharing": data_score,
            "Payment Risk": payment_score,
            "Incidents": incident_score,
        },

        "analysisMetadata": {
            "apkSize": app_record.apk_size,
            "targetSdkVersion": app_record.target_sdk,
            "apkHash": app_record.apk_hash,
            "staticAnalysisComplete": bool(provenance_data["runs"]) and all(r["sourceStatus"].get("code") == "complete" for r in provenance_data["runs"]),
            "dynamicAnalysisComplete": False,
            "provenanceStatus": provenance_data["status"],
        },

        "permissions": {
            "total": len(permissions),
            "dangerous": len(dangerous_perms),
            "list": [{
                "name": p.name,
                "status": p.status,
                "description": p.description,
                "justified": p.justified,
                "necessityScore": p.necessity_score,
                "educationalJustification": p.educational_justification,
                "sdkAttribution": p.sdk_attribution,
                "riskCategory": p.risk_category,
                "privacyRiskLevel": p.privacy_risk_level,
                "isActuallyUsed": p.is_actually_used,
                "alternativePermission": p.alternative_permission,
                "explanation": p.explanation,
                "childRiskMultiplier": p.child_risk_multiplier,
            } for p in permissions]
        },

        "trackers": {
            "total": len(trackers),
            "advertisingCount": len([t for t in trackers if t.category == "advertising"]),
            "undisclosedCount": len([t for t in trackers if t.disclosure_status == "undisclosed"]),
            "childInappropriateCount": len([t for t in trackers if t.child_appropriate is False]),
            "list": [{
                "name": t.name,
                "risk": t.risk,
                "description": t.description,
                "category": t.category,
                "provider": t.provider,
                "privacyImpact": t.privacy_impact,
                "dataAccessed": t.data_accessed,
                "permissionsConnected": t.permissions_connected,
                "networkDomains": t.network_domains,
                "childAppropriate": t.child_appropriate,
                "coppaAvailable": t.coppa_mode_available,
                "gdprCompliant": t.gdpr_compliant,
                "isDisclosed": t.is_disclosed,
                "disclosureStatus": t.disclosure_status,
                "riskScore": t.risk_score,
                "childRiskMultiplier": t.child_risk_multiplier,
                "privacyConfigIssues": t.privacy_config_issues,
                "recommendation": t.recommendation,
            } for t in trackers]
        },

        "personalData": {
            "total": len(personal_data),
            "collected": len([d for d in personal_data if d.is_collected]),
            "sharedWithThirdParties": len(shared_data),
            "list": [{
                "id": d.id,
                "dataCategory": d.data_category,
                "dataType": d.data_type,
                "isCollected": d.is_collected,
                "collectionMethod": d.collection_method,
                "storageLocation": d.storage_location,
                "encryptionStatus": d.encryption_status,
                "sharedWithThirdParties": d.shared_with_third_parties,
                "thirdPartyNames": d.third_party_names,
                "retentionPeriod": d.retention_period,
                "riskLevel": d.risk_level,
                "purpose": d.purpose,
                "legalBasis": d.legal_basis,
            } for d in personal_data]
        },

        "paymentGateways": {
            "total": len(payment_gateways),
            "list": [{
                "id": g.id,
                "paymentMethod": g.payment_method,
                "provider": g.provider,
                "encryptionStandard": g.encryption_standard,
                "pciDssCompliant": g.pci_dss_compliant,
                "fraudDetection": g.fraud_detection,
                "fraudDetectionDetails": g.fraud_detection_details,
                "stolenCardProtection": g.stolen_card_protection,
                "chargebackPolicy": g.chargeback_policy,
                "autoRenewal": g.auto_renewal,
                "cancellationDifficulty": g.cancellation_difficulty,
                "installmentAvailable": g.installment_available,
                "installmentDetails": g.installment_details,
                "dataRetainedAfterPayment": g.data_retained_after_payment,
                "riskLevel": g.risk_level,
            } for g in payment_gateways]
        },

        "securityIncidents": {
            "total": len(security_incidents),
            "list": [{
                "id": i.id,
                "incidentDate": i.incident_date,
                "title": i.title,
                "description": i.description,
                "severity": i.severity,
                "affectedUsers": i.affected_users,
                "dataCompromised": i.data_compromised,
                "cveId": i.cve_id,
                "sourceUrl": i.source_url,
                "resolution": i.resolution,
                "isResolved": i.is_resolved,
            } for i in security_incidents]
        },

        "securityMechanisms": {
            "total": len(security_mechanisms),
            "implemented": len([m for m in security_mechanisms if m.is_implemented]),
            "list": [{
                "id": m.id,
                "mechanismName": m.mechanism_name,
                "category": m.category,
                "isImplemented": m.is_implemented,
                "implementationQuality": m.implementation_quality,
                "details": m.details,
                "recommendation": m.recommendation,
            } for m in security_mechanisms]
        },

        "riskPredictions": {
            "total": len(risk_predictions),
            "list": [{
                "id": p.id,
                "predictionType": p.prediction_type,
                "riskCategory": p.risk_category,
                "probability": p.probability,
                "confidence": p.confidence,
                "timeframe": p.timeframe,
                "description": p.description,
                "contributingFactors": p.contributing_factors,
                "recommendedMitigation": p.recommended_mitigation,
                "severityIfRealized": p.severity_if_realized,
                "historicalBasis": p.historical_basis,
            } for p in risk_predictions]
        },
        
        "provenance": provenance_data,
        "evidenceSources": {
            "total": len(evidence_sources),
            "list": [{
                "id": e.id,
                "sourceType": e.source_type,
                "evidenceCategory": e.evidence_category,
                "dataType": e.data_type,
                "description": e.description,
                "confidence": e.confidence,
                "severity": e.severity,
                "rawEvidence": e.raw_evidence,
                "fileReference": e.file_reference,
                "lineNumber": e.line_number,
                "timestamp": e.timestamp,
                "evidenceStrengthScore": None,
            } for e in evidence_sources]
        },

        "disclosureMismatches": {
            "total": len(disclosure_mismatches),
            "list": [{
                "id": m.id,
                "dataType": m.data_type,
                "mismatchType": m.mismatch_type,
                "description": m.description,
                "severity": m.severity,
                "privacyPolicyClaim": m.privacy_policy_claim,
                "dataSafetyDeclaration": m.data_safety_declaration,
                "technicalEvidence": m.technical_evidence,
            } for m in disclosure_mismatches]
        },
        
        "llmReport": {
            "exists": llm_report is not None,
            "provider": llm_report.provider if llm_report else None,
            "tone": llm_report.tone if llm_report else None,
            "markdown": llm_report.report_markdown if llm_report else None,
            "generatedAt": llm_report.generated_at if llm_report else None,
        } if llm_report else None,

        # Legacy compatibility
        "network": {"domains": [], "unencryptedEndpoints": 0},
        "riskFactors": [],
    }

# ─── LLM Report Generator ──────────────────────────────────────────────────────

@app.post("/api/apps/{app_id}/generate-report")
def generate_llm_report(app_id: int, db: Session = Depends(get_db)):
    try:
        result = llm_report_generator.generate_report(app_id, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Compare Apps ───────────────────────────────────────────────────────────────

@app.get("/api/compare")
def get_compare_apps(db: Session = Depends(get_db)):
    apps = db.query(models.AppAnalysis).order_by(models.AppAnalysis.id.asc()).all()
    result = []
    for app_record in apps:
        permissions = db.query(models.AppPermission).filter(models.AppPermission.app_id == app_record.id).all()
        trackers = db.query(models.AppTracker).filter(models.AppTracker.app_id == app_record.id).all()
        personal_data = db.query(models.PersonalDataCollection).filter(
            models.PersonalDataCollection.app_id == app_record.id,
            models.PersonalDataCollection.is_collected == True
        ).all()
        payment_gateways = db.query(models.PaymentGateway).filter(models.PaymentGateway.app_id == app_record.id).all()
        incidents = db.query(models.SecurityIncident).filter(models.SecurityIncident.app_id == app_record.id).all()
        mechanisms = db.query(models.SecurityMechanism).filter(models.SecurityMechanism.app_id == app_record.id).all()
        predictions = db.query(models.RiskPrediction).filter(models.RiskPrediction.app_id == app_record.id).all()

        dangerous_perms = sum(1 for p in permissions if p.status == "dangerous")
        shared_data = sum(1 for d in personal_data if d.shared_with_third_parties)
        implemented_mechs = sum(1 for m in mechanisms if m.is_implemented)
        avg_prediction_prob = sum(p.probability for p in predictions) / len(predictions) if predictions else 0

        # Calculate dimension scores
        perm_score = min(100, dangerous_perms * 15)
        tracker_score = min(100, len(trackers) * 15)
        data_score = min(100, shared_data * 20)
        payment_risk = sum(1 for p in payment_gateways if p.risk_level in ("Medium", "High"))
        payment_score = min(100, payment_risk * 30)
        incident_score = min(100, len(incidents) * 25)

        result.append({
            "id": app_record.id,
            "name": app_record.app_name,
            "developer": app_record.developer,
            "riskScore": app_record.risk_score,
            "riskGrade": app_record.risk_grade,
            "riskLevel": app_record.risk_level,
            "targetAge": app_record.target_age,
            "installs": app_record.installs,
            "complianceStandards": app_record.compliance_standards,
            "has2fa": app_record.has_2fa,
            "permissions": {"total": len(permissions), "dangerous": dangerous_perms},
            "trackers": len(trackers),
            "personalDataItems": len(personal_data),
            "sharedDataItems": shared_data,
            "paymentMethods": len(payment_gateways),
            "incidents": len(incidents),
            "securityMechanisms": {"total": len(mechanisms), "implemented": implemented_mechs},
            "avgPredictionRisk": round(avg_prediction_prob * 100),
            "dimensions": {
                "Permissions": perm_score,
                "Trackers": tracker_score,
                "Data Sharing": data_score,
                "Payment Risk": payment_score,
                "Incidents": incident_score,
            }
        })
    return result


# ─── Chatbot ────────────────────────────────────────────────────────────────────

@app.post("/api/chatbot")
def chatbot_endpoint(chat: ChatMessage, db: Session = Depends(get_db)):
    if not chat.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    result = get_chatbot_response(chat.message, db, chat.app_id)
    return result


@app.get("/api/apps/{app_id}/provenance")
def get_app_provenance(app_id: int, db: Session = Depends(get_db)):
    if not db.get(models.AppAnalysis, app_id):
        raise HTTPException(status_code=404, detail="Application not found")
    try:
        return provenance.app_provenance(db, app_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


class FusionRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    apk_sha256: str
    application_version: str
    records: list[dict]
    source_status: dict[str, str]
    configuration: Literal['A', 'B', 'C', 'D', 'E'] = 'E'


class AblationRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    source_run_id: int
    configurations: list[Literal['A', 'B', 'C', 'D', 'E']] = Field(default_factory=lambda: list(PRESETS))


@app.get('/api/analysis-configurations')
def analysis_configurations():
    return {'configurations': [configuration(preset) for preset in PRESETS],
            'scoreMeaning': 'Evidence Strength Score is a rule-based score, not a probability.',
            'ablationScope': 'Evidence admission and fusion over a retained acquisition bundle; not acquisition-time benchmarking.'}


def graph_http_error(exc):
    return HTTPException(status_code=404 if isinstance(exc, LookupError) else 409, detail=str(exc))


@app.get('/api/apps/{app_id}/graph-runs')
def graph_runs(app_id: int, db: Session = Depends(get_db)):
    if db.get(models.AppAnalysis, app_id) is None:
        raise HTTPException(status_code=404, detail='Application not found')
    try:
        return {'graphs': graph_service.list_graphs(db, app_id)}
    except (ValueError, LookupError) as exc:
        raise graph_http_error(exc)


@app.post('/api/apps/{app_id}/runs/{run_id}/graph')
def build_privacy_graph(app_id: int, run_id: int, db: Session = Depends(get_db)):
    try:
        result = graph_service.materialize_graph(db, app_id, run_id)
        db.commit()
        return result
    except (ValueError, LookupError) as exc:
        db.rollback()
        raise graph_http_error(exc)


@app.get('/api/apps/{app_id}/versions/{app_version_id}/runs/{run_id}/graph')
def privacy_graph(app_id: int, app_version_id: int, run_id: int, db: Session = Depends(get_db)):
    try:
        return graph_service.read_graph(db, app_id, app_version_id, run_id)
    except (ValueError, LookupError) as exc:
        raise graph_http_error(exc)


@app.post('/api/apps/{app_id}/fusion')
def analyze_evidence_bundle(app_id: int, request: FusionRequest, db: Session = Depends(get_db)):
    if not fusion_service.schema_ready(db):
        raise HTTPException(status_code=503, detail='Phase 2 migration is required.')
    app_record = db.get(models.AppAnalysis, app_id)
    if app_record is None:
        raise HTTPException(status_code=404, detail='Application not found')
    try:
        run = fusion_service.analyze_bundle(db, app_record, request.model_dump(exclude={'configuration'}), request.configuration)
        result = {'app_id': app_id, 'run_id': run.id, 'provenance': provenance.app_provenance(db, app_id)}
        db.commit()
        return result
    except (ValueError, TypeError, KeyError) as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc))


@app.post('/api/apps/{app_id}/ablation')
def run_ablation(app_id: int, request: AblationRequest, db: Session = Depends(get_db)):
    if not fusion_service.schema_ready(db):
        raise HTTPException(status_code=503, detail='Phase 2 migration is required.')
    app_record = db.get(models.AppAnalysis, app_id)
    if app_record is None:
        raise HTTPException(status_code=404, detail='Application not found')
    try:
        runs = fusion_service.ablate(db, app_record, request.source_run_id, request.configurations)
        result = {'app_id': app_id, 'run_ids': [run.id for run in runs], 'provenance': provenance.app_provenance(db, app_id)}
        db.commit()
        return result
    except (ValueError, TypeError, KeyError) as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc))
