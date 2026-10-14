import time
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from app.evaluation.reference_loader import load_reference_or_paper_context
from app.evaluation.agent_evaluators import AGENT_EVALUATOR_MAP, evaluate_summary
from app.database.mongodb import evaluations_collection

logger = logging.getLogger(__name__)


def evaluate_agent_output(
    agent_name: str,
    output_text: str,
    paper_name: Optional[str] = None,
    context: Optional[str] = None,
    query: Optional[str] = None,
    reference_text: Optional[str] = None,
    user_id: Optional[str] = None,
    papers: Optional[List[Any]] = None,
    is_workspace: Optional[bool] = None
) -> Dict[str, Any]:
    """
    AGENT-SPECIFIC EVALUATION FRAMEWORK.
    Executes:
    1. Reference loading (Resolves benchmark dataset reference for the SAME paper,
       source paper document, or multi-paper workspace context).
    2. Agent-specific rubric evaluation (targeted metrics tailored to the specific agent).
    3. Performance logging (latency, mode).
    4. Persistence to MongoDB evaluations_collection.
    """
    start_time = time.time()
    clean_agent = (agent_name or "summary").lower().strip().replace("-", "_")

    # If workspace evaluation requested or multiple papers analyzed
    is_multi_doc = bool(is_workspace or clean_agent in ["workspace", "ai_workspace"] or (papers and len(papers) > 1))
    if clean_agent in ["workspace", "ai_workspace"]:
        clean_agent = "workspace"

    # 1. Resolve Reference Context (Ground Truth Benchmark vs Source Grounded vs Multi-Paper Workspace)
    ref_data = load_reference_or_paper_context(
        paper_name=paper_name,
        agent_name=clean_agent,
        fallback_context=context,
        explicit_reference=reference_text,
        papers=papers
    )

    source_text = ref_data.get("comparison_text", "")
    is_gt = ref_data.get("is_ground_truth", False)

    # 2. Select Agent-Specific Evaluator
    evaluator_fn = AGENT_EVALUATOR_MAP.get(clean_agent, evaluate_summary)

    try:
        eval_result = evaluator_fn(
            output_text=output_text,
            source_context=source_text,
            query=query,
            reference_text=source_text if is_gt else None
        )
    except Exception as e:
        logger.error(f"[Evaluation] Agent evaluator failed for {clean_agent}: {e}")
        eval_result = evaluate_summary(
            output_text=output_text,
            source_context=source_text,
            query=query,
            reference_text=source_text if is_gt else None
        )

    exec_time = round(time.time() - start_time, 2)

    # 3. Construct Unified Evaluation Record
    eval_id = str(uuid.uuid4())
    record = {
        "evaluation_id": eval_id,
        "agent": clean_agent,
        "agent_title": eval_result.get("agent_title", f"{clean_agent.capitalize()} Agent"),
        "paper_name": paper_name or ("Multi-Paper Workspace" if is_multi_doc else "Unnamed Document"),
        "query": query,
        "evaluation_mode": ref_data.get("evaluation_mode", "Source-Grounded Paper Evaluation"),
        "is_ground_truth": is_gt,
        "reference_source": ref_data.get("source_label", "Extracted Paper Context"),
        "source_context": source_text[:2000] if source_text else "",
        "metrics": eval_result.get("metrics", {}),
        "missing_information": eval_result.get("missing_information", []),
        "unsupported_claims": eval_result.get("unsupported_claims", []),
        "strengths": eval_result.get("strengths", []),
        "explanation": eval_result.get("explanation", ""),
        "human_validation": None,
        "execution_time_seconds": exec_time,
        "created_at": datetime.utcnow().isoformat(),
        "user_id": user_id
    }

    # Only include semantic_similarity if specifically computed by that agent (e.g. Summary Agent)
    if "semantic_similarity_score" in eval_result:
        record["semantic_similarity_score"] = eval_result["semantic_similarity_score"]
        record["semantic_similarity_percentage"] = eval_result.get("semantic_similarity_percentage", 0.0)
        record["semantic_label"] = eval_result.get("semantic_label", "Semantic Similarity Score")

    # Compute overall score from all valid metric numbers
    metric_vals = [float(v) for v in record["metrics"].values() if isinstance(v, (int, float))]
    record["overall_score"] = round(sum(metric_vals) / len(metric_vals), 1) if metric_vals else None

    # 4. Persist to MongoDB
    try:
        doc_to_save = dict(record)
        evaluations_collection.insert_one(doc_to_save)
    except Exception as e:
        logger.warning(f"[Evaluation] Could not save evaluation record to MongoDB: {e}")

    logger.info(
        f"[Evaluation] Completed {clean_agent} evaluation in {exec_time}s. "
        f"Mode: {record['evaluation_mode']}, Metrics: {list(record['metrics'].keys())}"
    )

    return record


def record_human_validation(
    evaluation_id: str,
    verdict: str,
    feedback_notes: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Record human researcher validation:
    verdict: 'Correct' | 'Partially Correct' | 'Incorrect'
    """
    valid_verdicts = ["Correct", "Partially Correct", "Incorrect"]
    if verdict not in valid_verdicts:
        raise ValueError(f"Verdict must be one of {valid_verdicts}")

    validation_payload = {
        "verdict": verdict,
        "feedback_notes": (feedback_notes or "").strip(),
        "validated_at": datetime.utcnow().isoformat(),
        "user_id": user_id or "researcher"
    }

    try:
        res = evaluations_collection.update_one(
            {"evaluation_id": evaluation_id},
            {"$set": {"human_validation": validation_payload}}
        )
        if res.matched_count == 0:
            logger.warning(f"[Evaluation] Evaluation ID {evaluation_id} not found in DB")
    except Exception as e:
        logger.error(f"[Evaluation] Error updating human validation in DB: {e}")

    return {
        "evaluation_id": evaluation_id,
        "human_validation": validation_payload,
        "status": "recorded"
    }


def get_agent_evaluation_history(agent_name: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieve historical evaluation runs for benchmark tracking."""
    clean_agent = (agent_name or "").lower().strip().replace("-", "_")
    try:
        query = {"agent": clean_agent} if clean_agent and clean_agent != "all" else {}
        cursor = evaluations_collection.find(query, {"_id": 0}).sort("created_at", -1).limit(limit)
        return list(cursor)
    except Exception as e:
        logger.error(f"[Evaluation] Error retrieving evaluation history: {e}")
        return []
