"""
EduPrivacy-X: Data Safety Declaration Scraper (Feature A/F Mock).
Scrapes the Google Play Data Safety section for an application.
"""

def fetch_data_safety(package_name: str) -> dict:
    """
    In a real implementation, this would:
    1. Request the Google Play Store page for package_name
    2. Parse the Data Safety HTML section
    3. Extract the declared collection and sharing practices

    For now, this returns mocked data to demonstrate three-way contradiction.
    """
    return {
        "fetched_at": "2026-07-22T10:00:00Z",
        "play_store_url": f"https://play.google.com/store/apps/details?id={package_name}",
        
        "declares_location_collected": False,  # Mocking an under-disclosure contradiction
        "declares_location_shared": False,
        "declares_personal_info_collected": True,
        "declares_personal_info_shared": False,
        "declares_financial_info_collected": False,
        "declares_contacts_collected": False,
        "declares_contacts_shared": False,
        "declares_photos_videos_collected": False,
        "declares_audio_collected": False,
        "declares_device_id_collected": True,
        "declares_device_id_shared": True,
        "declares_app_activity_collected": True,
        "declares_web_browsing_collected": False,
        
        "declares_data_encrypted_in_transit": True,
        "declares_data_deletion_available": False,
        "declares_independent_security_review": False,
        "declares_family_policy_compliance": True,
        
        "purposes_app_functionality": True,
        "purposes_analytics": True,
        "purposes_advertising": False,
        "purposes_personalization": True,
        "purposes_account_management": True,
        
        "raw_declaration": "{}"
    }
