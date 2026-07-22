from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base


class AppAnalysis(Base):
    __tablename__ = "app_analyses"

    id = Column(Integer, primary_key=True, index=True)
    app_name = Column(String, index=True)
    package_name = Column(String, index=True)
    developer = Column(String)
    category = Column(String)
    version_name = Column(String)
    apk_size = Column(String)
    target_sdk = Column(Integer)
    apk_hash = Column(String)
    analyzed_at = Column(String)
    description = Column(Text, default="")
    icon_url = Column(String, default="")
    play_store_rating = Column(Float, default=0.0)
    installs = Column(String, default="")
    target_age = Column(String, default="")

    # Risk scoring
    risk_score = Column(Integer)
    risk_grade = Column(String)
    risk_level = Column(String)
    risk_dimensions_json = Column(Text, default="{}")

    # Security overview fields
    encryption_protocol = Column(String, default="")
    authentication_method = Column(String, default="")
    data_storage_type = Column(String, default="")
    has_2fa = Column(Boolean, default=False)
    compliance_standards = Column(String, default="")  # comma-separated: COPPA,GDPR,FERPA

    # Relationships
    permissions = relationship("AppPermission", back_populates="app", cascade="all, delete-orphan")
    trackers = relationship("AppTracker", back_populates="app", cascade="all, delete-orphan")
    personal_data = relationship("PersonalDataCollection", back_populates="app", cascade="all, delete-orphan")
    payment_gateways = relationship("PaymentGateway", back_populates="app", cascade="all, delete-orphan")
    security_incidents = relationship("SecurityIncident", back_populates="app", cascade="all, delete-orphan")
    security_mechanisms = relationship("SecurityMechanism", back_populates="app", cascade="all, delete-orphan")
    risk_predictions = relationship("RiskPrediction", back_populates="app", cascade="all, delete-orphan")


class AppPermission(Base):
    __tablename__ = "app_permissions"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("app_analyses.id"))
    name = Column(String)
    status = Column(String)  # 'normal' or 'dangerous'
    description = Column(String)
    justified = Column(Boolean, default=False)

    # ── Context-Aware Permission Analysis (Feature B) ──
    necessity_score = Column(Integer, default=50)           # 0-100: how necessary for educational purpose
    educational_justification = Column(String, default="")  # justified | conditional | excessive | unnecessary
    sdk_attribution = Column(String, default="app")         # "app" or SDK name
    risk_category = Column(String, default="other")         # identity, location, media_capture, etc.
    privacy_risk_level = Column(String, default="medium")   # low | medium | high | critical
    is_actually_used = Column(Boolean, default=None, nullable=True)  # None = unknown
    alternative_permission = Column(Text, default="")       # JSON string: {"alternative": ..., "reason": ...}
    explanation = Column(Text, default="")                  # Human-readable context explanation
    child_risk_multiplier = Column(Float, default=1.0)      # 1.0-2.0 amplification for child apps
    base_risk_weight = Column(Float, default=0.3)           # 0.0-1.0 base privacy risk
    adjusted_risk_weight = Column(Float, default=0.3)       # 0.0-1.0 after child multiplier

    app = relationship("AppAnalysis", back_populates="permissions")


class AppTracker(Base):
    __tablename__ = "app_trackers"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("app_analyses.id"))
    name = Column(String)
    risk = Column(String)
    description = Column(String)
    category = Column(String)

    # ── SDK & Tracker Intelligence (Feature D) ──
    provider = Column(String, default="Unknown")
    privacy_impact = Column(String, default="medium")        # low | medium | high | critical
    data_accessed = Column(Text, default="[]")               # JSON array of data types
    permissions_connected = Column(Text, default="[]")       # JSON array of permissions
    network_domains = Column(Text, default="[]")             # JSON array of domains
    child_appropriate = Column(Boolean, default=None, nullable=True)
    coppa_mode_available = Column(Boolean, default=False)
    gdpr_compliant = Column(Boolean, default=True)
    is_disclosed = Column(Boolean, default=False)            # In Data Safety declaration
    disclosure_status = Column(String, default="unknown")    # disclosed | undisclosed | unknown
    risk_score = Column(Integer, default=50)                 # 0-100 SDK risk score
    child_risk_multiplier = Column(Float, default=1.0)
    privacy_config_issues = Column(Text, default="[]")       # JSON array of issues
    recommendation = Column(Text, default="")

    app = relationship("AppAnalysis", back_populates="trackers")


class PersonalDataCollection(Base):
    """Tracks what personal data each app collects."""
    __tablename__ = "personal_data_collection"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("app_analyses.id"))
    data_category = Column(String)        # e.g., "Student Marks", "Identity", "Contact", "Device", "Behavioral"
    data_type = Column(String)            # e.g., "Grades & Scores", "Full Name", "Email Address"
    is_collected = Column(Boolean, default=False)
    collection_method = Column(String)    # e.g., "User Input", "Automatic", "Third-Party SDK"
    storage_location = Column(String)     # e.g., "Cloud (Google Servers)", "Local Device"
    encryption_status = Column(String)    # e.g., "Encrypted at Rest", "Encrypted in Transit", "Not Encrypted"
    shared_with_third_parties = Column(Boolean, default=False)
    third_party_names = Column(String, default="")  # comma-separated
    retention_period = Column(String, default="")   # e.g., "Until account deletion", "1 year"
    risk_level = Column(String, default="Low")  # Low, Medium, High, Critical
    purpose = Column(String, default="")  # Why it's collected
    legal_basis = Column(String, default="")  # e.g., "Consent", "Legitimate Interest"

    app = relationship("AppAnalysis", back_populates="personal_data")


class PaymentGateway(Base):
    """Analyzes payment security for each app."""
    __tablename__ = "payment_gateways"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("app_analyses.id"))
    payment_method = Column(String)         # e.g., "Google Play Billing", "PayPal", "Credit Card", "Installment"
    provider = Column(String)               # e.g., "Stripe", "PayPal", "Google"
    encryption_standard = Column(String)    # e.g., "TLS 1.3", "AES-256"
    pci_dss_compliant = Column(Boolean, default=False)
    fraud_detection = Column(Boolean, default=False)
    fraud_detection_details = Column(Text, default="")
    stolen_card_protection = Column(String, default="")  # What happens if stolen card is used
    chargeback_policy = Column(String, default="")
    auto_renewal = Column(Boolean, default=False)
    cancellation_difficulty = Column(String, default="")  # Easy, Medium, Hard
    installment_available = Column(Boolean, default=False)
    installment_details = Column(Text, default="")  # What data is retained, terms
    data_retained_after_payment = Column(String, default="")
    risk_level = Column(String, default="Low")

    app = relationship("AppAnalysis", back_populates="payment_gateways")


class SecurityIncident(Base):
    """Historical security breaches and incidents."""
    __tablename__ = "security_incidents"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("app_analyses.id"))
    incident_date = Column(String)          # ISO date string
    title = Column(String)
    description = Column(Text)
    severity = Column(String)               # Critical, High, Medium, Low
    affected_users = Column(String)         # e.g., "500,000", "Unknown"
    data_compromised = Column(String)       # What data was leaked
    cve_id = Column(String, default="")     # CVE identifier if applicable
    source_url = Column(String, default="") # Link to report/news
    resolution = Column(Text, default="")   # How it was resolved
    is_resolved = Column(Boolean, default=True)

    app = relationship("AppAnalysis", back_populates="security_incidents")


class SecurityMechanism(Base):
    """Security features and protocols used by the app."""
    __tablename__ = "security_mechanisms"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("app_analyses.id"))
    mechanism_name = Column(String)         # e.g., "SSL Certificate Pinning"
    category = Column(String)               # e.g., "Network", "Authentication", "Data Protection", "Compliance"
    is_implemented = Column(Boolean, default=False)
    implementation_quality = Column(String, default="")  # Good, Partial, Poor
    details = Column(Text, default="")
    recommendation = Column(Text, default="")

    app = relationship("AppAnalysis", back_populates="security_mechanisms")


class RiskPrediction(Base):
    """Predicted future risks based on historical patterns."""
    __tablename__ = "risk_predictions"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("app_analyses.id"))
    prediction_type = Column(String)        # e.g., "Data Breach", "Permission Escalation", "Third-Party SDK Vulnerability"
    risk_category = Column(String)          # e.g., "Personal Data", "Payment", "Network"
    probability = Column(Float)             # 0.0 to 1.0
    confidence = Column(Float)             # 0.0 to 1.0
    timeframe = Column(String)             # e.g., "6 months", "1 year"
    description = Column(Text)
    contributing_factors = Column(Text)    # JSON string of factors
    recommended_mitigation = Column(Text)
    severity_if_realized = Column(String)  # Critical, High, Medium, Low
    historical_basis = Column(Text)        # What past data supports this prediction

    app = relationship("AppAnalysis", back_populates="risk_predictions")
