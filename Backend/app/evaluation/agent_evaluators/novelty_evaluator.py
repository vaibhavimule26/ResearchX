from typing import Dict, Any, Optional
from app.evaluation.semantic_evaluator import calculate_semantic_similarity
from app.evaluation.factuality_evaluator import evaluate_factuality_and_faithfulness


def evaluate_novelty(
    output_text: str,
    source_context: str,
    query: Optional[str] = None,
    reference_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluate Novelty Analysis Agent Output.
    Criteria:
    - Literature evidence & grounding
    - Claim verification (real novelty vs existing standard techniques)
    - Factual consistency with source paper
    - Unsupported novelty claims / exaggeration
    - Semantic Similarity Score
    """
    comp_ref = reference_text or source_context
    sem_res = calculate_semantic_similarity(comp_ref, output_text)

    rubric = (
        "Check that novelty assessment accurately isolates the genuine conceptual, architectural, "
        "or algorithmic contributions of the work. Detect overclaimed novelty (attributing standard "
        "techniques as novel inventions) or failure to acknowledge prior art limitations."
    )
    fact_res = evaluate_factuality_and_faithfulness(
        output_text=output_text,
        source_context=source_context,
        agent_name="Novelty Analysis Agent",
        rubric_guidance=rubric
    )

    metrics = {
        "semantic_similarity": sem_res["semantic_similarity_percentage"],
        "novelty_validation": fact_res["faithfulness_score"],
        "literature_grounding": fact_res["factuality_score"],
        "contribution_coverage": fact_res["coverage_score"],
        "claim_factuality": fact_res["factuality_score"],
    }

    explanation = (
        f"Novelty analysis demonstrates {metrics['novelty_validation']}% novelty validation rigor "
        f"and {metrics['contribution_coverage']}% contribution coverage. "
        f"{fact_res.get('explanation', '')}"
    )

    return {
        "agent": "novelty",
        "agent_title": "Novelty Analysis Agent",
        "semantic_similarity_score": sem_res["semantic_similarity_score"],
        "semantic_similarity_percentage": sem_res["semantic_similarity_percentage"],
        "semantic_label": sem_res["label"],
        "metrics": metrics,
        "missing_information": fact_res.get("missing_information", []),
        "unsupported_claims": fact_res.get("unsupported_claims", []),
        "strengths": fact_res.get("strengths", []),
        "explanation": explanation
    }
