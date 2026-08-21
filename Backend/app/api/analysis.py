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


class AnalysisPaper(BaseModel):
    title: str
    summary: Optional[str] = None
    authors: Optional[str] = None
    published: Optional[str] = None
    pdf_url: Optional[str] = None


class AnalysisRequest(BaseModel):
    paper_name: Optional[str] = None
    paper_names: Optional[List[str]] = None
    papers: Optional[List[AnalysisPaper]] = None
    query: Optional[str] = None
    analysis_type: Optional[str] = "summary"


class WorkspaceRequest(BaseModel):
    topic: str
    session_id: str
    papers: List[AnalysisPaper]


@router.post("/run")
async def run_paper_analysis(request: AnalysisRequest):
    try:
        query_map = {
            "summary": """
Analyze ONLY this research paper and generate a SHORT structured summary.

Use EXACTLY this format:

### 📌 Research Snapshot
* **Problem:** Maximum 1-2 concise sentences.
* **Method:** Maximum 1-2 concise sentences.
* **Domain:** Mention the research field.
* **Objective:** Mention the main goal in 1 sentence.

### 📊 Key Findings
* **Main Result:** Mention the most important finding or metric. If no exact result is provided, write "Not specified in the paper."
* **Baseline/Comparison:** Mention comparison with existing methods. If unavailable, write "Not specified in the paper."

### ⚠️ Limitations & Future Work
* **Limitation:** Explicit limitation only. If unavailable, write "Not specified in the paper."
* **Future Direction:** Explicit future work only. If unavailable, write "Not specified in the paper."

### 💡 Core Takeaways
1. First important takeaway in one short sentence.
2. Second important takeaway in one short sentence.
3. Third important takeaway in one short sentence.

IMPORTANT RULES:
- Keep the entire summary concise and focused.
- Do NOT write long paragraphs.
- Do NOT invent facts, metrics, comparisons, or limitations.
- Use ONLY information available in the provided paper context.
- For unavailable information, write exactly: "Not specified in the paper."
- Do not add an introduction or conclusion outside this format.
""",
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

        if request.analysis_type in query_map:
            active_query = query_map[request.analysis_type]
        else:
            active_query = request.query or request.analysis_type

        # --------------------------------------------
        # MULTIPLE SELECTED PAPERS WITH ACTUAL CONTEXT
        # --------------------------------------------
        if request.papers and len(request.papers) > 0:
            paper_results = []

            for paper in request.papers:
                paper_context = f"""
You must analyze ONLY this selected research paper.

Paper Title:
{paper.title}

Authors:
{paper.authors or "Not specified"}

Published:
{paper.published or "Not specified"}

Abstract / Paper Summary:
{paper.summary or "Not specified in the paper."}

PDF URL:
{paper.pdf_url or "Not specified"}
"""
                raw_result = run_agent(
                    query=active_query,
                    paper_name=paper.title,
                    context=paper_context
                )

                clean_result = format_clean_analysis_output(raw_result)

                paper_results.append(
                    {
                        "paper_name": paper.title,
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
        # MULTIPLE SELECTED PAPERS (NAMES ONLY)
        # --------------------------------------------
        if request.paper_names and len(request.paper_names) > 0:
            paper_results = []

            for paper_name in request.paper_names:
                raw_result = run_agent(
                    query=active_query,
                    paper_name=paper_name
                )

                clean_result = format_clean_analysis_output(raw_result)

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