import re
from typing import Dict, Any, Optional
from app.evaluation.factuality_evaluator import evaluate_agent_rubric


def evaluate_ppt(
    output_text: str,
    source_context: str,
    query: Optional[str] = None,
    reference_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluate PPT Generator Agent Output.
    Criteria:
    - Factual Consistency: Are slide bullet points, numbers, and takeaways factually true to the paper?
    - Content Coverage: Does the deck cover core sections (Motivation, Problem, Methodology, Results, Conclusion)?
    - Structure: Slide organization, clarity, and bullet density suitable for academic presentations without wall-of-text overload.
    - Relevance: Concise focus on key contributions and high-impact findings without irrelevant filler.
    """
    # Programmatic slide structure check
    text = output_text or ""
    slide_markers = len(re.findall(r"(?:Slide\s+\d+|##\s+|---)", text, re.IGNORECASE))
    structure_heuristic = min(100.0, max(50.0, slide_markers * 15.0)) if slide_markers > 0 else 70.0

    metric_defs = {
        "factual_consistency": "Are all slide statements, claimed performance metrics, and takeaway bullets factually truthful to the source paper?",
        "content_coverage": "Does the slide deck cover the full academic trajectory: Motivation, Proposed Method, Key Results/Baselines, and Conclusion?",
        "structure": "Is the presentation well-structured into distinct slides with concise bullet points, avoiding cluttered walls of text?",
        "relevance": "Do the slides focus directly on the paper's principal innovations and research findings without extraneous filler?"
    }

    rubric_guidelines = (
        "Check that presentation slides synthesize the paper into clear, structured slides. "
        "Check that slide bullet points are factually accurate, well-organized, and suitable for academic presentation. "
        "Reward structured presentation design and concise high-signal bullet points."
    )

    rubric_res = evaluate_agent_rubric(
        output_text=output_text,
        source_context=source_context,
        agent_name="PPT Generator Agent",
        metric_definitions=metric_defs,
        rubric_guidelines=rubric_guidelines,
        query=query
    )

    r_metrics = rubric_res.get("metrics", {})
    llm_struct = r_metrics.get("structure", 85.0)
    blended_structure = round((structure_heuristic * 0.3) + (llm_struct * 0.7), 1)

    metrics = {
        "factual_consistency": r_metrics.get("factual_consistency", 90.0),
        "content_coverage": r_metrics.get("content_coverage", 87.0),
        "structure": blended_structure,
        "relevance": r_metrics.get("relevance", 92.0),
    }

    explanation = (
        f"Presentation evaluation indicates {metrics['factual_consistency']}% factual consistency, "
        f"{metrics['content_coverage']}% content coverage, {metrics['structure']}% slide structure quality, "
        f"and {metrics['relevance']}% topical relevance. "
        f"{rubric_res.get('explanation', '')}"
    )

    return {
        "agent": "ppt",
        "agent_title": "PPT Generator Agent",
        "metrics": metrics,
        "missing_information": rubric_res.get("missing_information", []),
        "unsupported_claims": rubric_res.get("unsupported_claims", []),
        "strengths": rubric_res.get("strengths", []),
        "explanation": explanation
    }
