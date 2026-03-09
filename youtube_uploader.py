"""
YouTube Uploader v3 — Per Channel Token
Har channel ka alag YouTube token
"""

import os, io, logging, requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from database import supabase

log = logging.getLogger(__name__)
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube"
]


class YouTubeUploader:
    def __init__(self, access_token: str, refresh_token: str, channel_id: str):
        self.channel_id = channel_id
        self.service = self._get_service(access_token, refresh_token)

    def _get_service(self, access_token, refresh_token):
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.environ.get("GOOGLE_CLIENT_ID"),
            client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
            scopes=SCOPES
        )

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Updated token Supabase mein save karo
            supabase.table("channels").update({
                "yt_access_token": creds.token,
            }).eq("id", self.channel_id).execute()

        return build("youtube", "v3", credentials=creds)

    def upload(self, video_path, title, description, thumbnail_url=None, privacy="public"):
        log.info(f"🚀 Uploading: {title}")

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "categoryId": "24",
                "defaultLanguage": "hi",
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False,
                "notifySubscribers": True
            }
        }

        media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True, chunksize=50*1024*1024)
        request = self.service.videos().insert(part="snippet,status", body=body, media_body=media)

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                log.info(f"  📤 {int(status.progress()*100)}%")

        if thumbnail_url:
            self._set_thumbnail(response["id"], thumbnail_url)

        return response

    def _set_thumbnail(self, video_id, thumbnail_url):
        try:
            resp = requests.get(thumbnail_url, timeout=30)
            self.service.thumbnails().set(
                videoId=video_id,
                media_body=MediaIoBaseUpload(io.BytesIO(resp.content), mimetype="image/jpeg")
            ).execute()
            log.info("✅ Thumbnail set!")
        except Exception as e:
            log.error(f"Thumbnail error: {e}")
