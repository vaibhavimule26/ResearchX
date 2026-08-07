from fastapi import APIRouter, Query

from app.services.retrieval_service import search_papers

router = APIRouter(tags=["Paper Search"])


@router.get("/search")
def search_research_papers(query: str = Query(...)):

    papers = search_papers(query)

    return {
        "success": True,
        "results": papers
    }