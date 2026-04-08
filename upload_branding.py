import os
import json
import base64
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

creds = Credentials.from_authorized_user_file("token1.json", SCOPES)
youtube = build("youtube", "v3", credentials=creds)

ch_resp = youtube.channels().list(part="snippet,brandingSettings", mine=True).execute()
channel = ch_resp["items"][0]
channel_id = channel["id"]
print(f"Channel: {channel['snippet']['title']} ({channel_id})")

# Step 1: Upload profile picture (channel avatar)
print("\n[1/2] Uploading profile picture...")
try:
    with open("logo.png", "rb") as f:
        logo_data = f.read()
    
    # YouTube uses channelBanners.insert for banner, but profile pic needs different approach
    # Profile picture is set via Google account, not YouTube API directly
    print("  Note: Profile picture must be set via YouTube Studio (API limitation)")
    print("  File ready: logo.png (800x800)")
except Exception as e:
    print(f"  Error: {e}")

# Step 2: Upload channel banner
print("\n[2/2] Uploading channel banner...")
try:
    media = MediaFileUpload("banner.png", mimetype="image/png", resumable=True)
    banner_resp = youtube.channelBanners().insert(
        media_body=media
    ).execute()
    
    banner_url = banner_resp["url"]
    print(f"  Banner uploaded! URL: {banner_url}")
    
    body = {
        "id": channel_id,
        "brandingSettings": {
            "image": {
                "bannerExternalUrl": banner_url
            },
            "channel": channel["brandingSettings"]["channel"]
        }
    }
    
    update_resp = youtube.channels().update(
        part="brandingSettings",
        body=body
    ).execute()
    print("  Banner set on channel successfully!")
    
except Exception as e:
    print(f"  Error: {e}")

print(f"\nDone! Channel: https://www.youtube.com/channel/{channel_id}")
print("Note: Upload logo.png as profile picture manually in YouTube Studio")
