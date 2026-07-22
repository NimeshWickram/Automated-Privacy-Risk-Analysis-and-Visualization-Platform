"""
Context-Aware Permission Analysis Engine for EduPrivacy-X.

Goes beyond simple dangerous/normal classification to provide:
- Permission Necessity Score (0-100) based on educational context
- SDK attribution (app vs third-party SDK)
- Educational justification assessment
- Alternative permission suggestions
- Usage detection status
- Permission grouping by privacy risk category
"""

# ─── Permission Knowledge Base ──────────────────────────────────────────────────

# Educational categories and their legitimately needed permissions
EDUCATIONAL_PERMISSION_PROFILES = {
    "early-childhood": {
        "justified": ["INTERNET", "ACCESS_NETWORK_STATE", "WAKE_LOCK", "VIBRATE",
                       "RECORD_AUDIO", "FOREGROUND_SERVICE"],
        "conditional": ["CAMERA", "WRITE_EXTERNAL_STORAGE", "READ_EXTERNAL_STORAGE",
                         "POST_NOTIFICATIONS"],
        "excessive": ["ACCESS_FINE_LOCATION", "ACCESS_COARSE_LOCATION", "READ_CONTACTS",
                       "READ_SMS", "SEND_SMS", "READ_PHONE_STATE", "GET_ACCOUNTS",
                       "READ_CALENDAR", "WRITE_CALENDAR", "BLUETOOTH_CONNECT",
                       "NEARBY_WIFI_DEVICES", "BODY_SENSORS"],
    },
    "mathematics": {
        "justified": ["INTERNET", "ACCESS_NETWORK_STATE", "WAKE_LOCK", "VIBRATE",
                       "FOREGROUND_SERVICE"],
        "conditional": ["CAMERA", "WRITE_EXTERNAL_STORAGE", "READ_EXTERNAL_STORAGE",
                         "POST_NOTIFICATIONS", "RECORD_AUDIO"],
        "excessive": ["ACCESS_FINE_LOCATION", "ACCESS_COARSE_LOCATION", "READ_CONTACTS",
                       "READ_SMS", "SEND_SMS", "READ_PHONE_STATE", "GET_ACCOUNTS",
                       "READ_CALENDAR", "WRITE_CALENDAR", "BLUETOOTH_CONNECT"],
    },
    "language-learning": {
        "justified": ["INTERNET", "ACCESS_NETWORK_STATE", "WAKE_LOCK", "VIBRATE",
                       "RECORD_AUDIO", "FOREGROUND_SERVICE", "POST_NOTIFICATIONS"],
        "conditional": ["CAMERA", "WRITE_EXTERNAL_STORAGE", "READ_EXTERNAL_STORAGE",
                         "ACCESS_COARSE_LOCATION"],
        "excessive": ["ACCESS_FINE_LOCATION", "READ_CONTACTS", "READ_SMS", "SEND_SMS",
                       "READ_PHONE_STATE", "GET_ACCOUNTS", "READ_CALENDAR",
                       "WRITE_CALENDAR", "BLUETOOTH_CONNECT", "BODY_SENSORS"],
    },
    "science": {
        "justified": ["INTERNET", "ACCESS_NETWORK_STATE", "WAKE_LOCK", "VIBRATE",
                       "CAMERA", "RECORD_AUDIO", "FOREGROUND_SERVICE"],
        "conditional": ["WRITE_EXTERNAL_STORAGE", "READ_EXTERNAL_STORAGE",
                         "ACCESS_COARSE_LOCATION", "POST_NOTIFICATIONS",
                         "BLUETOOTH_CONNECT", "BODY_SENSORS"],
        "excessive": ["ACCESS_FINE_LOCATION", "READ_CONTACTS", "READ_SMS", "SEND_SMS",
                       "READ_PHONE_STATE", "GET_ACCOUNTS", "READ_CALENDAR",
                       "WRITE_CALENDAR"],
    },
    "exam-preparation": {
        "justified": ["INTERNET", "ACCESS_NETWORK_STATE", "WAKE_LOCK", "VIBRATE",
                       "FOREGROUND_SERVICE", "POST_NOTIFICATIONS"],
        "conditional": ["CAMERA", "WRITE_EXTERNAL_STORAGE", "READ_EXTERNAL_STORAGE",
                         "RECORD_AUDIO"],
        "excessive": ["ACCESS_FINE_LOCATION", "ACCESS_COARSE_LOCATION", "READ_CONTACTS",
                       "READ_SMS", "SEND_SMS", "READ_PHONE_STATE", "GET_ACCOUNTS",
                       "READ_CALENDAR", "WRITE_CALENDAR"],
    },
    "classroom-management": {
        "justified": ["INTERNET", "ACCESS_NETWORK_STATE", "WAKE_LOCK", "VIBRATE",
                       "CAMERA", "RECORD_AUDIO", "FOREGROUND_SERVICE",
                       "POST_NOTIFICATIONS", "GET_ACCOUNTS"],
        "conditional": ["WRITE_EXTERNAL_STORAGE", "READ_EXTERNAL_STORAGE",
                         "ACCESS_COARSE_LOCATION", "READ_CONTACTS", "READ_CALENDAR",
                         "WRITE_CALENDAR"],
        "excessive": ["ACCESS_FINE_LOCATION", "READ_SMS", "SEND_SMS",
                       "READ_PHONE_STATE", "BLUETOOTH_CONNECT", "BODY_SENSORS"],
    },
    "educational-games": {
        "justified": ["INTERNET", "ACCESS_NETWORK_STATE", "WAKE_LOCK", "VIBRATE",
                       "FOREGROUND_SERVICE"],
        "conditional": ["CAMERA", "RECORD_AUDIO", "WRITE_EXTERNAL_STORAGE",
                         "READ_EXTERNAL_STORAGE", "POST_NOTIFICATIONS"],
        "excessive": ["ACCESS_FINE_LOCATION", "ACCESS_COARSE_LOCATION", "READ_CONTACTS",
                       "READ_SMS", "SEND_SMS", "READ_PHONE_STATE", "GET_ACCOUNTS",
                       "READ_CALENDAR", "WRITE_CALENDAR", "BLUETOOTH_CONNECT",
                       "BODY_SENSORS"],
    },
    # Default fallback for "Education" or unclassified
    "education": {
        "justified": ["INTERNET", "ACCESS_NETWORK_STATE", "WAKE_LOCK", "VIBRATE",
                       "FOREGROUND_SERVICE", "POST_NOTIFICATIONS"],
        "conditional": ["CAMERA", "RECORD_AUDIO", "WRITE_EXTERNAL_STORAGE",
                         "READ_EXTERNAL_STORAGE", "GET_ACCOUNTS"],
        "excessive": ["ACCESS_FINE_LOCATION", "ACCESS_COARSE_LOCATION", "READ_CONTACTS",
                       "READ_SMS", "SEND_SMS", "READ_PHONE_STATE", "READ_CALENDAR",
                       "WRITE_CALENDAR", "BLUETOOTH_CONNECT", "BODY_SENSORS"],
    },
}


