from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth.jwt_handler import get_current_authenticated_user
from app.services.activity_service import (
    log_user_activity,
    get_user_activities,
    delete_user_activity,
    clear_user_history,
)

router = APIRouter(prefix="/api/history", tags=["User Activity History"])


class RecordActivityRequest(BaseModel):
    action_name: str = Field(..., min_length=1, max_length=150)
    activity_type: str = Field(default="general", max_length=50)
    topic: Optional[str] = None
    paper_name: Optional[str] = None
    agent: Optional[str] = None
    status: Optional[str] = "Completed"
    details: Optional[str] = None


@router.get("")
@router.get("/")
def get_history_endpoint(
    limit: int = Query(150, ge=1, le=500),
    activity_type: Optional[str] = Query("all"),
    current_user: dict = Depends(get_current_authenticated_user),
):
    """
    Fetch activity history strictly for the authenticated user.
    Grouped by date (Today, Yesterday, Earlier) with timestamps.
    """
    user_id = current_user["user_id"]
    data = get_user_activities(
        user_id=user_id,
        limit=limit,
        activity_type=activity_type,
    )
    return {
        "success": True,
        "message": "User history retrieved successfully",
        "user_id": user_id,
        "data": data,
    }


@router.post("/activity")
def record_activity_endpoint(
    req: RecordActivityRequest,
    current_user: dict = Depends(get_current_authenticated_user),
):
    """
    Record an activity for the authenticated user.
    """
    activity = log_user_activity(
        user_id=current_user["user_id"],
        user_email=current_user["email"],
        action_name=req.action_name,
        activity_type=req.activity_type,
        topic=req.topic,
        paper_name=req.paper_name,
        agent=req.agent,
        status=req.status or "Completed",
        details=req.details,
    )
    return {
        "success": True,
        "message": "Activity recorded successfully",
        "data": activity,
    }


@router.delete("/{activity_id}")
def delete_single_activity_endpoint(
    activity_id: str,
    current_user: dict = Depends(get_current_authenticated_user),
):
    """
    Delete a single activity belonging strictly to the authenticated user.
    """
    success = delete_user_activity(
        user_id=current_user["user_id"],
        activity_id=activity_id,
    )
    if not success:
        raise HTTPException(status_code=404, detail="Activity not found or unauthorized")
    return {
        "success": True,
        "message": "Activity deleted successfully",
    }


@router.delete("")
@router.delete("/")
def clear_all_history_endpoint(
    current_user: dict = Depends(get_current_authenticated_user),
):
    """
    Clear all activity history belonging strictly to the authenticated user.
    """
    count = clear_user_history(user_id=current_user["user_id"])
    return {
        "success": True,
        "message": f"Cleared {count} activity records",
        "deleted_count": count,
    }
