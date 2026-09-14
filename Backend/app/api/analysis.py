import os
import re
import json
import concurrent.futures
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.coordinator import run_agent
from app.agents.workspace_coordinator import run_workspace
from app.database.mongodb import research_sessions_collection, papers_collection
from app.workflow.research_graph import research_graph
from app.utils.metrics import PerformanceTimer

router = APIRouter(prefix="/analysis", tags=["analysis"])


def format_clean_analysis_output(raw_output) -> str:
    """
    Return clean user-facing agent output.
    Preserves all Markdown headings, bold, bullet points, and tables.
    """
    if not raw_output:
        return "No response generated."

    text = ""

    # Extract output from API response or dictionary
    if isinstance(raw_output, dict):
        results = raw_output.get("results", {})
        if isinstance(results, dict):
            for key in [
                "datasets",
                "literature_survey",
                "literature",
                "gaps",
                "research_gap",
                "summary",
                "experiments",
                "novelty",
                "comparison",
                "final_report",
            ]:
                value = results.get(key)
                if isinstance(value, dict) and "output" in value:
                    text = value["output"]
                    break
                elif isinstance(value, str) and value:
                    text = value
                    break

            if not text:
                for value in results.values():
                    if isinstance(value, dict) and "output" in value:
                        text = value["output"]
                        break
                    elif isinstance(value, str) and value:
                        text = value
                        break

        if not text:
            for key in ["output", "answer", "result", "text", "final_report", "summary"]:
                if key in raw_output and raw_output[key]:
                    val = raw_output[key]
                    text = val if isinstance(val, str) else str(val)
                    break

    elif isinstance(raw_output, list):
        # Format list of items (e.g. per-paper results)
        formatted_items = []
        for item in raw_output:
            if isinstance(item, dict):
                p_name = item.get("paper_name", "")
                res = item.get("result", "") or item.get("output", "")
                if p_name and res:
                    formatted_items.append(f"### {p_name}\n\n{res}")
                elif res:
                    formatted_items.append(res)
            else:
                formatted_items.append(str(item))
        return "\n\n---\n\n".join(formatted_items)

    elif isinstance(raw_output, str):
        trimmed = raw_output.strip()

        # Handle JSON returned as a string
        if (
            (trimmed.startswith("{") and trimmed.endswith("}"))
            or (trimmed.startswith("[") and trimmed.endswith("]"))
        ):
            try:
                parsed = json.loads(trimmed)
                return format_clean_analysis_output(parsed)
            except Exception:
                try:
                    parsed = json.loads(trimmed.replace("'", '"'))
                    return format_clean_analysis_output(parsed)
                except Exception:
                    pass

            # Extract embedded "output" if present in a JSON-like string
            match = re.search(
                r'["\']output["\']\s*:\s*["\']([\s\S]*?)["\']\s*(?:,\s*["\']|\})',
                trimmed,
            )
            text = match.group(1) if match and match.group(1) else trimmed
        else:
            text = trimmed
    else:
        text = str(raw_output)

    # Decode literal escaped characters
    cleaned = (
        text.replace("\\n", "\n")
        .replace("\\r", "")
        .replace('\\"', '"')
        .replace("\\'", "'")
    )

    # Remove internal wrapper debug banners (e.g. === PAPER 1 ===)
    lines = cleaned.splitlines()
    final_lines = []
    for line in lines:
        stripped = line.strip()
        # Remove decorative equals/hyphen separators (5 or more in a row if not a table divider)
        if re.fullmatch(r"={5,}", stripped):
            continue
        # Remove PAPER 1 / PAPER 2 debug headers if followed by colons
        if re.fullmatch(r"={3,}\s*PAPER\s+\d+\s*={3,}", stripped, flags=re.IGNORECASE):
            continue
        final_lines.append(line.rstrip())

    cleaned = "\n".join(final_lines)
    # Normalize excessive blank lines (3+ into 2)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


class AnalysisPaper(BaseModel):
    title: str
    paper_name: Optional[str] = None
    summary: Optional[str] = None
    abstract: Optional[str] = None
    authors: Optional[Any] = None
    published: Optional[str] = None
    pdf_url: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None
    venue: Optional[str] = None
    why_chosen: Optional[str] = None
    key_contribution: Optional[str] = None
    citations: Optional[int] = None
    citation_count: Optional[int] = None
    doi: Optional[str] = None


class AnalysisRequest(BaseModel):
    paper_name: Optional[str] = None
    paper_names: Optional[List[str]] = None
    papers: Optional[List[AnalysisPaper]] = None
    query: Optional[str] = None
    analysis_type: Optional[str] = "summary"
    session_id: Optional[str] = None


class WorkspaceRequest(BaseModel):
    topic: str
    session_id: str
    papers: List[AnalysisPaper]


