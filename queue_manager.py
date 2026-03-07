"""
Video Queue Manager
- Videos ko queue mein store karo (JSON file)
- Ek ek karke process karo
- Failed videos track karo
- Already processed skip karo
"""

import json
import logging
import os
from datetime import datetime

log = logging.getLogger(__name__)

QUEUE_FILE = 'video_queue.json'


class VideoQueue:
    def __init__(self):
        self.queue_data = self._load()

    def _load(self) -> dict:
        """Queue file load karo"""
        if os.path.exists(QUEUE_FILE):
            with open(QUEUE_FILE, 'r') as f:
                return json.load(f)
        # Fresh queue structure
        return {
            "pending": [],      # Process hone wali videos
            "processing": [],   # Abhi chal rahi hai
            "done": [],         # Complete ho gayi
            "failed": []        # Error aayi
        }

    def _save(self):
        """Queue file save karo"""
        with open(QUEUE_FILE, 'w') as f:
            json.dump(self.queue_data, f, indent=2)

    def add(self, video: dict) -> bool:
        """
        Nayi video queue mein daalo
        Already queue mein hai toh skip karo
        """
        video_id = video['id']

        # Check karo kahin pehle se toh nahi hai
        all_ids = (
            [v['id'] for v in self.queue_data['pending']] +
            [v['id'] for v in self.queue_data['done']] +
            [v['id'] for v in self.queue_data['failed']]
        )

        if video_id in all_ids:
            log.debug(f"⏭️ Already queue mein hai: {video.get('name', video_id)}")
            return False

        # Queue mein add karo
        video['queued_at'] = datetime.now().isoformat()
        video['attempts'] = 0
        self.queue_data['pending'].append(video)
        self._save()

        log.info(f"➕ Queue mein add: {video.get('name', video_id)} | "
                 f"Total pending: {len(self.queue_data['pending'])}")
        return True

    def get_next(self) -> dict | None:
        """
        Queue se agle video lao process karne ke liye
        Returns None agar queue khali hai
        """
        if not self.queue_data['pending']:
            log.info("📭 Queue empty hai")
            return None

        # Pehli video uthao (FIFO - First In First Out)
        video = self.queue_data['pending'].pop(0)
        video['started_at'] = datetime.now().isoformat()
        video['attempts'] = video.get('attempts', 0) + 1

        # Processing mein move karo
        self.queue_data['processing'] = [video]
        self._save()

        log.info(f"🎬 Processing shuru: {video.get('name')} "
                 f"| Attempt #{video['attempts']}")
        return video

    def mark_done(self, video_id: str):
        """Video successfully upload ho gayi"""
        self._move_to(video_id, 'processing', 'done')
        log.info(f"✅ Done: {video_id}")

    def mark_failed(self, video_id: str):
        """Video upload fail ho gayi"""
        # 3 baar try karo, phir failed mein daalo
        video = self._find_in(video_id, 'processing')
        if video:
            if video.get('attempts', 0) < 3:
                # Retry ke liye pending mein wapas daalo
                self.queue_data['processing'] = []
                video['retry_after'] = datetime.now().isoformat()
                self.queue_data['pending'].append(video)
                log.warning(f"🔄 Retry #{video['attempts']}: {video.get('name')}")
            else:
                # 3 attempts ho gaye — failed mein daalo
                self._move_to(video_id, 'processing', 'failed')
                log.error(f"❌ 3 attempts fail — giving up: {video.get('name')}")
            self._save()

    def is_empty(self) -> bool:
        return len(self.queue_data['pending']) == 0

    def get_status(self) -> dict:
        """Queue ki current status"""
        return {
            "pending": len(self.queue_data['pending']),
            "processing": len(self.queue_data['processing']),
            "done": len(self.queue_data['done']),
            "failed": len(self.queue_data['failed'])
        }

    def _find_in(self, video_id: str, status: str) -> dict | None:
        """Specific status mein video dhundho"""
        for v in self.queue_data[status]:
            if v['id'] == video_id:
                return v
        return None

    def _move_to(self, video_id: str, from_status: str, to_status: str):
        """Video ek status se doosre mein move karo"""
        video = self._find_in(video_id, from_status)
        if video:
            video['completed_at'] = datetime.now().isoformat()
            self.queue_data[from_status] = [
                v for v in self.queue_data[from_status]
                if v['id'] != video_id
            ]
            self.queue_data[to_status].append(video)
            self._save()
