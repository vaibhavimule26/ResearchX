from typing import Any, Dict, List, Optional, Tuple, Union
from fastapi import APIRouter, Query

from app.search.paper_search_service import search_workspace_papers

router = APIRouter()


@router.get("/paper-search")
@router.get("/papers/search")
@router.get("/search")
async def search_papers_api(
    query: str = Query(..., description="Query for academic research"),
    sort_by: Optional[str] = Query(
        "relevance",
        description="Sorting criteria: relevance, year_desc, citations_desc, year_asc",
    ),
    year: Optional[str] = Query(
        "all",
        description="Optional year filter: all, 2026, 2025, 2024, 2023, 2022, last_3_years, last_5_years, foundational",
    ),
    source: Optional[str] = Query(
        "all",
        description="Optional publisher/source filter: all, ieee, arxiv, openalex, semantic_scholar, crossref",
    ),
    limit: Optional[int] = Query(10, description="Maximum number of papers to return"),
):
    results = await search_workspace_papers(
        query=query,
        limit=limit or 10,
        sort_by=sort_by or "relevance",
        year=year or "all",
        source=source or "all",
    )

    corrected_query = results[0].get("search_corrected_query", query) if results else query

    return {
        "success": True,
        "data": results,
        "results": results,
        "total": len(results),
        "query": query,
        "original_query": query,
        "corrected_query": corrected_query,
        "sort_by": sort_by or "relevance",
        "filter_year": year or "all",
        "filter_source": source or "all",
    }