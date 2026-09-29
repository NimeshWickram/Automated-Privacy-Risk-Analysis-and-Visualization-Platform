"""Versioned concepts. Observations, behavior, claims and findings are distinct."""
from enum import Enum
import hashlib
import json

ONTOLOGY_VERSION = "privacy-ontology-1.0"
RULE_VERSION = "privacy-fusion-1.0"
ANALYSIS_VERSION = "phase2-fusion-1.0"


class Source(str, Enum):
    MANIFEST = "MANIFEST"
    CODE = "CODE"
    SDK = "SDK"
    NETWORK = "NETWORK"
    POLICY = "POLICY"
    DATA_SAFETY = "DATA_SAFETY"


class DataCategory(str, Enum):
    LOCATION = "LOCATION"
    CONTACTS = "CONTACTS"
    DEVICE_IDENTIFIER = "DEVICE_IDENTIFIER"
    ADVERTISING_IDENTIFIER = "ADVERTISING_IDENTIFIER"
    CAMERA = "CAMERA"
    MICROPHONE = "MICROPHONE"
    PERSONAL_INFORMATION = "PERSONAL_INFORMATION"
    EMAIL = "EMAIL"
    NAME = "NAME"
    AGE = "AGE"
    SCHOOL_INFORMATION = "SCHOOL_INFORMATION"
    ACADEMIC_DATA = "ACADEMIC_DATA"
    BEHAVIORAL_DATA = "BEHAVIORAL_DATA"
    UNKNOWN = "UNKNOWN"


class Behavior(str, Enum):
    PERMISSION_REQUESTED = "PERMISSION_REQUESTED"
    API_REFERENCE = "API_REFERENCE"
    API_ACCESS = "API_ACCESS"  # Reserved: static string scanning never emits this.
    SDK_PRESENT = "SDK_PRESENT"
    THIRD_PARTY_ACCESS = "THIRD_PARTY_ACCESS"  # Reserved; presence is insufficient.
    CONTACTS_DOMAIN = "CONTACTS_DOMAIN"
    DATA_TRANSMISSION = "DATA_TRANSMISSION"


class Claim(str, Enum):
    POLICY_CLAIMS_COLLECTION = "POLICY_CLAIMS_COLLECTION"
    POLICY_DENIES_COLLECTION = "POLICY_DENIES_COLLECTION"
    DATA_SAFETY_CLAIMS_COLLECTION = "DATA_SAFETY_CLAIMS_COLLECTION"
    DATA_SAFETY_DENIES_COLLECTION = "DATA_SAFETY_DENIES_COLLECTION"
    UNKNOWN = "UNKNOWN"
    NOT_MENTIONED = "NOT_MENTIONED"


class Finding(str, Enum):
    CAPABILITY = "Sensitive Permission Capability"
    UNNECESSARY_PERMISSION = "Potentially Unnecessary Permission"
    ACCESS = "Potential Sensitive Data Access"
    TRANSMISSION = "Potential Data Transmission"
    DISCLOSURE = "Potential Disclosure Inconsistency"
    SDK_PRESENCE = "Third-Party SDK Presence"


# Exact permission mappings; substring matches must not manufacture categories.
PERMISSIONS = {
    **dict.fromkeys(("ACCESS_FINE_LOCATION", "ACCESS_COARSE_LOCATION", "ACCESS_BACKGROUND_LOCATION"), "LOCATION"),
    "READ_CONTACTS": "CONTACTS", "WRITE_CONTACTS": "CONTACTS",
    "READ_PHONE_STATE": "DEVICE_IDENTIFIER", "AD_ID": "ADVERTISING_IDENTIFIER",
    "CAMERA": "CAMERA", "RECORD_AUDIO": "MICROPHONE",
}

# Intentionally excludes ambiguous generic strings such as 'age', 'score',
# ContentResolver.query and AccountManager. An unknown category stays unknown.
API_CATEGORIES = {
    **dict.fromkeys(("LocationManager", "FusedLocationProviderClient", "getLastKnownLocation", "requestLocationUpdates", "LocationRequest", "LocationCallback", "com.google.android.gms.location"), "LOCATION"),
    **dict.fromkeys(("getDeviceId", "getAndroidId", "Settings.Secure.ANDROID_ID", "TelephonyManager", "getImei", "getSubscriberId", "Build.SERIAL", "Build.FINGERPRINT"), "DEVICE_IDENTIFIER"),
    "AdvertisingIdClient": "ADVERTISING_IDENTIFIER", "getAdvertisingId": "ADVERTISING_IDENTIFIER",
    "ContactsContract": "CONTACTS",
    **dict.fromkeys(("Camera", "CameraManager", "camera2", "takePicture", "ImageCapture", "CameraX"), "CAMERA"),
    **dict.fromkeys(("MediaRecorder", "AudioRecord", "SpeechRecognizer", "startListening", "setAudioSource"), "MICROPHONE"),
}

PRESETS = {
    "A": ("MANIFEST",),
    "B": ("MANIFEST", "CODE"),
    "C": ("MANIFEST", "CODE", "SDK"),
    "D": ("MANIFEST", "CODE", "SDK", "NETWORK"),
    "E": tuple(source.value for source in Source),
}
WEIGHTS = {"MANIFEST": 40, "CODE": 60, "SDK": 50, "NETWORK": 90, "POLICY": 70, "DATA_SAFETY": 80}


def canonical_json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def configuration(preset):
    if preset not in PRESETS:
        raise ValueError("Configuration must be one of A, B, C, D, E.")
    value = {"preset": preset, "enabled_sources": sorted(PRESETS[preset]),
             "ontology_version": ONTOLOGY_VERSION, "rule_version": RULE_VERSION,
             "base_strength_points": dict(WEIGHTS), "capability_corroboration_points": 10}
    return {"id": digest(value), **value}
