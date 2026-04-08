import os
import json
import webbrowser
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

os.environ['DISPLAY'] = ':1'

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

TOKEN_FILE = "token1.json"

creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
youtube = build("youtube", "v3", credentials=creds)

# Check if channel already exists
try:
    ch_resp = youtube.channels().list(part="snippet,brandingSettings,status", mine=True).execute()
    if ch_resp.get("items"):
        ch = ch_resp["items"][0]
        print(f"Channel already exists!")
        print(f"  ID: {ch['id']}")
        print(f"  Title: {ch['snippet']['title']}")
        print(f"  Description: {ch['snippet'].get('description', 'N/A')}")
        channel_id = ch["id"]
    else:
        print("No channel found on this account.")
        print("Opening YouTube to create channel...")
        webbrowser.open("https://www.youtube.com/create_channel")
        print("Create the channel manually in browser, then run this script again.")
        exit()
except Exception as e:
    print(f"Error: {e}")
    print("Opening YouTube to create channel...")
    webbrowser.open("https://www.youtube.com/create_channel")
    exit()

CHANNEL_NAME = "Innere Stärke"
CHANNEL_DESCRIPTION = """Beziehungspsychologie, emotionale Heilung und persönliches Wachstum — ohne Floskeln.

Wir helfen dir, Selbstbewusstsein aufzubauen, gesunde Grenzen zu setzen und echte Verbindungen zu schaffen.

Hier lernst du:
🧠 Weibliche Psychologie verstehen
💪 Männliche Stärke und innere Ruhe entwickeln
❤️ Gesunde Beziehungen aufbauen
🔥 Nach einer Trennung stärker zurückkommen

Jeden Tag neue Videos über Beziehungspsychologie, Selbstverbesserung und emotionale Intelligenz.

Abonniere jetzt und werde die beste Version von dir selbst!

#BeziehungspsychologieDeutsch #MännlicheStärke #WeiblichePsychologie #Selbstverbesserung #EmotionaleHeilung"""

CHANNEL_KEYWORDS = (
    "Beziehungspsychologie Deutsch weibliche Psychologie männliche Stärke "
    "Selbstverbesserung emotionale Heilung Trennung überwinden "
    "Beziehungsberatung Männer Selbstbewusstsein innere Ruhe "
    "Dating Tipps Deutsch Psychologie Beziehung "
    "Männer Motivation Selbstwert persönliches Wachstum"
)

print(f"\nUpdating channel branding...")
print(f"  Name: {CHANNEL_NAME}")

body = {
    "id": channel_id,
    "brandingSettings": {
        "channel": {
            "title": CHANNEL_NAME,
            "description": CHANNEL_DESCRIPTION,
            "keywords": CHANNEL_KEYWORDS,
            "defaultLanguage": "de",
            "country": "DE",
            "unsubscribedTrailer": "",
        }
    }
}

try:
    update_resp = youtube.channels().update(
        part="brandingSettings",
        body=body
    ).execute()
    print(f"\nChannel branding updated successfully!")
    print(f"  Title: {update_resp['brandingSettings']['channel']['title']}")
    print(f"  Country: {update_resp['brandingSettings']['channel'].get('country', 'N/A')}")
    print(f"  Keywords set: YES")
    print(f"  Description set: YES")
    print(f"\nChannel URL: https://www.youtube.com/channel/{channel_id}")
except Exception as e:
    print(f"Error updating branding: {e}")
