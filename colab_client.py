"""
Colab Client - Sends requests to SadTalker running on Google Colab.

Usage:
    1. Open SadTalker_Pipeline.ipynb in Google Colab
    2. Run cells 1-5 (install + start API server)
    3. Copy the ngrok URL
    4. Run: python3 colab_client.py --url <ngrok_url> --script "German text..."
"""

import os
import sys
import json
import base64
import argparse
import asyncio
import subprocess
import requests
from config import *


def check_server(api_url):
    """Check if Colab server is running."""
    try:
        r = requests.get(f"{api_url}/health", timeout=10)
        if r.status_code == 200:
            data = r.json()
            print(f"  Server: OK (GPU: {data.get('gpu', False)})")
            return True
    except:
        pass
    print("  Server: NOT REACHABLE")
    return False


def generate_on_colab(api_url, script_text, avatar_path, voice=GERMAN_VOICE):
    """Send generation request to Colab and get video back."""
    
    print(f"\n[1/3] Encoding avatar...")
    with open(avatar_path, "rb") as f:
        avatar_b64 = base64.b64encode(f.read()).decode()
    print(f"  Avatar: {len(avatar_b64)} bytes (base64)")
    
    print(f"\n[2/3] Sending to Colab (SadTalker)...")
    print(f"  Script: {script_text[:80]}...")
    print(f"  Voice: {voice}")
    print(f"  This may take 2-5 minutes...")
    
    payload = {
        "script": script_text,
        "voice": voice,
        "avatar_base64": avatar_b64,
    }
    
    try:
        r = requests.post(
            f"{api_url}/generate",
            json=payload,
            timeout=600,
        )
        
        if r.status_code != 200:
            print(f"  Error: {r.status_code} - {r.text[:300]}")
            return None
        
        data = r.json()
        if data.get("status") != "ok":
            print(f"  Error: {data.get('msg', 'Unknown error')}")
            return None
        
        print(f"\n[3/3] Downloading video from Colab...")
        video_b64 = data["video_base64"]
        video_bytes = base64.b64decode(video_b64)
        
        return video_bytes
        
    except requests.exceptions.Timeout:
        print("  Timeout! Video generation took too long.")
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None


def compose_final_video(sadtalker_video_path, audio_path, srt_path, output_path):
    """Compose final video: black BG + animated character left + captions right."""
    
    srt_escaped = srt_path.replace(":", "\\\\:")
    
    filter_complex = (
        f"[0:v]scale=600:-1[avatar];"
        f"color=c=black:s=1920x1080:d=9999[bg];"
        f"[bg][avatar]overlay=80:(H-h)/2:shortest=1[base];"
        f"[base]subtitles={srt_escaped}:force_style='"
        f"FontName=Arial,FontSize=30,Bold=1,"
        f"PrimaryColour=&H0000FFFF,"
        f"OutlineColour=&H00000000,Outline=2,Shadow=1,"
        f"MarginL=550,MarginR=50,MarginV=50,Alignment=6'[v]"
    )
    
    cmd = [
        FFMPEG_PATH, "-y",
        "-i", sadtalker_video_path,
        "-i", audio_path,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "1:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_path,
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        cmd_nosub = [
            FFMPEG_PATH, "-y",
            "-i", sadtalker_video_path, "-i", audio_path,
            "-filter_complex",
            f"[0:v]scale=600:-1[avatar];"
            f"color=c=black:s=1920x1080:d=9999[bg];"
            f"[bg][avatar]overlay=80:(H-h)/2:shortest=1[v]",
            "-map", "[v]", "-map", "1:a",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-pix_fmt", "yuv420p", output_path,
        ]
        subprocess.run(cmd_nosub, capture_output=True, text=True, timeout=300)
    
    return os.path.exists(output_path)


async def generate_tts_local(text, audio_path, srt_path):
    """Generate TTS locally (faster than doing it on Colab)."""
    import edge_tts
    
    communicate = edge_tts.Communicate(text, voice=GERMAN_VOICE, rate=GERMAN_VOICE_RATE, pitch=GERMAN_VOICE_PITCH)
    submaker = edge_tts.SubMaker()
    
    with open(audio_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                submaker.feed(chunk)
    
    srt = submaker.get_srt()
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt)
    
    return srt


def full_pipeline(api_url, script_text, title_de, avatar_path, 
                  upload=False, privacy="private", token_file=None):
    """Complete pipeline: TTS -> Colab SadTalker -> Compose -> Upload."""
    
    safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in title_de)[:50].strip().replace(" ", "_")
    video_dir = os.path.join(OUTPUT_DIR, safe_title)
    os.makedirs(video_dir, exist_ok=True)
    
    audio_path = os.path.join(video_dir, "audio.mp3")
    srt_path = os.path.join(video_dir, "subtitles.srt")
    sadtalker_path = os.path.join(video_dir, "sadtalker_raw.mp4")
    final_path = os.path.join(video_dir, f"{safe_title}.mp4")
    
    print(f"\n{'='*60}")
    print(f"🎬 {title_de}")
    print(f"{'='*60}")
    
    # Step 1: Local TTS
    print(f"\n🔊 [1/4] Generating German TTS...")
    asyncio.run(generate_tts_local(script_text, audio_path, srt_path))
    print(f"  Audio: {audio_path}")
    print(f"  SRT: {srt_path}")
    
    # Step 2: SadTalker on Colab
    print(f"\n🎭 [2/4] SadTalker on Colab...")
    video_bytes = generate_on_colab(api_url, script_text, avatar_path)
    
    if not video_bytes:
        print("  FAILED - no video from Colab")
        return None
    
    with open(sadtalker_path, "wb") as f:
        f.write(video_bytes)
    print(f"  SadTalker video: {sadtalker_path} ({len(video_bytes)/1024/1024:.1f} MB)")
    
    # Step 3: Compose final video
    print(f"\n🎨 [3/4] Composing final video...")
    success = compose_final_video(sadtalker_path, audio_path, srt_path, final_path)
    
    if not success:
        print("  Compose failed, using SadTalker video directly")
        final_path = sadtalker_path
    else:
        size_mb = os.path.getsize(final_path) / (1024*1024)
        print(f"  Final: {final_path} ({size_mb:.1f} MB)")
    
    # Step 4: Upload (optional)
    if upload:
        print(f"\n📤 [4/4] Uploading to YouTube...")
        from upload_video import upload_video
        upload_video(
            video_path=final_path,
            title_de=title_de,
            description_de=f"#{' #'.join(DEFAULT_TAGS_DE[:5])}",
            tags_de=DEFAULT_TAGS_DE,
            caption_file_en=srt_path,
            privacy=privacy,
            token_file=token_file or TOKEN_FILE,
        )
    
    print(f"\n{'='*60}")
    print(f"✅ DONE: {final_path}")
    print(f"{'='*60}")
    return final_path


def main():
    parser = argparse.ArgumentParser(description="Colab SadTalker Client")
    parser.add_argument("--url", required=True, help="Colab ngrok API URL")
    parser.add_argument("--script", help="German script text")
    parser.add_argument("--script-file", help="JSON script file path")
    parser.add_argument("--title", default="Test Video", help="German video title")
    parser.add_argument("--avatar", default=os.path.join(AVATARS_DIR, "avatar.png"))
    parser.add_argument("--upload", action="store_true")
    parser.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"])
    parser.add_argument("--batch", help="Directory with JSON script files")
    
    args = parser.parse_args()
    
    print(f"Checking Colab server: {args.url}")
    if not check_server(args.url):
        print("Cannot reach Colab server! Make sure notebook is running.")
        sys.exit(1)
    
    if args.batch:
        script_files = sorted([f for f in os.listdir(args.batch) if f.endswith(".json")])
        print(f"\nBatch mode: {len(script_files)} scripts")
        for sf in script_files:
            with open(os.path.join(args.batch, sf)) as f:
                data = json.load(f)
            full_pipeline(
                args.url, data["script_de"], data["title_de"],
                args.avatar, args.upload, args.privacy,
            )
    elif args.script_file:
        with open(args.script_file) as f:
            data = json.load(f)
        full_pipeline(args.url, data["script_de"], data["title_de"], args.avatar, args.upload, args.privacy)
    elif args.script:
        full_pipeline(args.url, args.script, args.title, args.avatar, args.upload, args.privacy)
    else:
        print("Provide --script, --script-file, or --batch")


if __name__ == "__main__":
    main()
