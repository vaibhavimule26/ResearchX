import hashlib
import json
import os
import re
import tempfile
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.auth.jwt_handler import get_optional_user
from app.services.activity_service import log_user_activity
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
    force_refresh: Optional[bool] = False


class ReportResponse(BaseModel):
    success: bool
    message: str
    paper_name: str
    result: str
    plagiarism: Optional[Dict[str, Any]] = None
    edit_summary: Optional[str] = None


@router.post(
    "/generate",
    response_model=ReportResponse,
)
def generate_report(
    request: ReportRequest,
    request_http: Request = None,
):

    try:
        is_query_mode = request.paper_name.lower().strip() in (
            "query_focus", "query focus", "topic", "none", ""
        ) or not request.paper_name.strip()

        # ----------------------------------------
        # Cache Management
        # ----------------------------------------
        cache_dir = os.path.join(tempfile.gettempdir(), "researchx_cache")
        os.makedirs(cache_dir, exist_ok=True)

        safe_cache_name = "".join(
            c for c in request.paper_name if c.isalnum() or c in ("-", "_", ".")
        ).strip()
        query_slug = ""
        if request.query and request.query.strip():
            q_hash = hashlib.md5(request.query.strip().lower().encode("utf-8")).hexdigest()[:8]
            query_slug = f"_{q_hash}"
        cache_file = os.path.join(cache_dir, f"report_{safe_cache_name}{query_slug}.md")
        cache_audit_file = os.path.join(cache_dir, f"report_{safe_cache_name}{query_slug}_audit.json")

        if not request.force_refresh and os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_report = f.read()
                    if cached_report and len(cached_report.strip()) > 100:
                        cached_audit = None
                        cached_edit_summary = None
                        if os.path.exists(cache_audit_file):
                            try:
                                with open(cache_audit_file, "r", encoding="utf-8") as af:
                                    audit_payload = json.load(af)
                                    cached_audit = audit_payload.get("plagiarism")
                                    cached_edit_summary = audit_payload.get("edit_summary")
                            except Exception as af_err:
                                print(f"[Report Audit Cache Read Error]: {af_err}")
                        effective_name = request.paper_name if not is_query_mode else (request.query or "Research_Report")
                        return ReportResponse(
                            success=True,
                            message="IEEE Report loaded from cache",
                            paper_name=effective_name,
                            result=cached_report,
                            plagiarism=cached_audit,
                            edit_summary=cached_edit_summary,
                        )
            except Exception as cache_read_err:
                print(f"[Report Cache Read Error]: {cache_read_err}")

        context = ""
        if not is_query_mode:
            # Load comprehensive paper text from MongoDB / disk context cache
            context = load_context_for_paper(
                paper_name=request.paper_name,
                query=request.query or "",
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

        gen_result = generate_ieee_report(
            context=context,
            paper_name=request.paper_name,
            query=request.query,
            return_audit=True,
        )

        if isinstance(gen_result, tuple):
            report, plagiarism_audit, edit_summary = gen_result
        else:
            report = gen_result
            plagiarism_audit = None
            edit_summary = None

        effective_name = request.paper_name if not is_query_mode else (request.query or "Research_Report")

        # Save to disk cache
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(report)
            if plagiarism_audit is not None or edit_summary is not None:
                with open(cache_audit_file, "w", encoding="utf-8") as af:
                    json.dump({"plagiarism": plagiarism_audit, "edit_summary": edit_summary}, af, indent=2)
        except Exception as cache_write_err:
            print(f"[Report Cache Write Error]: {cache_write_err}")

        # Log user activity if authenticated
        try:
            user = get_optional_user(request_http)
            if user:
                log_user_activity(
                    user_id=user["user_id"],
                    user_email=user["email"],
                    action_name="IEEE Report",
                    activity_type="report",
                    topic=request.query,
                    paper_name=effective_name,
                    agent="IEEE Report Agent",
                    status="Completed",
                    details=f"Generated IEEE report for {effective_name}",
                )
        except Exception as act_err:
            print(f"[Report Activity Log Error]: {act_err}")

        return ReportResponse(
            success=True,
            message="IEEE Report generated successfully",
            paper_name=effective_name,
            result=report,
            plagiarism=plagiarism_audit,
            edit_summary=edit_summary,
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
            # Check disk cache first before expensive reload or generation
            cache_dir = os.path.join(tempfile.gettempdir(), "researchx_cache")
            safe_cache_name = "".join(
                c for c in request.paper_name if c.isalnum() or c in ("-", "_", ".")
            ).strip()
            query_slug = ""
            if request.query and request.query.strip():
                q_hash = hashlib.md5(request.query.strip().lower().encode("utf-8")).hexdigest()[:8]
                query_slug = f"_{q_hash}"
            cache_file = os.path.join(cache_dir, f"report_{safe_cache_name}{query_slug}.md")

            cached_report = None
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        cached_report = f.read()
                except Exception:
                    pass

            if cached_report and len(cached_report.strip()) > 100:
                report_markdown = cached_report
            else:
                # Fallback: Load context and generate if content was not supplied
                context = load_context_for_paper(
                    paper_name=request.paper_name,
                    query=request.query or "",
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