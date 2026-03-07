"""
YouTube Auto-Post Bot v2
- Google Drive mein saari videos pehle se hain
- Din mein 3 videos upload hoti hain: 9AM, 3PM, 9PM IST
- OpenRouter free API use karta hai
"""

import time
import schedule
import logging
from datetime import datetime
from queue_manager import VideoQueue
from drive_watcher import DriveWatcher
from metadata_generator import MetadataGenerator
from thumbnail_maker import ThumbnailMaker
from youtube_uploader import YouTubeUploader

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger(__name__)


def load_all_drive_videos():
    """Drive ki SAARI videos queue mein daalo. Already processed skip hongi."""
    log.info("📁 Drive se saari videos load ho rahi hain...")
    watcher = DriveWatcher()
    all_videos = watcher.get_all_videos()

    if not all_videos:
        log.warning("⚠️ Drive mein koi MP4 video nahi mili!")
        return 0

    queue = VideoQueue()
    added = 0
    for video in all_videos:
        if queue.add(video):
            added += 1

    status = queue.get_status()
    log.info(f"✅ {added} nayi videos queue mein add hui")
    log.info(f"📊 Queue → Pending: {status['pending']} | Done: {status['done']}")
    return added


def upload_one_video():
    """Queue se ek video uthao aur YouTube pe upload karo."""
    now = datetime.now().strftime('%H:%M')
    log.info(f"⏰ Upload triggered at {now}")

    queue = VideoQueue()

    if queue.get_status()['pending'] == 0:
        log.info("📭 Queue empty — Drive se reload kar raha hoon...")
        load_all_drive_videos()
        if queue.get_status()['pending'] == 0:
            log.info("✅ Saari videos upload ho chuki hain!")
            return

    video = queue.get_next()
    if not video:
        return

    log.info(f"🎬 Processing: {video['name']}")

    try:
        # Step 1: OpenRouter se metadata
        log.info("🧠 OpenRouter se title/description/hashtags generate ho rahe hain...")
        meta_gen = MetadataGenerator()
        metadata = meta_gen.generate(video['name'])
        log.info(f"✅ Title: {metadata['title']}")

        # Step 2: Cloudinary thumbnail
        log.info("🖼️ Cloudinary thumbnail ban raha hai...")
        thumb_maker = ThumbnailMaker()
        thumbnail_url = thumb_maker.create(
            video_id=video['id'],
            text=metadata['thumbnail_text']
        )
        log.info(f"✅ Thumbnail ready")

        # Step 3: Video download
        log.info("📥 Drive se video download ho rahi hai...")
        watcher = DriveWatcher()
        video_path = watcher.download_video(video['id'], video['name'])

        # Step 4: YouTube upload
        log.info("🚀 YouTube pe upload chal raha hai...")
        uploader = YouTubeUploader()
        result = uploader.upload(
            video_path=video_path,
            title=metadata['title'],
            description=metadata['description'] + '\n\n' + metadata['hashtags'],
            thumbnail_url=thumbnail_url
        )

        log.info(f"🎉 DONE! → https://youtube.com/watch?v={result['id']}")
        queue.mark_done(video['id'])

        # Temp file clean
        import os
        if os.path.exists(video_path):
            os.remove(video_path)

        s = queue.get_status()
        log.info(f"📊 Queue → Pending: {s['pending']} | Done: {s['done']}")

    except Exception as e:
        log.error(f"❌ Error: {video['name']} → {str(e)}")
        queue.mark_failed(video['id'])


if __name__ == "__main__":
    log.info("=" * 55)
    log.info("🤖 YouTube Auto-Post Bot v2 — START")
    log.info("📅 Schedule: 9:00 | 15:00 | 21:00 (IST)")
    log.info("🔗 API: OpenRouter (Free)")
    log.info("=" * 55)

    # Saari Drive videos queue mein load karo
    load_all_drive_videos()

    # Din mein 3 fixed times
    schedule.every().day.at("09:00").do(upload_one_video)
    schedule.every().day.at("15:00").do(upload_one_video)
    schedule.every().day.at("21:00").do(upload_one_video)

    # Subah Drive refresh
    schedule.every().day.at("08:45").do(load_all_drive_videos)

    log.info("⏰ Next slots: 09:00 | 15:00 | 21:00")

    while True:
        schedule.run_pending()
        time.sleep(30)
