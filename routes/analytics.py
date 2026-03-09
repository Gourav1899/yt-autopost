"""Analytics Routes"""
from fastapi import APIRouter, Header, HTTPException
from database import supabase

router = APIRouter()

def get_user_id(authorization: str) -> str:
    try:
        return supabase.auth.get_user(authorization.replace("Bearer ", "")).user.id
    except:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/summary")
async def analytics_summary(days: int = 30, authorization: str = Header(...)):
    user_id = get_user_id(authorization)

    # Total uploaded
    done = supabase.table("queue").select("id").eq("user_id", user_id).eq("status", "done").execute()
    failed = supabase.table("queue").select("id").eq("user_id", user_id).eq("status", "failed").execute()
    total = supabase.table("queue").select("id").eq("user_id", user_id).execute()

    # Total views
    views_result = supabase.table("analytics").select("views").eq("user_id", user_id).execute()
    total_views = sum(r["views"] for r in views_result.data)

    success_rate = round((len(done.data) / max(len(total.data), 1)) * 100, 1)

    return {
        "total_uploaded": len(done.data),
        "total_failed": len(failed.data),
        "total_views": total_views,
        "success_rate": success_rate
    }


@router.get("/per-channel")
async def analytics_per_channel(authorization: str = Header(...)):
    user_id = get_user_id(authorization)
    channels = supabase.table("channels").select("id, channel_name").eq("user_id", user_id).execute()

    result = []
    for ch in channels.data:
        done = supabase.table("queue").select("id").eq("channel_id", ch["id"]).eq("status", "done").execute()
        views = supabase.table("analytics").select("views").eq("channel_id", ch["id"]).execute()
        total_views = sum(r["views"] for r in views.data)
        result.append({
            "channel_name": ch["channel_name"],
            "total_uploaded": len(done.data),
            "total_views": total_views
        })
    return {"channels": result}
