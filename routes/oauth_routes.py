from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from database import supabase
import os, logging

router = APIRouter()
log = logging.getLogger(__name__)

BACKEND_URL = os.environ.get("BACKEND_URL", "https://yt-autopost.onrender.com")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://auto-tube-pro.lovable.app")
CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")

YT_SCOPES = ["https://www.googleapis.com/auth/youtube.upload","https://www.googleapis.com/auth/youtube.readonly","openid","email","profile"]
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.readonly","openid","email","profile"]

def make_flow(scopes, redirect_uri):
    return Flow.from_client_config(
        {"web":{"client_id":CLIENT_ID,"client_secret":CLIENT_SECRET,"auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","redirect_uris":[redirect_uri]}},
        scopes=scopes, redirect_uri=redirect_uri
    )

@router.get("/youtube/start")
async def yt_start(user_id: str, channel_name: str = "My Channel"):
    flow = make_flow(YT_SCOPES, f"{BACKEND_URL}/oauth/youtube/callback")
    url, _ = flow.authorization_url(access_type="offline", prompt="consent", state=f"{user_id}|{channel_name}")
    return {"auth_url": url}

@router.get("/youtube/callback")
async def yt_callback(code: str, state: str):
    try:
        user_id, channel_name = state.split("|", 1)
        flow = make_flow(YT_SCOPES, f"{BACKEND_URL}/oauth/youtube/callback")
        flow.fetch_token(code=code)
        creds = flow.credentials
        svc = build("youtube", "v3", credentials=creds)
        ch = svc.channels().list(part="snippet", mine=True).execute()
        item = ch["items"][0] if ch.get("items") else {}
        supabase.table("channels").update({
            "channel_yt_id": item.get("id",""),
            "channel_name": item.get("snippet",{}).get("title", channel_name),
            "channel_avatar": item.get("snippet",{}).get("thumbnails",{}).get("default",{}).get("url",""),
            "yt_access_token": creds.token,
            "yt_refresh_token": creds.refresh_token,
        }).eq("user_id", user_id).is_("yt_access_token", "null").execute()
        return RedirectResponse(f"{FRONTEND_URL}/channels?yt_connected=true")
    except Exception as e:
        return RedirectResponse(f"{FRONTEND_URL}/channels?yt_error={str(e)}")

@router.get("/drive/start")
async def drive_start(user_id: str, channel_id: str):
    flow = make_flow(DRIVE_SCOPES, f"{BACKEND_URL}/oauth/drive/callback")
    url, _ = flow.authorization_url(access_type="offline", prompt="consent", state=f"{user_id}|{channel_id}")
    return {"auth_url": url}

@router.get("/drive/callback")
async def drive_callback(code: str, state: str):
    try:
        user_id, channel_id = state.split("|", 1)
        flow = make_flow(DRIVE_SCOPES, f"{BACKEND_URL}/oauth/drive/callback")
        flow.fetch_token(code=code)
        creds = flow.credentials
        supabase.table("channels").update({
            "drive_token_data": {"token": creds.token,"refresh_token": creds.refresh_token,"token_uri": creds.token_uri,"client_id": creds.client_id,"client_secret": creds.client_secret}
        }).eq("id", channel_id).eq("user_id", user_id).execute()
        channel = supabase.table("channels").select("*").eq("id", channel_id).single().execute().data
        from scheduler import load_all_videos_for_channel
        added = load_all_videos_for_channel(channel)
        return RedirectResponse(f"{FRONTEND_URL}/channels?drive_connected=true&videos={added}")
    except Exception as e:
        return RedirectResponse(f"{FRONTEND_URL}/channels?drive_error={str(e)}")
