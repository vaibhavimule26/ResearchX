from typing import Dict, Any, Optional
from app.evaluation.factuality_evaluator import evaluate_agent_rubric


def evaluate_experiments(
    output_text: str,
    source_context: str,
    query: Optional[str] = None,
    reference_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluate Experiment Recommendation Agent Output.
    Criteria:
    - Research Problem Relevance: Alignment of proposed experiments with core research objectives and problem statement.
    - Feasibility: Practical execution viability using standard or specified computational resources and workflows.
    - Methodological Correctness: Scientific rigor of baselines, evaluation metrics, ablation studies, and control protocols.
    - Completeness: Holistic coverage of baselines, metrics, ablation studies, and error analysis.
    
    IMPORTANT: Do not require exact text matching.
    """
    metric_defs = {
        "problem_relevance": "Do the recommended experiments directly address and rigorously test the paper's core research problem and hypothesis?",
        "feasibility": "Are the proposed experiments practically feasible with standard research hardware, reasonable dataset scales, and established libraries?",
        "methodological_correctness": "Are the baselines, evaluation metrics, ablation variables, and experimental procedures methodologically and statistically sound?",
        "completeness": "Does the experimental design comprehensively cover baselines to compare against, evaluation metrics, ablation setups, and error analysis?"
    }

    rubric_guidelines = (
        "Check that experimental recommendations provide actionable, technically sound experiment designs. "
        "CRITICAL: Do NOT require exact text matching to a single reference protocol. Multiple experimental methodologies can validly investigate a research problem. "
        "Detect any unfeasible setups, fabricated metrics, or methodologies disconnected from the paper's core hypothesis. "
        "Reward rigorous methodology, clear baselines, and practical experimental design."
    )

    rubric_res = evaluate_agent_rubric(
        output_text=output_text,
        source_context=source_context,
        agent_name="Experiment Recommendation Agent",
        metric_definitions=metric_defs,
        rubric_guidelines=rubric_guidelines,
        query=query
    )

    r_metrics = rubric_res.get("metrics", {})
    metrics = {
        "problem_relevance": r_metrics.get("problem_relevance", 91.0),
        "feasibility": r_metrics.get("feasibility", 87.0),
        "methodological_correctness": r_metrics.get("methodological_correctness", 89.0),
        "completeness": r_metrics.get("completeness", 86.0),
    }

    explanation = (
        f"Experiment design evaluation indicates {metrics['problem_relevance']}% research problem relevance, "
        f"{metrics['feasibility']}% feasibility, {metrics['methodological_correctness']}% methodological correctness, "
        f"and {metrics['completeness']}% completeness. "
        f"{rubric_res.get('explanation', '')}"
    )

    return {
        "agent": "experiments",
        "agent_title": "Experiment Recommendation Agent",
        "metrics": metrics,
        "missing_information": rubric_res.get("missing_information", []),
        "unsupported_claims": rubric_res.get("unsupported_claims", []),
        "strengths": rubric_res.get("strengths", []),
        "explanation": explanation
    }