# Dangerous permissions as defined by Android
ANDROID_DANGEROUS_PERMISSIONS = {
    "READ_CALENDAR", "WRITE_CALENDAR",
    "CAMERA",
    "READ_CONTACTS", "WRITE_CONTACTS", "GET_ACCOUNTS",
    "ACCESS_FINE_LOCATION", "ACCESS_COARSE_LOCATION", "ACCESS_BACKGROUND_LOCATION",
    "RECORD_AUDIO",
    "READ_PHONE_STATE", "READ_PHONE_NUMBERS", "CALL_PHONE", "ANSWER_PHONE_CALLS",
    "READ_CALL_LOG", "WRITE_CALL_LOG",
    "BODY_SENSORS", "BODY_SENSORS_BACKGROUND",
    "SEND_SMS", "RECEIVE_SMS", "READ_SMS", "RECEIVE_WAP_PUSH", "RECEIVE_MMS",
    "READ_EXTERNAL_STORAGE", "WRITE_EXTERNAL_STORAGE", "READ_MEDIA_IMAGES",
    "READ_MEDIA_VIDEO", "READ_MEDIA_AUDIO",
    "POST_NOTIFICATIONS",
    "NEARBY_WIFI_DEVICES", "BLUETOOTH_CONNECT", "BLUETOOTH_SCAN",
    "ACTIVITY_RECOGNITION",
    "USE_EXACT_ALARM",
}


# SDK signatures → which permissions they typically require
SDK_PERMISSION_SIGNATURES = {
    "Google AdMob": {
        "permissions": ["INTERNET", "ACCESS_NETWORK_STATE", "ACCESS_COARSE_LOCATION",
                         "ACCESS_FINE_LOCATION", "AD_ID"],
        "category": "advertising",
        "child_appropriate": False,
    },
    "Google Firebase Analytics": {
        "permissions": ["INTERNET", "ACCESS_NETWORK_STATE", "WAKE_LOCK"],
        "category": "analytics",
        "child_appropriate": True,
    },
    "Google Firebase Crashlytics": {
        "permissions": ["INTERNET", "ACCESS_NETWORK_STATE"],
        "category": "crash-reporting",
        "child_appropriate": True,
    },
    "Facebook SDK": {
        "permissions": ["INTERNET", "ACCESS_NETWORK_STATE"],
        "category": "social-media",
        "child_appropriate": False,
    },
    "Facebook Ads": {
        "permissions": ["INTERNET", "ACCESS_NETWORK_STATE", "AD_ID"],
        "category": "advertising",
        "child_appropriate": False,
    },
    "Unity Ads": {
        "permissions": ["INTERNET", "ACCESS_NETWORK_STATE", "ACCESS_COARSE_LOCATION"],
        "category": "advertising",
        "child_appropriate": False,
    },
    "Appsflyer": {
        "permissions": ["INTERNET", "ACCESS_NETWORK_STATE", "ACCESS_WIFI_STATE"],
        "category": "analytics",
        "child_appropriate": False,
    },
    "Adjust SDK": {
        "permissions": ["INTERNET", "ACCESS_NETWORK_STATE", "ACCESS_WIFI_STATE"],
        "category": "analytics",
        "child_appropriate": False,
    },
    "Google Play Services (Auth)": {
        "permissions": ["INTERNET", "GET_ACCOUNTS", "USE_CREDENTIALS"],
        "category": "authentication",
        "child_appropriate": True,
    },
    "Google Maps SDK": {
        "permissions": ["INTERNET", "ACCESS_FINE_LOCATION", "ACCESS_COARSE_LOCATION",
                         "ACCESS_NETWORK_STATE"],
        "category": "location",
        "child_appropriate": True,  # depends on context
    },
    "OneSignal": {
        "permissions": ["INTERNET", "ACCESS_NETWORK_STATE", "POST_NOTIFICATIONS",
                         "RECEIVE_BOOT_COMPLETED", "VIBRATE"],
        "category": "analytics",
        "child_appropriate": True,
    },
    "Mixpanel": {
        "permissions": ["INTERNET", "ACCESS_NETWORK_STATE"],
        "category": "analytics",
        "child_appropriate": False,
    },
    "Braze": {
        "permissions": ["INTERNET", "ACCESS_NETWORK_STATE", "POST_NOTIFICATIONS"],
        "category": "analytics",
        "child_appropriate": False,
    },
}


# Less-intrusive alternatives for dangerous permissions
PERMISSION_ALTERNATIVES = {
    "ACCESS_FINE_LOCATION": {
        "alternative": "ACCESS_COARSE_LOCATION",
        "reason": "Coarse location (city-level) is sufficient for most educational features. "
                  "Precise GPS location is rarely needed for learning apps.",
    },
    "READ_CONTACTS": {
        "alternative": "Manual entry / invite link",
        "reason": "A share link or manual email entry avoids exposing the child's entire contact list.",
    },
    "READ_PHONE_STATE": {
        "alternative": "Instance ID / Firebase Installation ID",
        "reason": "Device identification can use anonymous instance IDs instead of phone IMEI/IMSI.",
    },
    "GET_ACCOUNTS": {
        "alternative": "OAuth flow without GET_ACCOUNTS",
        "reason": "Modern OAuth 2.0 flows do not require reading device accounts.",
    },
    "READ_EXTERNAL_STORAGE": {
        "alternative": "Storage Access Framework / Photo Picker",
        "reason": "Android's photo picker and SAF provide scoped access without broad storage permission.",
    },
    "WRITE_EXTERNAL_STORAGE": {
        "alternative": "MediaStore API / App-specific directory",
        "reason": "Apps targeting SDK 29+ should use MediaStore or app-scoped directories.",
    },
    "READ_SMS": {
        "alternative": "SMS Retriever API",
        "reason": "For OTP verification, the SMS Retriever API reads only the specific verification message.",
    },
    "SEND_SMS": {
        "alternative": "Server-side SMS / push notification",
        "reason": "Sending SMS should be handled server-side to avoid device-level access.",
    },
    "ACCESS_BACKGROUND_LOCATION": {
        "alternative": "Foreground-only location",
        "reason": "Educational apps should only access location while the user is actively using the app.",
    },
    "CAMERA": {
        "alternative": "Intent-based camera (ACTION_IMAGE_CAPTURE)",
        "reason": "Using an intent lets the system camera app handle capture without direct camera access.",
    },
    "RECORD_AUDIO": {
        "alternative": "Speech recognition API",
        "reason": "For voice input, the speech recognition API processes audio without raw microphone access.",
    },
}


# Privacy risk categories for permissions
PERMISSION_RISK_CATEGORIES = {
    "identity": ["GET_ACCOUNTS", "READ_CONTACTS", "WRITE_CONTACTS", "READ_PHONE_STATE",
                  "READ_PHONE_NUMBERS"],
    "location": ["ACCESS_FINE_LOCATION", "ACCESS_COARSE_LOCATION", "ACCESS_BACKGROUND_LOCATION"],
    "media_capture": ["CAMERA", "RECORD_AUDIO"],
    "communication": ["READ_SMS", "SEND_SMS", "RECEIVE_SMS", "READ_CALL_LOG",
                        "WRITE_CALL_LOG", "CALL_PHONE", "ANSWER_PHONE_CALLS"],
    "storage": ["READ_EXTERNAL_STORAGE", "WRITE_EXTERNAL_STORAGE", "READ_MEDIA_IMAGES",
                 "READ_MEDIA_VIDEO", "READ_MEDIA_AUDIO"],
    "biometric": ["BODY_SENSORS", "BODY_SENSORS_BACKGROUND", "ACTIVITY_RECOGNITION"],
    "network": ["INTERNET", "ACCESS_NETWORK_STATE", "ACCESS_WIFI_STATE",
                 "NEARBY_WIFI_DEVICES", "BLUETOOTH_CONNECT", "BLUETOOTH_SCAN"],
    "device_control": ["WAKE_LOCK", "VIBRATE", "RECEIVE_BOOT_COMPLETED",
                        "FOREGROUND_SERVICE", "POST_NOTIFICATIONS", "USE_EXACT_ALARM"],
    "calendar": ["READ_CALENDAR", "WRITE_CALENDAR"],
}


def _get_risk_category(permission_name: str) -> str:
    """Map a permission name to its privacy risk category."""
    for category, perms in PERMISSION_RISK_CATEGORIES.items():
        if permission_name in perms:
            return category
    return "other"


def _normalize_category(category: str) -> str:
    """Normalize app category to match our educational profiles."""
    category_lower = category.lower().strip()

    mapping = {
        "education": "education",
        "educational": "education",
        "early childhood": "early-childhood",
        "early-childhood": "early-childhood",
        "preschool": "early-childhood",
        "kindergarten": "early-childhood",
        "mathematics": "mathematics",
        "math": "mathematics",
        "maths": "mathematics",
        "language": "language-learning",
        "language learning": "language-learning",
        "language-learning": "language-learning",
        "languages": "language-learning",
        "science": "science",
        "stem": "science",
        "exam": "exam-preparation",
        "exam preparation": "exam-preparation",
        "exam-preparation": "exam-preparation",
        "test prep": "exam-preparation",
        "classroom": "classroom-management",
        "classroom management": "classroom-management",
        "classroom-management": "classroom-management",
        "lms": "classroom-management",
        "game": "educational-games",
        "games": "educational-games",
        "educational games": "educational-games",
        "educational-games": "educational-games",
    }

    for key, value in mapping.items():
        if key in category_lower:
            return value

    return "education"  # fallback


def _get_base_risk_weight(permission_name: str) -> float:
    """
    Base risk weight for a permission.
    Higher = more privacy-invasive.
    """
    HIGH_RISK = {
        "ACCESS_FINE_LOCATION": 0.9,
        "ACCESS_BACKGROUND_LOCATION": 1.0,
        "READ_CONTACTS": 0.85,
        "WRITE_CONTACTS": 0.85,
        "READ_SMS": 0.95,
        "SEND_SMS": 0.95,
        "READ_CALL_LOG": 0.9,
        "WRITE_CALL_LOG": 0.9,
        "CALL_PHONE": 0.8,
        "READ_PHONE_STATE": 0.8,
        "BODY_SENSORS": 0.85,
        "CAMERA": 0.7,
        "RECORD_AUDIO": 0.7,
    }
    MEDIUM_RISK = {
        "ACCESS_COARSE_LOCATION": 0.6,
        "GET_ACCOUNTS": 0.55,
        "READ_EXTERNAL_STORAGE": 0.5,
        "WRITE_EXTERNAL_STORAGE": 0.5,
        "READ_CALENDAR": 0.45,
        "WRITE_CALENDAR": 0.45,
        "READ_PHONE_NUMBERS": 0.6,
        "BLUETOOTH_CONNECT": 0.4,
        "NEARBY_WIFI_DEVICES": 0.45,
    }
    LOW_RISK = {
        "INTERNET": 0.1,
        "ACCESS_NETWORK_STATE": 0.05,
        "VIBRATE": 0.02,
        "WAKE_LOCK": 0.05,
        "RECEIVE_BOOT_COMPLETED": 0.1,
        "FOREGROUND_SERVICE": 0.1,
        "POST_NOTIFICATIONS": 0.15,
        "ACCESS_WIFI_STATE": 0.05,
    }

    if permission_name in HIGH_RISK:
        return HIGH_RISK[permission_name]
    if permission_name in MEDIUM_RISK:
        return MEDIUM_RISK[permission_name]
    if permission_name in LOW_RISK:
        return LOW_RISK[permission_name]
    # Unknown permissions: moderate risk
    return 0.3


def analyze_permission_context(
    permission_name: str,
    app_category: str,
    detected_sdks: list[str] | None = None,
    is_actually_used: bool | None = None,
    target_age: str = "",
) -> dict:
    """
    Perform context-aware analysis of a single permission.

    Returns a dict with:
    - necessity_score (0-100): How necessary this permission is for the app's educational purpose
    - educational_justification: "justified" | "conditional" | "excessive" | "unnecessary"
    - sdk_attribution: "app" | SDK name | "unknown"
    - risk_category: identity, location, media_capture, etc.
    - privacy_risk_level: "low" | "medium" | "high" | "critical"
    - is_dangerous: bool
    - is_actually_used: bool | None
    - alternative_permission: dict or None
    - explanation: human-readable explanation
    - child_risk_multiplier: float (1.0-2.0)
    """
    norm_category = _normalize_category(app_category)
    profile = EDUCATIONAL_PERMISSION_PROFILES.get(norm_category,
                EDUCATIONAL_PERMISSION_PROFILES["education"])

    is_dangerous = permission_name in ANDROID_DANGEROUS_PERMISSIONS

    # 1. Determine educational justification
    if permission_name in profile["justified"]:
        educational_justification = "justified"
        necessity_base = 85  # high necessity
    elif permission_name in profile["conditional"]:
        educational_justification = "conditional"
        necessity_base = 55  # moderate necessity
    elif permission_name in profile["excessive"]:
        educational_justification = "excessive"
        necessity_base = 15  # low necessity
    else:
        # Not in any list → unknown / normal permission
        if is_dangerous:
            educational_justification = "excessive"
            necessity_base = 20
        else:
            educational_justification = "justified"
            necessity_base = 70

    # 2. SDK attribution
    sdk_attribution = "app"
    sdk_child_appropriate = True
    if detected_sdks:
        for sdk_name in detected_sdks:
            sig = SDK_PERMISSION_SIGNATURES.get(sdk_name)
            if sig and permission_name in sig["permissions"]:
                sdk_attribution = sdk_name
                sdk_child_appropriate = sig.get("child_appropriate", True)
                # If SDK needs it, adjust necessity slightly
                if educational_justification == "excessive":
                    necessity_base = max(necessity_base, 25)
                break

    # 3. Adjust for actual usage
    if is_actually_used is False:
        # Declared but not used → lower necessity, higher concern
        necessity_base = max(5, necessity_base - 30)

    # 4. Child risk multiplier
    child_multiplier = 1.0
    target_lower = target_age.lower() if target_age else ""
    if any(x in target_lower for x in ["3-", "4-", "5-", "6-", "7-", "8-",
                                          "preschool", "kindergarten", "early",
                                          "toddler", "child"]):
        child_multiplier = 1.8
    elif any(x in target_lower for x in ["9-", "10-", "11-", "12-", "13-",
                                            "teen", "middle school", "elementary"]):
        child_multiplier = 1.5
    elif any(x in target_lower for x in ["14-", "15-", "16-", "17-",
                                            "high school"]):
        child_multiplier = 1.3
    elif any(x in target_lower for x in ["18", "adult", "university", "college"]):
        child_multiplier = 1.0
    else:
        child_multiplier = 1.4  # default: assume some child audience

    # 5. Calculate privacy risk level
    base_risk = _get_base_risk_weight(permission_name)
    adjusted_risk = min(1.0, base_risk * child_multiplier)

    if adjusted_risk >= 0.8:
        privacy_risk_level = "critical"
    elif adjusted_risk >= 0.55:
        privacy_risk_level = "high"
    elif adjusted_risk >= 0.3:
        privacy_risk_level = "medium"
    else:
        privacy_risk_level = "low"

    # If SDK is not child-appropriate and permission is for that SDK, bump risk
    if not sdk_child_appropriate and sdk_attribution != "app":
        if privacy_risk_level == "medium":
            privacy_risk_level = "high"
        elif privacy_risk_level == "low":
            privacy_risk_level = "medium"

    # 6. Get alternative permission suggestion
    alternative = PERMISSION_ALTERNATIVES.get(permission_name)

    # 7. Build human-readable explanation
    explanation = _build_explanation(
        permission_name, educational_justification, sdk_attribution,
        is_dangerous, is_actually_used, norm_category, alternative,
        child_multiplier, privacy_risk_level,
    )

    # 8. Final necessity score (clamped 0-100)
    necessity_score = max(0, min(100, necessity_base))

    risk_category = _get_risk_category(permission_name)

    return {
        "necessity_score": necessity_score,
        "educational_justification": educational_justification,
        "sdk_attribution": sdk_attribution,
        "risk_category": risk_category,
        "privacy_risk_level": privacy_risk_level,
        "is_dangerous": is_dangerous,
        "is_actually_used": is_actually_used,
        "alternative_permission": alternative,
        "explanation": explanation,
        "child_risk_multiplier": round(child_multiplier, 2),
        "base_risk_weight": round(base_risk, 3),
        "adjusted_risk_weight": round(adjusted_risk, 3),
    }


def _build_explanation(
    permission_name, justification, sdk_attribution, is_dangerous,
    is_actually_used, category, alternative, child_multiplier, risk_level,
) -> str:
    """Build a plain-language explanation for a permission assessment."""
    parts = []

    # Context
    if justification == "justified":
        parts.append(
            f"{permission_name} is commonly needed for {category} applications "
            f"and is considered justified for this app's educational purpose."
        )
    elif justification == "conditional":
        parts.append(
            f"{permission_name} may be needed depending on specific features. "
            f"In a {category} context, this permission requires clear justification."
        )
    elif justification == "excessive":
        parts.append(
            f"{permission_name} is not typically needed for {category} applications. "
            f"This permission raises privacy concerns in an educational context."
        )

    # Dangerous flag
    if is_dangerous:
        parts.append("This is classified as a dangerous permission by Android, "
                      "requiring explicit user consent at runtime.")

    # SDK attribution
    if sdk_attribution != "app" and sdk_attribution != "unknown":
        parts.append(f"This permission appears to be required by the {sdk_attribution} SDK "
                      f"rather than the app's core functionality.")

    # Usage
    if is_actually_used is False:
        parts.append("⚠ This permission is declared but no evidence of actual usage "
                      "was found in the code analysis. It may be over-declared.")

    # Child sensitivity
    if child_multiplier > 1.3:
        parts.append(f"Risk is amplified (×{child_multiplier}) because this app "
                      "targets children or young students.")

    # Alternative
    if alternative:
        parts.append(f"💡 Alternative: {alternative['reason']}")

    return " ".join(parts)


def analyze_all_permissions(
    permissions: list[dict],
    app_category: str,
    detected_sdks: list[str] | None = None,
    target_age: str = "",
) -> dict:
    """
    Analyze all permissions for an app and return a comprehensive report.

    Args:
        permissions: list of {"name": str, "status": str, "description": str}
        app_category: the app's educational sub-category
        detected_sdks: list of SDK names detected in the app
        target_age: target age range string

    Returns:
        dict with:
        - permissions: list of enriched permission dicts
        - summary: overall permission analysis summary
        - permission_necessity_score: aggregate score (0-100)
        - risk_breakdown: counts by risk level
        - category_breakdown: counts by risk category
    """
    analyzed = []
    total_necessity = 0
    risk_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    category_counts = {}
    excessive_count = 0
    dangerous_count = 0
    sdk_attributed_count = 0

    for perm in permissions:
        perm_name = perm.get("name", "")
        result = analyze_permission_context(
            permission_name=perm_name,
            app_category=app_category,
            detected_sdks=detected_sdks,
            is_actually_used=perm.get("is_actually_used"),
            target_age=target_age,
        )

        enriched = {
            **perm,
            **result,
        }
        analyzed.append(enriched)

        total_necessity += result["necessity_score"]
        risk_counts[result["privacy_risk_level"]] += 1

        cat = result["risk_category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1

        if result["educational_justification"] == "excessive":
            excessive_count += 1
        if result["is_dangerous"]:
            dangerous_count += 1
        if result["sdk_attribution"] != "app":
            sdk_attributed_count += 1

    total = len(analyzed) or 1
    avg_necessity = total_necessity / total

    # Overall Permission Necessity Score:
    # High avg_necessity = permissions are mostly justified = good
    # Low avg_necessity = many unnecessary permissions = bad
    # We invert for risk: high necessity = low risk contribution
    permission_risk_contribution = max(0, min(100, int(100 - avg_necessity)))

    summary = {
        "total_permissions": total,
        "dangerous_count": dangerous_count,
        "excessive_count": excessive_count,
        "sdk_attributed_count": sdk_attributed_count,
        "avg_necessity_score": round(avg_necessity, 1),
        "permission_risk_contribution": permission_risk_contribution,
        "verdict": _get_permission_verdict(avg_necessity, excessive_count, dangerous_count),
    }

    return {
        "permissions": analyzed,
        "summary": summary,
        "permission_necessity_score": round(avg_necessity, 1),
        "risk_breakdown": risk_counts,
        "category_breakdown": category_counts,
    }


def _get_permission_verdict(avg_necessity: float, excessive: int, dangerous: int) -> str:
    """Generate a human-readable verdict about the app's permission profile."""
    if avg_necessity >= 75 and excessive == 0:
        return ("This app requests only permissions that are well-justified for its "
                "educational purpose. Permission usage appears appropriate.")
    elif avg_necessity >= 60 and excessive <= 1:
        return ("Most permissions are justified, but some may warrant further review. "
                "The overall permission profile is acceptable.")
    elif avg_necessity >= 40:
        return ("Several permissions lack clear educational justification. "
                f"{excessive} permission(s) appear excessive for this app category. "
                "Parents and educators should review carefully.")
    else:
        return (f"This app requests {excessive} permission(s) that are excessive for its "
                f"educational purpose, including {dangerous} dangerous permission(s). "
                "This represents a significant privacy concern for child users.")
