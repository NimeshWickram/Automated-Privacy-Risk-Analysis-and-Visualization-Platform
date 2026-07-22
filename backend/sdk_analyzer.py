"""
SDK & Tracker Intelligence Engine for EduPrivacy-X (Feature D).

Goes beyond simple SDK name detection to provide:
- SDK privacy configuration analysis
- Child-appropriateness assessment
- Network domain attribution
- Data access profiling
- Disclosure status tracking
- SDK-to-permission mapping
"""

import json

# ─── Comprehensive SDK Knowledge Base ────────────────────────────────────────────

SDK_CATALOGUE = {
    # ── Advertising SDKs ──
    "Google AdMob": {
        "provider": "Google LLC",
        "category": "advertising",
        "package_signatures": [
            "com.google.android.gms.ads",
            "com.google.ads",
            "com.google.firebase.ads",
        ],
        "data_accessed": [
            "Advertising ID", "IP Address", "Device Model", "OS Version",
            "App Usage Data", "Approximate Location",
        ],
        "permissions_required": [
            "INTERNET", "ACCESS_NETWORK_STATE", "AD_ID",
            "ACCESS_COARSE_LOCATION", "ACCESS_FINE_LOCATION",
        ],
        "network_domains": [
            "googleads.g.doubleclick.net", "pagead2.googlesyndication.com",
            "adservice.google.com", "www.googleadservices.com",
        ],
        "child_appropriate": False,
        "child_appropriate_config": "ad_tag=child_directed_treatment",
        "privacy_impact": "high",
        "gdpr_compliant": True,
        "coppa_mode_available": True,
        "description": "Google's mobile advertising SDK. Serves display, interstitial, native, and rewarded ads. Collects device identifiers and behavioral data for ad targeting.",
    },
    "Facebook Ads": {
        "provider": "Meta Platforms Inc.",
        "category": "advertising",
        "package_signatures": [
            "com.facebook.ads",
            "com.facebook.ads.internal",
        ],
        "data_accessed": [
            "Advertising ID", "IP Address", "Device Info", "App Events",
            "Purchase Data", "User Demographics",
        ],
        "permissions_required": ["INTERNET", "ACCESS_NETWORK_STATE", "AD_ID"],
        "network_domains": [
            "graph.facebook.com", "an.facebook.com",
            "www.facebook.com", "edge-mqtt.facebook.com",
        ],
        "child_appropriate": False,
        "child_appropriate_config": None,
        "privacy_impact": "critical",
        "gdpr_compliant": True,
        "coppa_mode_available": False,
        "description": "Meta Audience Network SDK. Enables Facebook ad serving and cross-app tracking. Shares behavioral data with Meta's advertising platform.",
    },
    "Unity Ads": {
        "provider": "Unity Technologies",
        "category": "advertising",
        "package_signatures": [
            "com.unity3d.ads",
            "com.unity3d.services",
        ],
        "data_accessed": [
            "Advertising ID", "Device Info", "IP Address",
            "App Usage Patterns", "In-App Purchase Data",
        ],
        "permissions_required": [
            "INTERNET", "ACCESS_NETWORK_STATE", "ACCESS_COARSE_LOCATION",
        ],
        "network_domains": [
            "unityads.unity3d.com", "ads.unity3d.com",
            "config.unityads.unity3d.com",
        ],
        "child_appropriate": False,
        "child_appropriate_config": "coppa=true",
        "privacy_impact": "high",
        "gdpr_compliant": True,
        "coppa_mode_available": True,
        "description": "Unity's monetization SDK for games and apps. Serves video and rewarded ads. Common in educational game apps.",
    },
    "AppLovin": {
        "provider": "AppLovin Corporation",
        "category": "advertising",
        "package_signatures": [
            "com.applovin",
            "com.applovin.sdk",
        ],
        "data_accessed": [
            "Advertising ID", "Device Info", "IP Address",
            "App Usage Data", "Location Data",
        ],
        "permissions_required": ["INTERNET", "ACCESS_NETWORK_STATE", "AD_ID"],
        "network_domains": [
            "ms.applovin.com", "d.applovin.com",
            "rt.applovin.com",
        ],
        "child_appropriate": False,
        "child_appropriate_config": None,
        "privacy_impact": "high",
        "gdpr_compliant": True,
        "coppa_mode_available": True,
        "description": "AppLovin MAX mediation and ad serving platform. Aggregates multiple ad networks for maximum fill rate.",
    },
    "IronSource": {
        "provider": "Unity (ironSource) Ltd.",
        "category": "advertising",
        "package_signatures": [
            "com.ironsource",
            "com.ironsource.sdk",
        ],
        "data_accessed": [
            "Advertising ID", "Device Info", "IP Address",
            "App Install Data", "In-App Events",
        ],
        "permissions_required": ["INTERNET", "ACCESS_NETWORK_STATE"],
        "network_domains": [
            "outcome-ssp.supersonicads.com", "init.supersonicads.com",
        ],
        "child_appropriate": False,
        "child_appropriate_config": "setCoppa(true)",
        "privacy_impact": "high",
        "gdpr_compliant": True,
        "coppa_mode_available": True,
        "description": "ironSource (now Unity LevelPlay) ad mediation platform. Used in freemium educational and game apps.",
    },

    # ── Analytics SDKs ──
    "Google Firebase Analytics": {
        "provider": "Google LLC",
        "category": "analytics",
        "package_signatures": [
            "com.google.firebase.analytics",
            "com.google.android.gms.measurement",
        ],
        "data_accessed": [
            "App Events", "Screen Views", "User Properties",
            "Device Info", "OS Version", "App Version",
        ],
        "permissions_required": ["INTERNET", "ACCESS_NETWORK_STATE", "WAKE_LOCK"],
        "network_domains": [
            "app-measurement.com", "firebase-settings.crashlytics.com",
            "firebaseinstallations.googleapis.com",
        ],
        "child_appropriate": True,
        "child_appropriate_config": "analytics_collection_deactivated",
        "privacy_impact": "medium",
        "gdpr_compliant": True,
        "coppa_mode_available": True,
        "description": "Google's app analytics SDK. Tracks user events, screen views, and engagement. Data shared with Google for analytics processing.",
    },
    "Google Firebase Crashlytics": {
        "provider": "Google LLC",
        "category": "crash-reporting",
        "package_signatures": [
            "com.google.firebase.crashlytics",
            "com.crashlytics.sdk",
        ],
        "data_accessed": [
            "Crash Logs", "Device State", "Stack Traces",
            "OS Version", "Device Model", "App State",
        ],
        "permissions_required": ["INTERNET", "ACCESS_NETWORK_STATE"],
        "network_domains": [
            "firebase-settings.crashlytics.com",
            "reports.crashlytics.com",
        ],
        "child_appropriate": True,
        "child_appropriate_config": None,
        "privacy_impact": "low",
        "gdpr_compliant": True,
        "coppa_mode_available": True,
        "description": "Crash reporting service. Collects crash logs and device state to help developers fix bugs. Minimal personal data collection.",
    },
    "Facebook SDK": {
        "provider": "Meta Platforms Inc.",
        "category": "analytics",
        "package_signatures": [
            "com.facebook.appevents",
            "com.facebook.FacebookSdk",
            "com.facebook.internal",
        ],
        "data_accessed": [
            "App Events", "User Engagement", "Purchase Events",
            "Device Info", "Advertising ID",
        ],
        "permissions_required": ["INTERNET", "ACCESS_NETWORK_STATE"],
        "network_domains": [
            "graph.facebook.com", "www.facebook.com",
            "connect.facebook.net",
        ],
        "child_appropriate": False,
        "child_appropriate_config": None,
        "privacy_impact": "high",
        "gdpr_compliant": True,
        "coppa_mode_available": False,
        "description": "Facebook's analytics and event tracking SDK. Shares app usage data with Meta's platform for analytics and ad optimization.",
    },
    "Mixpanel": {
        "provider": "Mixpanel Inc.",
        "category": "analytics",
        "package_signatures": [
            "com.mixpanel.android",
        ],
        "data_accessed": [
            "App Events", "User Properties", "Device Info",
            "IP Address", "User Interactions",
        ],
        "permissions_required": ["INTERNET", "ACCESS_NETWORK_STATE"],
        "network_domains": [
            "api.mixpanel.com", "decide.mixpanel.com",
        ],
        "child_appropriate": False,
        "child_appropriate_config": None,
        "privacy_impact": "medium",
        "gdpr_compliant": True,
        "coppa_mode_available": False,
        "description": "Product analytics platform. Tracks user behavior and events to help optimize product features and user engagement.",
    },
    "Amplitude": {
        "provider": "Amplitude Inc.",
        "category": "analytics",
        "package_signatures": [
            "com.amplitude.api",
            "com.amplitude.android",
        ],
        "data_accessed": [
            "App Events", "User Properties", "Device Info",
            "Session Data", "User Journey",
        ],
        "permissions_required": ["INTERNET", "ACCESS_NETWORK_STATE"],
        "network_domains": [
            "api.amplitude.com", "api2.amplitude.com",
        ],
        "child_appropriate": False,
        "child_appropriate_config": None,
        "privacy_impact": "medium",
        "gdpr_compliant": True,
        "coppa_mode_available": False,
        "description": "Digital analytics platform. Provides behavioral analytics and user journey tracking.",
    },
    "Appsflyer": {
        "provider": "AppsFlyer Ltd.",
        "category": "analytics",
        "package_signatures": [
            "com.appsflyer",
            "com.appsflyer.internal",
        ],
        "data_accessed": [
            "Advertising ID", "Install Attribution", "In-App Events",
            "Device Info", "IP Address", "Referrer Data",
        ],
        "permissions_required": ["INTERNET", "ACCESS_NETWORK_STATE", "ACCESS_WIFI_STATE"],
        "network_domains": [
            "launches.appsflyer.com", "t.appsflyer.com",
            "register.appsflyer.com",
        ],
        "child_appropriate": False,
        "child_appropriate_config": None,
        "privacy_impact": "high",
        "gdpr_compliant": True,
        "coppa_mode_available": True,
        "description": "Mobile attribution and marketing analytics platform. Tracks app installs and in-app events for advertising attribution.",
    },
    "Adjust SDK": {
        "provider": "Adjust GmbH",
        "category": "analytics",
        "package_signatures": [
            "com.adjust.sdk",
        ],
        "data_accessed": [
            "Advertising ID", "Install Attribution", "Device Info",
            "IP Address", "In-App Events",
        ],
        "permissions_required": ["INTERNET", "ACCESS_NETWORK_STATE", "ACCESS_WIFI_STATE"],
        "network_domains": [
            "app.adjust.com", "app.adjust.io",
        ],
        "child_appropriate": False,
        "child_appropriate_config": "setCoppaCompliantEnabled(true)",
        "privacy_impact": "medium",
        "gdpr_compliant": True,
        "coppa_mode_available": True,
        "description": "Mobile measurement and attribution SDK. Tracks installs and conversions for marketing campaigns.",
    },
    "Braze": {
        "provider": "Braze Inc.",
        "category": "analytics",
        "package_signatures": [
            "com.braze",
            "com.appboy",
        ],
        "data_accessed": [
            "User Profile", "App Events", "Push Tokens",
            "Device Info", "Location Data",
        ],
        "permissions_required": ["INTERNET", "ACCESS_NETWORK_STATE", "POST_NOTIFICATIONS"],
        "network_domains": [
            "sdk.iad-01.braze.com", "sdk.iad-03.braze.com",
        ],
        "child_appropriate": False,
        "child_appropriate_config": None,
        "privacy_impact": "medium",
        "gdpr_compliant": True,
        "coppa_mode_available": False,
        "description": "Customer engagement platform. Sends push notifications and tracks user engagement. Collects user profiles and behavioral data.",
    },

    # ── Push Notification SDKs ──
    "OneSignal": {
        "provider": "OneSignal Inc.",
        "category": "push-notifications",
        "package_signatures": [
            "com.onesignal",
        ],
        "data_accessed": [
            "Push Token", "Device Info", "App Events",
            "Tags/Segments", "IP Address",
        ],
        "permissions_required": [
            "INTERNET", "ACCESS_NETWORK_STATE", "POST_NOTIFICATIONS",
            "RECEIVE_BOOT_COMPLETED", "VIBRATE",
        ],
        "network_domains": [
            "onesignal.com", "api.onesignal.com",
        ],
        "child_appropriate": True,
        "child_appropriate_config": None,
        "privacy_impact": "low",
        "gdpr_compliant": True,
        "coppa_mode_available": True,
        "description": "Push notification delivery platform. Manages notification tokens and user segments for targeted messaging.",
    },
    "Firebase Cloud Messaging": {
        "provider": "Google LLC",
        "category": "push-notifications",
        "package_signatures": [
            "com.google.firebase.messaging",
        ],
        "data_accessed": [
            "Push Token", "Device Info", "Message Metadata",
        ],
        "permissions_required": ["INTERNET", "WAKE_LOCK"],
        "network_domains": [
            "fcm.googleapis.com", "mtalk.google.com",
        ],
        "child_appropriate": True,
        "child_appropriate_config": None,
        "privacy_impact": "low",
        "gdpr_compliant": True,
        "coppa_mode_available": True,
        "description": "Google's cloud messaging service for push notifications. Minimal data collection beyond device tokens.",
    },

    # ── Authentication SDKs ──
    "Google Play Services (Auth)": {
        "provider": "Google LLC",
        "category": "authentication",
        "package_signatures": [
            "com.google.android.gms.auth",
            "com.google.android.gms.common",
        ],
        "data_accessed": [
            "Google Account", "Email", "Display Name",
            "Profile Photo URL",
        ],
        "permissions_required": ["INTERNET", "GET_ACCOUNTS", "USE_CREDENTIALS"],
        "network_domains": [
            "accounts.google.com", "oauth2.googleapis.com",
        ],
        "child_appropriate": True,
        "child_appropriate_config": None,
        "privacy_impact": "medium",
        "gdpr_compliant": True,
        "coppa_mode_available": True,
        "description": "Google Sign-In and OAuth2 authentication. Provides account linking and user identity services.",
    },
    "Firebase Authentication": {
        "provider": "Google LLC",
        "category": "authentication",
        "package_signatures": [
            "com.google.firebase.auth",
        ],
        "data_accessed": [
            "Email", "Phone Number", "User ID",
            "Auth Tokens", "Provider Data",
        ],
        "permissions_required": ["INTERNET"],
        "network_domains": [
            "securetoken.googleapis.com",
            "identitytoolkit.googleapis.com",
        ],
        "child_appropriate": True,
        "child_appropriate_config": None,
        "privacy_impact": "low",
        "gdpr_compliant": True,
        "coppa_mode_available": True,
        "description": "Firebase's authentication service. Supports email, phone, OAuth, and anonymous login. Stores minimal user identity data.",
    },

    # ── Location SDKs ──
    "Google Maps SDK": {
        "provider": "Google LLC",
        "category": "location",
        "package_signatures": [
            "com.google.android.gms.maps",
            "com.google.maps.android",
        ],
        "data_accessed": [
            "Location Data", "Map Interactions", "Device Info",
        ],
        "permissions_required": [
            "INTERNET", "ACCESS_FINE_LOCATION", "ACCESS_COARSE_LOCATION",
            "ACCESS_NETWORK_STATE",
        ],
        "network_domains": [
            "maps.googleapis.com", "maps.google.com",
        ],
        "child_appropriate": True,
        "child_appropriate_config": None,
        "privacy_impact": "medium",
        "gdpr_compliant": True,
        "coppa_mode_available": True,
        "description": "Google Maps rendering and geocoding SDK. Requires location permissions for map features.",
    },

    # ── Social Media SDKs ──
    "Facebook Login": {
        "provider": "Meta Platforms Inc.",
        "category": "social-media",
        "package_signatures": [
            "com.facebook.login",
            "com.facebook.LoginActivity",
        ],
        "data_accessed": [
            "Facebook Profile", "Email", "Friends List",
            "Public Profile", "User ID",
        ],
        "permissions_required": ["INTERNET"],
        "network_domains": [
            "graph.facebook.com", "www.facebook.com",
        ],
        "child_appropriate": False,
        "child_appropriate_config": None,
        "privacy_impact": "high",
        "gdpr_compliant": True,
        "coppa_mode_available": False,
        "description": "Facebook Login SDK. Enables social login and can request access to user's Facebook profile data.",
    },

    # ── Cloud Storage SDKs ──
    "Firebase Firestore": {
        "provider": "Google LLC",
        "category": "cloud-storage",
        "package_signatures": [
            "com.google.firebase.firestore",
        ],
        "data_accessed": [
            "App Data", "User Documents", "Sync State",
        ],
        "permissions_required": ["INTERNET"],
        "network_domains": [
            "firestore.googleapis.com",
        ],
        "child_appropriate": True,
        "child_appropriate_config": None,
        "privacy_impact": "low",
        "gdpr_compliant": True,
        "coppa_mode_available": True,
        "description": "Cloud-hosted NoSQL database. Stores app data including potentially personal user-generated content.",
    },
    "Firebase Realtime Database": {
        "provider": "Google LLC",
        "category": "cloud-storage",
        "package_signatures": [
            "com.google.firebase.database",
        ],
        "data_accessed": [
            "App Data", "Real-time Sync Data", "User Content",
        ],
        "permissions_required": ["INTERNET"],
        "network_domains": [
            "firebaseio.com",
        ],
        "child_appropriate": True,
        "child_appropriate_config": None,
        "privacy_impact": "low",
        "gdpr_compliant": True,
        "coppa_mode_available": True,
        "description": "Real-time cloud database. Syncs data across clients in real time. Content depends on developer implementation.",
    },
    "AWS Amplify": {
        "provider": "Amazon Web Services",
        "category": "cloud-storage",
        "package_signatures": [
            "com.amplifyframework",
            "com.amazonaws.mobile",
        ],
        "data_accessed": [
            "App Data", "User Authentication", "File Storage",
        ],
        "permissions_required": ["INTERNET"],
        "network_domains": [
            "cognito-idp.amazonaws.com", "s3.amazonaws.com",
        ],
        "child_appropriate": True,
        "child_appropriate_config": None,
        "privacy_impact": "low",
        "gdpr_compliant": True,
        "coppa_mode_available": True,
        "description": "AWS mobile backend SDK. Provides authentication, storage, and API access. Data handling depends on configuration.",
    },

    # ── AI / Chatbot SDKs ──
    "Google ML Kit": {
        "provider": "Google LLC",
        "category": "ai-chatbot",
        "package_signatures": [
            "com.google.mlkit",
            "com.google.android.gms.vision",
        ],
        "data_accessed": [
            "Camera Input", "Image Data", "Text Input",
            "On-device Processing Results",
        ],
        "permissions_required": ["CAMERA", "INTERNET"],
        "network_domains": [
            "firebaseml.googleapis.com",
        ],
        "child_appropriate": True,
        "child_appropriate_config": None,
        "privacy_impact": "medium",
        "gdpr_compliant": True,
        "coppa_mode_available": True,
        "description": "On-device machine learning SDK. Supports text recognition, face detection, and image labeling. Mostly processes data locally.",
    },
    "OpenAI API": {
        "provider": "OpenAI",
        "category": "ai-chatbot",
        "package_signatures": [
            "com.openai",
        ],
        "data_accessed": [
            "Text Input", "Conversation Data", "User Prompts",
        ],
        "permissions_required": ["INTERNET"],
        "network_domains": [
            "api.openai.com",
        ],
        "child_appropriate": False,
        "child_appropriate_config": None,
        "privacy_impact": "high",
        "gdpr_compliant": True,
        "coppa_mode_available": False,
        "description": "OpenAI API integration. User conversations may be sent to cloud servers. Content filtering may be limited.",
    },
}


