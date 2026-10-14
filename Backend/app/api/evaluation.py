from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.utils.response import success_response, error_response
from app.evaluation.evaluator import (
    evaluate_agent_output,
    record_human_validation,
    get_agent_evaluation_history,
)

router = APIRouter(prefix="/api/evaluation", tags=["Evaluation"])


class EvaluationRequest(BaseModel):
    output_text: str = Field(..., description="The generated agent output to evaluate")
    paper_name: Optional[str] = Field(None, description="The paper file name or title")
    context: Optional[str] = Field(None, description="The source paper text or context")
    query: Optional[str] = Field(None, description="The user query or agent query")
    reference_text: Optional[str] = Field(None, description="Optional ground-truth reference text")
    user_id: Optional[str] = Field(None, description="User ID triggering evaluation")
    papers: Optional[list] = Field(None, description="List of selected papers for multi-paper workspace evaluation")
    is_workspace: Optional[bool] = Field(None, description="Whether this evaluation is for the multi-paper AI Workspace")


class HumanValidationRequest(BaseModel):
    evaluation_id: str = Field(..., description="The ID of the evaluation to validate")
    verdict: str = Field(..., description="'Correct' | 'Partially Correct' | 'Incorrect'")
    feedback_notes: Optional[str] = Field(None, description="Optional feedback notes from researcher")
    user_id: Optional[str] = Field(None, description="Researcher user ID")


@router.post("/human-validation")
def submit_human_validation(payload: HumanValidationRequest):
    """Record human researcher feedback and validation verdict for an evaluation run."""
    if payload.verdict not in ["Correct", "Partially Correct", "Incorrect"]:
        raise HTTPException(status_code=400, detail="Verdict must be Correct, Partially Correct, or Incorrect")

    try:
        res = record_human_validation(
            evaluation_id=payload.evaluation_id,
            verdict=payload.verdict,
            feedback_notes=payload.feedback_notes,
            user_id=payload.user_id,
        )
        return success_response(
            message="Human validation submitted successfully",
            data=res
        )
    except Exception as e:
        return error_response(
            message=f"Failed to record human validation: {str(e)}",
            status_code=500
        )


@router.post("/{agent_name}")
def run_evaluation(agent_name: str, payload: EvaluationRequest):
    """
    On-Demand Evaluation for any ResearchX Agent output.
    Does NOT trigger automatically during normal generation.
    Evaluates using agent-specific rubrics, checks evidence grounding,
    detects hallucinations, and verifies multi-paper workspace synthesis.
    """
    if not payload.output_text or not payload.output_text.strip():
        raise HTTPException(status_code=400, detail="output_text is required for evaluation")

    result = evaluate_agent_output(
        agent_name=agent_name,
        output_text=payload.output_text,
        paper_name=payload.paper_name,
        context=payload.context,
        query=payload.query,
        reference_text=payload.reference_text,
        user_id=payload.user_id,
        papers=payload.papers,
        is_workspace=payload.is_workspace,
    )

    return success_response(
        message=f"{agent_name.capitalize()} evaluation completed successfully",
        data=result
    )



@router.get("/{agent_name}/history")
def get_evaluation_history(agent_name: str, limit: int = Query(10, ge=1, le=100)):
    """Retrieve historical evaluation runs for benchmark tracking and auditing."""
    try:
        records = get_agent_evaluation_history(agent_name=agent_name, limit=limit)
        return success_response(
            message=f"Retrieved {len(records)} evaluation records for {agent_name}",
            data=records
        )
    except Exception as e:
        return error_response(
            message=f"Failed to fetch evaluation history: {str(e)}",
            status_code=500
        )