def save_agent_result(
    session_id: Optional[str],
    analysis_type: Optional[str],
    results,
    topic: Optional[str] = None,
    papers: Optional[List[Any]] = None,
):
    """Save completed agent result to the research workspace with full session metadata."""

    if not session_id or not analysis_type:
        return

    now = datetime.now(timezone.utc)
    update_doc: dict = {
        f"agent_results.{analysis_type}": results,
        "updated_at": now,
        "status": "Completed",
    }
    if topic:
        update_doc["topic"] = topic
    if papers:
        update_doc["papers"] = [
            p.dict() if hasattr(p, "dict") else (p if isinstance(p, dict) else dict(p))
            for p in papers
        ]

    research_sessions_collection.update_one(
        {"session_id": session_id},
        {
            "$set": update_doc,
            "$setOnInsert": {
                "created_at": now,
                "session_id": session_id,
            },
        },
        upsert=True,
    )


from app.agents.summarizer import run_summary_agent, summarize_paper
from app.agents.research_gap import run_gap_agent, analyze_research_gap
from app.agents.literature_agent import run_literature_agent, generate_literature_survey
from app.agents.novelty_agent import run_novelty_agent, analyze_novelty
from app.agents.dataset_agent import run_dataset_agent, recommend_datasets
from app.agents.experiment_agent import run_experiment_agent, plan_experiments
from app.agents.comparison_agent import run_comparison_agent, compare_papers


@router.post("/run")
async def run_paper_analysis(request: AnalysisRequest):
    try:
        a_type = (request.analysis_type or "summary").lower()
        topic = request.query or "Academic Research Topic"

        # --------------------------------------------
        # MULTIPLE SELECTED PAPERS (WORKSPACE MODE)
        # --------------------------------------------
        if request.papers and len(request.papers) > 0:
            if topic and topic.strip() and topic.lower() != "academic research topic":
                try:
                    from app.search.paper_search_service import correct_query_spelling
                    corrected_query = await correct_query_spelling(topic)
                    if corrected_query and len(corrected_query.strip()) > 2:
                        topic = corrected_query.strip()
                except Exception as e:
                    print(f"[Workspace Auto-Correct Error]: {e}")

            if a_type in ("summary", "executive_summary"):
                paper_results = run_summary_agent(topic=topic, papers=request.papers)
            elif a_type in ("gaps", "research_gap", "gap"):
                paper_results = run_gap_agent(topic=topic, papers=request.papers)
            elif a_type in ("literature", "literature_survey"):
                paper_results = run_literature_agent(topic=topic, papers=request.papers)
            elif a_type in ("novelty", "novelty_analysis"):
                paper_results = run_novelty_agent(topic=topic, papers=request.papers)
            elif a_type in ("datasets", "dataset", "dataset_recommendation"):
                paper_results = run_dataset_agent(topic=topic, papers=request.papers)
            elif a_type in ("experiments", "experiment", "experiment_recommendation"):
                paper_results = run_experiment_agent(topic=topic, papers=request.papers)
            elif a_type in ("comparison", "compare"):
                comp_result = run_comparison_agent(topic=topic, papers=request.papers)
                paper_results = [{"paper_name": "Comparative Analysis", "result": comp_result}]
            else:
                paper_results = run_summary_agent(topic=topic, papers=request.papers)

            # Format the output clean while preserving markdown/tables
            for item in paper_results:
                if isinstance(item, dict) and "result" in item:
                    item["result"] = format_clean_analysis_output(item["result"])

            save_agent_result(
                session_id=request.session_id,
                analysis_type=request.analysis_type,
                results=paper_results,
                topic=topic,
                papers=request.papers,
            )

            return {
                "status": "success",
                "analysis_type": request.analysis_type,
                "total_papers": len(request.papers),
                "results": paper_results,
                "data": paper_results,
                "result": paper_results[0]["result"] if len(paper_results) == 1 else None,
                "interpreted_query": topic,
            }

        # --------------------------------------------
        # MULTIPLE SELECTED PAPERS (NAMES ONLY)
        # --------------------------------------------
        if request.paper_names and len(request.paper_names) > 0:
            converted_papers = [
                AnalysisPaper(title=name)
                for name in request.paper_names
            ]
            return await run_paper_analysis(
                AnalysisRequest(
                    papers=converted_papers,
                    query=request.query,
                    analysis_type=request.analysis_type,
                    session_id=request.session_id,
                )
            )

        # --------------------------------------------
        # SINGLE PAPER / QUERY
        # --------------------------------------------
        raw_result = run_agent(
            query=request.query or request.analysis_type or "summary",
            paper_name=request.paper_name,
            analysis_type=request.analysis_type,
        )

        clean_result = format_clean_analysis_output(raw_result)

        save_agent_result(
            session_id=request.session_id,
            analysis_type=request.analysis_type,
            results=clean_result,
        )

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
            detail=str(e),
        )


