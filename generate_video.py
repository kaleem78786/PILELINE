"""
Video Generation Pipeline - Philosopher Style
==============================================
Layout:
  - Black background (1920x1080)
  - Left side: Lady character with subtle movement (sway, shift)
  - Right side: Bold captions (Line 1: Yellow, Line 2: Red, Line 3: White)

Pipeline:
  1. Generate German TTS audio + SRT timestamps
  2. Render video frames with animated character + styled captions
  3. Combine with audio using ffmpeg
"""

import os
import sys
import json
import math
import asyncio
import subprocess
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from config import *

os.environ["IMAGEIO_FFMPEG_EXE"] = FFMPEG_PATH

CAPTION_COLORS = [
    (255, 255, 0),    # Yellow - line 1
    (255, 50, 50),    # Red - line 2
    (255, 255, 255),  # White - line 3
]

FONT_SIZE = 58
LINE_SPACING = 22
CAPTION_X_START = 980
CAPTION_Y_CENTER = 540
CHAR_SCALE = 0.95
CHAR_X_BASE = 100
CHAR_Y_BASE = None


async def generate_tts(text, output_audio, output_srt):
    """Generate German TTS audio and SRT subtitles."""
    import edge_tts

    communicate = edge_tts.Communicate(
        text,
        voice=GERMAN_VOICE,
        rate=GERMAN_VOICE_RATE,
        pitch=GERMAN_VOICE_PITCH,
    )

    submaker = edge_tts.SubMaker()
    with open(output_audio, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                submaker.feed(chunk)

    srt_content = submaker.get_srt()
    with open(output_srt, "w", encoding="utf-8") as f:
        f.write(srt_content)

    blocks = parse_srt(srt_content)
    print(f"  Audio saved: {output_audio}")
    print(f"  SRT saved: {output_srt} ({len(blocks)} blocks)")
    return blocks


def parse_srt(srt_text):
    """Parse SRT text into list of {start_sec, end_sec, text} dicts."""
    blocks = []
    parts = srt_text.strip().split("\n\n")
    for part in parts:
        lines = part.strip().split("\n")
        if len(lines) >= 3:
            times = lines[1].split(" --> ")
            start = srt_time_to_sec(times[0].strip())
            end = srt_time_to_sec(times[1].strip())
            text = " ".join(lines[2:])
            blocks.append({"start": start, "end": end, "text": text})
    return blocks


def srt_time_to_sec(t):
    """Convert SRT timestamp (HH:MM:SS,mmm) to seconds."""
    t = t.replace(",", ".")
    parts = t.split(":")
    return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])


def load_character(avatar_path):
    """Load and prepare character image (transparent PNG)."""
    char_img = Image.open(avatar_path).convert("RGBA")
    target_h = int(VIDEO_HEIGHT * CHAR_SCALE)
    ratio = target_h / char_img.height
    target_w = int(char_img.width * ratio)
    char_img = char_img.resize((target_w, target_h), Image.LANCZOS)
    return char_img


def get_character_position(frame_num, total_frames, char_width, char_height):
    """Speaker-style movement: walks left and right like on a stage."""
    t = frame_num / max(total_frames, 1)
    seconds = frame_num / VIDEO_FPS

    walk_range = 180
    walk_speed = 0.06
    walk_x = math.sin(seconds * walk_speed * 2 * math.pi) * walk_range

    pause_factor = 0.3 + 0.7 * abs(math.cos(seconds * walk_speed * 2 * math.pi))
    walk_x *= pause_factor

    step_bob = math.sin(seconds * 1.8 * 2 * math.pi) * 4 * min(abs(math.cos(seconds * walk_speed * 2 * math.pi)), 0.8)

    lean = math.sin(seconds * 0.15 * 2 * math.pi) * 6

    x = CHAR_X_BASE + int(walk_x + lean)
    x = max(0, min(x, VIDEO_WIDTH // 2 - char_width // 2))

    y = VIDEO_HEIGHT - char_height + int(step_bob)

    return x, y


def get_font(size=FONT_SIZE, bold=True):
    """Get a font, trying system fonts first."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    ]
    if not bold:
        font_paths = [p.replace("-Bold", "-Regular").replace("Bold", "Regular") for p in font_paths]

    for fp in font_paths:
        if os.path.exists(fp):
            return ImageFont.truetype(fp, size)
    return ImageFont.load_default()


def wrap_text(text, font, max_width):
    """Wrap text to fit within max_width pixels."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = font.getbbox(test)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def render_captions(draw, text, font, x_start, y_center, max_width):
    """Render 3-color bold captions on the right side."""
    lines = wrap_text(text, font, max_width)

    total_height = len(lines) * (FONT_SIZE + LINE_SPACING)
    y = y_center - total_height // 2

    for i, line in enumerate(lines):
        color = CAPTION_COLORS[i % len(CAPTION_COLORS)]

        draw.text((x_start + 2, y + 2), line, font=font, fill=(0, 0, 0, 180))
        draw.text((x_start, y), line, font=font, fill=color)
        y += FONT_SIZE + LINE_SPACING


def render_frame(frame_num, total_frames, char_img, subtitle_blocks, time_sec, font):
    """Render a single video frame."""
    frame = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 255))

    cx, cy = get_character_position(frame_num, total_frames, char_img.width, char_img.height)
    frame.paste(char_img, (cx, cy), char_img)

    current_text = ""
    for block in subtitle_blocks:
        if block["start"] <= time_sec <= block["end"]:
            current_text = block["text"]
            break

    if current_text:
        draw = ImageDraw.Draw(frame)
        caption_max_w = VIDEO_WIDTH - CAPTION_X_START - 40
        render_captions(draw, current_text, font, CAPTION_X_START, CAPTION_Y_CENTER, caption_max_w)

    return frame.convert("RGB")


def get_audio_duration(audio_path):
    """Get audio duration in seconds using ffprobe."""
    cmd = [
        FFMPEG_PATH.replace("ffmpeg", "ffprobe") if "ffprobe" not in FFMPEG_PATH else FFMPEG_PATH,
        "-i", audio_path,
        "-show_entries", "format=duration",
        "-v", "quiet", "-of", "csv=p=0",
    ]
    try:
        ffprobe_path = FFMPEG_PATH.replace("ffmpeg-linux", "ffprobe-linux") if "ffmpeg" in FFMPEG_PATH else FFMPEG_PATH
        if not os.path.exists(ffprobe_path):
            ffprobe_path = FFMPEG_PATH

        import struct
        import wave
        try:
            result = subprocess.run(
                [ffprobe_path, "-i", audio_path, "-show_entries", "format=duration",
                 "-v", "quiet", "-of", "csv=p=0"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
        except:
            pass

        from mutagen.mp3 import MP3
        return MP3(audio_path).info.length
    except:
        pass

    try:
        import io
        size = os.path.getsize(audio_path)
        return size / (192000 / 8)
    except:
        return 120


def create_video(avatar_path, audio_path, srt_blocks, output_path):
    """Create the full video with animated character and styled captions."""

    print(f"  Loading character image...")
    char_img = load_character(avatar_path)
    print(f"  Character: {char_img.size} (scaled)")

    print(f"  Calculating duration...")
    if srt_blocks:
        duration = max(b["end"] for b in srt_blocks) + 1.0
    else:
        size_bytes = os.path.getsize(audio_path)
        duration = size_bytes / (192000 / 8)
    print(f"  Duration: {duration:.1f}s")

    total_frames = int(duration * VIDEO_FPS)
    font = get_font(FONT_SIZE, bold=True)

    frames_dir = os.path.join(os.path.dirname(output_path), "frames")
    os.makedirs(frames_dir, exist_ok=True)

    print(f"  Rendering {total_frames} frames...")
    for i in range(total_frames):
        time_sec = i / VIDEO_FPS
        frame = render_frame(i, total_frames, char_img, srt_blocks, time_sec, font)
        frame.save(os.path.join(frames_dir, f"frame_{i:06d}.png"), "PNG")

        if i % (VIDEO_FPS * 10) == 0:
            pct = int(i / total_frames * 100)
            print(f"    {pct}% ({i}/{total_frames} frames)")

    print(f"  100% ({total_frames}/{total_frames} frames)")

    print(f"  Encoding video with ffmpeg...")
    cmd = [
        FFMPEG_PATH, "-y",
        "-framerate", str(VIDEO_FPS),
        "-i", os.path.join(frames_dir, "frame_%06d.png"),
        "-i", audio_path,
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        "-movflags", "+faststart",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if result.returncode != 0:
        print(f"  FFmpeg error: {result.stderr[-400:]}")
        return False

    print(f"  Cleaning up frames...")
    for f in os.listdir(frames_dir):
        os.remove(os.path.join(frames_dir, f))
    os.rmdir(frames_dir)

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  Video created: {output_path} ({size_mb:.1f} MB)")
    return True


def generate_video(script_text, title_de, avatar_image, english_subtitle_text=None):
    """Main function to generate a complete video."""

    safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in title_de)[:50].strip()
    safe_title = safe_title.replace(" ", "_")

    video_dir = os.path.join(OUTPUT_DIR, safe_title)
    os.makedirs(video_dir, exist_ok=True)

    audio_path = os.path.join(video_dir, "audio.mp3")
    srt_path = os.path.join(video_dir, "subtitles_de.srt")
    video_path = os.path.join(video_dir, f"{safe_title}.mp4")
    meta_path = os.path.join(video_dir, "metadata.json")

    print(f"\n{'='*60}")
    print(f"Generating: {title_de}")
    print(f"{'='*60}")

    print("\n[1/2] Generating German TTS audio + subtitles...")
    srt_blocks = asyncio.run(generate_tts(script_text, audio_path, srt_path))

    print("\n[2/2] Creating video with animated character + captions...")
    success = create_video(avatar_image, audio_path, srt_blocks, video_path)

    if success:
        metadata = {
            "title_de": title_de,
            "video_path": video_path,
            "audio_path": audio_path,
            "srt_path": srt_path,
            "avatar": avatar_image,
            "voice": GERMAN_VOICE,
        }
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        print(f"\n  Metadata saved: {meta_path}")

    return video_path if success else None


if __name__ == "__main__":
    test_script = """Ich werde mit etwas beginnen, das dich vielleicht ein wenig unwohl fuehlen laesst. Wenn du merkst, dass du dich defensiv fuehlst, ist das voellig in Ordnung. Bemerke es einfach. Aber frage dich warum."""

    avatar = os.path.join(AVATARS_DIR, "avatar.png")

    if not os.path.exists(avatar):
        print(f"Avatar not found: {avatar}")
        print(f"Place your avatar image at: {avatar}")
        exit(1)

    result = generate_video(
        script_text=test_script,
        title_de="Test Video - Philosophische Beratung",
        avatar_image=avatar,
    )

    if result:
        print(f"\n{'='*60}")
        print(f"SUCCESS! Video: {result}")
        print(f"{'='*60}")
