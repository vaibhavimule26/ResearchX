import traceback
from typing import List, Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer

from app.database.chroma import collection
from app.database.mongodb import (
    agent_outputs_collection,
    agent_runs_collection,
    research_sessions_collection,
)

# Agent imports
from app.agents.coordinator import run_agent
from app.agents.comparison_agent import (
    compare_papers,
    run_comparison_agent,
)
from app.agents.dataset_agent import (
    recommend_datasets,
    run_dataset_agent,
)
from app.agents.experiment_agent import (
    recommend_experiments,
    run_experiment_agent,
)
from app.agents.literature_agent import (
    generate_literature_survey,
    run_literature_survey_agent,
)
from app.agents.novelty_agent import (
    analyze_novelty,
    run_novelty_agent,
)
from app.agents.ppt_agent import (
    generate_presentation,
    run_ppt_agent,
)
from app.agents.report_agent import (
    generate_ieee_report,
    run_ieee_report_agent,
)
from app.agents.research_gap import (
    find_research_gaps,
    run_research_gap_agent,
)
from app.agents.summarizer import (
    run_summary_agent,
    summarize_paper,
)
from app.agents.workspace_coordinator import run_workspace
from app.services.retrieval_service import search_papers

router = APIRouter(
    prefix="/analysis",
    tags=["Analysis"],
)


# ==========================================================
# Load Embedding Model Once
# ==========================================================
model = SentenceTransformer("all-MiniLM-L6-v2")


# ==========================================================
# Supported Analysis Types
# ==========================================================
AnalysisType = Literal[
    "summary",
    "gaps",
    "datasets",
    "experiments",
    "literature",
    "novelty",
    "report",
    "ppt",
]


# ==========================================================
# Request Models
# ==========================================================
class AnalysisRequest(BaseModel):
    paper_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    analysis_type: AnalysisType


class SelectedPaper(BaseModel):
    title: str
    authors: List[str]
    summary: str
    published: str
    pdf_url: str


class WorkspaceRequest(BaseModel):
    topic: str
    papers: List[SelectedPaper]


class RunAgentRequest(BaseModel):
    session_id: str
    topic: str
    papers: List[SelectedPaper]
    agent: str


class SearchPaperRequest(BaseModel):
    topic: str


# ==========================================================
# Response Models
# ==========================================================
class AnalysisResponse(BaseModel):
    success: bool
    message: str
    paper_name: str
    analysis_type: AnalysisType
    result: str


class WorkspaceResponse(BaseModel):
    success: bool
    session_id: str
    topic: str
    message: str
    agents: list
    summary: str


class RunAgentResponse(BaseModel):
    success: bool
    agent: str
    result: str


class SearchPaperResponse(BaseModel):
    success: bool
    papers: list


# ==========================================================
# Analysis Queries
# ==========================================================
ANALYSIS_QUERIES = {
    "summary": (
        "main objective methodology key contributions "
        "results conclusion research paper summary"
    ),
    "gaps": (
        "research gaps limitations weaknesses "
        "future work challenges open problems"
    ),
    "datasets": (
        "datasets data sources benchmarks training data "
        "evaluation data experimental data"
    ),
    "experiments": (
        "experiments methodology evaluation setup "
        "metrics baselines implementation results"
    ),
    "literature": (
        "related work literature review prior studies "
        "existing methods previous research"
    ),
    "novelty": (
        "novelty innovation original contribution "
        "unique method new approach contributions"
    ),
    "report": (
        "complete research paper methodology results "
        "datasets experiments literature contributions "
        "limitations future work"
    ),
    "ppt": (
        "complete research paper abstract methodology "
        "results datasets experiments conclusion "
        "contributions"
    ),
}


# ==========================================================
# Agent Handlers
# ==========================================================
ANALYSIS_HANDLERS = {
    "summary": summarize_paper,
    "gaps": find_research_gaps,
    "datasets": recommend_datasets,
    "experiments": recommend_experiments,
    "literature": generate_literature_survey,
    "novelty": analyze_novelty,
    "ppt": generate_presentation,
    "report": generate_ieee_report,
}


WORKSPACE_AGENT_HANDLERS = {
    "Summary": run_summary_agent,
    "Research Gap": run_research_gap_agent,
    "Dataset Recommendation": run_dataset_agent,
    "Experiment Recommendation": run_experiment_agent,
    "Literature Survey": run_literature_survey_agent,
    "Novelty Analysis": run_novelty_agent,
    "Comparison": run_comparison_agent,
    "IEEE Report": run_ieee_report_agent,
    "PPT Generator": run_ppt_agent,
}


