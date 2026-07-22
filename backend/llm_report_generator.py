"""
EduPrivacy-X: Evidence-Grounded LLM Report Generator (Feature Q).

Uses Google Gemini 1.5 Pro to synthesize multimodal evidence, 
disclosure mismatches, and app metadata into an accessible, 
educational privacy report for parents and teachers.
"""

import os
import json
import logging
from sqlalchemy.orm import Session
import google.generativeai as genai

import models
import models_evidence

logger = logging.getLogger(__name__)

# Try to configure Gemini API Key from environment
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def generate_educational_prompt(app_record, evidence_sources, disclosure_mismatches, permissions, trackers):
    """
    Constructs the prompt for the LLM to generate an educational privacy report.
    """
    prompt = f"""
    You are an expert privacy auditor for educational technology. Your task is to write a highly accessible, 
    educational privacy report for parents and teachers about an Android app called "{app_record.app_name}".
    
    The tone MUST be:
    - Accessible: Avoid overly technical jargon. Explain what things mean.
    - Educational: Help the parent/teacher understand *why* this matters.
    - Balanced: Point out both good privacy practices and areas of concern.
    
    Here is the evidence collected by our multimodal privacy engine:
    
    APP METADATA:
    - Name: {app_record.app_name}
    - Developer: {app_record.developer}
    - Target Age: {app_record.target_age}
    - Risk Level: {app_record.risk_level} (Score: {app_record.risk_score}/100)
    
    DISCLOSURE MISMATCHES (Differences between what they claim and what they do):
    """
    
    if disclosure_mismatches:
        for m in disclosure_mismatches:
            prompt += f"- {m.data_type}: {m.description} (Severity: {m.severity})\n"
    else:
        prompt += "- Excellent: The app's technical behavior completely matches its privacy policy and Data Safety declaration.\n"
        
    prompt += "\nKEY EVIDENCE SOURCES (Technical findings):\n"
    for e in evidence_sources[:10]: # Limit to top 10 to fit context window safely
        prompt += f"- {e.data_type} ({e.evidence_category}): {e.description} (Severity: {e.severity})\n"
        
    prompt += f"\nTRACKERS ({len(trackers)} total):\n"
    for t in trackers[:5]:
        prompt += f"- {t.name} (Category: {t.category}, Child Appropriate: {t.child_appropriate})\n"
        
    prompt += """
    Based on this data, please generate a Markdown report with the following structure:
    
    # 🏫 Educator & Parent Privacy Brief: [App Name]
    
    ## 📝 Executive Summary
    (2-3 sentences summarizing the overall privacy posture for a non-technical reader).
    
    ## 🚩 Key Privacy Findings
    (Use bullet points. Highlight the most important evidence sources and trackers. Explain what data is collected and why a parent should care).
    
    ## 🔍 Transparency & Disclosures
    (Explain any "Disclosure Mismatches". Are they hiding anything? Or are they very transparent?)
    
    ## 🎓 Final Recommendation
    (A clear verdict: e.g., "Safe for Classroom Use", "Use with Parental Supervision", or "Not Recommended").
    
    Format the output strictly as Markdown. Do not include introductory conversational text like "Here is the report".
    """
    return prompt


def generate_report(app_id: int, db: Session) -> dict:
    """
    Generates the LLM report. Uses a mocked fallback if no API key is present.
    """
    # 1. Check if report already exists in DB
    existing_report = db.query(models_evidence.LLMReport).filter(models_evidence.LLMReport.app_id == app_id).first()
    if existing_report:
        return {
            "status": "success",
            "source": "cache",
            "provider": existing_report.provider,
            "tone": existing_report.tone,
            "markdown": existing_report.report_markdown,
            "generated_at": existing_report.generated_at
        }
        
    # 2. Gather data for the prompt
    app_record = db.query(models.AppAnalysis).filter(models.AppAnalysis.id == app_id).first()
    if not app_record:
        raise ValueError(f"App ID {app_id} not found.")
        
    evidence_sources = db.query(models_evidence.EvidenceSource).filter(models_evidence.EvidenceSource.app_id == app_id).order_by(models_evidence.EvidenceSource.severity.desc()).all()
    disclosure_mismatches = db.query(models_evidence.DisclosureMismatch).filter(models_evidence.DisclosureMismatch.app_id == app_id).all()
    permissions = db.query(models.AppPermission).filter(models.AppPermission.app_id == app_id).all()
    trackers = db.query(models.AppTracker).filter(models.AppTracker.app_id == app_id).all()
    
    prompt = generate_educational_prompt(app_record, evidence_sources, disclosure_mismatches, permissions, trackers)
    
    report_markdown = ""
    provider_used = "gemini-1.5-pro"
    
    # 3. Call Gemini if configured, else fallback
    if GEMINI_API_KEY:
        try:
            model = genai.GenerativeModel('gemini-1.5-pro')
            response = model.generate_content(prompt)
            report_markdown = response.text
        except Exception as e:
            logger.error(f"Gemini API failed: {e}")
            report_markdown = generate_mock_report(app_record, disclosure_mismatches)
            provider_used = "mock-fallback"
    else:
        report_markdown = generate_mock_report(app_record, disclosure_mismatches)
        provider_used = "mock-fallback"
        
    from datetime import datetime
    
    # 4. Save to DB
    new_report = models_evidence.LLMReport(
        app_id=app_id,
        provider=provider_used,
        tone="Accessible & Educational",
        report_markdown=report_markdown,
        generated_at=datetime.utcnow().isoformat() + "Z"
    )
    db.add(new_report)
    db.commit()
    
    return {
        "status": "success",
        "source": "generated",
        "provider": new_report.provider,
        "tone": new_report.tone,
        "markdown": new_report.report_markdown,
        "generated_at": new_report.generated_at
    }


def generate_mock_report(app_record, mismatches) -> str:
    """Fallback generator if Gemini API key is not configured."""
    
    mismatch_text = ""
    if mismatches:
        mismatch_text = "We found some inconsistencies between what the app claims to do and what our technical analysis detected. "
        for m in mismatches[:2]:
            mismatch_text += f"For example, regarding {m.data_type}: {m.description}. "
    else:
        mismatch_text = "The app's privacy policy and data safety declarations accurately reflect its technical behavior."

    return f"""# 🏫 Educator & Parent Privacy Brief: {app_record.app_name}

> **Note**: This is a simulated AI report. To enable real Gemini 1.5 Pro generation, please configure the `GEMINI_API_KEY` environment variable on the backend server.

## 📝 Executive Summary
{app_record.app_name} is an educational application intended for {app_record.target_age}. Overall, it presents a {app_record.risk_level.lower()} privacy risk (Score: {app_record.risk_score}/100). The application collects some device information for analytics and functionality, but parents should review the specific tracking services used.

## 🚩 Key Privacy Findings
* **Location Data**: The app includes technical capabilities to access Location, though it may only be used for regional content personalization.
* **Tracking Services**: We detected standard analytics frameworks (like Firebase Analytics). These are generally used to monitor app stability but do collect device-level identifiers.
* **Child-Appropriate Design**: The app restricts dangerous permissions that are unnecessary for an educational context.

## 🔍 Transparency & Disclosures
{mismatch_text}

Parents should be aware that "Data Safety" labels on the app store are self-reported by developers, so independent technical audits like this one provide an important second layer of verification.

## 🎓 Final Recommendation
**Use with Parental Supervision**. While the app provides valuable educational content, the presence of certain tracking SDKs means parents should review their device's privacy settings and consider using Android's built-in app permission controls to restrict unnecessary data access.
"""
