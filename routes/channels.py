"""
Channels Routes — CRUD for YouTube channels
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List
from database import supabase

router = APIRouter()


def get_user_id(authorization: str) -> str:
    """Supabase JWT token se user ID nikalo"""
    try:
        token = authorization.replace("Bearer ", "")
        user = supabase.auth.get_user(token)
        return user.user.id
    except:
        raise HTTPException(status_code=401, detail="Invalid token")


def check_plan_limit(user_id: str):
    """Plan ke hisaab se channel limit check karo"""
    profile = supabase.table("profiles").select("plan").eq("id", user_id).single().execute().data
    plan = profile.get("plan", "free")

    limits = {"free": 1, "starter": 3, "pro": 10, "agency": 999}
    max_channels = limits.get(plan, 1)

    current = supabase.table("channels").select("id").eq("user_id", user_id).execute()
    if len(current.data) >= max_channels:
        raise HTTPException(
            status_code=403,
            detail=f"Plan limit reached! {plan} plan mein max {max_channels} channels. Upgrade karo!"
        )


class ChannelCreate(BaseModel):
    channel_name: str
    drive_folder_id: str
    schedule_times: List[str] = ["09:00", "15:00", "21:00"]
    ai_style: str = "energetic"
    ai_custom_prompt: Optional[str] = None
    videos_per_day: int = 3
    yt_access_token: Optional[str] = None
    yt_refresh_token: Optional[str] = None
    drive_token_data: Optional[dict] = None
    channel_yt_id: Optional[str] = None
    channel_avatar: Optional[str] = None


class ChannelUpdate(BaseModel):
    channel_name: Optional[str] = None
    drive_folder_id: Optional[str] = None
    schedule_times: Optional[List[str]] = None
    ai_style: Optional[str] = None
    ai_custom_prompt: Optional[str] = None
    videos_per_day: Optional[int] = None
    is_active: Optional[bool] = None


@router.get("/")
async def get_channels(authorization: str = Header(...)):
    user_id = get_user_id(authorization)
    result = supabase.table("channels").select("*").eq("user_id", user_id).order("created_at").execute()
    return {"channels": result.data}


@router.post("/")
async def create_channel(channel: ChannelCreate, authorization: str = Header(...)):
    user_id = get_user_id(authorization)
    check_plan_limit(user_id)

    data = {**channel.dict(), "user_id": user_id}
    result = supabase.table("channels").insert(data).execute()

    # Immediately load videos for this channel
    from scheduler import load_all_videos_for_channel
    load_all_videos_for_channel(result.data[0])

    return {"channel": result.data[0], "message": "Channel added! Videos loading ho rahe hain..."}


@router.patch("/{channel_id}")
async def update_channel(channel_id: str, update: ChannelUpdate, authorization: str = Header(...)):
    user_id = get_user_id(authorization)

    data = {k: v for k, v in update.dict().items() if v is not None}
    result = supabase.table("channels").update(data).eq("id", channel_id).eq("user_id", user_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Channel not found")

    return {"channel": result.data[0]}


@router.delete("/{channel_id}")
async def delete_channel(channel_id: str, authorization: str = Header(...)):
    user_id = get_user_id(authorization)
    supabase.table("channels").delete().eq("id", channel_id).eq("user_id", user_id).execute()
    return {"message": "Channel deleted!"}


@router.post("/{channel_id}/toggle")
async def toggle_channel(channel_id: str, authorization: str = Header(...)):
    user_id = get_user_id(authorization)

    channel = supabase.table("channels").select("is_active").eq("id", channel_id).eq("user_id", user_id).single().execute().data
    new_status = not channel["is_active"]

    supabase.table("channels").update({"is_active": new_status}).eq("id", channel_id).execute()
    return {"is_active": new_status, "message": f"Channel {'activated' if new_status else 'paused'}!"}


@router.post("/{channel_id}/load-videos")
async def load_videos(channel_id: str, authorization: str = Header(...)):
    """Manually Drive se videos reload karo"""
    user_id = get_user_id(authorization)
    channel = supabase.table("channels").select("*").eq("id", channel_id).eq("user_id", user_id).single().execute().data

    from scheduler import load_all_videos_for_channel
    added = load_all_videos_for_channel(channel)
    return {"added": added, "message": f"{added} new videos queue mein add kiye!"}
