# PILELINE - German YouTube Video Factory

Automated pipeline for creating German psychology/relationship YouTube videos with AI talking avatar.

## Quick Start (Google Colab)

### InfiniteTalk - AI Talking Avatar
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/kaleem78786/PILELINE/blob/main/InfiniteTalk.ipynb)

### ComfyUI Version (Less disk space)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/kaleem78786/PILELINE/blob/main/ComfyUI_InfiniteTalk.ipynb)

## Pipeline

1. **German TTS** - edge-tts (Microsoft SeraphinaMultilingualNeural)
2. **Lip Sync** - InfiniteTalk (on Colab GPU)
3. **Video Compose** - Black BG + Character left + Captions right (Yellow/Red/White)
4. **Upload** - YouTube API with full SEO optimization

## Local Scripts

| Script | Purpose |
|--------|---------|
| `config.py` | Settings (voice, video, API, tags) |
| `generate_video.py` | TTS + video creation |
| `upload_video.py` | YouTube upload with SEO |
| `video_factory.py` | Batch video factory |
| `colab_client.py` | Communicates with Colab API |
| `auth_all.py` | YouTube OAuth authentication |

## Setup

```bash
pip install edge-tts google-api-python-client google-auth-oauthlib Pillow
python3 auth_all.py  # Authenticate YouTube accounts
```