# ==========================================================
# Run Intelligent Coordinator Analysis
# ==========================================================
@router.post(
    "/run",
    response_model=AnalysisResponse,
)
def run_analysis(
    request: AnalysisRequest,
):
    try:

        # --------------------------------------------------
        # Retrieve paper context from ChromaDB
        # --------------------------------------------------

        retrieval_query = ANALYSIS_QUERIES[request.analysis_type]

        query_embedding = model.encode(
            retrieval_query
        ).tolist()

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=10,
            where={
                "paper_name": request.paper_name
            },
        )

        documents = results.get(
            "documents",
            [[]],
        )[0]

        if not documents:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"No indexed content found for "
                    f"'{request.paper_name}'"
                ),
            )

        context = "\n\n".join(documents)

        # --------------------------------------------------
        # Convert frontend analysis type into a natural
        # language query for the Coordinator
        # --------------------------------------------------

        coordinator_queries = {
            "summary": (
                "Summarize this research paper "
                "and explain its main objective, "
                "methodology, contributions, results, "
                "and conclusion."
            ),

            "gaps": (
                "Analyze this research paper and identify "
                "research gaps, limitations, weaknesses, "
                "future work, and open research problems."
            ),

            "datasets": (
                "Analyze this research paper and recommend "
                "suitable datasets for reproducing, "
                "validating, or extending the research."
            ),

            "experiments": (
                "Analyze this research paper and recommend "
                "appropriate experiments, methodology, "
                "baselines, evaluation metrics, and "
                "experimental setup."
            ),

            "literature": (
                "Generate a detailed literature survey "
                "for this research paper including existing "
                "work, limitations, research gaps, and "
                "future directions."
            ),

            "novelty": (
                "Analyze the novelty, originality, "
                "contributions, strengths, weaknesses, "
                "and research differentiation of this paper."
            ),

            "report": (
                "Perform a complete analysis of this "
                "research paper and generate a comprehensive "
                "research report."
            ),

            "ppt": (
                "Perform a complete analysis of this "
                "research paper to prepare research "
                "presentation content."
            ),
        }

        coordinator_query = coordinator_queries.get(
            request.analysis_type
        )

        if not coordinator_query:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unsupported analysis type: "
                    f"{request.analysis_type}"
                ),
            )

        # --------------------------------------------------
        # Run Intelligent Coordinator
        # --------------------------------------------------

        result = run_agent(
            query=coordinator_query,
            context=context,
        )

        if not result:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Coordinator returned an empty result."
                ),
            )

        # --------------------------------------------------
        # Convert Coordinator result into frontend-friendly
        # response
        # --------------------------------------------------

        if isinstance(result, dict):

            # Complete analysis returns the final report
            if request.analysis_type == "report":
                final_result = result

            # Other workflows return structured results
            else:
                final_result = result

        else:
            final_result = result

        # --------------------------------------------------
        # Store summary execution statistics
        # --------------------------------------------------

        if request.analysis_type == "summary":
            agent_runs_collection.update_one(
                {},
                {
                    "$inc": {
                        "summary": 1
                    }
                },
                upsert=True,
            )

        return AnalysisResponse(
            success=True,
            message=(
                "Coordinator analysis completed successfully"
            ),
            paper_name=request.paper_name,
            analysis_type=request.analysis_type,
            result=(
                final_result
                if isinstance(final_result, str)
                else str(final_result)
            ),
        )

    except HTTPException:
        raise

    except Exception as exc:

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Coordinator analysis failed: {str(exc)}"
            ),
        ) from exc


# ==========================================================
# Paper Search Endpoint
# ==========================================================
@router.post("/search-papers", response_model=SearchPaperResponse)
def search_workspace_papers(request: SearchPaperRequest):
    try:
        papers = search_papers(request.topic)

        return SearchPaperResponse(
            success=True,
            papers=papers
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Paper search failed: {str(e)}"
        )


# ==========================================================
# Run Multi-Agent Workspace Analysis
# ==========================================================
@router.post(
    "/workspace",
    response_model=WorkspaceResponse,
)
def run_workspace_analysis(request: WorkspaceRequest):
    try:
        session_id = str(uuid4())

        agents = run_workspace(
            request.topic,
            session_id,
            request.papers,
        )

        return WorkspaceResponse(
            success=True,
            session_id=session_id,
            topic=request.topic,
            message="Research session created successfully.",
            agents=agents,
            summary="",
        )

    except Exception as e:
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# ==========================================================
# Get Recent Workspace Research Sessions
# ==========================================================
@router.get("/recent")
def get_recent_research():
    try:
        sessions = list(
            research_sessions_collection.find({}, {"_id": 0})
            .sort("created_at", -1)
            .limit(10)
        )
        return sessions
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch recent research: {str(exc)}",
        )


# ==========================================================
# Restore Workspace Session
# ==========================================================
@router.get("/workspace/{session_id}")
def get_workspace(session_id: str):
    try:
        session = research_sessions_collection.find_one(
            {"session_id": session_id},
            {"_id": 0},
        )

        if not session:
            raise HTTPException(
                status_code=404,
                detail="Workspace not found.",
            )

        outputs = list(
            agent_outputs_collection.find(
                {"session_id": session_id},
                {"_id": 0},
            )
        )

        agent_results = {
            output["agent"]: output["result"]
            for output in outputs
        }

        return {
            "success": True,
            "session_id": session["session_id"],
            "topic": session["topic"],
            "papers": session.get("papers", []),
            "agents": session.get("agents", []),
            "agent_results": agent_results,
        }

    except HTTPException:
        raise

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# ==========================================================
# Run Single Agent Endpoint
# ==========================================================
@router.post(
    "/run-agent",
    response_model=RunAgentResponse,
)
def run_single_agent(request: RunAgentRequest):
    try:
        handler = WORKSPACE_AGENT_HANDLERS.get(request.agent)

        if handler is None:
            raise HTTPException(
                status_code=400,
                detail=f"{request.agent} agent not implemented.",
            )

        result = handler(
            request.topic,
            request.papers,
        )

        agent_outputs_collection.insert_one(
            {
                "session_id": request.session_id,
                "agent": request.agent,
                "result": result,
            }
        )

        return RunAgentResponse(
            success=True,
            agent=request.agent,
            result=result,
        )

    except HTTPException:
        raise

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )