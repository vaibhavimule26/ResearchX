import os
import re
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.database.chroma import collection
from app.agents.coordinator import load_context_for_paper
from app.agents.report_agent import generate_ieee_report
from app.services.pdf_report import build_ieee_pdf_from_markdown, generate_ieee_pdf

router = APIRouter(
    prefix="/report",
    tags=["IEEE Report"],
)


class ReportRequest(BaseModel):
    paper_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )
    query: Optional[str] = None
    content: Optional[str] = None


class ReportResponse(BaseModel):
    success: bool
    message: str
    paper_name: str
    result: str


@router.post(
    "/generate",
    response_model=ReportResponse,
)
def generate_report(
    request: ReportRequest,
):
    try:
        is_query_mode = request.paper_name.lower().strip() in (
            "query_focus", "query focus", "topic", "none", ""
        ) or not request.paper_name.strip()

        context = ""
        if not is_query_mode:
            # Load comprehensive paper text from MongoDB / disk context cache
            context = load_context_for_paper(
                paper_name=request.paper_name,
                query=request.query or "methodology results datasets experiments literature",
            )

            # Fallback to ChromaDB if paper context was not in MongoDB or disk
            if not context or len(context.strip()) < 50:
                try:
                    from sentence_transformers import SentenceTransformer
                    model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
                    search_query = request.query or (
                        "complete research paper methodology results "
                        "datasets experiments literature contributions limitations"
                    )
                    embedding = model.encode(search_query).tolist()
                    results = collection.query(
                        query_embeddings=[embedding],
                        n_results=15,
                        where={"paper_name": request.paper_name},
                    )
                    documents = results.get("documents", [[]])[0]
                    if documents:
                        context = "\n\n".join(documents)
                except Exception as chroma_err:
                    print(f"[Report API] ChromaDB fallback error: {chroma_err}")

        # If still no context found, check if query exists for Query-Only mode
        if not context or not context.strip():
            if request.query and request.query.strip():
                # Query-Only topic research mode: Attempt cross-document retrieval or generate pure topic report
                try:
                    from sentence_transformers import SentenceTransformer
                    model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
                    embedding = model.encode(request.query).tolist()
                    results = collection.query(
                        query_embeddings=[embedding],
                        n_results=8,
                    )
                    documents = results.get("documents", [[]])[0]
                    if documents:
                        context = "\n\n".join(documents)
                except Exception:
                    pass
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Research paper '{request.paper_name}' not found and no research query provided.",
                )

        report = generate_ieee_report(
            context=context,
            paper_name=request.paper_name,
            query=request.query,
        )

        effective_name = request.paper_name if not is_query_mode else (request.query or "Research_Report")

        return ReportResponse(
            success=True,
            message="IEEE Report generated successfully",
            paper_name=effective_name,
            result=report,
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[Report API Error]: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.post(
    "/pdf",
)
def export_report_pdf(
    request: ReportRequest,
):
    """
    Generate and stream an official publication-grade two-column IEEE PDF.
    """
    try:
        # 1. Single Source of Truth: Use preview markdown from frontend if provided
        if request.content and request.content.strip():
            report_markdown = request.content.strip()
        else:
            # Fallback: Load context and generate if content was not supplied
            context = load_context_for_paper(
                paper_name=request.paper_name,
                query=request.query or "methodology results datasets experiments literature",
            )

            if not context or len(context.strip()) < 50:
                try:
                    from sentence_transformers import SentenceTransformer
                    model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
                    embedding = model.encode(request.query or "methodology results datasets experiments").tolist()
                    results = collection.query(
                        query_embeddings=[embedding],
                        n_results=15,
                        where={"paper_name": request.paper_name} if request.paper_name else None,
                    )
                    documents = results.get("documents", [[]])[0]
                    if documents:
                        context = "\n\n".join(documents)
                except Exception:
                    pass

            report_markdown = generate_ieee_report(
                context=context,
                paper_name=request.paper_name,
                query=request.query,
            )

        # 3. Compile Two-Column IEEE PDF
        paper_clean = request.paper_name if (request.paper_name and request.paper_name.lower().strip() not in ("query_focus", "query focus")) else (request.query or "IEEE_Research_Report")
        clean_name = re.sub(
            r"[^a-zA-Z0-9_\-]",
            "_",
            paper_clean.replace(".pdf", ""),
        ).strip("_")
        if not clean_name:
            clean_name = "IEEE_Transactions_Report"
        os.makedirs("uploads/generated_reports", exist_ok=True)
        pdf_path = f"uploads/generated_reports/{clean_name[:40]}_IEEE_Transactions_Paper.pdf"

        build_ieee_pdf_from_markdown(
            markdown_content=report_markdown,
            title=paper_clean,
            output_path=pdf_path,
        )

        if not os.path.exists(pdf_path):
            raise HTTPException(
                status_code=500,
                detail="Failed to generate IEEE PDF file.",
            )

        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"{clean_name[:30]}_IEEE_Transactions_Paper.pdf",
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[Report PDF Export Error]: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )