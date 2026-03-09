"""
Drive Watcher v3 — Per Channel Token Support
Har channel ka alag Drive token hoga
"""

import os, io, json, base64, logging
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

log = logging.getLogger(__name__)
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


class DriveWatcher:
    def __init__(self, folder_id: str, token_data: dict):
        self.folder_id = folder_id
        self.service = self._get_service(token_data)

    def _get_service(self, token_data):
        if isinstance(token_data, str):
            token_data = json.loads(token_data)

        creds = Credentials(
            token=token_data.get("token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.environ.get("GOOGLE_CLIENT_ID"),
            client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
            scopes=SCOPES
        )

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())

        return build("drive", "v3", credentials=creds)

    def get_all_videos(self):
        all_videos = []
        page_token = None
        while True:
            params = {
                "q": f"'{self.folder_id}' in parents and mimeType='video/mp4' and trashed=false",
                "fields": "nextPageToken, files(id, name, size, createdTime)",
                "orderBy": "createdTime asc",
                "pageSize": 100
            }
            if page_token:
                params["pageToken"] = page_token
            result = self.service.files().list(**params).execute()
            all_videos.extend(result.get("files", []))
            page_token = result.get("nextPageToken")
            if not page_token:
                break
        log.info(f"📁 {len(all_videos)} videos found in Drive")
        return all_videos

    def download_video(self, file_id: str, file_name: str) -> str:
        os.makedirs("/tmp/yt_videos", exist_ok=True)
        safe_name = "".join(c for c in file_name if c.isalnum() or c in " ._-").strip()
        path = f"/tmp/yt_videos/{file_id[:8]}_{safe_name}"

        if os.path.exists(path):
            return path

        log.info(f"📥 Downloading: {file_name}")
        req = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        dl = MediaIoBaseDownload(fh, req, chunksize=20*1024*1024)
        done = False
        while not done:
            status, done = dl.next_chunk()
            if status:
                log.info(f"  ⬇️ {int(status.progress()*100)}%")

        with open(path, "wb") as f:
            fh.seek(0)
            f.write(fh.read())
        return path
