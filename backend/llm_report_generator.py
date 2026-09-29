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
    """Render only persisted, linked findings until LLM grounding is validated."""
    import provenance
    app_record = db.query(models.AppAnalysis).filter(models.AppAnalysis.id == app_id).first()
    if not app_record:
        raise ValueError(f"App ID {app_id} not found.")
    data = provenance.app_provenance(db, app_id)
    lines = ["# Evidence-backed privacy summary", "",
             "This is a deterministic evidence summary, not an LLM assessment or an empirical accuracy result.", ""]
    if data["status"] != "available":
        lines.append("Legacy analysis: provenance has not been verified. Re-analyze the APK to obtain linked observations.")
    else:
        for run in data['runs']:
            lines.extend([f"## Run {run['id']} — configuration {run.get('configuration', 'Phase 1')}",
                          f"APK SHA-256: {run['apkSha256']}; application version: {run['applicationVersion']}",
                          f"Analysis version: {run['analysisVersion']}; configuration ID: {run.get('analysisConfigurationId', 'not recorded in Phase 1')}"])
            if run.get('enabledSources'):
                lines.append('Enabled sources: ' + ', '.join(run['enabledSources']))
            for finding in (item for item in data['findings'] if item['runId'] == run['id']):
                lines.extend(["### " + finding["category"], finding["interpretation"]])
                if finding['evidenceStrengthScore'] is not None:
                    lines.append(f"Evidence Strength Score: {finding['evidenceStrengthScore']:.2f} (rule-based; not a probability).")
                for link in finding["evidence"]:
                    lines.append(f"- {link['relationship']}: evidence #{link['evidenceSourceId']} ({link['analyzer']}); snapshot SHA-256 {link['snapshotSha256']}")
        if not data["findings"]:
            lines.append("No supported findings were generated. This does not establish absence of privacy risks.")
        lines.append("Permission and static API references do not establish runtime collection. Any payload or disclosure interpretation is limited to its retained evidence and requires review. No legal conclusion or empirical accuracy is asserted.")
    return {"status": "success", "source": "structured_evidence", "provider": "deterministic-evidence-template-v2",
            "tone": "Evidence-based", "markdown": "\n\n".join(lines), "generated_at": provenance.utc_now()}


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
