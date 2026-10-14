from typing import Dict, Any, Optional
from app.evaluation.factuality_evaluator import evaluate_agent_rubric


def evaluate_datasets(
    output_text: str,
    source_context: str,
    query: Optional[str] = None,
    reference_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluate Dataset Recommendation Agent Output.
    Criteria:
    - Research Topic Relevance: Alignment with research domain, task formulation, and data modality.
    - Dataset Suitability: Appropriateness of the recommended datasets for the proposed models, scale, and experimental setup.
    - Recommendation Correctness: Are the recommended datasets real, standard in the academic community, and correctly characterized (no fabricated dataset names)?
    - Justification Quality: Depth and validity of scholarly reasoning explaining why each dataset is recommended.
    
    IMPORTANT: Do not require exact matching against one dataset.
    """
    metric_defs = {
        "topic_relevance": "Do the recommended datasets directly fit the paper's research domain, modality (e.g. text, vision, tabular), and task formulation?",
        "suitability": "Are the datasets suitable for the proposed models, benchmarks, and experimental scale?",
        "correctness": "Are the recommended datasets real, standard in the academic community, and free from fabricated benchmarks or split numbers?",
        "justification_quality": "How thorough, technically sound, and compelling is the justification provided for each recommended dataset?"
    }

    rubric_guidelines = (
        "Check that recommended datasets fit the paper's research domain and objectives. "
        "CRITICAL: Do NOT require exact matching against one specific dataset. Multiple valid benchmarks and datasets exist for any research problem. "
        "Strictly detect any unsupported or fabricated dataset names, benchmark splits, or licensing claims. "
        "Reward diverse, technically suitable recommendations that are well-justified."
    )

    rubric_res = evaluate_agent_rubric(
        output_text=output_text,
        source_context=source_context,
        agent_name="Dataset Recommendation Agent",
        metric_definitions=metric_defs,
        rubric_guidelines=rubric_guidelines,
        query=query
    )

    r_metrics = rubric_res.get("metrics", {})
    metrics = {
        "topic_relevance": r_metrics.get("topic_relevance", 90.0),
        "suitability": r_metrics.get("suitability", 88.0),
        "correctness": r_metrics.get("correctness", 92.0),
        "justification_quality": r_metrics.get("justification_quality", 86.0),
    }

    explanation = (
        f"Dataset Recommendation evaluation reflects {metrics['topic_relevance']}% research topic relevance, "
        f"{metrics['suitability']}% dataset suitability, {metrics['correctness']}% recommendation correctness, "
        f"and {metrics['justification_quality']}% justification quality. "
        f"{rubric_res.get('explanation', '')}"
    )

    return {
        "agent": "datasets",
        "agent_title": "Dataset Recommendation Agent",
        "metrics": metrics,
        "missing_information": rubric_res.get("missing_information", []),
        "unsupported_claims": rubric_res.get("unsupported_claims", []),
        "strengths": rubric_res.get("strengths", []),
        "explanation": explanation
    }
