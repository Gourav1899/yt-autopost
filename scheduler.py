"""
Multi-Channel Scheduler
- Supabase se saare active channels fetch karo
- Har channel ka schedule check karo
- Queue se videos process karo
"""

import schedule
import time
import logging
from datetime import datetime, timezone
from database import supabase
from processor import process_one_video

log = logging.getLogger(__name__)


def check_and_upload():
    """
    Abhi ke time ke liye kaunse channels ka upload slot hai?
    Unke queue se ek ek video process karo.
    """
    now = datetime.now()
    current_time = now.strftime("%H:%M")

    log.info(f"⏰ Schedule check at {current_time}")

    try:
        # Supabase se saare active channels lo
        result = supabase.table("channels").select("*").eq("is_active", True).execute()
        channels = result.data

        if not channels:
            log.info("📭 Koi active channel nahi")
            return

        log.info(f"📡 {len(channels)} active channels found")

        for channel in channels:
            schedule_times = channel.get("schedule_times", ["09:00", "15:00", "21:00"])

            # Is channel ka upload time hai abhi?
            if current_time in schedule_times:
                log.info(f"🎬 Channel: {channel['channel_name']} — upload time!")
                process_one_video(channel)
            else:
                log.debug(f"⏭️ {channel['channel_name']} — not scheduled now")

    except Exception as e:
        log.error(f"Scheduler error: {e}")


def load_all_videos_for_channel(channel: dict):
    """
    Channel ke Drive folder se saari videos queue mein daalo
    """
    from drive_watcher import DriveWatcher
    import json, base64

    log.info(f"📁 Loading videos for: {channel['channel_name']}")

    try:
        # Channel ka Drive token decode karo
        drive_token_data = channel.get("drive_token_data")
        if not drive_token_data:
            log.error(f"❌ {channel['channel_name']} — Drive token missing!")
            return 0

        watcher = DriveWatcher(
            folder_id=channel["drive_folder_id"],
            token_data=drive_token_data
        )
        all_videos = watcher.get_all_videos()

        added = 0
        for video in all_videos:
            # Already queue mein hai?
            existing = supabase.table("queue").select("id").eq(
                "video_file_id", video["id"]
            ).eq("channel_id", channel["id"]).execute()

            if not existing.data:
                supabase.table("queue").insert({
                    "channel_id": channel["id"],
                    "user_id": channel["user_id"],
                    "video_file_id": video["id"],
                    "video_name": video["name"],
                    "status": "pending"
                }).execute()
                added += 1

        log.info(f"✅ {added} new videos added for {channel['channel_name']}")
        return added

    except Exception as e:
        log.error(f"Load videos error for {channel['channel_name']}: {e}")
        return 0


def daily_drive_refresh():
    """Roz subah saare channels ke liye Drive refresh"""
    log.info("🔄 Daily Drive refresh starting...")
    try:
        result = supabase.table("channels").select("*").eq("is_active", True).execute()
        for channel in result.data:
            load_all_videos_for_channel(channel)
    except Exception as e:
        log.error(f"Daily refresh error: {e}")


def run_scheduler():
    """Main scheduler loop"""
    log.info("=" * 50)
    log.info("🤖 Multi-Channel Scheduler Starting")
    log.info("=" * 50)

    # Startup pe saare channels ke videos load karo
    daily_drive_refresh()

    # Har minute check karo (schedule times match ke liye)
    schedule.every(1).minutes.do(check_and_upload)

    # Roz subah 8:45 pe Drive refresh
    schedule.every().day.at("08:45").do(daily_drive_refresh)

    log.info("✅ Scheduler running — checking every minute")

    while True:
        schedule.run_pending()
        time.sleep(30)
