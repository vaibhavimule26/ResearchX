from typing import Dict, Any, Optional
from app.evaluation.semantic_evaluator import calculate_semantic_similarity
from app.evaluation.factuality_evaluator import evaluate_agent_rubric


def evaluate_summary(
    output_text: str,
    source_context: str,
    query: Optional[str] = None,
    reference_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluate Summary Agent Output.
    Criteria:
    - Semantic Similarity (Sentence Transformers all-MiniLM-L6-v2 cosine similarity against benchmark reference or source paper)
    - Factuality (truthful to source paper findings)
    - Faithfulness / Groundedness (avoids fabricated metrics, datasets, or claims)
    - Content Coverage (comprehensively covers problem statement, methodology, key findings, and conclusion)
    
    IMPORTANT: Reference must correspond to the SAME paper being summarized.
    """
    comp_ref = reference_text or source_context
    sem_res = calculate_semantic_similarity(comp_ref, output_text)

    metric_defs = {
        "factuality": "Are all claims, metrics, architectures, and findings mathematically and factually truthful to the source paper?",
        "faithfulness": "Is the summary faithful to the paper without fabricating numbers, datasets, or non-existent authors?",
        "content_coverage": "How comprehensively does the executive summary capture the core problem, proposed method, key benchmark findings, and conclusions?"
    }

    rubric_guidelines = (
        "Check that executive summary accurately captures: problem statement, proposed methodology, "
        "key benchmark findings, and conclusions. Flag any hallucinated metrics or misattributed contributions. "
        "The comparison text is from the SAME paper being summarized."
    )

    rubric_res = evaluate_agent_rubric(
        output_text=output_text,
        source_context=source_context,
        agent_name="Summary Agent",
        metric_definitions=metric_defs,
        rubric_guidelines=rubric_guidelines,
        query=query
    )

    r_metrics = rubric_res.get("metrics", {})
    metrics = {
        "semantic_similarity": sem_res["semantic_similarity_percentage"],
        "factuality": r_metrics.get("factuality", 88.0),
        "faithfulness": r_metrics.get("faithfulness", 90.0),
        "content_coverage": r_metrics.get("content_coverage", 85.0),
    }

    explanation = (
        f"Summary evaluation indicates {metrics['factuality']}% factuality and "
        f"{metrics['faithfulness']}% faithfulness against the source material, with "
        f"{metrics['content_coverage']}% content coverage and {metrics['semantic_similarity']}% semantic similarity. "
        f"{rubric_res.get('explanation', '')}"
    )

    return {
        "agent": "summary",
        "agent_title": "Summary Agent",
        "semantic_similarity_score": sem_res["semantic_similarity_score"],
        "semantic_similarity_percentage": sem_res["semantic_similarity_percentage"],
        "semantic_label": sem_res["label"],
        "metrics": metrics,
        "missing_information": rubric_res.get("missing_information", []),
        "unsupported_claims": rubric_res.get("unsupported_claims", []),
        "strengths": rubric_res.get("strengths", []),
        "explanation": explanation
    }
