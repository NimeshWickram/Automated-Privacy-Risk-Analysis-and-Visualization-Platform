"""
Rule-based chatbot engine for Privacy Risk Analysis.
Uses keyword matching and decision trees with contextual app data.
"""

import re
from sqlalchemy.orm import Session
import models


# ─── Knowledge Base: Common Q&A patterns ───────────────────────────────────────

GENERAL_KNOWLEDGE = {
    "coppa": {
        "answer": "COPPA (Children's Online Privacy Protection Act) is a US federal law that imposes requirements on operators of websites or online services directed at children under 13. It requires verifiable parental consent before collecting personal information from children.",
        "follow_up": "Would you like to know which of our analyzed apps are COPPA compliant?"
    },
    "gdpr": {
        "answer": "GDPR (General Data Protection Regulation) is a European Union regulation on data protection and privacy. It gives individuals control over their personal data and applies to any organization processing EU citizens' data, regardless of the organization's location.",
        "follow_up": "Would you like to check GDPR compliance status for a specific app?"
    },
    "ferpa": {
        "answer": "FERPA (Family Educational Rights and Privacy Act) protects the privacy of student education records. Schools must have written permission from parents or eligible students to release any information from a student's education record.",
        "follow_up": "Student marks and grades are specifically protected under FERPA."
    },
    "pci_dss": {
        "answer": "PCI-DSS (Payment Card Industry Data Security Standard) is a set of security standards designed to ensure that all companies that accept, process, store or transmit credit card information maintain a secure environment. Compliance is mandatory for any app handling payment card data.",
        "follow_up": "Would you like to know the PCI-DSS compliance status of a specific app?"
    },
    "ssl_pinning": {
        "answer": "SSL Certificate Pinning is a security mechanism that associates a host with its expected SSL certificate. It prevents man-in-the-middle attacks by rejecting certificates that don't match the pinned certificate, even if they are signed by a trusted CA.",
        "follow_up": "Apps without SSL pinning are vulnerable to traffic interception on public Wi-Fi networks."
    },
    "two_factor": {
        "answer": "Two-Factor Authentication (2FA) adds an extra layer of security by requiring two different types of verification: something you know (password) and something you have (phone, security key). This significantly reduces unauthorized access risk.",
        "follow_up": "Would you like to check which apps support 2FA?"
    },
}

# ─── Intent patterns ────────────────────────────────────────────────────────────

INTENT_PATTERNS = [
    # Stolen card / fraud scenarios
    {
        "patterns": [r"stolen\s*(atm|card|credit)", r"fraud", r"unauthorized.*payment", r"someone.*stole.*card"],
        "intent": "stolen_card",
    },
    # PayPal specific
    {
        "patterns": [r"paypal", r"pay\s*pal"],
        "intent": "paypal",
    },
    # Installment payment
    {
        "patterns": [r"install?ment", r"emi", r"monthly.*pay", r"pay.*monthly", r"recurring.*pay"],
        "intent": "installment",
    },
    # Student marks / grades
    {
        "patterns": [r"student.*mark", r"grade", r"score", r"academic.*record", r"mark.*safe", r"marks.*third"],
        "intent": "student_marks",
    },
    # Personal data
    {
        "patterns": [r"personal\s*data", r"collect.*data", r"what.*data", r"privacy", r"data.*collect"],
        "intent": "personal_data",
    },
    # Security mechanisms
    {
        "patterns": [r"security.*feature", r"security.*mechanism", r"how.*secure", r"is.*safe", r"protection"],
        "intent": "security_mechanisms",
    },
    # Security incidents / breaches
    {
        "patterns": [r"breach", r"hack", r"incident", r"leak", r"vulnerability", r"cve", r"compromis"],
        "intent": "security_incidents",
    },
    # Risk predictions
    {
        "patterns": [r"predict", r"future.*risk", r"what.*might.*happen", r"forecast", r"trend"],
        "intent": "risk_predictions",
    },
    # Payment security general
    {
        "patterns": [r"payment.*secur", r"pay.*safe", r"transaction", r"billing"],
        "intent": "payment_security",
    },
    # Third-party data sharing
    {
        "patterns": [r"third.*party", r"shar.*data", r"who.*access", r"who.*get.*data"],
        "intent": "third_party_sharing",
    },
    # Compare apps
    {
        "patterns": [r"compar", r"which.*better", r"which.*safer", r"safest.*app", r"best.*app"],
        "intent": "compare_apps",
    },
    # Compliance
    {
        "patterns": [r"coppa", r"gdpr", r"ferpa", r"complian", r"regulation", r"law"],
        "intent": "compliance",
    },
    # General help / greeting
    {
        "patterns": [r"^(hi|hello|hey|help|what can you)", r"how.*work", r"what.*do"],
        "intent": "greeting",
    },
]


def detect_intent(message: str) -> tuple:
    """Detect the intent of a user message. Returns (intent, matched_pattern)."""
    message_lower = message.lower().strip()
    for item in INTENT_PATTERNS:
        for pattern in item["patterns"]:
            if re.search(pattern, message_lower):
                return item["intent"], pattern
    return "unknown", None


def find_app_in_message(message: str, db: Session) -> models.AppAnalysis | None:
    """Try to find which app the user is asking about."""
    apps = db.query(models.AppAnalysis).all()
    message_lower = message.lower()
    for app in apps:
        if app.app_name.lower() in message_lower:
            return app
        # Also check partial matches
        name_parts = app.app_name.lower().split()
        for part in name_parts:
            if len(part) > 3 and part in message_lower:
                return app
    return None


def get_all_app_names(db: Session) -> list:
    """Get all app names from the database."""
    apps = db.query(models.AppAnalysis).all()
    return [app.app_name for app in apps]


# ─── Response generators ────────────────────────────────────────────────────────

def handle_greeting(db: Session) -> str:
    app_names = get_all_app_names(db)
    apps_list = ", ".join(app_names) if app_names else "no apps yet"
    return (
        f"👋 Hello! I'm the **PrivacyGuard AI Advisor**. I can help you understand the privacy and security risks of educational apps.\n\n"
        f"I currently have analysis data for: **{apps_list}**.\n\n"
        f"Here are some things you can ask me:\n"
        f"- 🔒 \"Is [app name] safe for my child's data?\"\n"
        f"- 💳 \"What happens if someone uses a stolen card on Duolingo?\"\n"
        f"- 📊 \"What personal data does Google Classroom collect?\"\n"
        f"- 🛡️ \"What security features does Khan Academy Kids have?\"\n"
        f"- ⚠️ \"Has Photomath had any security breaches?\"\n"
        f"- 🔮 \"What are the predicted risks for these apps?\"\n"
        f"- ⚖️ \"Which app is the safest?\""
    )


def handle_stolen_card(app: models.AppAnalysis | None, db: Session) -> str:
    if app is None:
        app_names = get_all_app_names(db)
        return (
            f"🚨 **Stolen Card Scenario**\n\n"
            f"This is a serious concern. When a stolen ATM/credit card is used on an educational app, several things can happen:\n\n"
            f"1. **Unauthorized purchases** — The thief can buy premium subscriptions or in-app content\n"
            f"2. **Data exposure** — Payment processing may store card details\n"
            f"3. **Chargeback complications** — Reversing transactions can be difficult\n\n"
            f"I can give you specific details for these apps: **{', '.join(app_names)}**.\n"
            f"Which app would you like to know about?"
        )

    gateways = db.query(models.PaymentGateway).filter(models.PaymentGateway.app_id == app.id).all()
    if not gateways:
        return f"📱 **{app.app_name}** does not appear to have any direct payment processing, which means the stolen card risk is **minimal** for this app."

    response = f"🚨 **Stolen Card Risk for {app.app_name}**\n\n"
    for gw in gateways:
        response += f"**{gw.payment_method}** (via {gw.provider}):\n"
        response += f"- Fraud Detection: {'✅ Yes' if gw.fraud_detection else '❌ No'}"
        if gw.fraud_detection_details:
            response += f" — {gw.fraud_detection_details}"
        response += "\n"
        response += f"- Stolen Card Protection: {gw.stolen_card_protection or 'Not specified'}\n"
        response += f"- Chargeback Policy: {gw.chargeback_policy or 'Standard'}\n"
        response += f"- PCI-DSS Compliant: {'✅ Yes' if gw.pci_dss_compliant else '❌ No'}\n\n"

    response += (
        "**🛡️ What to do if your card was stolen:**\n"
        "1. Contact your bank immediately to freeze the card\n"
        "2. Report unauthorized transactions to the app provider\n"
        "3. Request a chargeback through your bank\n"
        "4. Change your app account password\n"
        "5. Enable 2FA on your account if available"
    )
    return response


def handle_paypal(app: models.AppAnalysis | None, db: Session) -> str:
    if app is None:
        apps = db.query(models.AppAnalysis).all()
        paypal_apps = []
        for a in apps:
            gws = db.query(models.PaymentGateway).filter(
                models.PaymentGateway.app_id == a.id,
                models.PaymentGateway.provider.ilike("%paypal%")
            ).all()
            if gws:
                paypal_apps.append(a.app_name)

        if paypal_apps:
            return (
                f"💳 **PayPal Usage in Educational Apps**\n\n"
                f"The following apps support PayPal: **{', '.join(paypal_apps)}**.\n\n"
                f"PayPal provides several security features:\n"
                f"- **Buyer Protection** — refunds for unauthorized transactions\n"
                f"- **OAuth 2.0** — secure token-based authentication\n"
                f"- **No card details shared** — the merchant never sees your full card number\n"
                f"- **Dispute resolution** — built-in process for unauthorized charges\n\n"
                f"Ask me about a specific app for detailed PayPal security analysis."
            )
        else:
            return "None of the analyzed apps currently support PayPal as a payment method. They primarily use Google Play Billing."

    gws = db.query(models.PaymentGateway).filter(
        models.PaymentGateway.app_id == app.id,
        models.PaymentGateway.provider.ilike("%paypal%")
    ).all()

    if not gws:
        return f"**{app.app_name}** does not use PayPal. It primarily uses Google Play Billing for payments."

    response = f"💳 **PayPal Security for {app.app_name}**\n\n"
    for gw in gws:
        response += f"- Encryption: {gw.encryption_standard}\n"
        response += f"- Fraud Detection: {'✅' if gw.fraud_detection else '❌'}\n"
        response += f"- PCI-DSS Compliant: {'✅' if gw.pci_dss_compliant else '❌'}\n\n"
    return response


def handle_installment(app: models.AppAnalysis | None, db: Session) -> str:
    if app is None:
        app_names = get_all_app_names(db)
        return (
            f"📅 **Installment Payments in Educational Apps**\n\n"
            f"When installment payments are used:\n\n"
            f"1. **More data is retained** — The app stores payment details for recurring charges\n"
            f"2. **Auto-renewal risk** — Subscriptions may auto-renew without clear notification\n"
            f"3. **Cancellation difficulty** — Some apps make it hard to cancel installment plans\n"
            f"4. **Credit impact** — Failed installments may affect credit reporting\n\n"
            f"Ask about a specific app ({', '.join(app_names)}) for detailed installment analysis."
        )

    gws = db.query(models.PaymentGateway).filter(
        models.PaymentGateway.app_id == app.id,
        models.PaymentGateway.installment_available == True
    ).all()

    if not gws:
        return f"**{app.app_name}** does not currently offer installment payment plans."

    response = f"📅 **Installment Payment Analysis for {app.app_name}**\n\n"
    for gw in gws:
        response += f"- Auto-renewal: {'⚠️ Yes' if gw.auto_renewal else '✅ No'}\n"
        response += f"- Cancellation: {gw.cancellation_difficulty}\n"
        response += f"- Data retained: {gw.data_retained_after_payment}\n"
        if gw.installment_details:
            response += f"- Details: {gw.installment_details}\n"
    return response


def handle_student_marks(app: models.AppAnalysis | None, db: Session) -> str:
    if app is None:
        apps = db.query(models.AppAnalysis).all()
        response = "📊 **Student Marks & Academic Data Risk**\n\n"
        response += "Student marks and grades are among the **most sensitive** data in educational apps because:\n\n"
        response += "- They can reveal a child's academic performance to unauthorized parties\n"
        response += "- Third-party analytics SDKs may inadvertently collect this data\n"
        response += "- If breached, this data could be used for profiling or discrimination\n"
        response += "- FERPA specifically protects student education records\n\n"
        response += "**Per-app summary:**\n\n"

        for a in apps:
            marks_data = db.query(models.PersonalDataCollection).filter(
                models.PersonalDataCollection.app_id == a.id,
                models.PersonalDataCollection.data_category == "Student Marks"
            ).all()
            if marks_data:
                for d in marks_data:
                    response += f"- **{a.app_name}**: {d.risk_level} risk — {d.data_type} ({'Shared with 3rd parties ⚠️' if d.shared_with_third_parties else 'Not shared externally ✅'})\n"
            else:
                response += f"- **{a.app_name}**: Does not collect student marks directly ✅\n"

        return response

    marks_data = db.query(models.PersonalDataCollection).filter(
        models.PersonalDataCollection.app_id == app.id,
        models.PersonalDataCollection.data_category == "Student Marks"
    ).all()

    if not marks_data:
        return f"✅ **{app.app_name}** does not collect student marks or grades directly."

    response = f"📊 **Student Marks Analysis for {app.app_name}**\n\n"
    for d in marks_data:
        response += f"**{d.data_type}**\n"
        response += f"- Collection: {d.collection_method}\n"
        response += f"- Storage: {d.storage_location}\n"
        response += f"- Encryption: {d.encryption_status}\n"
        response += f"- Shared with third parties: {'⚠️ Yes — ' + d.third_party_names if d.shared_with_third_parties else '✅ No'}\n"
        response += f"- Retention: {d.retention_period}\n"
        response += f"- Risk Level: **{d.risk_level}**\n"
        response += f"- Purpose: {d.purpose}\n\n"

    return response


def handle_personal_data(app: models.AppAnalysis | None, db: Session) -> str:
    if app is None:
        app_names = get_all_app_names(db)
        return f"🔍 I can show you what personal data each app collects. Which app are you interested in? ({', '.join(app_names)})"

    data = db.query(models.PersonalDataCollection).filter(
        models.PersonalDataCollection.app_id == app.id
    ).all()

    if not data:
        return f"No personal data collection records found for **{app.app_name}**."

    response = f"🔍 **Personal Data Collected by {app.app_name}**\n\n"
    categories = {}
    for d in data:
        if d.data_category not in categories:
            categories[d.data_category] = []
        categories[d.data_category].append(d)

    for cat, items in categories.items():
        response += f"**{cat}**\n"
        for d in items:
            risk_emoji = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(d.risk_level, "⚪")
            response += f"  {risk_emoji} {d.data_type} — {d.collection_method} | {'Shared ⚠️' if d.shared_with_third_parties else 'Private ✅'}\n"
        response += "\n"

    return response


def handle_security_mechanisms(app: models.AppAnalysis | None, db: Session) -> str:
    if app is None:
        app_names = get_all_app_names(db)
        return f"🛡️ I can show security mechanisms for each app. Which one? ({', '.join(app_names)})"

    mechanisms = db.query(models.SecurityMechanism).filter(
        models.SecurityMechanism.app_id == app.id
    ).all()

    if not mechanisms:
        return f"No security mechanism data available for **{app.app_name}**."

    response = f"🛡️ **Security Mechanisms for {app.app_name}**\n\n"
    categories = {}
    for m in mechanisms:
        if m.category not in categories:
            categories[m.category] = []
        categories[m.category].append(m)

    for cat, items in categories.items():
        response += f"**{cat}**\n"
        for m in items:
            status = "✅" if m.is_implemented else "❌"
            quality = f" ({m.implementation_quality})" if m.implementation_quality else ""
            response += f"  {status} {m.mechanism_name}{quality}\n"
            if m.details:
                response += f"     _{m.details}_\n"
        response += "\n"

    return response


def handle_security_incidents(app: models.AppAnalysis | None, db: Session) -> str:
    if app is None:
        app_names = get_all_app_names(db)
        return f"⚠️ I can show historical security incidents. Which app? ({', '.join(app_names)})"

    incidents = db.query(models.SecurityIncident).filter(
        models.SecurityIncident.app_id == app.id
    ).order_by(models.SecurityIncident.incident_date.desc()).all()

    if not incidents:
        return f"✅ No known security incidents have been recorded for **{app.app_name}**. This is a positive sign, though it doesn't guarantee the app is incident-proof."

    response = f"⚠️ **Security Incident History for {app.app_name}**\n\n"
    for inc in incidents:
        severity_emoji = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(inc.severity, "⚪")
        response += f"{severity_emoji} **{inc.title}** ({inc.incident_date})\n"
        response += f"  Severity: {inc.severity} | Affected: {inc.affected_users}\n"
        response += f"  {inc.description}\n"
        if inc.resolution:
            response += f"  Resolution: {inc.resolution}\n"
        response += "\n"

    return response


def handle_risk_predictions(app: models.AppAnalysis | None, db: Session) -> str:
    if app is None:
        app_names = get_all_app_names(db)
        return f"🔮 I can show risk predictions. Which app? ({', '.join(app_names)})"

    predictions = db.query(models.RiskPrediction).filter(
        models.RiskPrediction.app_id == app.id
    ).order_by(models.RiskPrediction.probability.desc()).all()

    if not predictions:
        return f"No risk predictions available for **{app.app_name}**."

    response = f"🔮 **Risk Predictions for {app.app_name}**\n\n"
    for pred in predictions:
        prob_pct = int(pred.probability * 100)
        conf_pct = int(pred.confidence * 100)
        response += f"**{pred.prediction_type}** ({pred.risk_category})\n"
        response += f"  Probability: {prob_pct}% | Confidence: {conf_pct}% | Timeframe: {pred.timeframe}\n"
        response += f"  Severity if realized: {pred.severity_if_realized}\n"
        response += f"  {pred.description}\n"
        if pred.recommended_mitigation:
            response += f"  💡 Mitigation: {pred.recommended_mitigation}\n"
        response += "\n"

    return response


def handle_payment_security(app: models.AppAnalysis | None, db: Session) -> str:
    if app is None:
        app_names = get_all_app_names(db)
        return f"💳 I can analyze payment security. Which app? ({', '.join(app_names)})"

    gateways = db.query(models.PaymentGateway).filter(
        models.PaymentGateway.app_id == app.id
    ).all()

    if not gateways:
        return f"**{app.app_name}** does not process payments directly, which means **no payment security risk**."

    response = f"💳 **Payment Security for {app.app_name}**\n\n"
    for gw in gateways:
        response += f"**{gw.payment_method}** ({gw.provider})\n"
        response += f"  - Encryption: {gw.encryption_standard}\n"
        response += f"  - PCI-DSS: {'✅' if gw.pci_dss_compliant else '❌'}\n"
        response += f"  - Fraud Detection: {'✅' if gw.fraud_detection else '❌'}\n"
        response += f"  - Risk Level: {gw.risk_level}\n\n"
    return response


def handle_third_party_sharing(app: models.AppAnalysis | None, db: Session) -> str:
    if app is None:
        app_names = get_all_app_names(db)
        return f"🔗 I can show third-party data sharing details. Which app? ({', '.join(app_names)})"

    shared = db.query(models.PersonalDataCollection).filter(
        models.PersonalDataCollection.app_id == app.id,
        models.PersonalDataCollection.shared_with_third_parties == True
    ).all()

    if not shared:
        return f"✅ **{app.app_name}** does not share personal data with third parties based on our analysis."

    response = f"🔗 **Third-Party Data Sharing by {app.app_name}**\n\n"
    for d in shared:
        response += f"- **{d.data_type}** ({d.data_category}) → shared with: {d.third_party_names}\n"
        response += f"  Purpose: {d.purpose} | Risk: {d.risk_level}\n\n"
    return response


def handle_compare_apps(db: Session) -> str:
    apps = db.query(models.AppAnalysis).all()
    if not apps:
        return "No apps have been analyzed yet."

    response = "⚖️ **App Comparison Summary**\n\n"
    response += "| App | Risk Score | Grade | Personal Data Items | Payment Methods | Incidents |\n"
    response += "|-----|-----------|-------|--------------------|-----------------|-----------|\n"

    for a in apps:
        pd_count = db.query(models.PersonalDataCollection).filter(
            models.PersonalDataCollection.app_id == a.id,
            models.PersonalDataCollection.is_collected == True
        ).count()
        pg_count = db.query(models.PaymentGateway).filter(models.PaymentGateway.app_id == a.id).count()
        inc_count = db.query(models.SecurityIncident).filter(models.SecurityIncident.app_id == a.id).count()
        response += f"| {a.app_name} | {a.risk_score}/100 | {a.risk_grade} | {pd_count} | {pg_count} | {inc_count} |\n"

    # Find safest
    safest = max(apps, key=lambda a: a.risk_score)
    response += f"\n🏆 **Safest app**: {safest.app_name} (score: {safest.risk_score}/100)"
    return response


def handle_compliance(app: models.AppAnalysis | None, db: Session) -> str:
    if app is None:
        apps = db.query(models.AppAnalysis).all()
        response = "⚖️ **Compliance Overview**\n\n"
        for a in apps:
            standards = a.compliance_standards or "None documented"
            response += f"- **{a.app_name}**: {standards}\n"

        response += "\n"
        # Check for relevant general knowledge
        for key in ["coppa", "gdpr", "ferpa"]:
            response += f"\n**{key.upper()}**: {GENERAL_KNOWLEDGE[key]['answer'][:100]}...\n"

        return response

    standards = app.compliance_standards or "None documented"
    response = f"⚖️ **Compliance Status for {app.app_name}**\n\n"
    response += f"Standards: **{standards}**\n\n"

    mechanisms = db.query(models.SecurityMechanism).filter(
        models.SecurityMechanism.app_id == app.id,
        models.SecurityMechanism.category == "Compliance"
    ).all()

    for m in mechanisms:
        status = "✅" if m.is_implemented else "❌"
        response += f"{status} {m.mechanism_name}: {m.details}\n"

    return response


def handle_unknown(message: str, db: Session) -> str:
    # Check general knowledge base
    message_lower = message.lower()
    for key, knowledge in GENERAL_KNOWLEDGE.items():
        if key.replace("_", " ") in message_lower or key in message_lower:
            return f"ℹ️ {knowledge['answer']}\n\n{knowledge.get('follow_up', '')}"

    app_names = get_all_app_names(db)
    return (
        f"🤔 I'm not sure I understood that. I can help you with:\n\n"
        f"- **Personal data** collection analysis\n"
        f"- **Student marks** & grades security\n"
        f"- **Payment gateway** security (PayPal, stolen cards, installments)\n"
        f"- **Security mechanisms** used by apps\n"
        f"- **Security incidents** & breach history\n"
        f"- **Risk predictions** based on historical data\n"
        f"- **App comparisons** & compliance checks\n\n"
        f"Try asking about a specific app: {', '.join(app_names)}"
    )


# ─── Main chatbot function ──────────────────────────────────────────────────────

def get_chatbot_response(message: str, db: Session, app_id: int | None = None) -> dict:
    """
    Main entry point for the chatbot.
    Returns a dict with 'response' (str) and 'suggestions' (list of str).
    """
    intent, _ = detect_intent(message)
    app = None
    if app_id:
        app = db.query(models.AppAnalysis).filter(models.AppAnalysis.id == app_id).first()
        
    if not app:
        app = find_app_in_message(message, db)
        
    app_names = get_all_app_names(db)

    # Route to the correct handler
    handlers = {
        "greeting": lambda: handle_greeting(db),
        "stolen_card": lambda: handle_stolen_card(app, db),
        "paypal": lambda: handle_paypal(app, db),
        "installment": lambda: handle_installment(app, db),
        "student_marks": lambda: handle_student_marks(app, db),
        "personal_data": lambda: handle_personal_data(app, db),
        "security_mechanisms": lambda: handle_security_mechanisms(app, db),
        "security_incidents": lambda: handle_security_incidents(app, db),
        "risk_predictions": lambda: handle_risk_predictions(app, db),
        "payment_security": lambda: handle_payment_security(app, db),
        "third_party_sharing": lambda: handle_third_party_sharing(app, db),
        "compare_apps": lambda: handle_compare_apps(db),
        "compliance": lambda: handle_compliance(app, db),
        "unknown": lambda: handle_unknown(message, db),
    }

    response_text = handlers.get(intent, handlers["unknown"])()

    # Generate contextual suggestions
    suggestions = _get_suggestions(intent, app, app_names)

    return {
        "response": response_text,
        "suggestions": suggestions,
        "intent": intent,
        "app_detected": app.app_name if app else None,
    }


def _get_suggestions(intent: str, app, app_names: list) -> list:
    """Generate contextual follow-up suggestions."""
    base_suggestions = []

    if app:
        base_suggestions = [
            f"What personal data does {app.app_name} collect?",
            f"Is {app.app_name} payment secure?",
            f"Has {app.app_name} had any security breaches?",
            f"What are the predicted risks for {app.app_name}?",
        ]
    else:
        base_suggestions = [
            "Which app is the safest?",
            "Tell me about student marks security",
            "What happens if someone uses a stolen card?",
            "Compare all apps",
        ]

    # Filter out the current intent's suggestion
    intent_keywords = {
        "personal_data": "personal data",
        "payment_security": "payment",
        "security_incidents": "breaches",
        "risk_predictions": "predicted",
        "student_marks": "student marks",
        "stolen_card": "stolen card",
        "compare_apps": "Compare",
    }

    keyword = intent_keywords.get(intent, "")
    if keyword:
        base_suggestions = [s for s in base_suggestions if keyword.lower() not in s.lower()]

    return base_suggestions[:4]
