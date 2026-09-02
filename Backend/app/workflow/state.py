from typing import Any, Dict, List, TypedDict


class ResearchState(TypedDict, total=False):

    # ======================================================
    # Research Input
    # ======================================================

    topic: str
    papers: List[Any]
    paper_id: str

    # ======================================================
    # RAG
    # ======================================================

    rag_context: str

    # ======================================================
    # Agent Outputs
    # ======================================================

    summary: Any
    research_gap: Any
    literature: Any
    novelty: Any
    datasets: Any
    experiments: Any
    comparison: Any

    # ======================================================
    # Final Output
    # ======================================================

    final_report: str

    # ======================================================
    # Workflow
    # ======================================================

    status: str
    error: str