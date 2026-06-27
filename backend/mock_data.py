# backend/mock_data.py

DASHBOARD_DATA = {
    "totalAppsAnalyzed": 3,
    "averageRiskScore": 59,
    "lastScanDate": "2023-10-24 14:30 UTC",
    "riskDistribution": [
        {"name": "Low Risk", "value": 1, "color": "#10b981"},
        {"name": "Medium Risk", "value": 1, "color": "#f59e0b"},
        {"name": "High Risk", "value": 1, "color": "#ef4444"}
    ],
    "recentApps": [
        {
            "id": "1",
            "name": "Kids Math Pro",
            "developer": "EduPlay Inc.",
            "category": "Education",
            "riskScore": 65,
            "riskGrade": "C",
            "riskLevel": "Medium",
            "analyzedAt": "2h ago"
        },
        {
            "id": "2",
            "name": "ABC Phonics Adventure",
            "developer": "LearnRight Labs",
            "category": "Education",
            "riskScore": 25,
            "riskGrade": "A",
            "riskLevel": "Low",
            "analyzedAt": "5h ago"
        },
        {
            "id": "3",
            "name": "Science Explorer Kids",
            "developer": "STEM World Apps",
            "category": "Education",
            "riskScore": 88,
            "riskGrade": "F",
            "riskLevel": "High",
            "analyzedAt": "1d ago"
        }
    ]
}

APP_DETAILS = {
    "1": {
        "id": "1",
        "name": "Kids Math Pro",
        "developer": "EduPlay Inc.",
        "category": "Education",
        "analyzedAt": "2023-10-24T14:30:00Z",
        "riskScore": 65,
        "riskGrade": "C",
        "riskLevel": "Medium",
        "dimensions": {
            "Permissions": 70,
            "Trackers": 60,
            "Network": 50,
            "Storage": 45,
            "Child Safety": 80
        },
        "permissions": {
            "total": 12,
            "dangerous": 3,
            "list": [
                {"name": "ACCESS_FINE_LOCATION", "status": "dangerous", "description": "Precise location tracking", "justified": False},
                {"name": "READ_EXTERNAL_STORAGE", "status": "dangerous", "description": "Read photos and files", "justified": True},
                {"name": "CAMERA", "status": "dangerous", "description": "Take pictures and videos", "justified": False},
                {"name": "INTERNET", "status": "normal", "description": "Full network access", "justified": True}
            ]
        },
        "trackers": {
            "total": 4,
            "list": [
                {"name": "Google AdMob", "type": "Advertising", "risk": "High"},
                {"name": "Facebook Analytics", "type": "Analytics", "risk": "High"},
                {"name": "Crashlytics", "type": "Crash Reporting", "risk": "Low"}
            ]
        },
        "network": {
            "unencryptedEndpoints": 2,
            "domains": ["api.eduplay.com (HTTPS)", "ads.eduplay.com (HTTP)"]
        },
        "disclosureMismatch": [
            {
                "id": "1",
                "claim": "No location data collected",
                "finding": "Location data sent to ad network",
                "severity": "critical"
            },
            {
                "id": "2",
                "claim": "Data is encrypted in transit",
                "finding": "HTTP endpoints detected",
                "severity": "high"
            }
        ]
    },
    "2": {
        "id": "2",
        "name": "ABC Phonics Adventure",
        "developer": "LearnRight Labs",
        "category": "Education",
        "analyzedAt": "2023-10-24T11:15:00Z",
        "riskScore": 25,
        "riskGrade": "A",
        "riskLevel": "Low",
        "dimensions": {
            "Permissions": 20,
            "Trackers": 15,
            "Network": 10,
            "Storage": 5,
            "Child Safety": 30
        },
        "permissions": {
            "total": 3,
            "dangerous": 0,
            "list": [
                {"name": "INTERNET", "status": "normal", "description": "Full network access", "justified": True},
                {"name": "ACCESS_NETWORK_STATE", "status": "normal", "description": "View network connections", "justified": True}
            ]
        },
        "trackers": {
            "total": 1,
            "list": [
                {"name": "Crashlytics", "type": "Crash Reporting", "risk": "Low"}
            ]
        },
        "network": {
            "unencryptedEndpoints": 0,
            "domains": ["api.learnright.com (HTTPS)"]
        },
        "disclosureMismatch": []
    },
    "3": {
        "id": "3",
        "name": "Science Explorer Kids",
        "developer": "STEM World Apps",
        "category": "Education",
        "analyzedAt": "2023-10-23T09:45:00Z",
        "riskScore": 88,
        "riskGrade": "F",
        "riskLevel": "High",
        "dimensions": {
            "Permissions": 90,
            "Trackers": 85,
            "Network": 95,
            "Storage": 70,
            "Child Safety": 100
        },
        "permissions": {
            "total": 18,
            "dangerous": 7,
            "list": [
                {"name": "ACCESS_FINE_LOCATION", "status": "dangerous", "description": "Precise location tracking", "justified": False},
                {"name": "READ_CONTACTS", "status": "dangerous", "description": "Read your contacts", "justified": False},
                {"name": "RECORD_AUDIO", "status": "dangerous", "description": "Record audio", "justified": False},
                {"name": "CAMERA", "status": "dangerous", "description": "Take pictures and videos", "justified": False}
            ]
        },
        "trackers": {
            "total": 8,
            "list": [
                {"name": "AppFlyer", "type": "Analytics/Ads", "risk": "High"},
                {"name": "Flurry", "type": "Analytics", "risk": "High"},
                {"name": "Chartboost", "type": "Advertising", "risk": "High"}
            ]
        },
        "network": {
            "unencryptedEndpoints": 5,
            "domains": ["api.stemworld.com (HTTP)", "tracking.stemworld.com (HTTP)"]
        },
        "disclosureMismatch": [
            {
                "id": "1",
                "claim": "No personal data collected",
                "finding": "Contacts and audio data sent off-device",
                "severity": "critical"
            },
            {
                "id": "2",
                "claim": "App is COPPA compliant",
                "finding": "Tracks users with persistent ad IDs without age gate",
                "severity": "critical"
            }
        ]
    }
}

