#!/usr/bin/env python3
"""
Script to enable multiple Google Cloud APIs for the multi-platform system
"""

import subprocess
import sys
import time

# List of APIs to enable
APIS_TO_ENABLE = [
    # Advertising & Marketing
    "googleads.googleapis.com",  # Google Ads API
    "adsense.googleapis.com",    # AdSense Management API
    "admob.googleapis.com",      # AdMob API
    "searchads360.googleapis.com", # Search Ads 360 API
    
    # AI & Machine Learning
    "vision.googleapis.com",     # Cloud Vision API
    "language.googleapis.com",   # Cloud Natural Language API
    "speech.googleapis.com",     # Cloud Speech-to-Text API
    "translate.googleapis.com",  # Cloud Translation API
    "videointelligence.googleapis.com", # Cloud Video Intelligence API
    "dialogflow.googleapis.com", # Dialogflow API
    
    # Google Workspace
    "sheets.googleapis.com",     # Google Sheets API
    "slides.googleapis.com",     # Google Slides API
    "docs.googleapis.com",       # Google Docs API
    
    # Mobile & Social
    "androidpublisher.googleapis.com", # Google Play Android Developer API
    "people.googleapis.com",     # Google People API
    "blogger.googleapis.com",    # Blogger API
    
    # Search & Discovery
    "customsearch.googleapis.com", # Custom Search API
    "pagespeedonline.googleapis.com", # PageSpeed Insights API
    
    # Maps & Location
    "maps-backend.googleapis.com", # Maps JavaScript API
    "places-backend.googleapis.com", # Places API
    "directions-backend.googleapis.com", # Directions API
    
    # Cloud Infrastructure
    "cloudfunctions.googleapis.com", # Cloud Functions API
    "pubsub.googleapis.com",     # Cloud Pub/Sub API
    "cloudscheduler.googleapis.com", # Cloud Scheduler API
    
    # Security & Identity
    "iam.googleapis.com",        # IAM API
    "securitycenter.googleapis.com", # Security Command Center API
]

def enable_api(api_name, project_id="media-agent-support-system"):
    """Enable a single API"""
    try:
        print(f"Enabling {api_name}...")
        result = subprocess.run([
            "gcloud", "services", "enable", api_name,
            "--project", project_id
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(f"✅ Successfully enabled {api_name}")
            return True
        else:
            print(f"❌ Failed to enable {api_name}: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout enabling {api_name}")
        return False
    except Exception as e:
        print(f"❌ Error enabling {api_name}: {e}")
        return False

def main():
    """Main function to enable all APIs"""
    print("🚀 Starting API enablement process...")
    print(f"📋 Total APIs to enable: {len(APIS_TO_ENABLE)}")
    
    enabled_count = 0
    failed_count = 0
    
    for i, api in enumerate(APIS_TO_ENABLE, 1):
        print(f"\n[{i}/{len(APIS_TO_ENABLE)}] Processing {api}")
        
        if enable_api(api):
            enabled_count += 1
        else:
            failed_count += 1
        
        # Small delay to avoid rate limiting
        time.sleep(2)
    
    print(f"\n🎉 API enablement completed!")
    print(f"✅ Successfully enabled: {enabled_count}")
    print(f"❌ Failed to enable: {failed_count}")
    print(f"📊 Success rate: {(enabled_count / len(APIS_TO_ENABLE)) * 100:.1f}%")

if __name__ == "__main__":
    main()
