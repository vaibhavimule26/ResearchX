from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer

from app.database.chroma import collection
from app.agents.summarizer import summarize_paper
from app.agents.research_gap import find_research_gaps
from app.agents.dataset_agent import recommend_datasets
from app.agents.experiment_agent import recommend_experiments
from app.agents.literature_agent import generate_literature_survey
from app.agents.novelty_agent import analyze_novelty
from app.agents.report_agent import generate_final_report


router = APIRouter(
    prefix="/analysis",
    tags=["Analysis"],
)


# ==========================================================
# Load Embedding Model Once
# ==========================================================
model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


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
]


# ==========================================================
# Request Model
# ==========================================================
class AnalysisRequest(BaseModel):
    paper_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    analysis_type: AnalysisType


# ==========================================================
# Response Model
# ==========================================================
class AnalysisResponse(BaseModel):
    success: bool
    message: str
    paper_name: str
    analysis_type: AnalysisType
    result: str


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
        # --------------------------------------------------
        # Build retrieval query for selected analysis type
        # --------------------------------------------------
        retrieval_query = ANALYSIS_QUERIES[
            request.analysis_type
        ]

        # --------------------------------------------------
        # Generate query embedding
        # --------------------------------------------------
        query_embedding = model.encode(
            retrieval_query
        ).tolist()

        # --------------------------------------------------
        # Retrieve relevant chunks only from selected paper
        # --------------------------------------------------
        results = collection.query(
            query_embeddings=[
                query_embedding
            ],
            n_results=10,
            where={
                "paper_name": request.paper_name
            },
        )

        documents = (
            results.get("documents", [[]])[0]
        )

        # --------------------------------------------------
        # Validate retrieved context
        # --------------------------------------------------
        if not documents:
            raise HTTPException(
                status_code=404,
                detail=(
                    "No indexed content found for "
                    f"'{request.paper_name}'"
                ),
            )

        # --------------------------------------------------
        # Build real research paper context
        # --------------------------------------------------
        context = "\n\n".join(documents)

        # --------------------------------------------------
        # Select specialized AI agent
        # --------------------------------------------------
        handler = ANALYSIS_HANDLERS[
            request.analysis_type
        ]

        # --------------------------------------------------
        # Run specialized agent
        # --------------------------------------------------
        result = handler(context)

        # --------------------------------------------------
        # Validate AI result
        # --------------------------------------------------
        if not result:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Analysis returned an empty result"
                ),
            )

        # --------------------------------------------------
        # Return structured response
        # --------------------------------------------------
        return AnalysisResponse(
            success=True,
            message=(
                "Analysis completed successfully"
            ),
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