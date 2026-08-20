import os
import re
import json
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.coordinator import run_agent
from app.agents.workspace_coordinator import run_workspace
from app.database.mongodb import research_sessions_collection

router = APIRouter(prefix="/analysis", tags=["analysis"])


def format_clean_analysis_output(raw_output) -> str:
    """Extract clean, properly structured markdown text from agent outputs
    without destroying tables, headings, lists, or bolding.
    """
    if not raw_output:
        return "No response generated."

    text = ""
    if isinstance(raw_output, dict):
        results = raw_output.get("results", {})
        if isinstance(results, dict):
            for key in ["datasets", "literature_survey", "literature", "gaps", "summary", "experiments", "novelty"]:
                if key in results and isinstance(results[key], dict) and "output" in results[key]:
                    text = results[key]["output"]
                    break
            if not text:
                for v in results.values():
                    if isinstance(v, dict) and "output" in v:
                        text = v["output"]
                        break
        if not text:
            for direct_key in ["output", "answer", "result", "text"]:
                if direct_key in raw_output:
                    text = raw_output[direct_key]
                    break

    elif isinstance(raw_output, str):
        trimmed = raw_output.strip()
        if (trimmed.startswith("{") and trimmed.endswith("}")) or (trimmed.startswith("[") and trimmed.endswith("]")):
            try:
                parsed = json.loads(trimmed.replace("'", '"'))
                return format_clean_analysis_output(parsed)
            except Exception:
                pass

        m = re.search(r'["\']output["\']\s*:\s*["\']([\s\S]*?)["\']\s*(?:,\s*["\']|\})', trimmed)
        text = m.group(1) if m and m.group(1) else trimmed
    else:
        text = str(raw_output)

    # Clean basic escaped characters
    cleaned = (
        text.replace("\\n", "\n")
        .replace("\\r", "")
        .replace('\\"', '"')
        .replace("\\'", "'")
    )

    # Normalize excessive newlines while preserving markdown spacing
    cleaned = re.sub(r"\n{4,}", "\n\n\n", cleaned)

    return cleaned.strip()


class AnalysisRequest(BaseModel):
    paper_name: Optional[str] = None
    paper_names: Optional[List[str]] = None
    query: Optional[str] = None
    analysis_type: Optional[str] = "summary"


class WorkspacePaper(BaseModel):
    title: str
    authors: Optional[str] = None
    summary: Optional[str] = None
    published: Optional[str] = None
    pdf_url: Optional[str] = None


class WorkspaceRequest(BaseModel):
    topic: str
    session_id: str
    papers: List[WorkspacePaper]


@router.post("/run")
async def run_paper_analysis(request: AnalysisRequest):
    try:
        query_map = {
            "summary": (
                "Summarize this research paper covering problem, methodology, "
                "findings, and takeaways."
            ),
            "literature_survey": (
                "Provide a structured academic Literature Survey for this paper "
                "covering Foundations, Methodologies, Comparative Baselines, "
                "and Research Gap Addressed."
            ),
            "literature": (
                "Provide a structured academic Literature Survey for this paper."
            ),
            "gaps": (
                "Analyze the stated and implied research gaps, limitations, "
                "bottlenecks, and future research directions."
            ),
            "datasets": (
                request.query
                or "Recommend benchmark datasets relevant to this research "
                "with licenses, metrics, and selection reasons."
            ),
            "experiments": (
                "Design an experimental replication and benchmarking protocol "
                "for this research."
            ),
        }

        active_query = (
            request.query
            or query_map.get(
                request.analysis_type,
                request.analysis_type
            )
        )

        # --------------------------------------------
        # MULTIPLE SELECTED PAPERS
        # --------------------------------------------
        if request.paper_names and len(request.paper_names) > 0:

            paper_results = []

            for paper_name in request.paper_names:

                raw_result = run_agent(
                    query=active_query,
                    paper_name=paper_name
                )

                clean_result = format_clean_analysis_output(
                    raw_result
                )

                paper_results.append(
                    {
                        "paper_name": paper_name,
                        "result": clean_result,
                    }
                )

            return {
                "status": "success",
                "analysis_type": request.analysis_type,
                "total_papers": len(paper_results),
                "results": paper_results,
                "data": paper_results,
            }

        # --------------------------------------------
        # SINGLE PAPER
        # --------------------------------------------
        raw_result = run_agent(
            query=active_query,
            paper_name=request.paper_name
        )

        clean_result = format_clean_analysis_output(raw_result)

        return {
            "status": "success",
            "paper_name": request.paper_name or "Custom Query",
            "analysis_type": request.analysis_type,
            "result": clean_result,
            "data": clean_result,
        }

    except Exception as e:
        print(f"Analysis route error: {e}")

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post("/workspace")
async def create_workspace(request: WorkspaceRequest):
    try:
        agents = run_workspace(
            topic=request.topic,
            session_id=request.session_id,
            papers=request.papers
        )

        return {
            "status": "success",
            "message": "Research workspace created successfully",
            "session_id": request.session_id,
            "topic": request.topic,
            "agents": agents,
        }

    except Exception as e:
        print(f"Workspace creation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/recent")
async def get_recent_research():
    try:
        sessions = list(
            research_sessions_collection
            .find(
                {},
                {"_id": 0}
            )
            .sort("created_at", -1)
            .limit(10)
        )

        for session in sessions:
            if session.get("created_at"):
                session["created_at"] = session["created_at"].isoformat()

        return {
            "status": "success",
            "data": sessions
        }

    except Exception as e:
        print(f"Recent research error: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )