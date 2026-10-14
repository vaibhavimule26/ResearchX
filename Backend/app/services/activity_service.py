from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from bson import ObjectId

from app.database.mongodb import user_activities_collection


def log_user_activity(
    user_id: str,
    user_email: str,
    action_name: str,
    activity_type: str,
    topic: Optional[str] = None,
    paper_name: Optional[str] = None,
    agent: Optional[str] = None,
    status: str = "Completed",
    details: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Log an authenticated user activity in MongoDB strictly tied to their user_id.
    """
    if not user_id:
        return {}

    now = datetime.now(timezone.utc)

    # Normalize clean display titles
    clean_topic = topic.strip() if topic and isinstance(topic, str) and topic.strip() else None
    clean_paper = paper_name.strip() if paper_name and isinstance(paper_name, str) and paper_name.strip() else None

    # Avoid logging default dummy queries
    if clean_topic and clean_topic.lower() in ["academic research topic", "query_focus", "query focus", "none", "null"]:
        clean_topic = None

    doc = {
        "user_id": str(user_id),
        "user_email": str(user_email or ""),
        "action_name": action_name.strip(),
        "activity_type": activity_type.strip().lower(),
        "topic": clean_topic,
        "paper_name": clean_paper,
        "agent": agent.strip() if agent else None,
        "status": status.strip() if status else "Completed",
        "details": details.strip() if details else None,
        "created_at": now,
    }

    try:
        res = user_activities_collection.insert_one(doc)
        doc["_id"] = str(res.inserted_id)
        doc["id"] = str(res.inserted_id)
        doc["created_at"] = now.isoformat()
        return doc
    except Exception as e:
        print(f"[ActivityService] Error logging activity: {e}")
        return {}


def format_activity_item(doc: Dict[str, Any], now_utc: datetime) -> Dict[str, Any]:
    """
    Format a database activity record with human-readable date and time.
    """
    created_at = doc.get("created_at")
    if isinstance(created_at, str):
        try:
            created_at = datetime.fromisoformat(created_at)
        except Exception:
            created_at = now_utc

    if not isinstance(created_at, datetime):
        created_at = now_utc

    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    # Compute relative date label
    today_date = now_utc.date()
    item_date = created_at.date()
    days_diff = (today_date - item_date).days

    if days_diff == 0:
        date_group = "Today"
    elif days_diff == 1:
        date_group = "Yesterday"
    elif days_diff < 7:
        date_group = created_at.strftime("%A")
    else:
        date_group = created_at.strftime("%B %d, %Y")

    # Time format e.g. "12:42 PM"
    formatted_time = created_at.strftime("%I:%M %p").lstrip("0")
    if not formatted_time.endswith("M"):
        formatted_time = created_at.strftime("%H:%M")

    return {
        "id": str(doc.get("_id") or doc.get("id")),
        "user_id": str(doc.get("user_id")),
        "action_name": doc.get("action_name") or "Research Activity",
        "activity_type": doc.get("activity_type") or "general",
        "topic": doc.get("topic"),
        "paper_name": doc.get("paper_name"),
        "agent": doc.get("agent"),
        "status": doc.get("status") or "Completed",
        "details": doc.get("details"),
        "timestamp": created_at.isoformat(),
        "date_group": date_group,
        "formatted_time": formatted_time,
        "formatted_date": created_at.strftime("%b %d, %Y"),
    }


def get_user_activities(
    user_id: str,
    limit: int = 150,
    activity_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fetch activities belonging strictly to the specified user_id, grouped into date sections.
    """
    if not user_id:
        return {"activities": [], "grouped": [], "total": 0}

    query: Dict[str, Any] = {"user_id": str(user_id)}
    if activity_type and activity_type.lower() != "all":
        query["activity_type"] = activity_type.lower()

    now_utc = datetime.now(timezone.utc)

    try:
        cursor = user_activities_collection.find(query).sort("created_at", -1).limit(limit)
        items = []
        for raw in cursor:
            items.append(format_activity_item(raw, now_utc))

        # Group by date_group while preserving order
        grouped: List[Dict[str, Any]] = []
        seen_groups: Dict[str, List[Dict[str, Any]]] = {}

        for item in items:
            grp = item["date_group"]
            if grp not in seen_groups:
                group_entry = {"date": grp, "items": []}
                grouped.append(group_entry)
                seen_groups[grp] = group_entry["items"]
            seen_groups[grp].append(item)

        return {
            "activities": items,
            "grouped": grouped,
            "total": len(items),
        }
    except Exception as e:
        print(f"[ActivityService] Error fetching activities for user {user_id}: {e}")
        return {"activities": [], "grouped": [], "total": 0}


def delete_user_activity(user_id: str, activity_id: str) -> bool:
    """
    Delete a specific activity only if it belongs to the authenticated user.
    """
    if not user_id or not activity_id:
        return False
    try:
        res = user_activities_collection.delete_one({
            "_id": ObjectId(activity_id),
            "user_id": str(user_id),
        })
        return res.deleted_count > 0
    except Exception as e:
        print(f"[ActivityService] Error deleting activity {activity_id}: {e}")
        return False


def clear_user_history(user_id: str) -> int:
    """
    Clear all activities belonging strictly to the authenticated user.
    """
    if not user_id:
        return 0
    try:
        res = user_activities_collection.delete_many({"user_id": str(user_id)})
        return res.deleted_count
    except Exception as e:
        print(f"[ActivityService] Error clearing history for user {user_id}: {e}")
        return 0
