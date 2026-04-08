"""
YouTube Video Upload Pipeline with SEO optimization.
Uploads video with German title, description, tags and English captions.
"""

import os
import sys
import json
import time
import http.client
import httplib2
import random
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from config import *

httplib2.RETRIES = 1
MAX_RETRIES = 10
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, http.client.NotConnected,
    http.client.IncompleteRead, http.client.ImproperConnectionState,
    http.client.CannotSendRequest, http.client.CannotSendHeader,
    http.client.ResponseNotReady, http.client.BadStatusLine)
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]


def get_youtube_service(token_file=None):
    if token_file is None:
        token_file = TOKEN_FILE
    creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    return build("youtube", "v3", credentials=creds)


def upload_video(video_path, title_de, description_de, tags_de, 
                 caption_file_en=None, thumbnail_path=None,
                 category_id="22", privacy="public", token_file=None):
    """Upload video to YouTube with full SEO metadata."""
    
    youtube = get_youtube_service(token_file)
    
    all_tags = list(set(tags_de + DEFAULT_TAGS_DE))[:30]
    
    body = {
        "snippet": {
            "title": title_de,
            "description": description_de,
            "tags": all_tags,
            "categoryId": category_id,
            "defaultLanguage": "de",
            "defaultAudioLanguage": "de",
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
            "embeddable": True,
            "publicStatsViewable": True,
        },
    }
    
    print(f"\nUploading: {title_de}")
    print(f"  File: {video_path}")
    print(f"  Tags: {len(all_tags)}")
    print(f"  Privacy: {privacy}")
    
    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True, chunksize=1024*1024)
    
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )
    
    video_id = resumable_upload(request)
    
    if video_id and caption_file_en and os.path.exists(caption_file_en):
        print(f"\n  Uploading English captions...")
        upload_captions(youtube, video_id, caption_file_en, "en", "English")
    
    if video_id and thumbnail_path and os.path.exists(thumbnail_path):
        print(f"\n  Setting thumbnail...")
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path, mimetype="image/png")
            ).execute()
            print(f"  Thumbnail set!")
        except HttpError as e:
            print(f"  Thumbnail error (may need verification): {e}")
    
    if video_id:
        print(f"\n  Video uploaded successfully!")
        print(f"  URL: https://www.youtube.com/watch?v={video_id}")
    
    return video_id


def resumable_upload(request):
    """Upload with retry logic."""
    response = None
    error = None
    retry = 0
    
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                print(f"  Progress: {int(status.progress() * 100)}%")
            if response:
                video_id = response.get("id")
                print(f"  Upload complete! Video ID: {video_id}")
                return video_id
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = f"HTTP {e.resp.status}: {e.content}"
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error = str(e)
        
        if error:
            retry += 1
            if retry > MAX_RETRIES:
                print(f"  Max retries reached. Giving up.")
                return None
            
            sleep_seconds = random.random() * (2 ** retry)
            print(f"  Retry {retry}/{MAX_RETRIES} in {sleep_seconds:.1f}s... ({error})")
            time.sleep(sleep_seconds)


def upload_captions(youtube, video_id, caption_file, language, name):
    """Upload caption/subtitle file to a video."""
    try:
        body = {
            "snippet": {
                "videoId": video_id,
                "language": language,
                "name": name,
                "isDraft": False,
            }
        }
        youtube.captions().insert(
            part="snippet",
            body=body,
            media_body=MediaFileUpload(caption_file, mimetype="application/x-subrip"),
        ).execute()
        print(f"  Captions uploaded: {language} ({name})")
    except HttpError as e:
        print(f"  Caption upload error: {e}")


def upload_from_metadata(metadata_path, description_de, tags_de, 
                         english_srt=None, privacy="public", token_file=None):
    """Upload video using metadata.json from generate_video output."""
    with open(metadata_path) as f:
        meta = json.load(f)
    
    video_dir = os.path.dirname(metadata_path)
    srt_en = english_srt or os.path.join(video_dir, "subtitles_en.srt")
    
    return upload_video(
        video_path=meta["video_path"],
        title_de=meta["title_de"],
        description_de=description_de,
        tags_de=tags_de,
        caption_file_en=srt_en if os.path.exists(srt_en) else None,
        privacy=privacy,
        token_file=token_file,
    )


if __name__ == "__main__":
    print("Usage: Import and call upload_video() or upload_from_metadata()")
    print("Example:")
    print('  upload_video("output/video.mp4", "Titel", "Beschreibung", ["tag1", "tag2"])')
