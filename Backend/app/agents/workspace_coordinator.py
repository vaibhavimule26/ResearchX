from datetime import datetime

from app.database.mongodb import (
    research_sessions_collection,
    papers_collection,
)


# ==========================================================
# Workspace Agents
# ==========================================================
WORKSPACE_AGENTS = [
    "Summary",
    "Research Gap",
    "Dataset Recommendation",
    "Experiment Recommendation",
    "Literature Survey",
    "Novelty Analysis",
    "Comparison",
    "IEEE Report",
    "PPT Generator",
]


# ==========================================================
# Workspace Coordinator
# ==========================================================
def run_workspace(topic: str, session_id: str, papers):
    """
    Creates a new research workspace.

    Responsibilities:
    1. Create Research Session
    2. Save Selected Papers
    3. Return Available Agents

    NOTE:
    The coordinator DOES NOT execute any AI agent.
    Each agent is executed separately through
    /analysis/run-agent.
    """

    agents = [
        {
            "agent": agent_name,
            "status": "Pending",
            "progress": 0,
        }
        for agent_name in WORKSPACE_AGENTS
    ]

    print("Creating Research Session...")

    research_sessions_collection.insert_one(
        {
            "session_id": session_id,
            "topic": topic,
            "status": "Created",
            "created_at": datetime.utcnow(),
            "agents": agents,
        }
    )

    print("Saving Selected Papers...")

    paper_documents = [
        {
            "session_id": session_id,
            "topic": topic,
            "title": paper.title,
            "authors": paper.authors,
            "summary": paper.summary,
            "published": paper.published,
            "pdf_url": paper.pdf_url,
        }
        for paper in papers
    ]

    if paper_documents:
        papers_collection.insert_many(paper_documents)

    print("Research Session Ready.")

    return agents