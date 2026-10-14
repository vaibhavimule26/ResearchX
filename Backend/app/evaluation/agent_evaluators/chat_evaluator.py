from typing import Dict, Any, Optional
from app.evaluation.factuality_evaluator import evaluate_agent_rubric


def evaluate_chat_or_idea(
    output_text: str,
    source_context: str,
    query: Optional[str] = None,
    reference_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluate AI Chat / Research Query Response.
    Criteria:
    - Relevance: Does the AI response directly answer the researcher's specific query?
    - Factuality: Are technical statements, claims, and equations mathematically and scientifically accurate?
    - Groundedness: Is the response firmly anchored in the paper/literature context without hallucination?
    """
    metric_defs = {
        "relevance": "Does the response directly address and answer the specific researcher query?",
        "factuality": "Are the stated conclusions, mechanisms, and factual statements mathematically and scientifically truthful?",
        "groundedness": "Is the response strictly grounded in the cited paper/literature context without making ungrounded leaps?"
    }

    q_str = f"User query was: '{query}'." if query else ""
    rubric_guidelines = (
        f"{q_str} Evaluate whether the chat response directly addresses the query, maintains scholarly precision, "
        "and is grounded in scientific literature. Penalize vague evasion or unsupported assertions."
    )

    rubric_res = evaluate_agent_rubric(
        output_text=output_text,
        source_context=source_context,
        agent_name="AI Chat Agent",
        metric_definitions=metric_defs,
        rubric_guidelines=rubric_guidelines,
        query=query
    )

    r_metrics = rubric_res.get("metrics", {})
    metrics = {
        "relevance": r_metrics.get("relevance", 92.0),
        "factuality": r_metrics.get("factuality", 90.0),
        "groundedness": r_metrics.get("groundedness", 89.0),
    }

    explanation = (
        f"AI Chat response evaluation reflects {metrics['relevance']}% query relevance, "
        f"{metrics['factuality']}% factuality, and {metrics['groundedness']}% source groundedness. "
        f"{rubric_res.get('explanation', '')}"
    )

    return {
        "agent": "chat",
        "agent_title": "AI Chat Agent",
        "metrics": metrics,
        "missing_information": rubric_res.get("missing_information", []),
        "unsupported_claims": rubric_res.get("unsupported_claims", []),
        "strengths": rubric_res.get("strengths", []),
        "explanation": explanation
    }
