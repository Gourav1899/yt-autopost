"""
Video Processor
Ek video ko end-to-end process karta hai:
Drive → GPT Metadata → Cloudinary Thumbnail → YouTube Upload
"""

import os
import logging
from database import supabase
from metadata_generator import MetadataGenerator
from thumbnail_maker import ThumbnailMaker
from drive_watcher import DriveWatcher
from youtube_uploader import YouTubeUploader

log = logging.getLogger(__name__)


def process_one_video(channel: dict):
    """
    Channel ke queue se ek pending video uthao aur upload karo
    """
    channel_id = channel["id"]
    channel_name = channel["channel_name"]

    # Pending video lo queue se
    result = supabase.table("queue").select("*").eq(
        "channel_id", channel_id
    ).eq("status", "pending").order("created_at").limit(1).execute()

    if not result.data:
        log.info(f"📭 {channel_name} — queue empty")
        return

    video = result.data[0]
    queue_id = video["id"]

    log.info(f"🎬 Processing: {video['video_name']} | Channel: {channel_name}")

    # Status → processing
    supabase.table("queue").update({
        "status": "processing",
        "started_at": "now()",
        "attempts": video.get("attempts", 0) + 1
    }).eq("id", queue_id).execute()

    try:
        # User ki profile lo (API keys ke liye)
        profile = supabase.table("profiles").select("*").eq(
            "id", channel["user_id"]
        ).single().execute().data

        # Step 1: Metadata generate karo
        log.info(f"🧠 Generating metadata...")
        meta_gen = MetadataGenerator(
            api_key=profile.get("openrouter_api_key"),
            ai_style=channel.get("ai_style", "energetic"),
            custom_prompt=channel.get("ai_custom_prompt")
        )
        metadata = meta_gen.generate(video["video_name"])
        log.info(f"✅ Title: {metadata['title']}")

        # Step 2: Thumbnail banao
        log.info(f"🖼️ Creating thumbnail...")
        thumb_maker = ThumbnailMaker(
            cloud_name=profile.get("cloudinary_cloud_name"),
            api_key=profile.get("cloudinary_api_key"),
            api_secret=profile.get("cloudinary_api_secret")
        )
        thumbnail_url = thumb_maker.create(
            video_id=video["video_file_id"],
            text=metadata["thumbnail_text"]
        )

        # Step 3: Video download karo
        log.info(f"📥 Downloading video...")
        watcher = DriveWatcher(
            folder_id=channel["drive_folder_id"],
            token_data=channel.get("drive_token_data")
        )
        video_path = watcher.download_video(
            video["video_file_id"],
            video["video_name"]
        )

        # Step 4: YouTube upload karo
        log.info(f"🚀 Uploading to YouTube...")
        uploader = YouTubeUploader(
            access_token=channel.get("yt_access_token"),
            refresh_token=channel.get("yt_refresh_token"),
            channel_id=channel_id
        )
        result_yt = uploader.upload(
            video_path=video_path,
            title=metadata["title"],
            description=metadata["description"] + "\n\n" + metadata["hashtags"],
            thumbnail_url=thumbnail_url
        )

        yt_video_id = result_yt["id"]
        log.info(f"🎉 Uploaded! https://youtube.com/watch?v={yt_video_id}")

        # Queue → done
        supabase.table("queue").update({
            "status": "done",
            "uploaded_at": "now()",
            "youtube_video_id": yt_video_id,
            "youtube_title": metadata["title"],
            "youtube_thumbnail": f"https://img.youtube.com/vi/{yt_video_id}/maxresdefault.jpg"
        }).eq("id", queue_id).execute()

        # Analytics mein add karo
        supabase.table("analytics").insert({
            "channel_id": channel_id,
            "user_id": channel["user_id"],
            "queue_id": queue_id,
            "youtube_video_id": yt_video_id,
            "title": metadata["title"],
            "uploaded_at": "now()"
        }).execute()

        # Channel total_uploaded increment
        supabase.table("channels").update({
            "total_uploaded": (channel.get("total_uploaded", 0) + 1)
        }).eq("id", channel_id).execute()

        # Temp file delete
        if os.path.exists(video_path):
            os.remove(video_path)

    except Exception as e:
        log.error(f"❌ Error: {video['video_name']} → {str(e)}")

        # 3 se zyada attempts → failed
        attempts = video.get("attempts", 0) + 1
        new_status = "failed" if attempts >= 3 else "pending"

        supabase.table("queue").update({
            "status": new_status,
            "error_message": str(e),
            "attempts": attempts
        }).eq("id", queue_id).execute()
