import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

os.environ['DISPLAY'] = ':1'

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

creds = Credentials.from_authorized_user_file("token1.json", SCOPES)
youtube = build("youtube", "v3", credentials=creds)

CHANNEL_HANDLE = "laurinponceadvises"

# Step 1: Find channel by handle
search = youtube.search().list(
    part="snippet",
    q=CHANNEL_HANDLE,
    type="channel",
    maxResults=1
).execute()

if not search["items"]:
    print("Channel not found!")
    exit()

channel_id = search["items"][0]["snippet"]["channelId"]
channel_title = search["items"][0]["snippet"]["title"]
print(f"Channel: {channel_title}")
print(f"Channel ID: {channel_id}")

# Step 2: Get channel stats
ch_resp = youtube.channels().list(
    part="snippet,statistics,contentDetails,brandingSettings",
    id=channel_id
).execute()

ch = ch_resp["items"][0]
stats = ch["statistics"]
print(f"\n{'='*60}")
print(f"CHANNEL STATISTICS")
print(f"{'='*60}")
print(f"  Subscribers: {stats.get('subscriberCount', 'Hidden')}")
print(f"  Total Views: {stats.get('viewCount', '0')}")
print(f"  Total Videos: {stats.get('videoCount', '0')}")
print(f"  Description: {ch['snippet'].get('description', 'N/A')[:300]}")
print(f"  Created: {ch['snippet'].get('publishedAt', 'N/A')}")
print(f"  Country: {ch['snippet'].get('country', 'N/A')}")

# Step 3: Get uploads playlist
uploads_id = ch["contentDetails"]["relatedPlaylists"]["uploads"]

# Step 4: Get all videos (up to 50)
videos_list = []
next_page = None
for _ in range(3):
    pl_resp = youtube.playlistItems().list(
        part="snippet,contentDetails",
        playlistId=uploads_id,
        maxResults=50,
        pageToken=next_page
    ).execute()
    videos_list.extend(pl_resp["items"])
    next_page = pl_resp.get("nextPageToken")
    if not next_page:
        break

print(f"\n{'='*60}")
print(f"ALL VIDEOS ({len(videos_list)} total)")
print(f"{'='*60}")

# Step 5: Get detailed stats for each video
video_ids = [v["contentDetails"]["videoId"] for v in videos_list]

all_video_details = []
for i in range(0, len(video_ids), 50):
    batch = video_ids[i:i+50]
    v_resp = youtube.videos().list(
        part="snippet,statistics,contentDetails",
        id=",".join(batch)
    ).execute()
    all_video_details.extend(v_resp["items"])

total_views = 0
total_likes = 0
total_comments = 0

for idx, v in enumerate(all_video_details, 1):
    title = v["snippet"]["title"]
    published = v["snippet"]["publishedAt"][:10]
    duration = v["contentDetails"]["duration"]
    views = int(v["statistics"].get("viewCount", 0))
    likes = int(v["statistics"].get("likeCount", 0))
    comments = int(v["statistics"].get("commentCount", 0))
    total_views += views
    total_likes += likes
    total_comments += comments
    
    tags = v["snippet"].get("tags", [])
    tag_str = ", ".join(tags[:5]) if tags else "No tags"
    
    print(f"\n  [{idx}] {title}")
    print(f"      Date: {published} | Duration: {duration}")
    print(f"      Views: {views:,} | Likes: {likes:,} | Comments: {comments:,}")
    print(f"      Tags: {tag_str}")

print(f"\n{'='*60}")
print(f"SUMMARY ANALYTICS")
print(f"{'='*60}")
print(f"  Total Videos: {len(all_video_details)}")
print(f"  Total Views: {total_views:,}")
print(f"  Total Likes: {total_likes:,}")
print(f"  Total Comments: {total_comments:,}")
if all_video_details:
    print(f"  Avg Views/Video: {total_views // len(all_video_details):,}")
    print(f"  Avg Likes/Video: {total_likes // len(all_video_details):,}")
    print(f"  Avg Comments/Video: {total_comments // len(all_video_details):,}")

# Top 5 by views
sorted_by_views = sorted(all_video_details, key=lambda x: int(x["statistics"].get("viewCount", 0)), reverse=True)
print(f"\n{'='*60}")
print(f"TOP 5 MOST VIEWED VIDEOS")
print(f"{'='*60}")
for i, v in enumerate(sorted_by_views[:5], 1):
    print(f"  {i}. {v['snippet']['title']}")
    print(f"     Views: {int(v['statistics'].get('viewCount',0)):,} | Likes: {int(v['statistics'].get('likeCount',0)):,}")

# Upload frequency
if len(all_video_details) >= 2:
    from datetime import datetime
    dates = sorted([datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00")) for v in all_video_details])
    total_days = (dates[-1] - dates[0]).days
    if total_days > 0:
        freq = total_days / len(all_video_details)
        print(f"\n{'='*60}")
        print(f"UPLOAD FREQUENCY")
        print(f"{'='*60}")
        print(f"  First Video: {dates[0].strftime('%Y-%m-%d')}")
        print(f"  Latest Video: {dates[-1].strftime('%Y-%m-%d')}")
        print(f"  Active Days: {total_days}")
        print(f"  Avg Upload: Every {freq:.1f} days")
        print(f"  Videos/Month: {len(all_video_details) / (total_days/30):.1f}")
