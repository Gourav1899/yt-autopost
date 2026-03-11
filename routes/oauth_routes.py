"""
OAuth Routes — YouTube + Drive per user
"""

import os
import json
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from database import supabase

router = APIRouter()
log = logging.getLogger(__name__)

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
BACKEND_URL = os.environ.get("BACKEND_URL", "https://yt-autopost.onrender.com")

YT_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "openid", "email", "profile"
]

DRIVE_SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "openid", "email", "profile"
]


def make_flow(scopes, redirect_uri):
    return Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri]
            }
        },
        scopes=scopes,
        redirect_uri=redirect_uri
    )


@router.get("/youtube/start")
async def youtube_oauth_start(user_id: str, channel_name: str = "My Channel"):
    redirect_uri = f"{BACKEND_URL}/oauth/youtube/callback"
    flow = make_flow(YT_SCOPES, redirect_uri)
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="false",
        prompt="consent",
        state=f"{user_id}|{channel_name}"
    )
    return {"auth_url": auth_url}


@router.get("/youtube/callback")
async def youtube_oauth_callback(code: str, state: str):
    try:
        user_id, channel_name = state.split("|", 1)
        redirect_uri = f"{BACKEND_URL}/oauth/youtube/callback"
        flow = make_flow(YT_SCOPES, redirect_uri)
        flow.fetch_token(code=code)
        creds = flow.credentials

        yt_service = build("youtube", "v3", credentials=creds)
        ch_resp = yt_service.channels().list(part="snippet", mine=True).execute()
        yt_channel = ch_resp["items"][0] if ch_resp.get("items") else {}
        yt_channel_id = yt_channel.get("id", "")
        yt_channel_name = yt_channel.get("snippet", {}).get("title", channel_name)
        yt_avatar = yt_channel.get("snippet", {}).get("thumbnails", {}).get("default", {}).get("url", "")

        supabase.table("channels").update({
            "channel_yt_id": yt_channel_id,
            "channel_name": yt_channel_name,
            "channel_avatar": yt_avatar,
            "yt_access_token": creds.token,
            "yt_refresh_token": creds.refresh_token,
        }).eq("user_id", user_id).eq("yt_access_token", None).execute()

        frontend_url = os.environ.get("FRONTEND_URL", "https://auto-tube-pro.lovable.app")
        return RedirectResponse(f"{frontend_url}/channels?yt_connected=true")

    except Exception as e:
        log.error(f"YouTube OAuth error: {e}")
        frontend_url = os.environ.get("FRONTEND_URL", "https://auto-tube-pro.lovable.app")
        return RedirectResponse(f"{frontend_url}/channels?yt_error={str(e)}")


@router.get("/drive/start")
async def drive_oauth_start(user_id: str, channel_id: str):
    redirect_uri = f"{BACKEND_URL}/oauth/drive/callback"
    flow = make_flow(DRIVE_SCOPES, redirect_uri)
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        state=f"{user_id}|{channel_id}"
    )
    return {"auth_url": auth_url}


@router.get("/drive/callback")
async def drive_oauth_callback(code: str, state: str):
    try:
        user_id, channel_id = state.split("|", 1)
        redirect_uri = f"{BACKEND_URL}/oauth/drive/callback"
        flow = make_flow(DRIVE_SCOPES, redirect_uri)
        flow.fetch_token(code=code)
        creds = flow.credentials

        token_data = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
        }

        supabase.table("channels").update({
            "drive_token_data": token_data
        }).eq("id", channel_id).eq("user_id", user_id).execute()

        channel = supabase.table("channels").select("*").eq("id", channel_id).single().execute().data
        from scheduler import load_all_videos_for_channel
        added = load_all_videos_for_channel(channel)

        frontend_url = os.environ.get("FRONTEND_URL", "https://auto-tube-pro.lovable.app")
        return RedirectResponse(f"{frontend_url}/channels?drive_connected=true&videos={added}")

    except Exception as e:
        log.error(f"Drive OAuth error: {e}")
        frontend_url = os.environ.get("FRONTEND_URL", "https://auto-tube-pro.lovable.app")
        return RedirectResponse(f"{frontend_url}/channels?drive_error={str(e)}")
