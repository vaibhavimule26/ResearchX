import os
import tempfile

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

from app.auth.jwt_handler import get_optional_user
from app.services.activity_service import log_user_activity
from app.agents.coordinator import load_context_for_paper
from app.agents.ppt_agent import generate_presentation

router = APIRouter(
    prefix="/presentation",
    tags=["Presentation"],
)


class PresentationRequest(BaseModel):
    paper_name: str
    force_refresh: Optional[bool] = False


@router.post("/generate")
def generate_presentation_text(
    request: PresentationRequest,
    request_http: Request = None,
):

    try:
        if not request.paper_name or not request.paper_name.strip():
            raise HTTPException(
                status_code=400,
                detail="Paper name must not be empty.",
            )

        # ----------------------------------------
        # Cache Management
        # ----------------------------------------
        cache_dir = os.path.join(
            tempfile.gettempdir(),
            "researchx_cache",
        )
        os.makedirs(cache_dir, exist_ok=True)

        safe_cache_name = "".join(
            c for c in request.paper_name if c.isalnum() or c in ("-", "_", ".")
        ).strip()
        cache_file = os.path.join(cache_dir, f"{safe_cache_name}.txt")

        if not request.force_refresh and os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_text = f.read()
                if cached_text and len(cached_text.strip()) > 100:
                    return {
                        "success": True,
                        "presentation": cached_text,
                    }

        # ----------------------------------------
        # Retrieve Full Grounded Paper Context
        # ----------------------------------------
        context = load_context_for_paper(
            paper_name=request.paper_name,
            query="abstract methodology dataset experimental setup benchmark results conclusion",
        )

        if not context or len(context.strip()) < 50:
            raise HTTPException(
                status_code=404,
                detail=f"Paper '{request.paper_name}' not found in uploaded repository or database.",
            )

        presentation = generate_presentation(
            context=context,
            paper_name=request.paper_name,
        )

        # Save to cache
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(presentation)

        # Log user activity if authenticated
        try:
            user = get_optional_user(request_http)
            if user:
                log_user_activity(
                    user_id=user["user_id"],
                    user_email=user["email"],
                    action_name="Presentation (PPT)",
                    activity_type="presentation",
                    topic=None,
                    paper_name=request.paper_name,
                    agent="PowerPoint Agent",
                    status="Completed",
                    details=f"Generated presentation slides for {request.paper_name}",
                )
        except Exception as act_err:
            print(f"[Presentation Activity Log Error]: {act_err}")

        return {
            "success": True,
            "presentation": presentation,
        }


    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )