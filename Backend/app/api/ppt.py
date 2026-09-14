import os
import tempfile

from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.agents.coordinator import load_context_for_paper
from app.agents.ppt_agent import generate_presentation
from app.utils.ppt_export import create_ppt


router = APIRouter(
    prefix="/ppt",
    tags=["PowerPoint"],
)


class PPTRequest(BaseModel):
    paper_name: str
    presentation_text: Optional[str] = None


@router.post("/generate")
def generate_ppt(
    request: PPTRequest,
):
    try:
        if not request.paper_name or not request.paper_name.strip():
            raise HTTPException(
                status_code=400,
                detail="Paper name must not be empty.",
            )

        # ----------------------------------------
        # Single Source of Truth: Check if presentation text passed from UI
        # ----------------------------------------
        if request.presentation_text and request.presentation_text.strip():
            presentation = request.presentation_text.strip()
        else:
            # Fallback: Cache Directory & Cache Lookup
            cache_dir = os.path.join(
                tempfile.gettempdir(),
                "researchx_cache",
            )
            os.makedirs(cache_dir, exist_ok=True)

            safe_cache_name = "".join(
                c for c in request.paper_name if c.isalnum() or c in ("-", "_", ".")
            ).strip()
            cache_file = os.path.join(cache_dir, f"{safe_cache_name}.txt")

            if os.path.exists(cache_file):
                with open(cache_file, "r", encoding="utf-8") as f:
                    presentation = f.read()
            else:
                context = load_context_for_paper(
                    paper_name=request.paper_name,
                    query="abstract methodology dataset experimental setup benchmark results conclusion",
                )
                if not context or len(context.strip()) < 50:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Paper '{request.paper_name}' not found.",
                    )

                presentation = generate_presentation(
                    context=context,
                    paper_name=request.paper_name,
                )

                with open(cache_file, "w", encoding="utf-8") as f:
                    f.write(presentation)

        # ----------------------------------------
        # Generate PPTX
        # ----------------------------------------
        safe_name = (
            request.paper_name.replace(".pdf", "")
            .replace(".txt", "")
            .replace(" ", "_")
        )
        safe_filename = "".join(c for c in safe_name if c.isalnum() or c in ("-", "_"))[:35] or "ResearchX"

        output_file = os.path.join(
            tempfile.gettempdir(),
            f"{safe_filename}_Presentation.pptx",
        )

        create_ppt(
            presentation_text=presentation,
            output_path=output_file,
            paper_title=request.paper_name,
        )

        # ----------------------------------------
        # Return PPT File
        # ----------------------------------------
        return FileResponse(
            output_file,
            filename=f"{safe_filename}_Presentation.pptx",
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )