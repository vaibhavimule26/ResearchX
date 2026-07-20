from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer

from app.database.chroma import collection
from app.database.mongodb import (
    research_sessions_collection,
    agent_runs_collection,
)

from app.agents.summarizer import summarize_paper
from app.agents.research_gap import find_research_gaps
from app.agents.dataset_agent import recommend_datasets
from app.agents.experiment_agent import recommend_experiments
from app.agents.literature_agent import generate_literature_survey
from app.agents.novelty_agent import analyze_novelty
from app.agents.report_agent import generate_final_report
from app.agents.ppt_agent import generate_presentation
from app.agents.workspace_coordinator import run_workspace


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


class WorkspaceRequest(BaseModel):
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
    "report": generate_final_report,
    "ppt": generate_presentation,
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

        handler = ANALYSIS_HANDLERS[request.analysis_type]

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
        )

        return WorkspaceResponse(
            success=True,
            session_id=session_id,
            topic=request.topic,
            message="Research session started successfully.",
            agents=agents,
        )

    except Exception as e:
        import traceback

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