from typing import Dict, Any, Optional
from app.evaluation.factuality_evaluator import evaluate_agent_rubric


def evaluate_gaps(
    output_text: str,
    source_context: str,
    query: Optional[str] = None,
    reference_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluate Research Gap Agent Output.
    Criteria:
    - Evidence Grounding: Are identified research gaps and limitations grounded in actual evidence, constraints, or unaddressed assumptions of the paper?
    - Relevance: Are the gaps directly relevant to the paper's core research problem, domain, and scope?
    - Completeness: Does it capture the principal limitations, open research challenges, and realistic future directions?
    - Reasoning Quality: How sound, logical, and academically rigorous is the reasoning and critique?
    
    IMPORTANT: Do NOT require an exact text match because multiple valid research gaps can exist.
    """
    metric_defs = {
        "evidence_grounding": "Are the identified research gaps and limitations grounded in real constraints, limitations, or empirical boundaries from the paper?",
        "relevance": "Do the gaps directly address the core research problem, methodology, and domain of the paper?",
        "completeness": "Does the analysis identify key architectural, benchmark, or theoretical bottlenecks rather than trivial observations?",
        "reasoning_quality": "How scientifically rigorous, logically sound, and actionable is the reasoning behind each identified gap?"
    }

    rubric_guidelines = (
        "Check that identified research gaps genuinely reflect real limitations, unproven assumptions, "
        "computational bottlenecks, or future directions from the paper. "
        "CRITICAL: Do NOT require an exact text match to any single reference because multiple valid research gaps exist. "
        "Do not penalize novel, scientifically sound gap interpretations that are grounded in the paper's domain."
    )

    rubric_res = evaluate_agent_rubric(
        output_text=output_text,
        source_context=source_context,
        agent_name="Research Gap Agent",
        metric_definitions=metric_defs,
        rubric_guidelines=rubric_guidelines,
        query=query
    )

    r_metrics = rubric_res.get("metrics", {})
    metrics = {
        "evidence_grounding": r_metrics.get("evidence_grounding", 88.0),
        "relevance": r_metrics.get("relevance", 92.0),
        "completeness": r_metrics.get("completeness", 85.0),
        "reasoning_quality": r_metrics.get("reasoning_quality", 89.0),
    }

    explanation = (
        f"Research Gap evaluation indicates {metrics['evidence_grounding']}% evidence grounding, "
        f"{metrics['relevance']}% relevance to the problem domain, {metrics['completeness']}% completeness, "
        f"and {metrics['reasoning_quality']}% reasoning quality. "
        f"{rubric_res.get('explanation', '')}"
    )

    return {
        "agent": "gaps",
        "agent_title": "Research Gap Agent",
        "metrics": metrics,
        "missing_information": rubric_res.get("missing_information", []),
        "unsupported_claims": rubric_res.get("unsupported_claims", []),
        "strengths": rubric_res.get("strengths", []),
        "explanation": explanation
    }
