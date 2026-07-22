"""
EduPrivacy-X: Multimodal Evidence Engine Database Models.

New models for the advanced multi-source privacy analysis platform.
These extend the existing models.py with support for:
- Multi-source evidence tracking (Feature A)
- Source-to-sink data flows (Feature C)
- Privacy policy NLP extractions (Feature E)
- Google Play Data Safety declarations (Feature A/F)
- Three-way disclosure mismatches (Feature F)
- Dynamic network captures (Feature J)
- ML predictions with SHAP explainability (Feature G)
- App version tracking for privacy drift (Feature O)
- Privacy dark patterns (Feature L)
- App review mining (Feature P)
- LLM generated reports
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, Float, ForeignKey, Text,
    DateTime, Enum as SQLEnum, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship
from database import Base
import enum


class LLMReport(Base):
    __tablename__ = "llm_reports"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("app_analyses.id"), unique=True)
    provider = Column(String)  # e.g., "gemini-1.5-pro"
    tone = Column(String)      # e.g., "educational"
    report_markdown = Column(Text)
    generated_at = Column(String)
    
    app = relationship("AppAnalysis", backref="llm_report")


# ─── Enums ─────────────────────────────────────────────────────────────────────

class EvidenceSourceType(str, enum.Enum):
    """The six evidence sources defined in Feature A."""
    MANIFEST = "manifest"
    DECOMPILED_CODE = "decompiled_code"
    APP_UI = "app_ui"
    NETWORK_TRAFFIC = "network_traffic"
    PRIVACY_POLICY = "privacy_policy"
    DATA_SAFETY = "data_safety"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class DisclosureType(str, enum.Enum):
    """Four types of inconsistency from Feature F."""
    UNDER_DISCLOSURE = "under_disclosure"      # behaviour detected but not declared
    OVER_DISCLOSURE = "over_disclosure"         # declared but no evidence found
    POLICY_CONFLICT = "policy_conflict"         # policy and Data Safety disagree
    AMBIGUOUS_DISCLOSURE = "ambiguous_disclosure"  # vague language like "may collect"


class DataFlowNodeType(str, enum.Enum):
    SOURCE = "source"
    INTERMEDIATE = "intermediate"
    SINK = "sink"


# ─── Evidence Source Tracking (Feature A) ───────────────────────────────────────

class EvidenceSource(Base):
    """
    Tracks individual pieces of privacy-related evidence from any of
    the 6 multimodal sources. Each finding in the system links back
    to one or more EvidenceSource records, providing full provenance.
    """
    __tablename__ = "evidence_sources"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("app_analyses.id"), index=True)
    source_type = Column(String, index=True)  # EvidenceSourceType value
    evidence_category = Column(String)  # e.g., "location_collection", "device_id_access"
    data_type = Column(String)  # e.g., "Location", "Device ID", "Contacts"
    description = Column(Text)  # Human-readable description of the finding
    confidence = Column(Float, default=0.5)  # 0.0-1.0 confidence score
    severity = Column(String, default="medium")  # low, medium, high, critical
    raw_evidence = Column(Text, default="")  # Raw evidence data (manifest line, API call, etc.)
    file_reference = Column(String, default="")  # Source file/location within APK
    line_number = Column(Integer, nullable=True)  # Line number in source file
    timestamp = Column(String, default="")  # When the evidence was collected
    is_confirmed = Column(Boolean, default=False)  # Cross-validated by another source
    confirmed_by = Column(Text, default="[]")  # JSON: list of other evidence IDs that confirm

    app = relationship("AppAnalysis", backref="evidence_sources")


# ─── Source-to-Sink Data Flow (Feature C) ────────────────────────────────────

class DataFlow(Base):
    """
    Represents a traced data flow from a sensitive data source to a sink.
    Used by the taint analysis engine to show how private data moves
    through the application.
    """
    __tablename__ = "data_flows"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("app_analyses.id"), index=True)
    flow_name = Column(String)  # Human-readable label, e.g., "Location → Ad Network"
    data_type = Column(String)  # e.g., "Location", "Device ID", "Email"
    source_type = Column(String)  # e.g., "LocationManager.getLastKnownLocation()"
    source_class = Column(String, default="")  # Java class containing the source
    source_method = Column(String, default="")  # Method containing the source
    sink_type = Column(String)  # e.g., "HttpURLConnection.connect()", "analytics.logEvent()"
    sink_class = Column(String, default="")  # Java class containing the sink
    sink_method = Column(String, default="")  # Method containing the sink
    sink_category = Column(String)  # "network", "analytics_sdk", "ad_sdk", "log", "database", "storage", "clipboard", "third_party_api"
    intermediate_steps = Column(Text, default="[]")  # JSON array of intermediate nodes
    is_encrypted = Column(Boolean, default=None, nullable=True)
    destination_domain = Column(String, default="")  # Domain the data is sent to
    destination_country = Column(String, default="")  # Country of destination
    sdk_attribution = Column(String, default="app")  # "app" or SDK name
    risk_level = Column(String, default="medium")
    confidence = Column(Float, default=0.5)
    evidence_source_id = Column(Integer, ForeignKey("evidence_sources.id"), nullable=True)

    app = relationship("AppAnalysis", backref="data_flows")


class DataFlowNode(Base):
    """Individual node in a data flow graph for interactive Sankey visualisation."""
    __tablename__ = "data_flow_nodes"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("app_analyses.id"), index=True)
    flow_id = Column(Integer, ForeignKey("data_flows.id"), nullable=True)
    node_type = Column(String)  # "source", "intermediate", "sink"
    label = Column(String)  # Display label
    category = Column(String, default="")  # For grouping in Sankey
    class_name = Column(String, default="")
    method_name = Column(String, default="")
    order_index = Column(Integer, default=0)  # Position in the flow

    app = relationship("AppAnalysis", backref="data_flow_nodes")


# ─── Privacy Policy NLP Extraction (Feature E) ──────────────────────────────

class PrivacyPolicyExtraction(Base):
    """
    Stores structured information extracted from an app's privacy policy
    using NLP (DistilBERT, RoBERTa, Legal-BERT, etc.).
    """
    __tablename__ = "privacy_policy_extractions"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("app_analyses.id"), index=True)
    policy_url = Column(String, default="")
    policy_text_hash = Column(String, default="")  # To detect changes
    policy_word_count = Column(Integer, default=0)
    readability_score = Column(Float, default=0.0)  # Flesch-Kincaid or similar
    extraction_model = Column(String, default="")  # Model used for extraction
    extracted_at = Column(String, default="")

    # ── Extracted structured claims ──
    collects_location = Column(Boolean, nullable=True)
    collects_device_id = Column(Boolean, nullable=True)
    collects_contacts = Column(Boolean, nullable=True)
    collects_camera = Column(Boolean, nullable=True)
    collects_microphone = Column(Boolean, nullable=True)
    collects_email = Column(Boolean, nullable=True)
    collects_name = Column(Boolean, nullable=True)
    collects_age_dob = Column(Boolean, nullable=True)
    collects_school_info = Column(Boolean, nullable=True)
    collects_academic_data = Column(Boolean, nullable=True)
    collects_behavioral_data = Column(Boolean, nullable=True)
    collects_financial_data = Column(Boolean, nullable=True)

    shares_with_advertisers = Column(Boolean, nullable=True)
    shares_with_analytics = Column(Boolean, nullable=True)
    shares_with_third_parties = Column(Boolean, nullable=True)
    third_party_names = Column(Text, default="[]")  # JSON array

    mentions_children = Column(Boolean, nullable=True)
    mentions_coppa = Column(Boolean, nullable=True)
    mentions_gdpr = Column(Boolean, nullable=True)
    mentions_parental_consent = Column(Boolean, nullable=True)
    provides_deletion_method = Column(Boolean, nullable=True)
    provides_opt_out = Column(Boolean, nullable=True)
    specifies_retention_period = Column(Boolean, nullable=True)
    retention_details = Column(Text, default="")

    advertising_practices = Column(Text, default="")  # Description of ad practices
    security_claims = Column(Text, default="")  # What security measures they claim
    contact_info = Column(Text, default="")  # DPO or contact
    international_transfer = Column(Boolean, nullable=True)
    user_rights_described = Column(Text, default="[]")  # JSON array of rights

    # Raw NLP confidence scores for each extraction
    extraction_confidences = Column(Text, default="{}")  # JSON dict of field→confidence

    app = relationship("AppAnalysis", backref="privacy_policy_extractions")


# ─── Google Play Data Safety Declaration (Feature A/F) ──────────────────────

class DataSafetyDeclaration(Base):
    """
    Stores the structured Data Safety declaration from Google Play.
    Used for three-way contradiction detection (Feature F).
    """
    __tablename__ = "data_safety_declarations"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("app_analyses.id"), index=True)
    fetched_at = Column(String, default="")
    play_store_url = Column(String, default="")

    # ── Data types declared as collected ──
    declares_location_collected = Column(Boolean, nullable=True)
    declares_location_shared = Column(Boolean, nullable=True)
    declares_personal_info_collected = Column(Boolean, nullable=True)
    declares_personal_info_shared = Column(Boolean, nullable=True)
    declares_financial_info_collected = Column(Boolean, nullable=True)
    declares_contacts_collected = Column(Boolean, nullable=True)
    declares_contacts_shared = Column(Boolean, nullable=True)
    declares_photos_videos_collected = Column(Boolean, nullable=True)
    declares_audio_collected = Column(Boolean, nullable=True)
    declares_device_id_collected = Column(Boolean, nullable=True)
    declares_device_id_shared = Column(Boolean, nullable=True)
    declares_app_activity_collected = Column(Boolean, nullable=True)
    declares_web_browsing_collected = Column(Boolean, nullable=True)
    declares_messages_collected = Column(Boolean, nullable=True)
    declares_health_fitness_collected = Column(Boolean, nullable=True)

    # ── Security & privacy practices ──
    declares_data_encrypted_in_transit = Column(Boolean, nullable=True)
    declares_data_deletion_available = Column(Boolean, nullable=True)
    declares_independent_security_review = Column(Boolean, nullable=True)
    declares_family_policy_compliance = Column(Boolean, nullable=True)

    # ── Purpose declarations ──
    purposes_app_functionality = Column(Boolean, nullable=True)
    purposes_analytics = Column(Boolean, nullable=True)
    purposes_advertising = Column(Boolean, nullable=True)
    purposes_personalization = Column(Boolean, nullable=True)
    purposes_account_management = Column(Boolean, nullable=True)
    purposes_fraud_prevention = Column(Boolean, nullable=True)

    # Raw scraped data for reference
    raw_declaration = Column(Text, default="{}")  # Full JSON of scraped data

    app = relationship("AppAnalysis", backref="data_safety_declarations")


# ─── Three-Way Disclosure Mismatch (Feature F) ──────────────────────────────

class DisclosureMismatch(Base):
    """
    Records inconsistencies between privacy policy, Data Safety declaration,
    and technically observed behaviour. This is the core of the three-way
    contradiction detection engine.
    """
    __tablename__ = "disclosure_mismatches"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("app_analyses.id"), index=True)
    data_type = Column(String)  # e.g., "Location", "Device ID", "Contacts"
    mismatch_type = Column(String)  # DisclosureType value

    # Three-way comparison
    privacy_policy_claim = Column(String, default="unknown")  # "collected", "not_mentioned", "denied", "ambiguous"
    data_safety_declaration = Column(String, default="unknown")  # "collected", "not_collected", "shared", "not_declared"
    technical_evidence = Column(String, default="unknown")  # "detected", "not_detected", "inconclusive"

    # Detail and scoring
    description = Column(Text, default="")
    severity = Column(String, default="medium")  # low, medium, high, critical
    confidence = Column(Float, default=0.5)
    risk_contribution = Column(Float, default=0.0)  # How much this adds to overall risk

    # Evidence linking
    evidence_source_ids = Column(Text, default="[]")  # JSON array of evidence IDs
    policy_excerpt = Column(Text, default="")  # Relevant policy text
    data_safety_detail = Column(Text, default="")  # What Data Safety says
    technical_detail = Column(Text, default="")  # Technical evidence description

    app = relationship("AppAnalysis", backref="disclosure_mismatches")


# ─── Dynamic Network Captures (Feature J) ───────────────────────────────────

class NetworkCapture(Base):
    """
    Records network traffic observed during dynamic analysis.
    Supports consent experiment and idle-behaviour experiment.
    """
    __tablename__ = "network_captures"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("app_analyses.id"), index=True)
    capture_phase = Column(String, default="runtime")  # "pre_consent", "post_consent", "post_rejection", "idle", "runtime"
    timestamp = Column(String, default="")
    domain = Column(String)
    full_url = Column(String, default="")
    ip_address = Column(String, default="")
    protocol = Column(String, default="https")  # http, https
    method = Column(String, default="GET")  # GET, POST, etc.
    request_size_bytes = Column(Integer, default=0)
    response_size_bytes = Column(Integer, default=0)
    content_type = Column(String, default="")

    # Traffic classification
    traffic_category = Column(String, default="unknown")  # "app_functionality", "analytics", "advertising", "social", "unknown"
    sdk_attribution = Column(String, default="")  # SDK name if attributable
    destination_country = Column(String, default="")
    destination_org = Column(String, default="")

    # Data sensitivity
    contains_device_id = Column(Boolean, default=False)
    contains_ad_id = Column(Boolean, default=False)
    contains_location = Column(Boolean, default=False)
    contains_personal_data = Column(Boolean, default=False)
    data_types_transmitted = Column(Text, default="[]")  # JSON array
    is_encrypted = Column(Boolean, default=True)

    # TLS details
    tls_version = Column(String, default="")
    certificate_valid = Column(Boolean, default=True)
    certificate_pinned = Column(Boolean, default=False)

    app = relationship("AppAnalysis", backref="network_captures")


# ─── ML Prediction with SHAP Explainability (Feature G) ─────────────────────

class MLRiskPrediction(Base):
    """
    Stores ML model predictions with SHAP-based explanations.
    Separate from the existing RiskPrediction model which stores
    heuristic-based predictions.
    """
    __tablename__ = "ml_risk_predictions"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("app_analyses.id"), index=True)
    model_name = Column(String)  # "xgboost", "lightgbm", "random_forest", "logistic_regression"
    model_version = Column(String, default="1.0")
    predicted_at = Column(String, default="")

    # Prediction output
    risk_category = Column(String)  # "low", "moderate", "high", "critical"
    risk_score = Column(Float)  # 0-100
    prediction_confidence = Column(Float)  # 0.0-1.0
    probability_low = Column(Float, default=0.0)
    probability_moderate = Column(Float, default=0.0)
    probability_high = Column(Float, default=0.0)
    probability_critical = Column(Float, default=0.0)

    # Feature importances (top features)
    feature_values = Column(Text, default="{}")  # JSON: feature_name → value
    shap_values = Column(Text, default="{}")  # JSON: feature_name → SHAP value
    top_risk_factors = Column(Text, default="[]")  # JSON array of {feature, value, shap_value, direction}
    top_protective_factors = Column(Text, default="[]")  # JSON array

    # Calibration
    is_calibrated = Column(Boolean, default=False)
    calibrated_score = Column(Float, nullable=True)

    app = relationship("AppAnalysis", backref="ml_risk_predictions")


# ─── Hybrid Risk Score (Feature H) ──────────────────────────────────────────

class HybridRiskScore(Base):
    """
    Two-stage hybrid risk score: expert rule-based + ML-calibrated.
    Stores both the theoretically grounded and empirically calibrated scores.
    """
    __tablename__ = "hybrid_risk_scores"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("app_analyses.id"), index=True)
    computed_at = Column(String, default="")

    # Stage 1: Expert rule-based dimensions
    sensitive_data_score = Column(Float, default=0.0)       # Weight: 20%
    data_transmission_score = Column(Float, default=0.0)    # Weight: 20%
    third_party_tracker_score = Column(Float, default=0.0)  # Weight: 15%
    disclosure_inconsistency_score = Column(Float, default=0.0)  # Weight: 15%
    child_vulnerability_score = Column(Float, default=0.0)  # Weight: 10%
    insecure_storage_comms_score = Column(Float, default=0.0)  # Weight: 10%
    transparency_control_score = Column(Float, default=0.0)  # Weight: 10%

    expert_weighted_score = Column(Float, default=0.0)  # Weighted combination
    expert_risk_category = Column(String, default="moderate")

    # Stage 2: ML-calibrated
    ml_calibrated_score = Column(Float, nullable=True)
    ml_calibrated_category = Column(String, nullable=True)
    calibration_delta = Column(Float, nullable=True)  # Difference between expert and ML

    # Final combined
    final_score = Column(Float, default=0.0)
    final_category = Column(String, default="moderate")

    app = relationship("AppAnalysis", backref="hybrid_risk_scores")


# ─── App Version Tracking (Feature O) ───────────────────────────────────────

class AppVersion(Base):
    """
    Tracks privacy changes across different versions of an application.
    Enables privacy drift detection.
    """
    __tablename__ = "app_versions"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("app_analyses.id"), index=True)
    version_name = Column(String)
    version_code = Column(Integer, nullable=True)
    analyzed_at = Column(String, default="")
    apk_hash = Column(String, default="")

    # Snapshot of key metrics at this version
    risk_score = Column(Float, default=0.0)
    permission_count = Column(Integer, default=0)
    dangerous_permission_count = Column(Integer, default=0)
    tracker_count = Column(Integer, default=0)
    ad_sdk_count = Column(Integer, default=0)
    data_flow_count = Column(Integer, default=0)
    mismatch_count = Column(Integer, default=0)
    network_domain_count = Column(Integer, default=0)

    # Change detection from previous version
    new_permissions = Column(Text, default="[]")  # JSON array
    removed_permissions = Column(Text, default="[]")
    new_trackers = Column(Text, default="[]")
    removed_trackers = Column(Text, default="[]")
    new_domains = Column(Text, default="[]")
    policy_changed = Column(Boolean, default=False)
    data_safety_changed = Column(Boolean, default=False)
    risk_score_delta = Column(Float, default=0.0)

    app = relationship("AppAnalysis", backref="app_versions")


# ─── Privacy Dark Patterns (Feature L) ──────────────────────────────────────

class DarkPattern(Base):
    """
    Records detected privacy dark patterns in the app's UI/UX.
    """
    __tablename__ = "dark_patterns"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("app_analyses.id"), index=True)
    pattern_type = Column(String)  # e.g., "forced_consent", "hidden_reject", "preselected_consent"
    pattern_name = Column(String)  # Human-readable name
    description = Column(Text, default="")
    severity = Column(String, default="medium")
    screen_name = Column(String, default="")  # Which app screen
    screenshot_path = Column(String, default="")
    ui_element_details = Column(Text, default="")  # UI hierarchy info
    detection_method = Column(String, default="rule_based")  # "rule_based", "ocr", "vlm"
    confidence = Column(Float, default=0.5)

    app = relationship("AppAnalysis", backref="dark_patterns")


# ─── App Review Mining (Feature P) ──────────────────────────────────────────

class AppReview(Base):
    """
    Stores privacy-relevant user reviews mined from public sources.
    """
    __tablename__ = "app_reviews"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("app_analyses.id"), index=True)
    review_text = Column(Text)
    rating = Column(Integer, default=0)  # 1-5 stars
    review_date = Column(String, default="")
    reviewer_name = Column(String, default="")

    # NLP classification
    is_privacy_related = Column(Boolean, default=False)
    privacy_topic = Column(String, default="")  # "permissions", "ads", "tracking", "data_deletion", etc.
    sentiment = Column(String, default="neutral")  # "positive", "negative", "neutral"
    sentiment_score = Column(Float, default=0.0)  # -1.0 to 1.0

    # Cross-reference with technical evidence
    matches_technical_evidence = Column(Boolean, nullable=True)
    matched_evidence_ids = Column(Text, default="[]")  # JSON array

    app = relationship("AppAnalysis", backref="app_reviews")


# ─── Child-Specific Privacy Assessment (Feature I) ──────────────────────────

class ChildPrivacyAssessment(Base):
    """
    Child and student-specific privacy risk assessment.
    Uses the Educational & Child Privacy Risk Taxonomy.
    """
    __tablename__ = "child_privacy_assessments"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("app_analyses.id"), index=True)
    assessed_at = Column(String, default="")

    # Student-specific data collection flags
    collects_student_name = Column(Boolean, nullable=True)
    collects_age_dob = Column(Boolean, nullable=True)
    collects_school_name = Column(Boolean, nullable=True)
    collects_class_grade = Column(Boolean, nullable=True)
    collects_academic_performance = Column(Boolean, nullable=True)
    collects_learning_difficulties = Column(Boolean, nullable=True)
    collects_behavioral_data = Column(Boolean, nullable=True)
    collects_voice_recordings = Column(Boolean, nullable=True)
    collects_facial_images = Column(Boolean, nullable=True)
    collects_parent_contact = Column(Boolean, nullable=True)
    collects_location = Column(Boolean, nullable=True)
    collects_peer_communication = Column(Boolean, nullable=True)
    collects_advertising_profile = Column(Boolean, nullable=True)
    collects_learner_profile = Column(Boolean, nullable=True)

    # Compliance flags
    has_parental_consent_mechanism = Column(Boolean, nullable=True)
    has_age_gate = Column(Boolean, nullable=True)
    has_child_directed_treatment = Column(Boolean, nullable=True)
    has_coppa_compliance = Column(Boolean, nullable=True)
    has_student_data_policy = Column(Boolean, nullable=True)

    # Scoring
    child_risk_score = Column(Float, default=0.0)  # 0-100 with child amplification
    general_risk_score = Column(Float, default=0.0)  # 0-100 without amplification
    amplification_factor = Column(Float, default=1.0)  # How much child context increases risk
    risk_category = Column(String, default="moderate")

    # Detail
    risk_factors = Column(Text, default="[]")  # JSON array of risk factor descriptions
    recommendations = Column(Text, default="[]")  # JSON array

    app = relationship("AppAnalysis", backref="child_privacy_assessments")
