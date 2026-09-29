"""
EduPrivacy-X: Multimodal Evidence Fusion Engine (Feature A).

Collects and correlates privacy evidence from six sources:
1. Android Manifest (permissions, components, intent filters)
2. Decompiled Code/Bytecode (API calls, data flows)
3. Application UIs (consent dialogs, dark patterns)
4. Runtime Network Traffic (domains, data transmitted)
5. Privacy Policy (NLP-extracted claims)
6. Google Play Data Safety Declaration

The engine fuses these sources to produce high-confidence privacy findings
and feeds the three-way contradiction detector (Feature F).
"""

import json
from datetime import datetime


# ─── Evidence Categories ────────────────────────────────────────────────────────

# Maps data types to the privacy categories they belong to
DATA_TYPE_CATEGORIES = {
    # Location
    "location": {
        "label": "Location",
        "manifest_indicators": [
            "ACCESS_FINE_LOCATION", "ACCESS_COARSE_LOCATION",
            "ACCESS_BACKGROUND_LOCATION"
        ],
        "code_indicators": [
            "LocationManager", "FusedLocationProviderClient",
            "getLastKnownLocation", "requestLocationUpdates",
            "LocationRequest", "LocationCallback",
            "com.google.android.gms.location",
        ],
        "network_indicators": [
            "latitude", "longitude", "lat", "lng", "geo", "location",
        ],
        "sdk_indicators": [
            "Google AdMob", "Facebook Ads", "Unity Ads", "AppLovin",
        ],
        "child_risk_multiplier": 1.5,
        "base_severity": "high",
    },
    "device_id": {
        "label": "Device Identifier",
        "manifest_indicators": ["READ_PHONE_STATE", "AD_ID"],
        "code_indicators": [
            "getDeviceId", "getAndroidId", "Settings.Secure.ANDROID_ID",
            "TelephonyManager", "getImei", "getSubscriberId",
            "AdvertisingIdClient", "getAdvertisingId",
            "Build.SERIAL", "Build.FINGERPRINT",
        ],
        "network_indicators": [
            "device_id", "android_id", "imei", "gaid", "adid",
            "advertising_id", "fingerprint",
        ],
        "sdk_indicators": [
            "Google AdMob", "Facebook Ads", "Google Analytics",
            "AppsFlyer", "Adjust", "Mixpanel",
        ],
        "child_risk_multiplier": 1.4,
        "base_severity": "high",
    },
    "contacts": {
        "label": "Contacts",
        "manifest_indicators": [
            "READ_CONTACTS", "WRITE_CONTACTS", "GET_ACCOUNTS",
        ],
        "code_indicators": [
            "ContactsContract", "ContentResolver.query",
            "AccountManager", "getAccounts",
        ],
        "network_indicators": [
            "contacts", "phone_number", "email_address", "address_book",
        ],
        "sdk_indicators": [],
        "child_risk_multiplier": 1.6,
        "base_severity": "high",
    },
    "camera": {
        "label": "Camera / Photos",
        "manifest_indicators": ["CAMERA", "READ_MEDIA_IMAGES"],
        "code_indicators": [
            "Camera", "CameraManager", "camera2",
            "MediaStore.Images", "takePicture",
            "ImageCapture", "CameraX",
        ],
        "network_indicators": [
            "photo", "image", "selfie", "picture",
        ],
        "sdk_indicators": [],
        "child_risk_multiplier": 1.7,
        "base_severity": "high",
    },
    "microphone": {
        "label": "Microphone / Audio",
        "manifest_indicators": ["RECORD_AUDIO"],
        "code_indicators": [
            "MediaRecorder", "AudioRecord", "SpeechRecognizer",
            "startListening", "setAudioSource",
        ],
        "network_indicators": [
            "audio", "voice", "recording", "speech",
        ],
        "sdk_indicators": [],
        "child_risk_multiplier": 1.7,
        "base_severity": "high",
    },
    "email": {
        "label": "Email Address",
        "manifest_indicators": ["GET_ACCOUNTS"],
        "code_indicators": [
            "getAccounts", "AccountManager",
            "EditText.*email", "inputType.*email",
        ],
        "network_indicators": [
            "email", "mail", "user_email", "email_address",
        ],
        "sdk_indicators": [
            "Google Firebase", "Facebook Login",
        ],
        "child_risk_multiplier": 1.3,
        "base_severity": "medium",
    },
    "name": {
        "label": "User Name",
        "manifest_indicators": [],
        "code_indicators": [
            "EditText.*name", "displayName", "userName",
            "firstName", "lastName",
        ],
        "network_indicators": [
            "name", "first_name", "last_name", "username",
            "display_name", "full_name",
        ],
        "sdk_indicators": [
            "Google Firebase", "Facebook Login",
        ],
        "child_risk_multiplier": 1.3,
        "base_severity": "medium",
    },
    "date_of_birth": {
        "label": "Date of Birth / Age",
        "manifest_indicators": [],
        "code_indicators": [
            "DatePicker", "DatePickerDialog",
            "birth", "dob", "age",
        ],
        "network_indicators": [
            "dob", "date_of_birth", "birthday", "age", "birth_date",
        ],
        "sdk_indicators": [],
        "child_risk_multiplier": 1.8,
        "base_severity": "high",
    },
    "school_info": {
        "label": "School / Institution",
        "manifest_indicators": [],
        "code_indicators": [
            "school", "institution", "class_name",
            "grade", "teacher", "student_id",
        ],
        "network_indicators": [
            "school", "institution", "class", "grade", "teacher",
            "student_id", "school_name", "school_id",
        ],
        "sdk_indicators": [],
        "child_risk_multiplier": 1.5,
        "base_severity": "high",
    },
    "academic_data": {
        "label": "Academic Performance",
        "manifest_indicators": [],
        "code_indicators": [
            "score", "marks", "result", "exam",
            "quiz", "grade", "performance", "progress",
            "learning_progress", "achievement",
        ],
        "network_indicators": [
            "score", "marks", "result", "exam_result",
            "quiz_score", "learning_progress", "achievement",
            "performance", "grades",
        ],
        "sdk_indicators": [
            "Google Analytics", "Google Firebase",
        ],
        "child_risk_multiplier": 1.4,
        "base_severity": "medium",
    },
    "behavioral_data": {
        "label": "Behavioural Data",
        "manifest_indicators": [],
        "code_indicators": [
            "UsageStatsManager", "screen_time",
            "session_duration", "engagement",
            "click_event", "scroll_event",
            "time_spent", "app_usage",
        ],
        "network_indicators": [
            "behavior", "behaviour", "engagement", "session",
            "screen_time", "usage", "interaction", "event",
        ],
        "sdk_indicators": [
            "Google Analytics", "Google Firebase",
            "Mixpanel", "Amplitude", "Segment",
        ],
        "child_risk_multiplier": 1.3,
        "base_severity": "medium",
    },
    "advertising_id": {
        "label": "Advertising Identifier",
        "manifest_indicators": ["AD_ID"],
        "code_indicators": [
            "AdvertisingIdClient", "getAdvertisingId",
            "getInfo", "advertisingId",
            "com.google.android.gms.ads.identifier",
        ],
        "network_indicators": [
            "gaid", "adid", "advertising_id", "idfa",
        ],
        "sdk_indicators": [
            "Google AdMob", "Facebook Ads", "Unity Ads",
            "AppLovin", "ironSource", "Vungle",
            "AppsFlyer", "Adjust",
        ],
        "child_risk_multiplier": 1.8,
        "base_severity": "critical",
    },
}

# Data sink categories
SINK_CATEGORIES = {
    "network": {
        "label": "Network Request",
        "indicators": [
            "HttpURLConnection", "OkHttpClient", "Retrofit",
            "Volley", "URLConnection", "HttpClient",
            "openConnection", "connect",
        ],
        "risk_weight": 0.9,
    },
    "analytics_sdk": {
        "label": "Analytics SDK",
        "indicators": [
            "FirebaseAnalytics", "logEvent",
            "Mixpanel.track", "Amplitude.logEvent",
            "analytics.track", "Analytics.log",
        ],
        "risk_weight": 0.7,
    },
    "advertising_sdk": {
        "label": "Advertising SDK",
        "indicators": [
            "AdRequest", "AdView", "InterstitialAd",
            "RewardedAd", "NativeAd", "BannerAd",
        ],
        "risk_weight": 0.9,
    },
    "log_file": {
        "label": "Log File",
        "indicators": [
            "Log.d", "Log.i", "Log.e", "Log.v", "Log.w",
            "System.out.println", "printStackTrace",
        ],
        "risk_weight": 0.4,
    },
    "local_database": {
        "label": "Local Database",
        "indicators": [
            "SQLiteDatabase", "Room", "ContentValues",
            "SharedPreferences", "getSharedPreferences",
        ],
        "risk_weight": 0.3,
    },
    "external_storage": {
        "label": "External Storage",
        "indicators": [
            "getExternalFilesDir", "getExternalStorageDirectory",
            "Environment.getExternalStorageDirectory",
            "FileOutputStream",
        ],
        "risk_weight": 0.6,
    },
    "clipboard": {
        "label": "Clipboard",
        "indicators": [
            "ClipboardManager", "setPrimaryClip",
            "ClipData", "clipboard",
        ],
        "risk_weight": 0.5,
    },
    "third_party_api": {
        "label": "Third-Party API",
        "indicators": [
            "graph.facebook.com", "api.twitter.com",
            "api.instagram.com", "googleapis.com",
        ],
        "risk_weight": 0.8,
    },
}


# ─── Evidence Fusion Engine ─────────────────────────────────────────────────────

class EvidenceFusionEngine:
    """
    Combines evidence from multiple sources to produce high-confidence
    privacy findings. Each finding is backed by specific evidence records.
    """

    def __init__(self):
        self.evidence_records = []
        self.fused_findings = []

    def add_manifest_evidence(self, permissions, components, intent_filters=None):
        """
        Process Android manifest to extract privacy-relevant evidence.

        Args:
            permissions: List of permission strings
            components: List of component class names (activities, services, etc.)
            intent_filters: Optional list of intent filter details
        """
        for data_type, config in DATA_TYPE_CATEGORIES.items():
            for perm_indicator in config["manifest_indicators"]:
                matching_perms = [p for p in permissions
                                  if perm_indicator in p.upper() or perm_indicator in p]
                for perm in matching_perms:
                    self.evidence_records.append({
                        "source_type": "manifest",
                        "evidence_category": f"{data_type}_collection",
                        "data_type": config["label"],
                        "description": f"Permission '{perm}' declared in AndroidManifest.xml",
                        "confidence": 0.7,
                        "severity": config["base_severity"],
                        "raw_evidence": f"<uses-permission android:name=\"{perm}\"/>",
                        "file_reference": "AndroidManifest.xml",
                    })

        # Detect SDK-related components
        sdk_packages = {
            "com.google.android.gms.ads": "Google AdMob",
            "com.facebook.ads": "Facebook Ads",
            "com.google.firebase": "Google Firebase",
            "com.google.firebase.analytics": "Google Analytics",
            "com.appsflyer": "AppsFlyer",
            "com.mixpanel": "Mixpanel",
            "com.amplitude": "Amplitude",
            "com.adjust.sdk": "Adjust",
            "com.braze": "Braze",
            "com.unity3d.ads": "Unity Ads",
            "com.applovin": "AppLovin",
            "io.sentry": "Sentry",
            "com.crashlytics": "Crashlytics",
            "com.flurry": "Flurry",
            "com.chartboost": "Chartboost",
            "com.ironsource": "ironSource",
            "com.inmobi": "InMobi",
            "com.mopub": "MoPub",
        }

        detected_sdks = set()
        for comp in components:
            for pkg, sdk_name in sdk_packages.items():
                if pkg in comp and sdk_name not in detected_sdks:
                    detected_sdks.add(sdk_name)
                    self.evidence_records.append({
                        "source_type": "manifest",
                        "evidence_category": "sdk_presence",
                        "data_type": sdk_name,
                        "description": f"SDK '{sdk_name}' detected via component '{comp}'",
                        "confidence": 0.9,
                        "severity": "medium",
                        "raw_evidence": comp,
                        "file_reference": "AndroidManifest.xml",
                    })

        return list(detected_sdks)

    def add_code_evidence(self, code_patterns):
        """
        Process decompiled code/bytecode analysis results.

        Args:
            code_patterns: List of dicts with {pattern, file, line, context}
        """
        for data_type, config in DATA_TYPE_CATEGORIES.items():
            for pattern in code_patterns:
                for indicator in config["code_indicators"]:
                    if indicator.lower() in pattern.get("pattern", "").lower():
                        self.evidence_records.append({
                            "source_type": "decompiled_code",
                            "evidence_category": f"{data_type}_access",
                            "data_type": config["label"],
                            "description": f"Code pattern '{indicator}' found in {pattern.get('file', 'unknown')}",
                            "confidence": 0.8,
                            "severity": config["base_severity"],
                            "raw_evidence": pattern.get("context", indicator),
                            "matched_indicator": indicator,
                            "file_reference": pattern.get("file", ""),
                            "line_number": pattern.get("line"),
                        })
                        break  # One match per pattern per data type is enough

    def add_network_evidence(self, network_requests):
        """
        Process dynamic network traffic observations.

        Args:
            network_requests: List of dicts with {domain, url, method, data_params, is_encrypted, phase}
        """
        for request in network_requests:
            data_types_found = []
            for data_type, config in DATA_TYPE_CATEGORIES.items():
                url_str = (request.get("url", "") + " " + json.dumps(request.get("data_params", {}))).lower()
                for indicator in config["network_indicators"]:
                    if indicator.lower() in url_str:
                        data_types_found.append(config["label"])
                        self.evidence_records.append({
                            "source_type": "network_traffic",
                            "evidence_category": f"{data_type}_transmission",
                            "data_type": config["label"],
                            "description": (
                                f"{config['label']} data indicator '{indicator}' detected "
                                f"in {'encrypted' if request.get('is_encrypted', True) else 'UNENCRYPTED'} "
                                f"request to {request.get('domain', 'unknown')}"
                            ),
                            "confidence": 0.85,
                            "severity": "critical" if not request.get("is_encrypted", True) else config["base_severity"],
                            "raw_evidence": json.dumps({
                                "domain": request.get("domain"),
                                "url": request.get("url"),
                                "method": request.get("method"),
                                "phase": request.get("phase", "runtime"),
                            }),
                            "file_reference": f"Network: {request.get('domain', 'unknown')}",
                        })
                        break

    def add_policy_evidence(self, policy_extraction):
        """
        Process NLP-extracted privacy policy claims.

        Args:
            policy_extraction: Dict of extracted privacy policy claims
        """
        field_to_data_type = {
            "collects_location": ("location", "Location"),
            "collects_device_id": ("device_id", "Device Identifier"),
            "collects_contacts": ("contacts", "Contacts"),
            "collects_camera": ("camera", "Camera / Photos"),
            "collects_microphone": ("microphone", "Microphone / Audio"),
            "collects_email": ("email", "Email Address"),
            "collects_name": ("name", "User Name"),
            "collects_age_dob": ("date_of_birth", "Date of Birth / Age"),
            "collects_school_info": ("school_info", "School / Institution"),
            "collects_academic_data": ("academic_data", "Academic Performance"),
            "collects_behavioral_data": ("behavioral_data", "Behavioural Data"),
        }

        for field, (category, label) in field_to_data_type.items():
            value = policy_extraction.get(field)
            if value is not None:
                claim = "claims to collect" if value else "does not mention collecting"
                self.evidence_records.append({
                    "source_type": "privacy_policy",
                    "evidence_category": f"{category}_policy_claim",
                    "data_type": label,
                    "description": f"Privacy policy {claim} {label}",
                    "confidence": policy_extraction.get("extraction_confidences", {}).get(field, 0.6),
                    "severity": "info",
                    "raw_evidence": policy_extraction.get("policy_excerpt", ""),
                    "file_reference": policy_extraction.get("policy_url", ""),
                })

    def add_data_safety_evidence(self, data_safety):
        """
        Process Google Play Data Safety declaration.

        Args:
            data_safety: Dict of Data Safety declaration fields
        """
        field_to_data_type = {
            "declares_location_collected": ("location", "Location"),
            "declares_contacts_collected": ("contacts", "Contacts"),
            "declares_photos_videos_collected": ("camera", "Camera / Photos"),
            "declares_audio_collected": ("microphone", "Microphone / Audio"),
            "declares_device_id_collected": ("device_id", "Device Identifier"),
            "declares_personal_info_collected": ("name", "Personal Information"),
        }

        for field, (category, label) in field_to_data_type.items():
            value = data_safety.get(field)
            if value is not None:
                declaration = "declares collection of" if value else "declares NO collection of"
                self.evidence_records.append({
                    "source_type": "data_safety",
                    "evidence_category": f"{category}_data_safety",
                    "data_type": label,
                    "description": f"Data Safety label {declaration} {label}",
                    "confidence": 0.95,  # Developer-declared, high confidence in what they claim
                    "severity": "info",
                    "raw_evidence": json.dumps({field: value}),
                    "file_reference": data_safety.get("play_store_url", "Google Play Data Safety"),
                })

    def fuse_evidence(self):
        """
        Cross-correlate evidence from all sources to produce fused findings.
        A finding is considered high-confidence when corroborated by
        multiple sources.

        Returns:
            List of fused findings with confidence scores and source attribution.
        """
        # Group evidence by data type
        by_data_type = {}
        for record in self.evidence_records:
            dt = record["data_type"]
            if dt not in by_data_type:
                by_data_type[dt] = []
            by_data_type[dt].append(record)

        self.fused_findings = []

        for data_type, records in by_data_type.items():
            sources = set(r["source_type"] for r in records)
            source_count = len(sources)

            # Calculate fused confidence based on corroboration
            max_confidence = max(r["confidence"] for r in records)
            fused_confidence = min(1.0, max_confidence + (source_count - 1) * 0.1)

            # Determine fused severity
            severity_order = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
            max_severity = max(records, key=lambda r: severity_order.get(r["severity"], 0))["severity"]

            # Determine if there are contradictions
            has_technical_evidence = any(
                s in sources for s in ["manifest", "decompiled_code", "network_traffic"]
            )
            policy_claims_collection = any(
                r["source_type"] == "privacy_policy" and "claims to collect" in r["description"]
                for r in records
            )
            policy_denies_collection = any(
                r["source_type"] == "privacy_policy" and "does not mention" in r["description"]
                for r in records
            )
            data_safety_declares = any(
                r["source_type"] == "data_safety" and "declares collection" in r["description"]
                for r in records
            )
            data_safety_denies = any(
                r["source_type"] == "data_safety" and "declares NO collection" in r["description"]
                for r in records
            )

            # Detect disclosure inconsistencies
            mismatches = []
            if has_technical_evidence and data_safety_denies:
                mismatches.append({
                    "type": "under_disclosure",
                    "description": f"{data_type} technically detected but Data Safety declares no collection",
                    "severity": "high",
                })
            if not has_technical_evidence and data_safety_declares:
                mismatches.append({
                    "type": "over_disclosure",
                    "description": f"{data_type} declared in Data Safety but no technical evidence found",
                    "severity": "low",
                })
            if policy_claims_collection and data_safety_denies:
                mismatches.append({
                    "type": "policy_conflict",
                    "description": f"Privacy policy claims {data_type} collection but Data Safety disagrees",
                    "severity": "medium",
                })
            if has_technical_evidence and policy_denies_collection:
                mismatches.append({
                    "type": "under_disclosure",
                    "description": f"{data_type} technically detected but not mentioned in privacy policy",
                    "severity": "high",
                })

            self.fused_findings.append({
                "data_type": data_type,
                "sources": list(sources),
                "source_count": source_count,
                "fused_confidence": round(fused_confidence, 2),
                "severity": max_severity,
                "is_confirmed": source_count >= 2,
                "has_technical_evidence": has_technical_evidence,
                "policy_mentions": policy_claims_collection,
                "data_safety_declares": data_safety_declares,
                "mismatches": mismatches,
                "evidence_count": len(records),
                "records": records,
            })

        # Sort by severity and confidence
        severity_order = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
        self.fused_findings.sort(
            key=lambda f: (severity_order.get(f["severity"], 0), f["fused_confidence"]),
            reverse=True,
        )

        return self.fused_findings

    def get_disclosure_consistency_score(self):
        """
        Calculate the Disclosure Consistency Score (0-100).
        100 = perfect consistency, 0 = maximum inconsistency.
        """
        if not self.fused_findings:
            return 100.0

        total_data_types = len(self.fused_findings)
        mismatched = sum(1 for f in self.fused_findings if f["mismatches"])
        mismatch_severity_sum = sum(
            {"low": 0.25, "medium": 0.5, "high": 0.75, "critical": 1.0}.get(m["severity"], 0.5)
            for f in self.fused_findings
            for m in f["mismatches"]
        )

        if total_data_types == 0:
            return 100.0

        # Score decreases with more mismatches and higher severity
        raw_score = max(0, 100 - (mismatch_severity_sum / total_data_types) * 100)
        return round(raw_score, 1)

    def get_summary(self):
        """Return a summary dict of the fused evidence analysis."""
        findings = self.fused_findings or self.fuse_evidence()
        all_mismatches = [m for f in findings for m in f["mismatches"]]

        return {
            "total_evidence_records": len(self.evidence_records),
            "total_data_types_detected": len(findings),
            "confirmed_findings": sum(1 for f in findings if f["is_confirmed"]),
            "high_confidence_findings": sum(1 for f in findings if f["fused_confidence"] >= 0.8),
            "total_mismatches": len(all_mismatches),
            "under_disclosures": sum(1 for m in all_mismatches if m["type"] == "under_disclosure"),
            "over_disclosures": sum(1 for m in all_mismatches if m["type"] == "over_disclosure"),
            "policy_conflicts": sum(1 for m in all_mismatches if m["type"] == "policy_conflict"),
            "ambiguous_disclosures": sum(1 for m in all_mismatches if m["type"] == "ambiguous_disclosure"),
            "disclosure_consistency_score": self.get_disclosure_consistency_score(),
            "sources_used": list(set(r["source_type"] for r in self.evidence_records)),
        }


# ─── Manifest Evidence Extractor ────────────────────────────────────────────────

def extract_manifest_evidence(apk_obj):
    """
    Extract all privacy-relevant evidence from an APK's manifest using Androguard.

    Args:
        apk_obj: An Androguard APK object

    Returns:
        Dict with permissions, components, intent_filters, and detected_sdks
    """
    permissions = apk_obj.get_permissions()
    activities = apk_obj.get_activities()
    services = apk_obj.get_services()
    receivers = apk_obj.get_receivers()
    providers = apk_obj.get_providers()

    components = list(activities) + list(services) + list(receivers) + list(providers)

    # Extract intent filters for deeper analysis
    intent_filters = []
    try:
        for activity in activities:
            filters = apk_obj.get_intent_filters("activity", activity)
            if filters:
                intent_filters.append({
                    "component": activity,
                    "type": "activity",
                    "filters": filters
                })
    except Exception:
        pass

    return {
        "permissions": permissions,
        "components": components,
        "activities": list(activities),
        "services": list(services),
        "receivers": list(receivers),
        "providers": list(providers),
        "intent_filters": intent_filters,
    }


# ─── Code Pattern Scanner (Simplified Static Analysis) ──────────────────────

def scan_code_patterns(apk_obj, diagnostics=None):
    """
    Scan decompiled bytecode for privacy-relevant API patterns.
    Uses Androguard's DEX analysis for bytecode-level scanning
    without requiring full decompilation.

    Args:
        apk_obj: An Androguard APK object

    Returns:
        List of detected code patterns
    """
    detected_patterns = []
    if diagnostics is not None:
        diagnostics["status"] = "complete"

    # Collect all code indicators from all data type categories
    all_indicators = []
    for data_type, config in DATA_TYPE_CATEGORIES.items():
        for indicator in config["code_indicators"]:
            all_indicators.append((data_type, indicator))

    # Add sink indicators
    for sink_cat, config in SINK_CATEGORIES.items():
        for indicator in config["indicators"]:
            all_indicators.append((f"sink_{sink_cat}", indicator))

    try:
        from androguard.core.dex import DEX
        from androguard.core.apk import APK

        # Get DEX files from the APK
        dex_files = apk_obj.get_all_dex()
        for dex_index, dex_data in enumerate(dex_files, 1):
            try:
                dex = DEX(dex_data)
                # Scan through strings in the DEX
                for string_item in dex.get_strings():
                    string_val = str(string_item)
                    for data_type, indicator in all_indicators:
                        if indicator.lower() in string_val.lower():
                            detected_patterns.append({
                                "pattern": indicator,
                                "file": "classes.dex" if dex_index == 1 else f"classes{dex_index}.dex",
                                "line": None,
                                "context": string_val,
                                "data_type": data_type,
                            })
            except Exception:
                if diagnostics is not None:
                    diagnostics["status"] = "partial_failure"
                continue
    except ImportError:
        if diagnostics is not None:
            diagnostics["status"] = "unavailable"
    except Exception:
        if diagnostics is not None:
            diagnostics["status"] = "failed"

    # Deduplicate patterns
    seen = set()
    unique_patterns = []
    for p in detected_patterns:
        key = (p["pattern"], p["data_type"], p["file"], p["context"])
        if key not in seen:
            seen.add(key)
            unique_patterns.append(p)

    return unique_patterns


# ─── Full Evidence Pipeline ─────────────────────────────────────────────────────

def run_evidence_pipeline(apk_obj, policy_data=None, data_safety_data=None, network_data=None):
    """
    Run the complete multimodal evidence pipeline on an APK.

    Args:
        apk_obj: Androguard APK object
        policy_data: Optional dict of NLP-extracted privacy policy claims
        data_safety_data: Optional dict of Data Safety declaration
        network_data: Optional list of network traffic observations

    Returns:
        Dict with fused findings, summary, and all evidence records
    """
    engine = EvidenceFusionEngine()

    # Source 1: Manifest
    manifest_data = extract_manifest_evidence(apk_obj)
    detected_sdks = engine.add_manifest_evidence(
        permissions=manifest_data["permissions"],
        components=manifest_data["components"],
        intent_filters=manifest_data.get("intent_filters"),
    )

    # Source 2: Decompiled code/bytecode
    scan_diagnostics = {}
    code_patterns = scan_code_patterns(apk_obj, scan_diagnostics)
    engine.add_code_evidence(code_patterns)

    # Source 3: Network traffic (if available)
    if network_data:
        engine.add_network_evidence(network_data)

    # Source 4: Privacy policy (if available)
    if policy_data:
        engine.add_policy_evidence(policy_data)

    # Source 5: Data Safety (if available)
    if data_safety_data:
        engine.add_data_safety_evidence(data_safety_data)

    # Fuse all evidence
    fused_findings = engine.fuse_evidence()
    summary = engine.get_summary()

    return {
        "code_scan_status": scan_diagnostics["status"],
        "manifest_data": manifest_data,
        "detected_sdks": detected_sdks,
        "code_patterns": code_patterns,
        "fused_findings": fused_findings,
        "summary": summary,
        "disclosure_consistency_score": summary["disclosure_consistency_score"],
        "evidence_records": engine.evidence_records,
    }