@router.post("/workspace")
async def create_workspace(request: WorkspaceRequest):
    try:
        agents = run_workspace(
            topic=request.topic,
            session_id=request.session_id,
            papers=request.papers,
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
            detail=str(e),
        )


# ==========================================================
# Run All Agents in Workspace
# ==========================================================
@router.post("/workspace/run-all")
async def run_all_workspace_agents(request: WorkspaceRequest):
    """
    Execute all 7 research agents concurrently/sequentially for the workspace session,
    persist all structured outputs in MongoDB, and return complete results.
    """
    try:
        original_topic = request.topic or "Academic Research Topic"
        topic = original_topic
        session_id = request.session_id
        papers = request.papers

        # Auto-interpret and correct spelling errors/typos in the research query within AI Workspace
        if topic and topic.strip() and topic.lower() != "academic research topic":
            try:
                from app.search.paper_search_service import correct_query_spelling
                corrected_topic = await correct_query_spelling(topic)
                if corrected_topic and len(corrected_topic.strip()) > 2:
                    topic = corrected_topic.strip()
                    print(f"\n[ResearchX Workspace Auto-Correct] Interpreted '{original_topic}' -> '{topic}'")
            except Exception as qc_err:
                print(f"[ResearchX Workspace Auto-Correct Error]: {qc_err}")

        print(f"\n[ResearchX Workspace] Running ALL 7 agents concurrently for session: {session_id}, Topic: '{topic}', Papers: {len(papers)}")

        timer = PerformanceTimer(f"workspace_run_all[{session_id}]")
        timer.start("workspace_run_all")

        agent_results = {}

        def _run_summary():
            try:
                res = run_summary_agent(topic=topic, papers=papers)
                for item in res:
                    item["result"] = format_clean_analysis_output(item.get("result", ""))
                return "summary", res
            except Exception as e:
                print(f"[Run-All Summary Error]: {e}")
                return "summary", [{"paper_name": "Summary", "result": "Unable to generate summary."}]

        def _run_literature():
            try:
                res = run_literature_agent(topic=topic, papers=papers)
                for item in res:
                    item["result"] = format_clean_analysis_output(item.get("result", ""))
                return "literature", res
            except Exception as e:
                print(f"[Run-All Literature Error]: {e}")
                return "literature", [{"paper_name": "Literature Survey", "result": "Unable to generate literature survey."}]

        def _run_gaps():
            try:
                res = run_gap_agent(topic=topic, papers=papers)
                for item in res:
                    item["result"] = format_clean_analysis_output(item.get("result", ""))
                return "gaps", res
            except Exception as e:
                print(f"[Run-All Gap Error]: {e}")
                return "gaps", [{"paper_name": "Research Gaps", "result": "Unable to generate gap analysis."}]

        def _run_novelty():
            try:
                res = run_novelty_agent(topic=topic, papers=papers)
                for item in res:
                    item["result"] = format_clean_analysis_output(item.get("result", ""))
                return "novelty", res
            except Exception as e:
                print(f"[Run-All Novelty Error]: {e}")
                return "novelty", [{"paper_name": "Novelty Analysis", "result": "Unable to generate novelty analysis."}]

        def _run_datasets():
            try:
                res = run_dataset_agent(topic=topic, papers=papers)
                for item in res:
                    item["result"] = format_clean_analysis_output(item.get("result", ""))
                return "datasets", res
            except Exception as e:
                print(f"[Run-All Dataset Error]: {e}")
                return "datasets", [{"paper_name": "Dataset Recommendation", "result": "Unable to generate dataset recommendation."}]

        def _run_experiments():
            try:
                res = run_experiment_agent(topic=topic, papers=papers)
                for item in res:
                    item["result"] = format_clean_analysis_output(item.get("result", ""))
                return "experiments", res
            except Exception as e:
                print(f"[Run-All Experiment Error]: {e}")
                return "experiments", [{"paper_name": "Experiment Recommendation", "result": "Unable to generate experiment protocol."}]

        def _run_comparison():
            try:
                comp_res = run_comparison_agent(topic=topic, papers=papers)
                comp_clean = format_clean_analysis_output(comp_res)
                return "comparison", [{"paper_name": "Comparative Analysis", "result": comp_clean}]
            except Exception as e:
                print(f"[Run-All Comparison Error]: {e}")
                return "comparison", [{"paper_name": "Comparative Analysis", "result": "Unable to compare papers."}]

        # Execute all 7 agents concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
            task_futures = [
                executor.submit(_run_summary),
                executor.submit(_run_literature),
                executor.submit(_run_gaps),
                executor.submit(_run_novelty),
                executor.submit(_run_datasets),
                executor.submit(_run_experiments),
                executor.submit(_run_comparison),
            ]
            for fut in concurrent.futures.as_completed(task_futures):
                agent_name, agent_val = fut.result()
                agent_results[agent_name] = agent_val

        timer.stop("workspace_run_all")
        timer.print_summary()

        # Persist full results to MongoDB session
        updated_agents = [
            {"agent": name, "status": "Completed", "progress": 100}
            for name in [
                "Summary",
                "Research Gap",
                "Dataset Recommendation",
                "Experiment Recommendation",
                "Literature Survey",
                "Novelty Analysis",
                "Comparison",
            ]
        ]

        now = datetime.now(timezone.utc)
        serialized_papers = [
            p.dict() if hasattr(p, "dict") else (p if isinstance(p, dict) else dict(p))
            for p in papers
        ] if papers else []

        try:
            research_sessions_collection.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "session_id": session_id,
                        "topic": topic,
                        "papers": serialized_papers,
                        "status": "Completed",
                        "agents": updated_agents,
                        "agent_results": agent_results,
                        "updated_at": now,
                    },
                    "$setOnInsert": {
                        "created_at": now,
                    },
                },
                upsert=True,
            )
        except Exception as db_err:
            print(f"[DB Update Error in run-all]: {db_err}")

        return {
            "status": "success",
            "message": "All research agents executed successfully",
            "session_id": session_id,
            "topic": topic,
            "interpreted_query": topic,
            "original_query": original_topic,
            "agents": updated_agents,
            "agent_results": agent_results,
        }

    except Exception as e:
        print(f"Run-all workspace error: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# ==========================
# Restore Research Workspace
# ==========================
@router.get("/workspace/{session_id}")
async def get_workspace(session_id: str):
    try:
        session = research_sessions_collection.find_one(
            {"session_id": session_id},
            {"_id": 0},
        )

        if not session:
            raise HTTPException(
                status_code=404,
                detail="Research workspace not found",
            )

        if session.get("created_at") and hasattr(session["created_at"], "isoformat"):
            session["created_at"] = session["created_at"].isoformat()
        if session.get("updated_at") and hasattr(session["updated_at"], "isoformat"):
            session["updated_at"] = session["updated_at"].isoformat()

        return {
            "success": True,
            "session_id": session.get("session_id"),
            "topic": session.get("topic", ""),
            "papers": session.get("papers", []),
            "agents": session.get("agents", []),
            "agent_results": session.get("agent_results", {}),
            "status": session.get("status", "Created"),
            "created_at": session.get("created_at"),
            "updated_at": session.get("updated_at"),
        }

    except HTTPException:
        raise

    except Exception as e:
        print(f"Workspace restore error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restore workspace: {str(e)}",
        )


# ==========================
# Delete Research Workspace Session
# ==========================
@router.delete("/workspace/{session_id}")
async def delete_workspace(session_id: str):
    try:
        research_sessions_collection.delete_one({"session_id": session_id})
        papers_collection.delete_many({"session_id": session_id})
        return {
            "success": True,
            "message": "Research workspace session deleted successfully",
            "session_id": session_id,
        }
    except Exception as e:
        print(f"Workspace delete error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete workspace: {str(e)}",
        )


@router.get("/recent")
async def get_recent_research():
    try:
        sessions = list(
            research_sessions_collection.find(
                {},
                {"_id": 0},
            )
            .sort([("updated_at", -1), ("created_at", -1)])
            .limit(50)
        )

        for session in sessions:
            if session.get("created_at") and hasattr(session["created_at"], "isoformat"):
                session["created_at"] = session["created_at"].isoformat()
            if session.get("updated_at") and hasattr(session["updated_at"], "isoformat"):
                session["updated_at"] = session["updated_at"].isoformat()

        return {
            "status": "success",
            "data": sessions,
        }

    except Exception as e:
        print(f"Recent research error: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# ==========================================================
# LangGraph Workspace
# ==========================================================
@router.post("/workspace/run-graph")
async def run_workspace_graph(request: WorkspaceRequest):
    try:
        print("\n[ResearchX] Starting LangGraph Workspace...")

        initial_state = {
            "topic": request.topic,
            "papers": request.papers,
            "status": "Running",
        }

        result = research_graph.invoke(initial_state)

        print("[ResearchX] LangGraph Workspace Completed.")

        return {
            "status": "success",
            "topic": request.topic,
            "final_status": result.get("status"),
            "rag_context": result.get("rag_context", ""),
            "summary": result.get("summary"),
            "research_gap": result.get("research_gap"),
            "literature": result.get("literature"),
            "novelty": result.get("novelty"),
            "datasets": result.get("datasets"),
            "experiments": result.get("experiments"),
            "comparison": result.get("comparison"),
            "final_report": result.get("final_report"),
        }

    except Exception as e:
        print(f"[ResearchX] LangGraph Workspace Error: {e}")

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )