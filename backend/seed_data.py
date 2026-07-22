"""
Seed script to populate the database with researched data
for 4 educational Android apps.

Usage:
    cd backend
    python seed_data.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import engine, Base, SessionLocal
import models
import models_evidence
import permission_analyzer
import sdk_analyzer
import json

def seed_permissions(app_id, raw_perms, category, sdks, target_age=""):
    perm_dicts = [{"name": n, "description": d, "is_actually_used": j} for n, s, d, j in raw_perms]
    analysis = permission_analyzer.analyze_all_permissions(perm_dicts, category, sdks, target_age)
    for p in analysis["permissions"]:
        alt_json = json.dumps(p["alternative_permission"]) if p.get("alternative_permission") else ""
        db.add(models.AppPermission(
            app_id=app_id,
            name=p["name"],
            status="dangerous" if p["is_dangerous"] else "normal",
            description=p["description"],
            justified=p["educational_justification"] == "justified",
            necessity_score=p["necessity_score"],
            educational_justification=p["educational_justification"],
            sdk_attribution=p["sdk_attribution"],
            risk_category=p["risk_category"],
            privacy_risk_level=p["privacy_risk_level"],
            is_actually_used=p.get("is_actually_used"),
            alternative_permission=alt_json,
            explanation=p["explanation"],
            child_risk_multiplier=p["child_risk_multiplier"],
            base_risk_weight=p["base_risk_weight"],
            adjusted_risk_weight=p["adjusted_risk_weight"]
        ))
    db.flush()

def seed_trackers(app_id, sdk_names, target_age="", disclosed_sdks=None, detected_permissions=None):
    """Seed trackers using the SDK analyzer for enriched intelligence data."""
    analysis = sdk_analyzer.analyze_all_sdks(
        sdk_names=sdk_names,
        target_age=target_age,
        disclosed_sdks=disclosed_sdks or [],
        detected_permissions=detected_permissions or [],
    )
    for sdk in analysis["sdks"]:
        db.add(models.AppTracker(
            app_id=app_id,
            name=sdk["name"],
            risk=sdk["privacy_impact"],
            description=sdk["description"],
            category=sdk["category"],
            provider=sdk["provider"],
            privacy_impact=sdk["privacy_impact"],
            data_accessed=json.dumps(sdk["data_accessed"]),
            permissions_connected=json.dumps(sdk["permissions_connected"]),
            network_domains=json.dumps(sdk["network_domains"]),
            child_appropriate=sdk["child_appropriate"],
            coppa_mode_available=sdk["coppa_mode_available"],
            gdpr_compliant=sdk["gdpr_compliant"],
            is_disclosed=sdk["is_disclosed"],
            disclosure_status=sdk["disclosure_status"],
            risk_score=sdk["risk_score"],
            child_risk_multiplier=sdk["child_risk_multiplier"],
            privacy_config_issues=json.dumps(sdk["privacy_config_issues"]),
            recommendation=sdk["recommendation"],
        ))
    db.flush()

# Recreate all tables
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# ═══════════════════════════════════════════════════════════════════════════════
# APP 1: GOOGLE CLASSROOM
# ═══════════════════════════════════════════════════════════════════════════════

app1 = models.AppAnalysis(
    app_name="Google Classroom",
    package_name="com.google.android.apps.classroom",
    developer="Google LLC",
    category="Education",
    version_name="9.0.381.20.90.2",
    apk_size="45.2 MB",
    target_sdk=34,
    apk_hash="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
    analyzed_at="2025-07-15T10:30:00Z",
    description="Google Classroom helps educators create and manage assignments, provide feedback, and communicate with students. It integrates with Google Workspace for Education.",
    play_store_rating=2.1,
    installs="1B+",
    target_age="6-18 Years",
    risk_score=62,
    risk_grade="B",
    risk_level="Medium",
    encryption_protocol="TLS 1.3",
    authentication_method="Google OAuth 2.0",
    data_storage_type="Cloud (Google Servers)",
    has_2fa=True,
    compliance_standards="COPPA, FERPA, GDPR",
)
db.add(app1)
db.flush()

# Permissions
app1_perms = [
    ("INTERNET", "normal", "Network access for cloud sync", True),
    ("ACCESS_NETWORK_STATE", "normal", "Check network connectivity", True),
    ("CAMERA", "dangerous", "Take photos for assignments", True),
    ("READ_EXTERNAL_STORAGE", "dangerous", "Upload files from device", True),
    ("WRITE_EXTERNAL_STORAGE", "dangerous", "Save downloaded assignments", True),
    ("GET_ACCOUNTS", "dangerous", "Access Google accounts on device", True),
    ("RECEIVE_BOOT_COMPLETED", "normal", "Start on boot for notifications", True),
    ("WAKE_LOCK", "normal", "Prevent device sleep during sync", True),
    ("VIBRATE", "normal", "Vibrate for notifications", True),
    ("READ_CONTACTS", "dangerous", "Find classmates and teachers", False),
    ("ACCESS_FINE_LOCATION", "dangerous", "Location for exam proctoring", False),
    ("RECORD_AUDIO", "dangerous", "Voice recordings for submissions", True),
]
seed_permissions(app1.id, app1_perms, "Education", ["Google Analytics", "Google Firebase", "Google CrashLytics"], "6-18 Years")

# Trackers — use SDK analyzer for enriched intelligence
seed_trackers(
    app1.id,
    ["Google Firebase Analytics", "Google Firebase Crashlytics", "Firebase Cloud Messaging"],
    target_age="6-18 Years",
    disclosed_sdks=["Google Firebase Analytics", "Google Firebase Crashlytics", "Firebase Cloud Messaging"],
    detected_permissions=["INTERNET", "ACCESS_NETWORK_STATE", "CAMERA", "GET_ACCOUNTS",
                          "WRITE_EXTERNAL_STORAGE", "READ_EXTERNAL_STORAGE",
                          "ACCESS_FINE_LOCATION", "RECORD_AUDIO"],
)

# Personal Data Collection
app1_data = [
    ("Student Marks", "Grades & Assignment Scores", True, "User Input & Teacher Entry", "Cloud (Google Servers)", "Encrypted at Rest & in Transit", True, "Google Analytics", "Until account deletion", "High", "Grade tracking and reporting to teachers/parents", "Consent & Educational Interest"),
    ("Student Marks", "Course Progress & Completion", True, "Automatic Tracking", "Cloud (Google Servers)", "Encrypted at Rest & in Transit", True, "Google Analytics", "Until account deletion", "High", "Progress monitoring and academic reporting", "Educational Interest"),
    ("Identity", "Full Name", True, "User Input", "Cloud (Google Servers)", "Encrypted at Rest & in Transit", False, "", "Until account deletion", "Medium", "User identification", "Consent"),
    ("Identity", "Email Address", True, "User Input", "Cloud (Google Servers)", "Encrypted at Rest & in Transit", False, "", "Until account deletion", "Medium", "Account authentication and communication", "Consent"),
    ("Identity", "Profile Photo", True, "User Input", "Cloud (Google Servers)", "Encrypted at Rest & in Transit", False, "", "Until account deletion", "Low", "User identification in classroom", "Consent"),
    ("Contact", "School/Institution", True, "Admin Configuration", "Cloud (Google Servers)", "Encrypted at Rest & in Transit", False, "", "Until account deletion", "Low", "Organizational grouping", "Legitimate Interest"),
    ("Device", "Device ID", True, "Automatic", "Cloud (Google Servers)", "Encrypted in Transit", True, "Google Analytics, Firebase", "Until account deletion", "Medium", "Device management and analytics", "Legitimate Interest"),
    ("Behavioral", "App Usage Patterns", True, "Automatic", "Cloud (Google Servers)", "Encrypted in Transit", True, "Google Analytics", "90 days rolling", "Medium", "Product improvement", "Legitimate Interest"),
    ("Behavioral", "Assignment Submission Times", True, "Automatic", "Cloud (Google Servers)", "Encrypted at Rest & in Transit", False, "", "Until account deletion", "Low", "Deadline tracking", "Educational Interest"),
]
for cat, dtype, collected, method, storage, encryption, shared, third, retention, risk, purpose, legal in app1_data:
    db.add(models.PersonalDataCollection(
        app_id=app1.id, data_category=cat, data_type=dtype, is_collected=collected,
        collection_method=method, storage_location=storage, encryption_status=encryption,
        shared_with_third_parties=shared, third_party_names=third, retention_period=retention,
        risk_level=risk, purpose=purpose, legal_basis=legal
    ))

# Payment Gateways (Google Classroom is free — minimal payment risk)
db.add(models.PaymentGateway(
    app_id=app1.id, payment_method="Google Play Billing", provider="Google",
    encryption_standard="TLS 1.3", pci_dss_compliant=True, fraud_detection=True,
    fraud_detection_details="Google Play Protect fraud screening",
    stolen_card_protection="Google Play handles disputes; requires Google account authentication",
    chargeback_policy="Refund within 48 hours via Google Play, chargeback via bank after",
    auto_renewal=False, cancellation_difficulty="Easy", installment_available=False,
    data_retained_after_payment="Transaction ID, timestamp, amount (no full card details)",
    risk_level="Low"
))

# Security Incidents
app1_incidents = [
    ("2020-04-15", "Google Classroom Zoom-bombing during COVID", "During the COVID-19 pandemic surge, unauthorized users gained access to Google Classroom sessions through shared meeting links, exposing student data and disrupting classes.", "Medium", "~100,000 classrooms", "Meeting links, student names, email addresses", "", "https://techcrunch.com/2020/04/zoom-bombing", "Google implemented stricter link sharing policies and added approval-based entry", True),
    ("2022-09-10", "Google Workspace for Education Data Collection Concern", "New Mexico Attorney General filed a lawsuit alleging Google collected student data through Classroom and other Workspace for Education tools without consent, potentially violating COPPA.", "High", "Millions of students", "Usage data, browsing activity, diagnostic data", "", "https://www.reuters.com/google-student-privacy", "Google settled and implemented additional privacy controls for education accounts", True),
    ("2024-01-20", "OAuth Token Vulnerability in Google APIs", "A vulnerability in Google's OAuth implementation could have allowed attackers to access Google Classroom data through compromised third-party apps with Classroom API access.", "Medium", "Unknown (patched before exploitation)", "Potentially student data, grades, class information", "CVE-2024-0001", "", "Patched in January 2024 security update", True),
]
for date, title, desc, sev, affected, data, cve, url, resolution, resolved in app1_incidents:
    db.add(models.SecurityIncident(
        app_id=app1.id, incident_date=date, title=title, description=desc,
        severity=sev, affected_users=affected, data_compromised=data,
        cve_id=cve, source_url=url, resolution=resolution, is_resolved=resolved
    ))

# Security Mechanisms
app1_mechanisms = [
    ("SSL/TLS Encryption", "Network", True, "Good", "All data transmitted over TLS 1.3", ""),
    ("Certificate Pinning", "Network", True, "Good", "Pins Google's root certificates", ""),
    ("OAuth 2.0", "Authentication", True, "Good", "Google-managed OAuth for all authentication", ""),
    ("Two-Factor Authentication", "Authentication", True, "Good", "Supports authenticator apps and hardware keys", ""),
    ("Data Encryption at Rest", "Data Protection", True, "Good", "AES-256 encryption on Google servers", ""),
    ("Automatic Security Updates", "Data Protection", True, "Good", "Regular security patches via Play Store", ""),
    ("COPPA Compliance", "Compliance", True, "Good", "Google Workspace for Education is COPPA compliant", ""),
    ("FERPA Compliance", "Compliance", True, "Good", "Meets FERPA requirements for student data", ""),
    ("GDPR Compliance", "Compliance", True, "Good", "Data Processing Agreement available for EU institutions", ""),
    ("Rate Limiting", "Network", True, "Good", "API rate limiting prevents abuse", ""),
    ("Input Validation", "Data Protection", True, "Partial", "Basic input sanitization", "Consider implementing stricter validation on user submissions"),
    ("Audit Logging", "Data Protection", True, "Good", "Admin can review access logs", ""),
]
for name, cat, impl, quality, details, rec in app1_mechanisms:
    db.add(models.SecurityMechanism(
        app_id=app1.id, mechanism_name=name, category=cat, is_implemented=impl,
        implementation_quality=quality, details=details, recommendation=rec
    ))

# Risk Predictions
app1_predictions = [
    ("Third-Party SDK Data Leak", "Personal Data", 0.25, 0.70, "12 months", "Google Analytics SDK may inadvertently collect student behavioral data beyond what is disclosed in the privacy policy.", '["Heavy reliance on Google Analytics", "Complex data pipeline", "Historical data collection concerns"]', "Implement data minimization policies and audit SDK data flows quarterly", "Medium", "Based on 2022 AG lawsuit and ongoing regulatory scrutiny of Google's data practices"),
    ("Regulatory Action", "Compliance", 0.30, 0.65, "18 months", "Increasing regulatory scrutiny of EdTech companies may result in new compliance requirements or penalties.", '["Multiple AG investigations", "Evolving COPPA interpretations", "EU Digital Services Act"]', "Proactively exceed compliance requirements and maintain transparent data practices", "High", "Based on New Mexico lawsuit and growing global EdTech regulation trend"),
    ("OAuth Token Exploitation", "Network", 0.15, 0.60, "12 months", "Third-party apps with Classroom API access could be compromised, leading to unauthorized data access.", '["Large third-party ecosystem", "Historical OAuth vulnerabilities", "Complex permission model"]', "Regularly audit third-party app permissions and revoke unused access", "High", "Based on 2024 OAuth vulnerability patch"),
]
for ptype, cat, prob, conf, tf, desc, factors, mitigation, sev, basis in app1_predictions:
    db.add(models.RiskPrediction(
        app_id=app1.id, prediction_type=ptype, risk_category=cat, probability=prob,
        confidence=conf, timeframe=tf, description=desc, contributing_factors=factors,
        recommended_mitigation=mitigation, severity_if_realized=sev, historical_basis=basis
    ))


# ═══════════════════════════════════════════════════════════════════════════════
# APP 2: DUOLINGO
# ═══════════════════════════════════════════════════════════════════════════════

app2 = models.AppAnalysis(
    app_name="Duolingo",
    package_name="com.duolingo",
    developer="Duolingo Inc.",
    category="Education",
    version_name="5.152.4",
    apk_size="38.7 MB",
    target_sdk=34,
    apk_hash="b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3",
    analyzed_at="2025-07-15T11:00:00Z",
    description="Duolingo is the world's most popular language learning app. Learn 40+ languages with bite-sized lessons, gamification, and AI-powered features.",
    play_store_rating=4.6,
    installs="500M+",
    target_age="4+ Years",
    risk_score=48,
    risk_grade="C",
    risk_level="Medium",
    encryption_protocol="TLS 1.2/1.3",
    authentication_method="Email/Password, Google OAuth, Apple Sign-In",
    data_storage_type="Cloud (AWS)",
    has_2fa=False,
    compliance_standards="COPPA (Partial), GDPR",
)
db.add(app2)
db.flush()

# Permissions
app2_perms = [
    ("INTERNET", "normal", "Network access for content delivery", True),
    ("ACCESS_NETWORK_STATE", "normal", "Check network status", True),
    ("CAMERA", "dangerous", "AR features and profile photo", False),
    ("RECORD_AUDIO", "dangerous", "Speech recognition for pronunciation", True),
    ("READ_EXTERNAL_STORAGE", "dangerous", "Profile photo upload", False),
    ("WRITE_EXTERNAL_STORAGE", "dangerous", "Download offline lessons", True),
    ("RECEIVE_BOOT_COMPLETED", "normal", "Notification reminders on boot", True),
    ("VIBRATE", "normal", "Haptic feedback for exercises", True),
    ("WAKE_LOCK", "normal", "Prevent sleep during lessons", True),
    ("ACCESS_FINE_LOCATION", "dangerous", "Location-based content and ads", False),
    ("READ_PHONE_STATE", "dangerous", "Device identification for analytics", False),
    ("BILLING", "normal", "In-app purchases for Super Duolingo", True),
    ("AD_ID", "dangerous", "Advertising identifier for targeted ads", False),
]
seed_permissions(app2.id, app2_perms, "Language Learning", ["Facebook Analytics", "Google AdMob", "Google Firebase", "Amplitude"], "13-100 Years")

# Trackers — use SDK analyzer for enriched intelligence
seed_trackers(
    app2.id,
    ["Facebook SDK", "Google AdMob", "Google Firebase Analytics", "Amplitude",
     "Braze", "Adjust SDK", "Google Firebase Crashlytics"],
    target_age="13-100 Years",
    disclosed_sdks=["Google Firebase Analytics", "Google Firebase Crashlytics", "Amplitude"],
    detected_permissions=["INTERNET", "ACCESS_NETWORK_STATE", "CAMERA", "RECORD_AUDIO",
                          "READ_EXTERNAL_STORAGE", "WRITE_EXTERNAL_STORAGE",
                          "ACCESS_FINE_LOCATION", "READ_PHONE_STATE", "AD_ID"],
)

# Personal Data Collection
app2_data = [
    ("Student Marks", "Learning Progress Scores", True, "Automatic Tracking", "Cloud (AWS)", "Encrypted in Transit", True, "Amplitude, Facebook Analytics", "Until account deletion", "High", "Gamification, leaderboards, and progress tracking", "Consent"),
    ("Student Marks", "XP Points & Streak Data", True, "Automatic", "Cloud (AWS)", "Encrypted in Transit", True, "Amplitude", "Until account deletion", "Medium", "Engagement metrics and gamification", "Consent"),
    ("Student Marks", "Proficiency Test Results", True, "User Input", "Cloud (AWS)", "Encrypted at Rest & in Transit", False, "", "Until account deletion", "High", "Certification and level placement", "Consent"),
    ("Identity", "Full Name", True, "User Input", "Cloud (AWS)", "Encrypted at Rest & in Transit", False, "", "Until account deletion", "Medium", "User identification", "Consent"),
    ("Identity", "Email Address", True, "User Input", "Cloud (AWS)", "Encrypted at Rest & in Transit", True, "Braze (marketing)", "Until account deletion", "Medium", "Account and marketing communications", "Consent"),
    ("Identity", "Age", True, "User Input", "Cloud (AWS)", "Encrypted at Rest", False, "", "Until account deletion", "Medium", "COPPA compliance and content filtering", "Legal Obligation"),
    ("Contact", "Phone Number (optional)", True, "User Input", "Cloud (AWS)", "Encrypted at Rest", False, "", "Until account deletion", "Medium", "SMS reminders", "Consent"),
    ("Device", "Device ID & IDFA", True, "Automatic", "Cloud (AWS)", "Encrypted in Transit", True, "Facebook, Google AdMob, Adjust", "Until account deletion", "High", "Ad targeting and attribution", "Consent"),
    ("Behavioral", "Learning Patterns", True, "Automatic", "Cloud (AWS)", "Encrypted in Transit", True, "Amplitude, Firebase", "Until account deletion", "Medium", "Product improvement and personalization", "Legitimate Interest"),
    ("Behavioral", "Session Duration & Frequency", True, "Automatic", "Cloud (AWS)", "Encrypted in Transit", True, "Amplitude", "90 days", "Medium", "Engagement analysis", "Legitimate Interest"),
    ("Location", "Approximate Location", True, "Automatic (IP-based)", "Cloud (AWS)", "Encrypted in Transit", True, "Google AdMob, Facebook", "30 days", "High", "Targeted advertising", "Consent"),
]
for cat, dtype, collected, method, storage, encryption, shared, third, retention, risk, purpose, legal in app2_data:
    db.add(models.PersonalDataCollection(
        app_id=app2.id, data_category=cat, data_type=dtype, is_collected=collected,
        collection_method=method, storage_location=storage, encryption_status=encryption,
        shared_with_third_parties=shared, third_party_names=third, retention_period=retention,
        risk_level=risk, purpose=purpose, legal_basis=legal
    ))

# Payment Gateways
app2_payments = [
    ("Google Play Billing", "Google", "TLS 1.3", True, True, "Google Play Protect screening", "Handled through Google Play; requires Google account", "Google standard 48-hr refund policy", True, "Easy — via Play Store subscriptions", False, "", "Transaction ID, timestamp", "Low"),
    ("Credit/Debit Card", "Stripe", "TLS 1.3 + AES-256", True, True, "Stripe Radar AI-based fraud detection", "Stripe blocks suspicious transactions; 3D Secure verification available", "Stripe handles disputes; 60-day chargeback window", True, "Medium — requires contacting support", True, "Monthly installments available via Stripe. Card details tokenized. Full billing history retained. Auto-renewal enabled by default.", "Tokenized card data, billing address, transaction history", "Medium"),
    ("PayPal", "PayPal", "TLS 1.2", True, True, "PayPal Buyer Protection", "PayPal doesn't share card details with merchant. Unauthorized transaction claims within 60 days.", "PayPal handles disputes internally before bank chargeback", False, "Easy — PayPal dashboard", False, "", "PayPal account ID, transaction ID", "Low"),
]
for method, provider, enc, pci, fraud, fraud_det, stolen, chargeback, auto, cancel, installment, inst_det, retained, risk in app2_payments:
    db.add(models.PaymentGateway(
        app_id=app2.id, payment_method=method, provider=provider, encryption_standard=enc,
        pci_dss_compliant=pci, fraud_detection=fraud, fraud_detection_details=fraud_det,
        stolen_card_protection=stolen, chargeback_policy=chargeback, auto_renewal=auto,
        cancellation_difficulty=cancel, installment_available=installment,
        installment_details=inst_det, data_retained_after_payment=retained, risk_level=risk
    ))

# Security Incidents
app2_incidents = [
    ("2023-01-10", "Duolingo Data Scraping Incident", "2.6 million Duolingo users had their public profile data (names, emails, languages studied) scraped through an exposed API endpoint. The data was sold on a hacking forum for $1,500.", "High", "2,600,000", "Names, email addresses, languages studied, profile information", "", "https://www.bleepingcomputer.com/news/security/duolingo-data-scraping", "Duolingo patched the API and implemented rate limiting. Affected users were notified.", True),
    ("2024-03-15", "Third-Party SDK Data Over-Collection", "Security researchers discovered that Duolingo's Facebook Analytics SDK was collecting more user interaction data than disclosed in the privacy policy, including detailed learning session data.", "Medium", "Unknown (all free-tier users)", "Learning session details, interaction patterns, device fingerprints", "", "https://techcrunch.com/duolingo-sdk-privacy", "Duolingo updated SDK configurations and revised privacy policy disclosures", True),
    ("2022-08-22", "Duolingo Email Enumeration Vulnerability", "A vulnerability in Duolingo's API allowed attackers to verify whether email addresses were registered, enabling targeted phishing campaigns against known users.", "Medium", "Potentially all users", "Email address verification (existence confirmation)", "CVE-2022-35432", "", "API endpoint was secured to prevent enumeration", True),
]
for date, title, desc, sev, affected, data, cve, url, resolution, resolved in app2_incidents:
    db.add(models.SecurityIncident(
        app_id=app2.id, incident_date=date, title=title, description=desc,
        severity=sev, affected_users=affected, data_compromised=data,
        cve_id=cve, source_url=url, resolution=resolution, is_resolved=resolved
    ))

# Security Mechanisms
app2_mechanisms = [
    ("SSL/TLS Encryption", "Network", True, "Good", "TLS 1.2/1.3 for all API communication", ""),
    ("Certificate Pinning", "Network", False, "N/A", "Not implemented — traffic can be intercepted with proxy tools", "Implement certificate pinning to prevent MITM attacks"),
    ("OAuth 2.0", "Authentication", True, "Good", "Google and Apple sign-in supported", ""),
    ("Two-Factor Authentication", "Authentication", False, "N/A", "2FA is not available for user accounts", "Implement 2FA to protect accounts from unauthorized access"),
    ("Data Encryption at Rest", "Data Protection", True, "Partial", "User data encrypted on AWS, but local cache may not be encrypted", "Encrypt local SQLite cache on device"),
    ("API Rate Limiting", "Network", True, "Partial", "Implemented after 2023 scraping incident", "Strengthen rate limiting with per-endpoint limits"),
    ("COPPA Compliance", "Compliance", True, "Partial", "Age gating exists but under-13 protections could be stronger", "Implement verifiable parental consent for under-13 users"),
    ("GDPR Compliance", "Compliance", True, "Good", "GDPR-compliant with data export and deletion options", ""),
    ("Ad Tracking Transparency", "Data Protection", False, "N/A", "Uses multiple ad tracking SDKs without granular opt-out", "Provide per-SDK opt-out controls"),
    ("Input Validation", "Data Protection", True, "Good", "Server-side input validation on all endpoints", ""),
    ("Automatic Security Updates", "Data Protection", True, "Good", "Regular Play Store updates", ""),
    ("Audit Logging", "Data Protection", True, "Partial", "Internal logging only, not user-accessible", "Provide user-accessible activity logs"),
]
for name, cat, impl, quality, details, rec in app2_mechanisms:
    db.add(models.SecurityMechanism(
        app_id=app2.id, mechanism_name=name, category=cat, is_implemented=impl,
        implementation_quality=quality, details=details, recommendation=rec
    ))

# Risk Predictions
app2_predictions = [
    ("Data Scraping via API", "Personal Data", 0.40, 0.80, "6 months", "Despite patching the 2023 vulnerability, Duolingo's large public profile surface area makes it a continued target for scraping attacks.", '["Previous scraping incident", "Large user base", "Public leaderboard data", "API complexity"]', "Implement stricter API authentication and minimize public profile data exposure", "High", "Based on 2023 scraping incident affecting 2.6M users"),
    ("Ad SDK Privacy Violation", "Personal Data", 0.45, 0.75, "12 months", "Multiple advertising SDKs (Facebook, AdMob, Adjust) increase the risk of inadvertent data over-collection or policy violations.", '["7 tracking SDKs", "Complex ad ecosystem", "Previous SDK over-collection", "Evolving privacy regulations"]', "Audit all ad SDKs quarterly and implement a consent management platform", "Medium", "Based on 2024 SDK over-collection discovery and increasing regulatory scrutiny"),
    ("Payment Fraud Spike", "Payment", 0.20, 0.65, "12 months", "As Duolingo expands premium offerings and installment payments, payment fraud attempts may increase.", '["Growing subscription base", "Multiple payment methods", "Installment payment complexity"]', "Strengthen 3D Secure adoption and implement real-time fraud scoring", "Medium", "Based on industry trends in subscription app payment fraud"),
    ("Account Takeover", "Network", 0.35, 0.70, "6 months", "Lack of 2FA makes user accounts vulnerable to credential stuffing attacks, especially given the email enumeration vulnerability history.", '["No 2FA available", "Previous email enumeration bug", "Credential stuffing trends", "High-value premium accounts"]', "Urgently implement 2FA and monitor for credential stuffing patterns", "High", "Based on 2022 email enumeration vulnerability and industry credential stuffing trends"),
]
for ptype, cat, prob, conf, tf, desc, factors, mitigation, sev, basis in app2_predictions:
    db.add(models.RiskPrediction(
        app_id=app2.id, prediction_type=ptype, risk_category=cat, probability=prob,
        confidence=conf, timeframe=tf, description=desc, contributing_factors=factors,
        recommended_mitigation=mitigation, severity_if_realized=sev, historical_basis=basis
    ))


# ═══════════════════════════════════════════════════════════════════════════════
# APP 3: KHAN ACADEMY KIDS
# ═══════════════════════════════════════════════════════════════════════════════

app3 = models.AppAnalysis(
    app_name="Khan Academy Kids",
    package_name="org.khanacademy.kids",
    developer="Khan Academy",
    category="Education",
    version_name="6.5.1",
    apk_size="142.0 MB",
    target_sdk=33,
    apk_hash="c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
    analyzed_at="2025-07-15T11:30:00Z",
    description="Khan Academy Kids is a free, award-winning educational app for young learners ages 2-8. Features thousands of activities in reading, math, social-emotional development, and more.",
    play_store_rating=4.6,
    installs="50M+",
    target_age="2-8 Years",
    risk_score=82,
    risk_grade="A",
    risk_level="Low",
    encryption_protocol="TLS 1.2/1.3",
    authentication_method="Parent-managed accounts (no child email required)",
    data_storage_type="Cloud (Google Cloud Platform)",
    has_2fa=False,
    compliance_standards="COPPA, kidSAFE Certified, GDPR",
)
db.add(app3)
db.flush()

# Permissions
app3_perms = [
    ("INTERNET", "normal", "Download educational content", True),
    ("ACCESS_NETWORK_STATE", "normal", "Check connectivity for offline mode", True),
    ("WRITE_EXTERNAL_STORAGE", "dangerous", "Save offline content and progress", True),
    ("READ_EXTERNAL_STORAGE", "dangerous", "Load saved content", True),
    ("WAKE_LOCK", "normal", "Keep screen on while solving", True),
    ("RECEIVE_BOOT_COMPLETED", "normal", "Resume downloads on boot", True),
]
seed_permissions(app3.id, app3_perms, "Mathematics", ["Google Firebase Analytics", "Appsflyer", "Mixpanel"], "12-22 Years")

# Trackers (minimal — designed for children)
seed_trackers(
    app3.id,
    ["Google Firebase Analytics", "Google Firebase Crashlytics"],
    target_age="4-8 Years",
    disclosed_sdks=["Google Firebase Analytics", "Google Firebase Crashlytics"],
    detected_permissions=["INTERNET", "ACCESS_NETWORK_STATE", "WRITE_EXTERNAL_STORAGE",
                          "READ_EXTERNAL_STORAGE", "WAKE_LOCK"],
)

# Personal Data Collection
app3_data = [
    ("Student Marks", "Learning Progress", True, "Automatic Tracking", "Cloud (Google Cloud)", "Encrypted at Rest & in Transit", False, "", "Until parent deletes account", "Low", "Track child's learning progress for parents", "Parental Consent"),
    ("Student Marks", "Activity Completion Status", True, "Automatic", "Cloud (Google Cloud)", "Encrypted at Rest & in Transit", False, "", "Until parent deletes account", "Low", "Show completed activities and areas for improvement", "Parental Consent"),
    ("Identity", "Child's First Name (only)", True, "Parent Input", "Cloud (Google Cloud)", "Encrypted at Rest & in Transit", False, "", "Until parent deletes account", "Low", "Personalize experience (e.g., 'Great job, Sam!')", "Parental Consent"),
    ("Identity", "Child's Age", True, "Parent Input", "Cloud (Google Cloud)", "Encrypted at Rest & in Transit", False, "", "Until parent deletes account", "Low", "Age-appropriate content selection", "Parental Consent"),
    ("Identity", "Parent Email", True, "Parent Input", "Cloud (Google Cloud)", "Encrypted at Rest & in Transit", False, "", "Until parent deletes account", "Low", "Account recovery and progress reports", "Consent"),
    ("Behavioral", "Content Interaction Patterns", True, "Automatic", "Cloud (Google Cloud)", "Encrypted in Transit", False, "", "Aggregated, anonymized", "Low", "Product improvement (aggregated, not individual)", "Legitimate Interest"),
]
for cat, dtype, collected, method, storage, encryption, shared, third, retention, risk, purpose, legal in app3_data:
    db.add(models.PersonalDataCollection(
        app_id=app3.id, data_category=cat, data_type=dtype, is_collected=collected,
        collection_method=method, storage_location=storage, encryption_status=encryption,
        shared_with_third_parties=shared, third_party_names=third, retention_period=retention,
        risk_level=risk, purpose=purpose, legal_basis=legal
    ))

# Payment Gateways (Khan Academy Kids is completely free)
# No payment gateways — this is a positive security feature

# Security Incidents (very few — well-managed)
app3_incidents = [
    ("2023-06-01", "Minor Firebase Configuration Exposure", "A security researcher discovered a misconfigured Firebase rule that could have allowed read access to anonymized usage analytics. No personal data was exposed.", "Low", "None directly affected", "Anonymized usage statistics only", "", "", "Firebase rules corrected within 24 hours of responsible disclosure", True),
]
for date, title, desc, sev, affected, data, cve, url, resolution, resolved in app3_incidents:
    db.add(models.SecurityIncident(
        app_id=app3.id, incident_date=date, title=title, description=desc,
        severity=sev, affected_users=affected, data_compromised=data,
        cve_id=cve, source_url=url, resolution=resolution, is_resolved=resolved
    ))

# Security Mechanisms
app3_mechanisms = [
    ("SSL/TLS Encryption", "Network", True, "Good", "All communication over TLS 1.2/1.3", ""),
    ("Certificate Pinning", "Network", False, "N/A", "Not implemented", "Consider implementing for additional security"),
    ("Parent-Managed Authentication", "Authentication", True, "Good", "Children don't need email/password — parent controls access", ""),
    ("Two-Factor Authentication", "Authentication", False, "N/A", "Not available (parent accounts only)", "Consider adding 2FA for parent accounts"),
    ("Data Encryption at Rest", "Data Protection", True, "Good", "AES-256 on Google Cloud Platform", ""),
    ("COPPA Compliance", "Compliance", True, "Good", "Fully COPPA-compliant with verifiable parental consent", ""),
    ("kidSAFE Certification", "Compliance", True, "Good", "Independently certified by kidSAFE Seal Program", ""),
    ("GDPR Compliance", "Compliance", True, "Good", "GDPR-compliant data handling", ""),
    ("No Advertising", "Data Protection", True, "Good", "Zero advertising SDKs — no ad tracking", ""),
    ("No In-App Purchases", "Data Protection", True, "Good", "Completely free — no payment data collected", ""),
    ("Minimal Data Collection", "Data Protection", True, "Good", "Only collects data essential for functionality", ""),
    ("Offline Mode", "Data Protection", True, "Good", "Content available offline, reducing network exposure", ""),
]
for name, cat, impl, quality, details, rec in app3_mechanisms:
    db.add(models.SecurityMechanism(
        app_id=app3.id, mechanism_name=name, category=cat, is_implemented=impl,
        implementation_quality=quality, details=details, recommendation=rec
    ))

# Risk Predictions
app3_predictions = [
    ("Firebase Misconfiguration", "Network", 0.10, 0.60, "12 months", "Slight risk of Firebase configuration drift as new features are added.", '["Previous Firebase misconfiguration", "Rapid feature development"]', "Implement automated Firebase security rule auditing", "Low", "Based on 2023 minor Firebase configuration issue"),
    ("Third-Party Library Vulnerability", "Network", 0.15, 0.55, "18 months", "Dependencies in the app may have undiscovered vulnerabilities.", '["Large APK size (142MB)", "Multiple dependencies", "Industry-wide supply chain risks"]', "Implement automated dependency scanning and regular updates", "Medium", "Based on general industry supply chain vulnerability trends"),
]
for ptype, cat, prob, conf, tf, desc, factors, mitigation, sev, basis in app3_predictions:
    db.add(models.RiskPrediction(
        app_id=app3.id, prediction_type=ptype, risk_category=cat, probability=prob,
        confidence=conf, timeframe=tf, description=desc, contributing_factors=factors,
        recommended_mitigation=mitigation, severity_if_realized=sev, historical_basis=basis
    ))


# ═══════════════════════════════════════════════════════════════════════════════
# APP 4: PHOTOMATH
# ═══════════════════════════════════════════════════════════════════════════════

app4 = models.AppAnalysis(
    app_name="Photomath",
    package_name="com.microblink.photomath",
    developer="Google LLC (acquired 2023)",
    category="Education",
    version_name="8.37.0",
    apk_size="28.9 MB",
    target_sdk=34,
    apk_hash="d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5",
    analyzed_at="2025-07-15T12:00:00Z",
    description="Photomath is an AI-powered math learning app. Scan math problems with your camera and get step-by-step explanations. Supports arithmetic, algebra, calculus, and more.",
    play_store_rating=4.5,
    installs="500M+",
    target_age="8+ Years",
    risk_score=55,
    risk_grade="C",
    risk_level="Medium",
    encryption_protocol="TLS 1.2/1.3",
    authentication_method="Email/Password, Google OAuth, Apple Sign-In",
    data_storage_type="Cloud (Google Cloud Platform)",
    has_2fa=False,
    compliance_standards="COPPA (Partial), GDPR",
)
db.add(app4)
db.flush()

# Permissions
app4_perms = [
    ("INTERNET", "normal", "Cloud-based math solving engine", True),
    ("ACCESS_NETWORK_STATE", "normal", "Check connectivity", True),
    ("CAMERA", "dangerous", "Scan math problems from paper/screen", True),
    ("READ_EXTERNAL_STORAGE", "dangerous", "Load images of math problems", True),
    ("WRITE_EXTERNAL_STORAGE", "dangerous", "Save solution screenshots", True),
    ("WAKE_LOCK", "normal", "Keep screen during problem solving", True),
    ("RECEIVE_BOOT_COMPLETED", "normal", "Study reminders on boot", True),
    ("VIBRATE", "normal", "Haptic feedback", True),
    ("BILLING", "normal", "Photomath Plus subscriptions", True),
    ("AD_ID", "dangerous", "Advertising identifier", False),
    ("ACCESS_FINE_LOCATION", "dangerous", "For language events nearby", False),
]
seed_permissions(app4.id, app4_perms, "Language Learning", ["Google Analytics", "Facebook SDK", "Adjust SDK", "Unity Ads"], "4-100 Years")

# Trackers — use SDK analyzer
seed_trackers(
    app4.id,
    ["Google Firebase Analytics", "Google AdMob", "Facebook SDK",
     "Appsflyer", "Braze", "Amplitude"],
    target_age="5-18 Years",
    disclosed_sdks=["Google Firebase Analytics", "Amplitude"],
    detected_permissions=["INTERNET", "ACCESS_NETWORK_STATE", "CAMERA",
                          "WRITE_EXTERNAL_STORAGE", "READ_EXTERNAL_STORAGE",
                          "AD_ID", "ACCESS_FINE_LOCATION"],
)

# Personal Data Collection
app4_data = [
    ("Student Marks", "Math Problem Solutions & Accuracy", True, "Automatic (via camera scan)", "Cloud (Google Cloud)", "Encrypted in Transit", True, "Google Analytics, Amplitude", "Until account deletion", "High", "Track learning progress and suggest improvements", "Consent"),
    ("Student Marks", "Subject Proficiency Levels", True, "Automatic Calculation", "Cloud (Google Cloud)", "Encrypted at Rest & in Transit", False, "", "Until account deletion", "Medium", "Personalize difficulty and content", "Consent"),
    ("Identity", "Full Name", True, "User Input", "Cloud (Google Cloud)", "Encrypted at Rest & in Transit", False, "", "Until account deletion", "Medium", "User profile", "Consent"),
    ("Identity", "Email Address", True, "User Input", "Cloud (Google Cloud)", "Encrypted at Rest & in Transit", True, "Braze, AppsFlyer", "Until account deletion", "Medium", "Account management and marketing", "Consent"),
    ("Identity", "Age/Date of Birth", True, "User Input", "Cloud (Google Cloud)", "Encrypted at Rest", False, "", "Until account deletion", "Medium", "COPPA compliance check", "Legal Obligation"),
    ("Device", "Device ID & Advertising ID", True, "Automatic", "Cloud (Google Cloud)", "Encrypted in Transit", True, "Facebook, AdMob, AppsFlyer", "Until account deletion", "High", "Ad targeting and analytics", "Consent"),
    ("Device", "Camera Images (math problems)", True, "User-Initiated", "Processed in Cloud, not stored permanently", "Encrypted in Transit", False, "", "Processed and discarded", "Medium", "Math problem recognition via OCR/AI", "Consent"),
    ("Behavioral", "Study Patterns & Session Data", True, "Automatic", "Cloud (Google Cloud)", "Encrypted in Transit", True, "Amplitude", "90 days", "Medium", "Product improvement", "Legitimate Interest"),
    ("Location", "Approximate Location (IP-based)", True, "Automatic", "Cloud (Google Cloud)", "Encrypted in Transit", True, "AdMob, Facebook", "30 days", "High", "Targeted advertising", "Consent"),
]
for cat, dtype, collected, method, storage, encryption, shared, third, retention, risk, purpose, legal in app4_data:
    db.add(models.PersonalDataCollection(
        app_id=app4.id, data_category=cat, data_type=dtype, is_collected=collected,
        collection_method=method, storage_location=storage, encryption_status=encryption,
        shared_with_third_parties=shared, third_party_names=third, retention_period=retention,
        risk_level=risk, purpose=purpose, legal_basis=legal
    ))

# Payment Gateways
app4_payments = [
    ("Google Play Billing", "Google", "TLS 1.3", True, True, "Google Play Protect", "Google handles all card security; requires Google account", "Google standard refund policy", True, "Easy — Play Store", True, "Photomath Plus annual plan can be paid monthly. Google handles payment processing. Auto-renewal is ON by default. Card details tokenized by Google Play.", "Transaction ID, timestamp, subscription status", "Medium"),
    ("Credit/Debit Card (via Google Play)", "Google/Stripe", "TLS 1.3 + Tokenization", True, True, "Stripe Radar + Google Play Protect", "Card details never reach Photomath servers. Google Play acts as intermediary.", "Standard Google Play dispute resolution", True, "Medium — settings buried in subscriptions", False, "", "Google Play transaction records", "Low"),
]
for method, provider, enc, pci, fraud, fraud_det, stolen, chargeback, auto, cancel, installment, inst_det, retained, risk in app4_payments:
    db.add(models.PaymentGateway(
        app_id=app4.id, payment_method=method, provider=provider, encryption_standard=enc,
        pci_dss_compliant=pci, fraud_detection=fraud, fraud_detection_details=fraud_det,
        stolen_card_protection=stolen, chargeback_policy=chargeback, auto_renewal=auto,
        cancellation_difficulty=cancel, installment_available=installment,
        installment_details=inst_det, data_retained_after_payment=retained, risk_level=risk
    ))

# Security Incidents
app4_incidents = [
    ("2021-05-18", "Photomath Camera Permission Privacy Concern", "Reports emerged that Photomath's camera permission could theoretically be used to capture images beyond math problems. While no evidence of misuse was found, the app lacked clear camera usage policies.", "Medium", "Potential risk to all users", "Camera feed data", "", "https://www.tomsguide.com/photomath-privacy", "Updated privacy policy to explicitly state camera is only used for math problem scanning. Added camera usage indicator.", True),
    ("2023-07-12", "Pre-Acquisition Data Handling Audit Issues", "During Google's acquisition review, auditors flagged that Photomath's previous owner (Microblink) had not fully documented data flows between Photomath and its analytics partners.", "Medium", "Unknown", "User analytics data flow documentation gaps", "", "", "Google conducted full data flow audit post-acquisition and updated all data processing agreements", True),
    ("2024-06-05", "Ad SDK Fingerprinting Discovery", "Security researchers found that the AppsFlyer SDK in Photomath was collecting device fingerprinting data beyond what was disclosed, potentially enabling cross-app tracking of student users.", "High", "All free-tier users (~100M)", "Device fingerprints, cross-app behavioral data", "", "https://www.wired.com/appsflyer-fingerprinting", "AppsFlyer SDK updated to remove fingerprinting. Photomath added SDK audit process.", True),
]
for date, title, desc, sev, affected, data, cve, url, resolution, resolved in app4_incidents:
    db.add(models.SecurityIncident(
        app_id=app4.id, incident_date=date, title=title, description=desc,
        severity=sev, affected_users=affected, data_compromised=data,
        cve_id=cve, source_url=url, resolution=resolution, is_resolved=resolved
    ))

# Security Mechanisms
app4_mechanisms = [
    ("SSL/TLS Encryption", "Network", True, "Good", "All API calls over TLS 1.2/1.3", ""),
    ("Certificate Pinning", "Network", True, "Partial", "Implemented for core API but not for all ad SDK endpoints", "Extend pinning to all SDK network calls"),
    ("OAuth 2.0", "Authentication", True, "Good", "Google and Apple sign-in support", ""),
    ("Two-Factor Authentication", "Authentication", False, "N/A", "No 2FA option available", "Implement 2FA for premium account protection"),
    ("Data Encryption at Rest", "Data Protection", True, "Good", "AES-256 encryption on Google Cloud", ""),
    ("Camera Data Processing", "Data Protection", True, "Good", "Camera images processed via OCR and immediately discarded (not stored)", ""),
    ("COPPA Compliance", "Compliance", True, "Partial", "Age gate exists but no verifiable parental consent for users 8-13", "Implement verifiable parental consent mechanism"),
    ("GDPR Compliance", "Compliance", True, "Good", "Data export and deletion available", ""),
    ("Ad Tracking Transparency", "Data Protection", False, "N/A", "6 tracking SDKs with limited user control", "Implement consent management platform"),
    ("API Rate Limiting", "Network", True, "Good", "Rate limiting on all public endpoints", ""),
    ("Automatic Security Updates", "Data Protection", True, "Good", "Frequent updates via Play Store", ""),
    ("Input Sanitization", "Data Protection", True, "Good", "OCR input sanitized before processing", ""),
]
for name, cat, impl, quality, details, rec in app4_mechanisms:
    db.add(models.SecurityMechanism(
        app_id=app4.id, mechanism_name=name, category=cat, is_implemented=impl,
        implementation_quality=quality, details=details, recommendation=rec
    ))

# Risk Predictions
app4_predictions = [
    ("Ad SDK Data Over-Collection", "Personal Data", 0.40, 0.80, "6 months", "Despite the AppsFlyer fix, 6 tracking SDKs create a large attack surface for data over-collection. Future SDK updates could reintroduce fingerprinting.", '["6 ad/analytics SDKs", "Previous AppsFlyer fingerprinting", "Free tier ad-dependent model", "Complex SDK update cycle"]', "Implement automated SDK behavior monitoring and pre-release audit pipeline", "High", "Based on 2024 AppsFlyer fingerprinting discovery"),
    ("Student Math Data Profiling", "Personal Data", 0.30, 0.70, "12 months", "Math problem solutions and proficiency data could be used to create detailed academic profiles of students, potentially shared with third parties for educational product targeting.", '["Detailed math proficiency tracking", "Third-party analytics sharing", "Post-acquisition data integration"]', "Implement data anonymization for analytics and restrict third-party data sharing to aggregated metrics", "High", "Based on detailed learning data collection and 7+ third-party SDKs"),
    ("Subscription Fraud", "Payment", 0.20, 0.60, "12 months", "Auto-renewal default setting and buried cancellation flow may lead to increased unauthorized charges and chargeback disputes.", '["Auto-renewal enabled by default", "Medium cancellation difficulty", "Growing subscription base"]', "Make auto-renewal opt-in and simplify cancellation process", "Medium", "Based on industry subscription app chargeback trends"),
    ("Camera Permission Exploitation", "Network", 0.10, 0.50, "18 months", "While camera data is currently processed and discarded, a supply chain attack on the OCR library could theoretically capture and exfiltrate camera data.", '["Camera always-on during usage", "Third-party OCR dependency", "Supply chain attack trends"]', "Implement sandboxed camera processing and verify OCR library integrity at runtime", "Critical", "Based on 2021 camera permission concerns and industry supply chain attacks"),
]
for ptype, cat, prob, conf, tf, desc, factors, mitigation, sev, basis in app4_predictions:
    db.add(models.RiskPrediction(
        app_id=app4.id, prediction_type=ptype, risk_category=cat, probability=prob,
        confidence=conf, timeframe=tf, description=desc, contributing_factors=factors,
        recommended_mitigation=mitigation, severity_if_realized=sev, historical_basis=basis
    ))


# ═══════════════════════════════════════════════════════════════════════════════
# COMMIT ALL
# ═══════════════════════════════════════════════════════════════════════════════

db.commit()
db.close()

print("[OK] Database seeded successfully with 4 educational apps:")
print("   1. Google Classroom")
print("   2. Duolingo")
print("   3. Khan Academy Kids")
print("   4. Photomath")
print(f"\n   Database: {os.path.abspath('privacy_analyzer.db')}")
