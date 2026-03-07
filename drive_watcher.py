"""
Google Drive Watcher v2
- get_all_videos(): Saari videos return karo (nahi sirf nayi)
- download_video(): Video download karo
"""

import os
import json
import logging
import io
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

log = logging.getLogger(__name__)
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
PROCESSED_FILE = 'processed_videos.json'


class DriveWatcher:
    def __init__(self):
        self.folder_id = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')
        self.service = self._get_service()
        self.processed = self._load_processed()

    def _get_service(self):
        creds = None
        if os.path.exists('credentials/drive_token.json'):
            creds = Credentials.from_authorized_user_file('credentials/drive_token.json', SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            self._save_token(creds)
        if not creds or not creds.valid:
            if not os.path.exists('credentials/drive_credentials.json'):
                raise FileNotFoundError("credentials/drive_credentials.json nahi mila!")
            flow = InstalledAppFlow.from_client_secrets_file('credentials/drive_credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            self._save_token(creds)
        return build('drive', 'v3', credentials=creds)

    def _save_token(self, creds):
        os.makedirs('credentials', exist_ok=True)
        with open('credentials/drive_token.json', 'w') as f:
            f.write(creds.to_json())

    def _load_processed(self):
        if os.path.exists(PROCESSED_FILE):
            with open(PROCESSED_FILE, 'r') as f:
                return set(json.load(f))
        return set()

    def get_all_videos(self):
        """
        Drive folder ki SAARI MP4 videos return karo.
        Already done wali queue se automatically skip hongi.
        """
        if not self.folder_id:
            raise ValueError("GOOGLE_DRIVE_FOLDER_ID set nahi hai!")

        all_videos = []
        page_token = None

        while True:
            query = f"'{self.folder_id}' in parents and mimeType='video/mp4' and trashed=false"
            params = {
                "q": query,
                "fields": "nextPageToken, files(id, name, size, createdTime)",
                "orderBy": "createdTime asc",   # Purani pehle upload hogi
                "pageSize": 100
            }
            if page_token:
                params["pageToken"] = page_token

            result = self.service.files().list(**params).execute()
            all_videos.extend(result.get('files', []))
            page_token = result.get('nextPageToken')
            if not page_token:
                break

        log.info(f"📁 Drive mein total {len(all_videos)} MP4 videos hain")
        return all_videos

    def download_video(self, file_id: str, file_name: str) -> str:
        os.makedirs('/tmp/yt_videos', exist_ok=True)
        # Safe filename
        safe_name = "".join(c for c in file_name if c.isalnum() or c in (' ', '.', '_', '-')).strip()
        local_path = f'/tmp/yt_videos/{file_id[:8]}_{safe_name}'

        if os.path.exists(local_path):
            log.info(f"📁 Already downloaded: {file_name}")
            return local_path

        log.info(f"📥 Downloading: {file_name}")
        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request, chunksize=20*1024*1024)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                log.info(f"  ⬇️  {int(status.progress() * 100)}%...")

        with open(local_path, 'wb') as f:
            fh.seek(0)
            f.write(fh.read())

        log.info(f"✅ Download complete: {local_path}")
        return local_path
