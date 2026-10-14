from typing import Dict, Any, Optional
from app.evaluation.semantic_evaluator import calculate_semantic_similarity
from app.evaluation.factuality_evaluator import evaluate_factuality_and_faithfulness


def evaluate_comparison(
    output_text: str,
    source_context: str,
    query: Optional[str] = None,
    reference_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluate Paper Comparison Agent Output.
    Criteria:
    - Cross-paper consistency
    - Metric correctness across benchmark comparisons
    - Dimension coverage (methodology, evaluation, limitations)
    - Factuality & fairness
    - Hallucinated comparative advantages
    - Semantic Similarity Score
    """
    comp_ref = reference_text or source_context
    sem_res = calculate_semantic_similarity(comp_ref, output_text)

    rubric = (
        "Check that comparative analysis directly compares methods on identical or equivalent benchmarks, "
        "correctly quotes performance numbers (accuracy, F1, latency, parameter count), and impartially "
        "lists trade-offs. Detect hallucinated advantages or false claims of superiority."
    )
    fact_res = evaluate_factuality_and_faithfulness(
        output_text=output_text,
        source_context=source_context,
        agent_name="Paper Comparison Agent",
        rubric_guidance=rubric
    )

    metrics = {
        "semantic_similarity": sem_res["semantic_similarity_percentage"],
        "metric_accuracy": fact_res["factuality_score"],
        "comparison_coverage": fact_res["coverage_score"],
        "cross_paper_consistency": fact_res["faithfulness_score"],
        "factuality": fact_res["factuality_score"],
    }

    explanation = (
        f"Comparative evaluation reveals {metrics['cross_paper_consistency']}% cross-paper consistency, "
        f"{metrics['metric_accuracy']}% metric accuracy with {metrics['comparison_coverage']}% dimension coverage. "
        f"{fact_res.get('explanation', '')}"
    )

    return {
        "agent": "comparison",
        "agent_title": "Paper Comparison Agent",
        "semantic_similarity_score": sem_res["semantic_similarity_score"],
        "semantic_similarity_percentage": sem_res["semantic_similarity_percentage"],
        "semantic_label": sem_res["label"],
        "metrics": metrics,
        "missing_information": fact_res.get("missing_information", []),
        "unsupported_claims": fact_res.get("unsupported_claims", []),
        "strengths": fact_res.get("strengths", []),
        "explanation": explanation
    }
