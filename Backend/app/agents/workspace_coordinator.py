from datetime import datetime
from app.database.mongodb import research_sessions_collection, papers_collection
from app.services.arxiv_service import search_papers

def run_workspace(topic, session_id):
    agents = [
        {
            "agent": "Summary",
            "status": "Pending",
            "progress": 0,
        },
        {
            "agent": "Research Gap",
            "status": "Pending",
            "progress": 0,
        },
        {
            "agent": "Dataset Recommendation",
            "status": "Pending",
            "progress": 0,
        },
        {
            "agent": "Experiment Recommendation",
            "status": "Pending",
            "progress": 0,
        },
        {
            "agent": "Literature Survey",
            "status": "Pending",
            "progress": 0,
        },
        {
            "agent": "Novelty Analysis",
            "status": "Pending",
            "progress": 0,
        },
        {
            "agent": "Comparison",
            "status": "Pending",
            "progress": 0,
        },
        {
            "agent": "IEEE Report",
            "status": "Pending",
            "progress": 0,
        },
        {
            "agent": "PPT Generator",
            "status": "Pending",
            "progress": 0,
        },
    ]

    print("Saving session...")
    research_sessions_collection.insert_one(
        {
            "session_id": session_id,
            "topic": topic,
            "status": "Running",
            "created_at": datetime.utcnow(),
            "agents": agents,
        }
    )

    # Step 2: Search papers from arXiv
    print("Searching papers from arXiv...")
    papers = search_papers(topic)
    print(f"Found {len(papers)} papers")

    # Step 3: Save papers into MongoDB
    for paper in papers:
        papers_collection.insert_one(
            {
                "session_id": session_id,
                "topic": topic,
                "title": paper["title"],
                "authors": paper["authors"],
                "summary": paper["summary"],
                "published": paper["published"],
                "pdf_url": paper["pdf_url"],
            }
        )

    # Step 4: Build Context
    context = ""
    for paper in papers:
        context += paper["summary"] + "\n\n"

    # The code can now proceed to use the `context` variable for the downstream agents
    return agents