COMPARISON_APPS = [
    {
        "id": 1,
        "name": "Kids Math Pro",
        "developer": "EduFun Learning",
        "riskScore": 72,
        "riskGrade": "D",
        "permissions": { "total": 18, "dangerous": 7 },
        "trackers": 7,
        "encryptedEndpoints": "71%",
        "disclosureMatch": "42%",
        "childSafety": "Non-compliant",
        "dimensions": {
            "Permissions": 78,
            "Trackers": 85,
            "Network": 60,
            "Storage": 45,
            "Child Safety": 90,
        },
    },
    {
        "id": 2,
        "name": "ABC Phonics",
        "developer": "LearnPlay Studios",
        "riskScore": 35,
        "riskGrade": "B",
        "permissions": { "total": 8, "dangerous": 2 },
        "trackers": 2,
        "encryptedEndpoints": "100%",
        "disclosureMatch": "89%",
        "childSafety": "Compliant",
        "dimensions": {
            "Permissions": 30,
            "Trackers": 25,
            "Network": 15,
            "Storage": 40,
            "Child Safety": 20,
        },
    },
    {
        "id": 3,
        "name": "Science Explorer",
        "developer": "BrightMind Apps",
        "riskScore": 55,
        "riskGrade": "C",
        "permissions": { "total": 12, "dangerous": 4 },
        "trackers": 4,
        "encryptedEndpoints": "85%",
        "disclosureMatch": "65%",
        "childSafety": "Partial",
        "dimensions": {
            "Permissions": 50,
            "Trackers": 55,
            "Network": 45,
            "Storage": 35,
            "Child Safety": 60,
        },
    }
]
