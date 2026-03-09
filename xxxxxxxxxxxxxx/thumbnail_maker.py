"""
Cloudinary Thumbnail Maker
- Drive video ka thumbnail frame Cloudinary pe upload karo
- Text overlay add karo (bold white text, black background)
- Final 1280x720 thumbnail URL return karo
"""

import os
import logging
import requests
import cloudinary
import cloudinary.uploader
import cloudinary.api

log = logging.getLogger(__name__)


class ThumbnailMaker:
    def __init__(self):
        # Cloudinary config
        cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME')
        api_key = os.environ.get('CLOUDINARY_API_KEY')
        api_secret = os.environ.get('CLOUDINARY_API_SECRET')

        if not all([cloud_name, api_key, api_secret]):
            raise ValueError(
                "❌ Cloudinary credentials missing!\n"
                "CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET\n"
                "sab set karo .env mein"
            )

        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )
        self.cloud_name = cloud_name

    def create(self, video_id: str, text: str, video_path: str = None) -> str:
        """
        Thumbnail banao aur URL return karo
        
        1. Video ka ek frame Cloudinary pe upload karo
        2. Text overlay transformation apply karo
        3. Final URL return karo
        """
        public_id = f"yt_thumbs/thumb_{video_id}"

        # Text clean karo — special chars hata do
        safe_text = self._clean_text(text)

        try:
            # Option A: Video file se frame extract (agar local path hai)
            if video_path and os.path.exists(video_path):
                thumb_url = self._upload_from_video(video_path, public_id, safe_text)
            else:
                # Option B: Drive thumbnail URL se
                thumb_url = self._upload_from_drive(video_id, public_id, safe_text)

            log.info(f"✅ Thumbnail URL ready: {thumb_url}")
            return thumb_url

        except Exception as e:
            log.error(f"Cloudinary error: {e}")
            # Fallback — sirf text pe thumbnail
            return self._text_only_thumbnail(safe_text, public_id)

    def _upload_from_video(self, video_path: str, public_id: str, text: str) -> str:
        """Local video file se thumbnail banao"""
        log.info("🎬 Video se frame extract karke Cloudinary pe upload ho raha hai...")

        result = cloudinary.uploader.upload(
            video_path,
            public_id=public_id,
            resource_type="video",
            eager=[
                {
                    "width": 1280,
                    "height": 720,
                    "crop": "fill",
                    "start_offset": "0",        # Pehla frame
                    "format": "jpg"
                }
            ],
            eager_async=False,
            overwrite=True
        )

        # Frame URL pe text overlay add karo
        base_url = result['eager'][0]['secure_url'] if result.get('eager') else result['secure_url']
        return self._add_text_overlay(public_id, text, is_video=True)

    def _upload_from_drive(self, video_id: str, public_id: str, text: str) -> str:
        """Google Drive thumbnail se Cloudinary pe upload karo"""
        log.info("🔗 Drive thumbnail se Cloudinary upload ho raha hai...")

        # Drive ka thumbnail URL
        drive_thumb_url = f"https://drive.google.com/thumbnail?id={video_id}&sz=w1280-h720"

        result = cloudinary.uploader.upload(
            drive_thumb_url,
            public_id=public_id,
            width=1280,
            height=720,
            crop="fill",
            overwrite=True
        )

        return self._add_text_overlay(public_id, text, is_video=False)

    def _add_text_overlay(self, public_id: str, text: str, is_video: bool = False) -> str:
        """
        Uploaded image pe text overlay URL banao
        Cloudinary transformation URL use karta hai — koi extra API call nahi
        """
        # URL-encoded text (spaces ko %20)
        encoded_text = text.replace(' ', '%20').replace('/', '%2F').replace(',', '%2C')

        # Cloudinary transformation URL build karo
        # l_text: = text layer
        # Arial_90_bold = font Arial, size 90, bold
        # co_white = color white
        # g_south = bottom center
        # y_80 = 80px from bottom
        # b_black,o_70 = black semi-transparent background
        transformation = (
            f"l_text:Arial_90_bold:{encoded_text},"
            f"co_white,"
            f"g_south,"
            f"y_80,"
            f"bo_20px_solid_rgb:000000,"
            f"b_rgb:000000,"
            f"o_80,"
            f"w_1200,"
            f"c_fit/"
            f"fl_layer_apply"
        )

        resource_type = "video" if is_video else "image"
        format_ext = "jpg"

        url = (
            f"https://res.cloudinary.com/{self.cloud_name}/"
            f"image/upload/{transformation}/{public_id}.{format_ext}"
        )

        return url

    def _text_only_thumbnail(self, text: str, public_id: str) -> str:
        """Fallback: Sirf black background pe white text"""
        encoded_text = text.replace(' ', '%20')
        url = (
            f"https://res.cloudinary.com/{self.cloud_name}/image/upload/"
            f"w_1280,h_720,c_fill,b_black/"
            f"l_text:Arial_100_bold:{encoded_text},co_white,g_center/"
            f"fl_layer_apply/sample.jpg"
        )
        return url

    def _clean_text(self, text: str) -> str:
        """Text se special characters hato jo Cloudinary support nahi karta"""
        # Sirf alphanumeric, spaces, common punctuation rakhna
        import re
        clean = re.sub(r'[^\w\s!?.]', '', text)
        clean = clean.upper().strip()
        # Max 30 chars thumbnail ke liye
        if len(clean) > 30:
            clean = clean[:27] + '...'
        return clean or 'WATCH NOW'
