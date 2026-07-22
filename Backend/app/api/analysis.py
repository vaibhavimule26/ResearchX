import traceback
from typing import Literal, List
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer

from app.database.chroma import collection
from app.database.mongodb import (
    research_sessions_collection,
    agent_runs_collection,
    agent_outputs_collection,
)

# Agent imports
from app.agents.summarizer import (
    summarize_paper,
    run_summary_agent,
)
from app.agents.research_gap import (
    find_research_gaps,
    run_research_gap_agent,
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
from app.agents.comparison_agent import (
    compare_papers,
    run_comparison_agent,
)
from app.agents.ppt_agent import (
    generate_presentation,
    run_ppt_agent,
)
from app.agents.report_agent import (
    generate_ieee_report,
    run_ieee_report_agent,
)
from app.agents.workspace_coordinator import run_workspace
from app.services.arxiv_service import search_papers


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
# Run Structured Paper Analysis
# ==========================================================
@router.post(
    "/run",
    response_model=AnalysisResponse,
)
def run_analysis(
    request: AnalysisRequest,
):
    try:
        retrieval_query = ANALYSIS_QUERIES[request.analysis_type]

        query_embedding = model.encode(retrieval_query).tolist()

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=10,
            where={"paper_name": request.paper_name},
        )

        documents = results.get(
            "documents",
            [[]],
        )[0]

        if not documents:
            raise HTTPException(
                status_code=404,
                detail=f"No indexed content found for '{request.paper_name}'",
            )

        context = "\n\n".join(documents)

        handler = ANALYSIS_HANDLERS.get(request.analysis_type)
        if not handler:
            raise HTTPException(
                status_code=400,
                detail=f"Handler for analysis type '{request.analysis_type}' is currently not implemented.",
            )

        result = handler(context)

        if not result:
            raise HTTPException(
                status_code=500,
                detail="Analysis returned an empty result",
            )

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
            message="Analysis completed successfully",
            paper_name=request.paper_name,
            analysis_type=request.analysis_type,
            result=result,
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(exc)}",
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