# ─── SDK Category Risk Profiles ──────────────────────────────────────────────────

SDK_CATEGORY_RISK = {
    "advertising": {
        "base_risk": 0.85,
        "child_risk_multiplier": 1.8,
        "description": "Advertising SDKs collect device identifiers, behavioral data, and sometimes location for ad targeting. Highest privacy concern for children.",
    },
    "analytics": {
        "base_risk": 0.45,
        "child_risk_multiplier": 1.4,
        "description": "Analytics SDKs collect usage events and device information. Risk depends on data sharing practices and whether ad IDs are collected.",
    },
    "crash-reporting": {
        "base_risk": 0.15,
        "child_risk_multiplier": 1.1,
        "description": "Crash reporting SDKs collect technical crash data. Minimal personal data risk when properly configured.",
    },
    "push-notifications": {
        "base_risk": 0.20,
        "child_risk_multiplier": 1.2,
        "description": "Push notification SDKs manage device tokens and notification delivery. Low risk when limited to notification functionality.",
    },
    "authentication": {
        "base_risk": 0.30,
        "child_risk_multiplier": 1.3,
        "description": "Authentication SDKs handle user identity data. Risk depends on scope of data accessed and third-party sharing.",
    },
    "social-media": {
        "base_risk": 0.75,
        "child_risk_multiplier": 1.7,
        "description": "Social media SDKs can expose user profiles and enable cross-platform tracking. Not appropriate for young children.",
    },
    "location": {
        "base_risk": 0.55,
        "child_risk_multiplier": 1.6,
        "description": "Location SDKs access precise or approximate location data. High concern when used in child-directed apps.",
    },
    "cloud-storage": {
        "base_risk": 0.20,
        "child_risk_multiplier": 1.1,
        "description": "Cloud storage SDKs handle app data. Risk depends on what data the developer stores and encryption practices.",
    },
    "ai-chatbot": {
        "base_risk": 0.50,
        "child_risk_multiplier": 1.5,
        "description": "AI/chatbot SDKs may process user input on cloud servers. Child conversations and input may be stored or used for training.",
    },
}


def analyze_sdk(
    sdk_name: str,
    is_disclosed_in_data_safety: bool = False,
    target_age: str = "",
    detected_permissions: list[str] | None = None,
) -> dict:
    """
    Perform deep privacy analysis of a single SDK.

    Returns a dict with:
    - provider, category, description
    - data_accessed: list of data types accessed
    - permissions_connected: permissions this SDK requires
    - network_domains: domains it contacts
    - privacy_impact: low | medium | high | critical
    - child_appropriate: bool
    - is_disclosed: whether it appears in Data Safety declarations
    - disclosure_status: "disclosed" | "undisclosed" | "unknown"
    - risk_score: 0-100 SDK-level risk score
    - privacy_config_analysis: assessment of SDK's privacy configuration
    - recommendation: human-readable recommendation
    """
    sdk_info = SDK_CATALOGUE.get(sdk_name)

    if not sdk_info:
        return _unknown_sdk_result(sdk_name, is_disclosed_in_data_safety)

    category = sdk_info["category"]
    cat_risk = SDK_CATEGORY_RISK.get(category, {"base_risk": 0.4, "child_risk_multiplier": 1.3})

    # Child risk assessment
    child_multiplier = 1.0
    target_lower = target_age.lower() if target_age else ""
    if any(x in target_lower for x in ["3-", "4-", "5-", "6-", "7-", "8-",
                                          "preschool", "kindergarten", "early",
                                          "toddler", "child"]):
        child_multiplier = cat_risk["child_risk_multiplier"]
    elif any(x in target_lower for x in ["9-", "10-", "11-", "12-", "13-",
                                            "teen", "middle school", "elementary"]):
        child_multiplier = min(cat_risk["child_risk_multiplier"], 1.5)
    elif any(x in target_lower for x in ["14-", "15-", "16-", "17-",
                                            "high school"]):
        child_multiplier = min(cat_risk["child_risk_multiplier"], 1.3)
    else:
        child_multiplier = min(cat_risk["child_risk_multiplier"], 1.4)

    # Calculate risk score
    base_risk = cat_risk["base_risk"]
    adjusted_risk = min(1.0, base_risk * child_multiplier)

    # Bonus risk for undisclosed SDKs
    if not is_disclosed_in_data_safety:
        adjusted_risk = min(1.0, adjusted_risk + 0.15)

    risk_score = int(adjusted_risk * 100)

    # Determine privacy impact
    if adjusted_risk >= 0.8:
        privacy_impact = "critical"
    elif adjusted_risk >= 0.55:
        privacy_impact = "high"
    elif adjusted_risk >= 0.3:
        privacy_impact = "medium"
    else:
        privacy_impact = "low"

    # Disclosure status
    if is_disclosed_in_data_safety:
        disclosure_status = "disclosed"
    else:
        disclosure_status = "undisclosed"

    # Privacy configuration analysis
    config_issues = []
    if not sdk_info["child_appropriate"]:
        config_issues.append("SDK is not designed for child-directed apps")
    if sdk_info.get("child_appropriate_config") and not sdk_info["child_appropriate"]:
        config_issues.append(
            f"COPPA-compliant mode available ({sdk_info['child_appropriate_config']}) "
            f"but SDK is not child-safe by default"
        )
    if not sdk_info.get("coppa_mode_available"):
        config_issues.append("No COPPA compliance mode available")
    if not is_disclosed_in_data_safety:
        config_issues.append("SDK not disclosed in Google Play Data Safety declaration")
    if "Advertising ID" in sdk_info["data_accessed"]:
        config_issues.append("Collects Advertising ID — cross-app tracking possible")
    if any("Location" in d for d in sdk_info["data_accessed"]):
        config_issues.append("Accesses location data")

    # Permission overlap check
    permission_overlap = []
    if detected_permissions:
        for perm in sdk_info["permissions_required"]:
            if perm in detected_permissions:
                permission_overlap.append(perm)

    # Recommendation
    recommendation = _build_sdk_recommendation(
        sdk_name, category, sdk_info["child_appropriate"],
        is_disclosed_in_data_safety, config_issues, target_age,
    )

    return {
        "name": sdk_name,
        "provider": sdk_info["provider"],
        "category": category,
        "description": sdk_info["description"],
        "data_accessed": sdk_info["data_accessed"],
        "permissions_connected": sdk_info["permissions_required"],
        "permission_overlap": permission_overlap,
        "network_domains": sdk_info["network_domains"],
        "privacy_impact": privacy_impact,
        "child_appropriate": sdk_info["child_appropriate"],
        "coppa_mode_available": sdk_info.get("coppa_mode_available", False),
        "gdpr_compliant": sdk_info.get("gdpr_compliant", False),
        "is_disclosed": is_disclosed_in_data_safety,
        "disclosure_status": disclosure_status,
        "risk_score": risk_score,
        "child_risk_multiplier": round(child_multiplier, 2),
        "privacy_config_issues": config_issues,
        "recommendation": recommendation,
    }


def _unknown_sdk_result(sdk_name: str, is_disclosed: bool) -> dict:
    """Fallback result for SDKs not in our catalogue."""
    return {
        "name": sdk_name,
        "provider": "Unknown",
        "category": "unknown",
        "description": f"SDK '{sdk_name}' was detected but is not in the known SDK catalogue. Manual review is recommended.",
        "data_accessed": ["Unknown — requires manual review"],
        "permissions_connected": [],
        "permission_overlap": [],
        "network_domains": [],
        "privacy_impact": "medium",
        "child_appropriate": None,
        "coppa_mode_available": None,
        "gdpr_compliant": None,
        "is_disclosed": is_disclosed,
        "disclosure_status": "disclosed" if is_disclosed else "undisclosed",
        "risk_score": 50,
        "child_risk_multiplier": 1.0,
        "privacy_config_issues": ["SDK not in known catalogue — data practices unknown"],
        "recommendation": f"The SDK '{sdk_name}' is not in the EduPrivacy-X catalogue. Its data collection and sharing practices should be manually reviewed before including in a child-directed educational app.",
    }


def _build_sdk_recommendation(
    sdk_name, category, child_appropriate, is_disclosed,
    config_issues, target_age,
) -> str:
    """Build a human-readable recommendation for an SDK."""
    parts = []

    if category == "advertising" and "child" in (target_age or "").lower():
        parts.append(
            f"⚠ {sdk_name} is an advertising SDK in a child-directed app. "
            f"COPPA and GDPR-K regulations restrict behavioral advertising to children. "
            f"Consider removing this SDK or enabling strict child-directed treatment."
        )
    elif category == "advertising":
        parts.append(
            f"{sdk_name} is an advertising SDK. It collects behavioral data for ad targeting. "
            f"Ensure users are informed and consent is obtained."
        )
    elif not child_appropriate:
        parts.append(
            f"{sdk_name} is not designed for child-directed applications. "
            f"Review its data practices carefully if this app targets minors."
        )

    if not is_disclosed:
        parts.append(
            f"This SDK is not disclosed in the Google Play Data Safety declaration. "
            f"Google Play policy requires developers to declare all SDKs that handle user data."
        )

    if not parts:
        parts.append(
            f"{sdk_name} appears to be a standard utility SDK with acceptable privacy practices "
            f"for this application context."
        )

    return " ".join(parts)


def analyze_all_sdks(
    sdk_names: list[str],
    target_age: str = "",
    disclosed_sdks: list[str] | None = None,
    detected_permissions: list[str] | None = None,
) -> dict:
    """
    Analyze all detected SDKs for an app.

    Returns:
    - sdks: list of enriched SDK analysis dicts
    - summary: overall SDK risk summary
    - category_breakdown: counts by SDK category
    """
    disclosed = disclosed_sdks or []
    analyzed = []
    category_counts = {}
    total_risk = 0
    advertising_count = 0
    undisclosed_count = 0
    child_inappropriate_count = 0

    for sdk_name in sdk_names:
        is_disclosed = sdk_name in disclosed
        result = analyze_sdk(
            sdk_name=sdk_name,
            is_disclosed_in_data_safety=is_disclosed,
            target_age=target_age,
            detected_permissions=detected_permissions,
        )
        analyzed.append(result)

        cat = result["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1
        total_risk += result["risk_score"]

        if cat == "advertising":
            advertising_count += 1
        if result["disclosure_status"] == "undisclosed":
            undisclosed_count += 1
        if result["child_appropriate"] is False:
            child_inappropriate_count += 1

    total = len(analyzed) or 1
    avg_risk = total_risk / total

    summary = {
        "total_sdks": len(analyzed),
        "advertising_sdks": advertising_count,
        "undisclosed_sdks": undisclosed_count,
        "child_inappropriate_sdks": child_inappropriate_count,
        "avg_sdk_risk_score": round(avg_risk, 1),
        "sdk_risk_contribution": int(min(100, avg_risk)),
        "verdict": _get_sdk_verdict(advertising_count, undisclosed_count, child_inappropriate_count, avg_risk),
    }

    return {
        "sdks": analyzed,
        "summary": summary,
        "category_breakdown": category_counts,
    }


def _get_sdk_verdict(ad_count, undisclosed, child_inappropriate, avg_risk) -> str:
    """Generate a human-readable verdict about the app's SDK profile."""
    if avg_risk < 30 and ad_count == 0 and undisclosed == 0:
        return ("This app uses only well-known, low-risk SDKs with proper disclosure. "
                "SDK usage appears appropriate for an educational context.")
    elif avg_risk < 50 and ad_count <= 1:
        return ("SDK usage is mostly acceptable, though some SDKs warrant review. "
                f"{undisclosed} SDK(s) lack Data Safety disclosure.")
    elif ad_count >= 2 or child_inappropriate >= 2:
        return (f"This app embeds {ad_count} advertising SDK(s) and {child_inappropriate} "
                f"SDK(s) not appropriate for children. This represents significant privacy "
                f"concern for an educational application.")
    else:
        return (f"The app's SDK profile raises moderate concerns. "
                f"{undisclosed} SDK(s) are undisclosed and average risk is {avg_risk:.0f}/100.")
