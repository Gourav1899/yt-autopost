"""Cloudinary Thumbnail Maker v3 — Per user credentials"""
import re, logging
import cloudinary, cloudinary.uploader

log = logging.getLogger(__name__)


class ThumbnailMaker:
    def __init__(self, cloud_name: str, api_key: str, api_secret: str):
        cloudinary.config(cloud_name=cloud_name, api_key=api_key, api_secret=api_secret)
        self.cloud_name = cloud_name

    def create(self, video_id: str, text: str) -> str:
        safe_text = self._clean(text)
        public_id = f"yt_thumbs/thumb_{video_id}"

        try:
            drive_thumb = f"https://drive.google.com/thumbnail?id={video_id}&sz=w1280-h720"
            cloudinary.uploader.upload(drive_thumb, public_id=public_id, width=1280, height=720, crop="fill", overwrite=True)
            encoded = safe_text.replace(" ", "%20").replace("/", "%2F")
            url = (
                f"https://res.cloudinary.com/{self.cloud_name}/image/upload/"
                f"l_text:Arial_90_bold:{encoded},co_white,g_south,y_80,"
                f"bo_20px_solid_rgb:000000,b_rgb:000000,o_80,w_1200,c_fit/"
                f"fl_layer_apply/{public_id}.jpg"
            )
            log.info(f"✅ Thumbnail ready")
            return url
        except Exception as e:
            log.error(f"Cloudinary error: {e}")
            return f"https://via.placeholder.com/1280x720/000000/FFFFFF?text={safe_text.replace(' ', '+')}"

    def _clean(self, text: str) -> str:
        clean = re.sub(r"[^\w\s!?.]", "", text).upper().strip()
        return (clean[:27] + "...") if len(clean) > 30 else clean or "WATCH NOW"
