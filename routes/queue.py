"""Queue Routes"""
from fastapi import APIRouter, Header, HTTPException
from database import supabase

router = APIRouter()

def get_user_id(authorization: str) -> str:
    try:
        token = authorization.replace("Bearer ", "")
        return supabase.auth.get_user(token).user.id
    except:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/")
async def get_queue(status: str = None, authorization: str = Header(...)):
    user_id = get_user_id(authorization)
    query = supabase.table("queue").select("*, channels(channel_name)").eq("user_id", user_id)
    if status:
        query = query.eq("status", status)
    result = query.order("created_at", desc=True).execute()
    return {"queue": result.data}


@router.get("/stats")
async def queue_stats(authorization: str = Header(...)):
    user_id = get_user_id(authorization)
    result = supabase.table("queue").select("status").eq("user_id", user_id).execute()
    stats = {"pending": 0, "processing": 0, "done": 0, "failed": 0}
    for item in result.data:
        stats[item["status"]] = stats.get(item["status"], 0) + 1
    return stats


@router.post("/{queue_id}/retry")
async def retry_video(queue_id: str, authorization: str = Header(...)):
    user_id = get_user_id(authorization)
    supabase.table("queue").update({
        "status": "pending", "attempts": 0, "error_message": None
    }).eq("id", queue_id).eq("user_id", user_id).execute()
    return {"message": "Retry queue mein add ho gaya!"}
