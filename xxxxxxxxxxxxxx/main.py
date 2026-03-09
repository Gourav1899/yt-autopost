"""
YouTube Auto-Post Bot v2 - Web Service Version
Render free tier ke liye dummy HTTP server saath mein chalta hai
"""

import time
import schedule
import logging
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from queue_manager import VideoQueue
from drive_watcher import DriveWatcher
from metadata_generator import MetadataGenerator
from thumbnail_maker import ThumbnailMaker
from youtube_uploader import YouTubeUploader
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Dummy HTTP Server — Render ke liye zaroori
# ─────────────────────────────────────────────
class StatusHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        queue = VideoQueue()
        status = queue.get_status()
        body = f"""
        <html><body style="font-family:monospace;background:#111;color:#0f0;padding:40px">
        <h2>🤖 YouTube Auto-Post Bot</h2>
        <p>Status: <b>RUNNING ✅</b></p>
        <p>📊 Queue Status:</p>
        <ul>
            <li>Pending: {status['pending']}</li>
            <li>Done: {status['done']}</li>
            <li>Failed: {status['failed']}</li>
        </ul>
        <p>⏰ Schedule: 09:00 | 15:00 | 21:00 IST</p>
        <p>Last check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </body></html>
        """.encode()
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass  # HTTP logs suppress karo


def run_web_server():
    """Dummy web server alag thread mein chalao"""
    server = HTTPServer(('0.0.0.0', 10000), StatusHandler)
    log.info("🌐 Web server chal raha hai port 10000 pe")
    server.serve_forever()


# ─────────────────────────────────────────────
# Bot Logic
# ─────────────────────────────────────────────
def load_all_drive_videos():
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
    now = datetime.now().strftime('%H:%M')
    log.info(f"⏰ Upload triggered at {now}")

    queue = VideoQueue()
    if queue.get_status()['pending'] == 0:
        log.info("📭 Queue empty — Drive se reload...")
        load_all_drive_videos()
        if queue.get_status()['pending'] == 0:
            log.info("✅ Saari videos upload ho chuki hain!")
            return

    video = queue.get_next()
    if not video:
        return

    log.info(f"🎬 Processing: {video['name']}")

    try:
        log.info("🧠 OpenRouter se metadata...")
        meta_gen = MetadataGenerator()
        metadata = meta_gen.generate(video['name'])
        log.info(f"✅ Title: {metadata['title']}")

        log.info("🖼️ Cloudinary thumbnail...")
        thumb_maker = ThumbnailMaker()
        thumbnail_url = thumb_maker.create(
            video_id=video['id'],
            text=metadata['thumbnail_text']
        )

        log.info("📥 Video download...")
        watcher = DriveWatcher()
        video_path = watcher.download_video(video['id'], video['name'])

        log.info("🚀 YouTube upload...")
        uploader = YouTubeUploader()
        result = uploader.upload(
            video_path=video_path,
            title=metadata['title'],
            description=metadata['description'] + '\n\n' + metadata['hashtags'],
            thumbnail_url=thumbnail_url
        )

        log.info(f"🎉 DONE! → https://youtube.com/watch?v={result['id']}")
        queue.mark_done(video['id'])

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
    log.info("🤖 YouTube Auto-Post Bot — Web Service Mode")
    log.info("📅 Schedule: 09:00 | 15:00 | 21:00 IST")
    log.info("=" * 55)

    # Web server alag thread mein start karo
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()

    # Drive videos load karo
    load_all_drive_videos()

    # Schedule
    schedule.every().day.at("09:00").do(upload_one_video)
    schedule.every().day.at("15:00").do(upload_one_video)
    schedule.every().day.at("21:00").do(upload_one_video)
    schedule.every().day.at("08:45").do(load_all_drive_videos)

    log.info("⏰ Scheduler ready! Next: 09:00 | 15:00 | 21:00")

    while True:
        schedule.run_pending()
        time.sleep(30)