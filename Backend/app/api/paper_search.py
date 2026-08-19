from typing import Optional
from fastapi import APIRouter, Query
from app.services.search_service import search_academic_papers

router = APIRouter()

@router.get("/paper-search")
@router.get("/papers/search")
@router.get("/search")
def search_papers_api(
    query: str = Query(..., description="Query for academic research"),
    sort_by: Optional[str] = Query("year_desc", description="Sorting criteria: year_desc, citations_desc, year_asc"),
    year: Optional[str] = Query(None, description="Optional year filter: all, 2025, 2024, 2023, 2022, foundational"),
    limit: Optional[int] = Query(12, description="Maximum number of papers to return")
):
    results = search_academic_papers(
        query=query,
        limit=limit or 12,
        sort_by=sort_by or "year_desc",
        filter_year=year
    )
    return {
        "success": True,
        "data": results,
        "results": results,
        "total": len(results),
        "query": query,
        "sort_by": sort_by or "year_desc",
        "filter_year": year or "all"
    }