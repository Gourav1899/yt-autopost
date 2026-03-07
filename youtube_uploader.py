"""
YouTube Uploader
- Video upload karo YouTube pe
- Custom thumbnail set karo
- Title, description, hashtags add karo
"""

import os
import logging
import requests
import tempfile
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
import io

log = logging.getLogger(__name__)

# YouTube upload + manage access chahiye
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube'
]

# YouTube category IDs (common ones)
CATEGORIES = {
    'entertainment': '24',
    'gaming': '20',
    'music': '10',
    'sports': '17',
    'film': '1',
    'people': '22',    # Default
    'howto': '26',
    'news': '25',
}


class YouTubeUploader:
    def __init__(self):
        self.service = self._get_service()
        # .env se category lo, default "people"
        category = os.environ.get('YT_CATEGORY', 'people').lower()
        self.category_id = CATEGORIES.get(category, '22')

    def _get_service(self):
        """YouTube API se connect karo"""
        creds = None

        if os.path.exists('credentials/youtube_token.json'):
            creds = Credentials.from_authorized_user_file(
                'credentials/youtube_token.json', SCOPES
            )

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            self._save_token(creds)

        if not creds or not creds.valid:
            if not os.path.exists('credentials/youtube_credentials.json'):
                raise FileNotFoundError(
                    "❌ credentials/youtube_credentials.json nahi mila!\n"
                    "Google Cloud Console se download karo"
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials/youtube_credentials.json', SCOPES
            )
            creds = flow.run_local_server(port=0)
            self._save_token(creds)

        return build('youtube', 'v3', credentials=creds)

    def _save_token(self, creds):
        os.makedirs('credentials', exist_ok=True)
        with open('credentials/youtube_token.json', 'w') as f:
            f.write(creds.to_json())

    def upload(self, video_path: str, title: str, description: str,
               thumbnail_url: str = None, privacy: str = 'public') -> dict:
        """
        YouTube pe video upload karo
        
        Args:
            video_path: Local video file ka path
            title: Video title
            description: Full description + hashtags
            thumbnail_url: Cloudinary thumbnail URL
            privacy: 'public', 'private', ya 'unlisted'
        
        Returns: YouTube video info dict
        """
        log.info(f"🚀 YouTube upload shuru: {title}")

        # Video metadata
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'categoryId': self.category_id,
                'defaultLanguage': 'hi',          # Hindi default
                'defaultAudioLanguage': 'hi'
            },
            'status': {
                'privacyStatus': privacy,
                'selfDeclaredMadeForKids': False,
                'notifySubscribers': True
            }
        }

        # Video file upload
        media = MediaFileUpload(
            video_path,
            mimetype='video/mp4',
            resumable=True,            # Large files ke liye resumable upload
            chunksize=50 * 1024 * 1024  # 50MB chunks
        )

        # Upload request
        request = self.service.videos().insert(
            part='snippet,status',
            body=body,
            media_body=media
        )

        # Upload execute karo with progress
        response = None
        log.info("⬆️ Upload chal raha hai...")

        while response is None:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                log.info(f"  📤 {progress}% uploaded...")

        video_id = response['id']
        log.info(f"✅ Video uploaded! ID: {video_id}")

        # Thumbnail set karo
        if thumbnail_url:
            self._set_thumbnail(video_id, thumbnail_url)

        return response

    def _set_thumbnail(self, video_id: str, thumbnail_url: str):
        """Cloudinary se thumbnail download karke YouTube pe set karo"""
        try:
            log.info("🖼️ Thumbnail set ho raha hai...")

            # Cloudinary se thumbnail download karo
            resp = requests.get(thumbnail_url, timeout=30)
            resp.raise_for_status()

            # YouTube pe set karo
            thumbnail_media = MediaIoBaseUpload(
                io.BytesIO(resp.content),
                mimetype='image/jpeg'
            )

            self.service.thumbnails().set(
                videoId=video_id,
                media_body=thumbnail_media
            ).execute()

            log.info("✅ Thumbnail set ho gayi!")

        except Exception as e:
            log.error(f"⚠️ Thumbnail set nahi hui: {e}")
            # Upload fail nahi karega thumbnail error se
