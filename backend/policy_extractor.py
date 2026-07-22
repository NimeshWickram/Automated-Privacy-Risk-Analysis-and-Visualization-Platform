"""
EduPrivacy-X: Privacy Policy NLP Analyser (Feature E).
Fetches HTML from a privacy policy URL, parses the main text,
and uses Gemini 1.5 Pro to extract structured privacy claims.
"""

import os
import json
import logging
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def fetch_and_clean_policy(url: str) -> str:
    """Fetches HTML and strips boilerplate to return core policy text."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (EduPrivacy-X Auditor)'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script, style, nav, header, footer elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'noscript']):
            element.decompose()
            
        text = soup.get_text(separator='\n')
        
        # Clean up excessive newlines and spaces
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        cleaned_text = '\n'.join(lines)
        
        return cleaned_text
    except Exception as e:
        logger.error(f"Failed to fetch policy from {url}: {e}")
        return ""


def extract_policy_claims(app_name: str, policy_url: str = "") -> dict:
    """
    Orchestrates the fetch and NLP extraction process.
    Falls back to mock data if API key is not configured or fetch fails.
    """
    if not policy_url:
        policy_url = "https://example.com/privacy-policy"

    # 1. Fetch text
    if GEMINI_API_KEY and policy_url != "https://example.com/privacy-policy":
        policy_text = fetch_and_clean_policy(policy_url)
        if policy_text:
            try:
                # 2. Run Gemini Extraction
                return run_gemini_extraction(policy_url, policy_text)
            except Exception as e:
                logger.error(f"Gemini NLP Extraction failed: {e}")
                # Fall back to mock
    
    # 3. Fallback (Mock Data)
    logger.info("Using mock policy extraction fallback.")
    return get_mock_extraction(policy_url)


def run_gemini_extraction(url: str, text: str) -> dict:
    """Uses Gemini 1.5 Pro to extract structured JSON from the policy text."""
    
    # Truncate text if it's absurdly long to save tokens (Gemini 1.5 Pro can handle 1M+, but just in case)
    if len(text) > 100000:
        text = text[:100000]
        
    prompt = f"""
    You are an expert legal and privacy auditor. Below is the text of a privacy policy found at {url}.
    Please analyze the text and extract the specific privacy practices.
    
    Output strictly as a JSON object matching this schema:
    {{
        "collects_location": boolean,
        "collects_device_id": boolean,
        "collects_contacts": boolean,
        "collects_camera": boolean,
        "collects_microphone": boolean,
        "collects_email": boolean,
        "collects_name": boolean,
        "collects_age_dob": boolean,
        "collects_school_info": boolean,
        "collects_academic_data": boolean,
        "collects_behavioral_data": boolean,
        
        "shares_with_advertisers": boolean,
        "shares_with_analytics": boolean,
        "shares_with_third_parties": boolean,
        "third_party_names": string (JSON array of names or "[]"),
        
        "mentions_children": boolean,
        "mentions_coppa": boolean,
        "mentions_gdpr": boolean,
        "mentions_parental_consent": boolean,
        "provides_deletion_method": boolean,
        "provides_opt_out": boolean,
        "specifies_retention_period": boolean,
        "retention_details": string (short summary),
        
        "advertising_practices": string (short summary),
        "security_claims": string (short summary),
        "contact_info": string (extracted email/address),
        "international_transfer": boolean,
        
        "extraction_confidences": {{
            "collects_location": float (0.0 to 1.0),
            "shares_with_third_parties": float,
            "mentions_coppa": float
        }}
    }}
    
    If the text explicitly states they DO NOT do something, set the boolean to False.
    If the text says they DO something, set the boolean to True.
    If the text DOES NOT MENTION a practice, set the boolean to False.
    
    POLICY TEXT:
    ---
    {text}
    ---
    """
    
    model = genai.GenerativeModel('gemini-1.5-pro')
    response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
    
    data = json.loads(response.text)
    
    word_count = len(text.split())
    text_hash = hashlib.md5(text.encode()).hexdigest()[:12]
    
    # Merge metadata
    data.update({
        "policy_url": url,
        "policy_text_hash": text_hash,
        "policy_word_count": word_count,
        "readability_score": 55.0, # Placeholder for Flesch-Kincaid
        "extraction_model": "Gemini-1.5-Pro",
        "extracted_at": datetime.utcnow().isoformat() + "Z"
    })
    
    return data


def get_mock_extraction(policy_url: str) -> dict:
    return {
        "policy_url": policy_url,
        "policy_text_hash": "a1b2c3d4e5f6",
        "policy_word_count": 1250,
        "readability_score": 45.2,
        "extraction_model": "Mock-Legal-BERT-v1",
        "extracted_at": datetime.utcnow().isoformat() + "Z",
        
        "collects_location": True,
        "collects_device_id": True,
        "collects_contacts": False,
        "collects_camera": False,
        "collects_microphone": False,
        "collects_email": True,
        "collects_name": True,
        "collects_age_dob": False,
        "collects_school_info": False,
        "collects_academic_data": True,
        "collects_behavioral_data": True,
        
        "shares_with_advertisers": True,
        "shares_with_analytics": True,
        "shares_with_third_parties": True,
        "third_party_names": '["Google", "Facebook"]',
        
        "mentions_children": True,
        "mentions_coppa": True,
        "mentions_gdpr": True,
        "mentions_parental_consent": False,
        "provides_deletion_method": False,
        "provides_opt_out": True,
        "specifies_retention_period": False,
        "retention_details": "We retain data for as long as necessary.",
        
        "advertising_practices": "We may use your data for targeted advertising.",
        "security_claims": "We use industry-standard encryption.",
        "contact_info": "privacy@example.com",
        "international_transfer": True,
        
        "extraction_confidences": {
            "collects_location": 0.85,
            "collects_device_id": 0.9,
            "collects_contacts": 0.95,
            "shares_with_third_parties": 0.88,
            "mentions_coppa": 0.99
        }
    }
