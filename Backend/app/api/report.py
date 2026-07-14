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
    prefix="/report",
    tags=["IEEE Report"],
)

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


class ReportRequest(BaseModel):
    paper_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )


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

        query = (
            "complete research paper "
            "methodology results "
            "datasets experiments "
            "literature contributions "
            "limitations future work"
        )

        embedding = model.encode(
            query
        ).tolist()

        results = collection.query(
            query_embeddings=[embedding],
            n_results=15,
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
                detail="Paper not found.",
            )

        context = "\n\n".join(documents)

        report = generate_final_report(context)
        

        return ReportResponse(
            success=True,
            message="IEEE Report generated successfully",
            paper_name=request.paper_name,
            result=report,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )