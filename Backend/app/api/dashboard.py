from fastapi import APIRouter, Query
from app.database.mongodb import papers_collection, agent_runs_collection

router = APIRouter()


@router.get("/dashboard")
def get_dashboard():
    agent_runs = agent_runs_collection.find_one({}, {"_id": 0})
    if not agent_runs:
        agent_runs = {
            "summary": 0,
            "datasets": 0,
            "experiments": 0,
            "literature": 0,
            "novelty": 0,
            "reports": 0,
            "ppt": 0,
        }

    papers = papers_collection.count_documents({})

    recent = []

    cursor = (
        papers_collection.find(
            {},
            {
                "_id": 0,
                "title": 1,
                "uploaded_at": 1,
            },
        )
        .sort("uploaded_at", -1)
        .limit(5)
    )

    for paper in cursor:
        recent.append(
            {
                "title": paper["title"],
                "agent": "Paper Upload",
                "time": paper["uploaded_at"],
                "status": "Completed",
            }
        )

    return {
        "success": True,
        "data": {
            "papers": papers,
            "projects": 0,
            "reports": 0,
            "presentations": 0,
            "agent_runs": agent_runs,

            "recentResearch": recent,

            "tasks": [
                {
                    "title": "Upload a new research paper",
                    "due": "Pending",
                },
                {
                    "title": "Generate IEEE Report",
                    "due": "Pending",
                },
                {
                    "title": "Generate Presentation",
                    "due": "Pending",
                },
            ],

            "activity": [
                {"name": "Mon", "value": 0},
                {"name": "Tue", "value": 0},
                {"name": "Wed", "value": 0},
                {"name": "Thu", "value": 0},
                {"name": "Fri", "value": 0},
                {"name": "Sat", "value": 0},
                {"name": "Sun", "value": 0},
            ],

            "progress": [
                {
                    "name": "Paper Upload",
                    "pct": 100,
                },
                {
                    "name": "Research Analysis",
                    "pct": 0,
                },
                {
                    "name": "IEEE Report",
                    "pct": 0,
                },
                {
                    "name": "Presentation",
                    "pct": 0,
                },
            ],

            "suggestions": [
                "Generate summary for latest uploaded paper",
                "Run Research Gap Analysis",
                "Generate IEEE Report",
                "Generates Presentation",
            ],
        },
    }


@router.get("/dashboard/search")
def search_dashboard(query: str = Query(...)):

    results = []

    cursor = papers_collection.find(
        {
            "title": {
                "$regex": query,
                "$options": "i",
            }
        },
        {
            "_id": 0,
            "title": 1,
            "uploaded_at": 1,
        },
    ).limit(10)

    for paper in cursor:
        results.append(
            {
                "title": paper["title"],
                "uploaded_at": paper["uploaded_at"],
            }
        )

    return {
        "success": True,
        "results": results,
    }