"""Admin Routes — Only for admin users"""
from fastapi import APIRouter, Header, HTTPException
from database import supabase

router = APIRouter()

def get_admin_user(authorization: str):
    try:
        user_id = supabase.auth.get_user(authorization.replace("Bearer ", "")).user.id
        profile = supabase.table("profiles").select("is_admin").eq("id", user_id).single().execute().data
        if not profile.get("is_admin"):
            raise HTTPException(status_code=403, detail="Admin access required!")
        return user_id
    except HTTPException:
        raise
    except:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/users")
async def get_all_users(authorization: str = Header(...)):
    get_admin_user(authorization)
    result = supabase.table("profiles").select("*").order("created_at", desc=True).execute()
    return {"users": result.data}


@router.get("/stats")
async def admin_stats(authorization: str = Header(...)):
    get_admin_user(authorization)
    users = supabase.table("profiles").select("id, plan").execute()
    channels = supabase.table("channels").select("id").eq("is_active", True).execute()
    uploads = supabase.table("queue").select("id").eq("status", "done").execute()

    plan_breakdown = {}
    for u in users.data:
        plan = u["plan"]
        plan_breakdown[plan] = plan_breakdown.get(plan, 0) + 1

    return {
        "total_users": len(users.data),
        "active_channels": len(channels.data),
        "total_uploads": len(uploads.data),
        "plan_breakdown": plan_breakdown
    }


@router.patch("/users/{user_id}/plan")
async def change_user_plan(user_id: str, plan: str, authorization: str = Header(...)):
    get_admin_user(authorization)
    valid_plans = ["free", "starter", "pro", "agency"]
    if plan not in valid_plans:
        raise HTTPException(status_code=400, detail=f"Invalid plan. Choose: {valid_plans}")
    supabase.table("profiles").update({"plan": plan}).eq("id", user_id).execute()
    return {"message": f"Plan updated to {plan}!"}
