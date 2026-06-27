import os
import hashlib
from datetime import datetime
from androguard.core.apk import APK

DANGEROUS_PERMISSIONS = [
    "android.permission.ACCESS_FINE_LOCATION",
    "android.permission.READ_CONTACTS",
    "android.permission.RECORD_AUDIO",
    "android.permission.CAMERA",
    "android.permission.READ_EXTERNAL_STORAGE",
    "android.permission.WRITE_EXTERNAL_STORAGE",
    "android.permission.READ_SMS",
    "android.permission.SEND_SMS",
    "android.permission.READ_PHONE_STATE",
    "android.permission.ACCESS_COARSE_LOCATION"
]

def get_file_hash(filepath):
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def analyze_apk(filepath: str):
    if not os.path.exists(filepath):
        raise FileNotFoundError("APK not found")
        
    apk_hash = get_file_hash(filepath)
    apk_size_mb = f"{os.path.getsize(filepath) / (1024 * 1024):.2f} MB"
    
    a = APK(filepath)
    
    app_name = a.get_app_name() or "Unknown App"
    package_name = a.get_package() or "unknown.package"
    version_name = a.get_androidversion_name() or "1.0"
    target_sdk = a.get_target_sdk_version()
    
    # Analyze permissions
    perms = a.get_permissions()
    permissions_list = []
    dangerous_count = 0
    for p in perms:
        status = "normal"
        if p in DANGEROUS_PERMISSIONS:
            status = "dangerous"
            dangerous_count += 1
            
        permissions_list.append({
            "name": p.split('.')[-1],
            "status": status,
            "description": p,
            "justified": False
        })
        
    # Calculate simple risk score based on dangerous permissions
    risk_score = 100 - (dangerous_count * 15)
    if risk_score < 0: risk_score = 0
    
    if risk_score > 80:
        risk_grade = "A"
        risk_level = "Low"
    elif risk_score > 60:
        risk_grade = "B"
        risk_level = "Medium"
    elif risk_score > 40:
        risk_grade = "C"
        risk_level = "Medium"
    elif risk_score > 20:
        risk_grade = "D"
        risk_level = "High"
    else:
        risk_grade = "F"
        risk_level = "High"
        
    return {
        "app_name": app_name,
        "package_name": package_name,
        "developer": "Unknown Developer", # Requires Play Store API integration for real data
        "category": "Education", # Defaulting for the dashboard scope
        "version_name": version_name,
        "apk_size": apk_size_mb,
        "target_sdk": int(target_sdk) if target_sdk else 0,
        "apk_hash": apk_hash,
        "analyzed_at": datetime.utcnow().isoformat() + "Z",
        "risk_score": risk_score,
        "risk_grade": risk_grade,
        "risk_level": risk_level,
        "permissions": permissions_list,
        "trackers": []
    }
