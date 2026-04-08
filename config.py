import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FFMPEG_PATH = os.path.expanduser("~/.local/lib/python3.12/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2")

# Directories
AVATARS_DIR = os.path.join(BASE_DIR, "avatars")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")

# TTS
GERMAN_VOICE = "de-DE-SeraphinaMultilingualNeural"
GERMAN_VOICE_RATE = "+0%"
GERMAN_VOICE_PITCH = "+0Hz"

# Video Settings
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
VIDEO_FPS = 30
VIDEO_BG_COLOR = "#1a1a2e"

# YouTube API
TOKEN_FILE = os.path.join(BASE_DIR, "token1.json")
SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

# Channel Info
CHANNEL_NAME = "Innere Staerke"
DEFAULT_TAGS_DE = [
    "weibliche Psychologie",
    "Beziehungspsychologie",
    "Selbstverbesserung Maenner",
    "maennliche Staerke",
    "emotionale Heilung",
    "Dating Tipps Deutsch",
    "Beziehungsberatung",
    "Psychologie Deutsch",
    "Trennung ueberwinden",
    "Selbstbewusstsein",
]
