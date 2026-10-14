from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.auth.jwt_handler import get_optional_user
from app.services.activity_service import log_user_activity
from app.services.plagiarism_service import (
    analyze_paper_similarity,
    clear_plagiarism_cache,
)


router = APIRouter(
    prefix="/plagiarism",
    tags=["Plagiarism & Similarity"],
)


class PlagiarismCheckRequest(BaseModel):
    pdf_id: str = Field(
        ...,
        min_length=1,
        max_length=300,
        description="The MongoDB ObjectId or unique filename of the uploaded paper",
    )
    force_refresh: Optional[bool] = False


class MatchItem(BaseModel):
    id: int
    match_id: Optional[int] = None
    page: int
    matched_text: str
    source_passage: str
    source_document: str
    source_page: Optional[int] = 1
    similarity: float
    similarity_percentage: Optional[float] = None
    match_type: str


class PlagiarismResultData(BaseModel):
    pdf_id: str
    filename: str
    title: str
    similarity_score: float
    original_content: float
    originality_score: Optional[float] = None
    potential_matches_count: int
    matches_count: Optional[int] = None
    comparison_sources_count: int
    total_compared_documents: Optional[int] = None
    comparison_scope: str
    comparison_corpus: Optional[str] = None
    total_words_analyzed: int
    matches: List[MatchItem]
    checked_at: str
    analyzed_at: Optional[str] = None
    cached: Optional[bool] = False


class PlagiarismResponse(BaseModel):
    success: bool
    status: Optional[str] = "success"
    message: str
    data: PlagiarismResultData


@router.post(
    "/check",
    response_model=PlagiarismResponse,
)
def check_plagiarism(
    request: PlagiarismCheckRequest,
    request_http: Request = None,
):
    """
    Analyze the uploaded PDF for plagiarism / text similarity against
    the ResearchX repository corpus.
    Uses multi-level text comparison without LLM hallucination.
    """
    try:
        result = analyze_paper_similarity(
            pdf_id=request.pdf_id,
            force_refresh=bool(request.force_refresh),
        )

        # Log user activity if authenticated
        try:
            user = get_optional_user(request_http)
            if user:
                sim_score = result.get("similarity_score", 0) if isinstance(result, dict) else getattr(result, "similarity_score", 0)
                matches_cnt = result.get("potential_matches_count", 0) if isinstance(result, dict) else getattr(result, "potential_matches_count", 0)
                p_title = (result.get("filename") or result.get("title") or request.pdf_id) if isinstance(result, dict) else (getattr(result, "filename", None) or request.pdf_id)
                log_user_activity(
                    user_id=user["user_id"],
                    user_email=user["email"],
                    action_name="Plagiarism Check",
                    activity_type="plagiarism",
                    topic=None,
                    paper_name=p_title,
                    agent="Plagiarism Checker",
                    status="Completed",
                    details=f"Similarity: {sim_score}%, {matches_cnt} potential match(es)",
                )
        except Exception as act_err:
            print(f"[Plagiarism Activity Log Error]: {act_err}")

        return PlagiarismResponse(
            success=True,
            message="Plagiarism analysis completed successfully",
            data=result,
        )


    except ValueError as val_err:
        raise HTTPException(
            status_code=404,
            detail=str(val_err),
        )
    except Exception as err:
        print(f"[Plagiarism API Error]: {err}")
        raise HTTPException(
            status_code=500,
            detail=f"Plagiarism analysis failed: {str(err)}",
        )


@router.get(
    "/{pdf_id}",
    response_model=PlagiarismResponse,
)
def get_plagiarism_result(
    pdf_id: str,
    force_refresh: bool = Query(False),
):
    """
    Retrieve similarity report for a given PDF ID.
    """
    try:
        result = analyze_paper_similarity(
            pdf_id=pdf_id,
            force_refresh=force_refresh,
        )

        return PlagiarismResponse(
            success=True,
            message="Plagiarism report retrieved successfully",
            data=result,
        )

    except ValueError as val_err:
        raise HTTPException(
            status_code=404,
            detail=str(val_err),
        )
    except Exception as err:
        print(f"[Plagiarism API Error]: {err}")
        raise HTTPException(
            status_code=500,
            detail=f"Plagiarism report retrieval failed: {str(err)}",
        )
