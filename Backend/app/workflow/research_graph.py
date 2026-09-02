from langgraph.graph import StateGraph, START, END

from app.workflow.state import ResearchState

from app.rag.rag_service import retrieve_rag_context

from app.agents.summarizer import run_summary_agent
from app.agents.research_gap import run_gap_agent
from app.agents.literature_agent import run_literature_agent
from app.agents.novelty_agent import run_novelty_agent
from app.agents.dataset_agent import run_dataset_agent
from app.agents.experiment_agent import run_experiment_agent
from app.agents.comparison_agent import run_comparison_agent
from app.agents.report_agent import generate_final_report


# ==========================================================
# RAG NODE
# ==========================================================

def rag_node(state: ResearchState):

    topic = state.get("topic", "")
    paper_id = state.get("paper_id")

    print("[LangGraph] Running RAG node...")

    context = retrieve_rag_context(
        query=topic,
        paper_id=paper_id,
        top_k=5,
    )

    return {
        "rag_context": context,
    }


# ==========================================================
# SUMMARY NODE
# ==========================================================

def summary_node(state: ResearchState):

    print("[LangGraph] Running Summary Agent...")

    result = run_summary_agent(
        state.get("topic", ""),
        state.get("papers", []),
    )

    return {
        "summary": result,
    }


# ==========================================================
# RESEARCH GAP NODE
# ==========================================================

def research_gap_node(state: ResearchState):

    print("[LangGraph] Running Research Gap Agent...")

    result = run_gap_agent(
        state.get("topic", ""),
        state.get("papers", []),
    )

    return {
        "research_gap": result,
    }


# ==========================================================
# LITERATURE NODE
# ==========================================================

def literature_node(state: ResearchState):

    print("[LangGraph] Running Literature Agent...")

    result = run_literature_agent(
        state.get("topic", ""),
        state.get("papers", []),
    )

    return {
        "literature": result,
    }


# ==========================================================
# NOVELTY NODE
# ==========================================================

def novelty_node(state: ResearchState):

    print("[LangGraph] Running Novelty Agent...")

    result = run_novelty_agent(
        state.get("topic", ""),
        state.get("papers", []),
    )

    return {
        "novelty": result,
    }


# ==========================================================
# DATASET NODE
# ==========================================================

def dataset_node(state: ResearchState):

    print("[LangGraph] Running Dataset Agent...")

    result = run_dataset_agent(
        state.get("topic", ""),
        state.get("papers", []),
    )

    return {
        "datasets": result,
    }


# ==========================================================
# EXPERIMENT NODE
# ==========================================================

def experiment_node(state: ResearchState):

    print("[LangGraph] Running Experiment Agent...")

    result = run_experiment_agent(
        state.get("topic", ""),
        state.get("papers", []),
    )

    return {
        "experiments": result,
    }


# ==========================================================
# COMPARISON NODE
# ==========================================================

def comparison_node(state: ResearchState):

    print("[LangGraph] Running Comparison Agent...")

    result = run_comparison_agent(
        state.get("topic", ""),
        state.get("papers", []),
    )

    return {
        "comparison": result,
    }


# ==========================================================
# FINAL REPORT NODE
# ==========================================================

def final_report_node(state: ResearchState):

    print("[LangGraph] Running Final Report Agent...")

    result = generate_final_report(
        summary=state.get("summary", ""),
        gaps=state.get("research_gap", ""),
        datasets=state.get("datasets", ""),
        experiments=state.get("experiments", ""),
        literature=state.get("literature", ""),
        novelty=state.get("novelty", ""),
    )

    return {
        "final_report": result,
        "status": "Completed",
    }


# ==========================================================
# BUILD RESEARCH GRAPH
# ==========================================================

def build_research_graph():

    workflow = StateGraph(ResearchState)

    # ------------------------------------------------------
    # Register Nodes
    # ------------------------------------------------------

    workflow.add_node("rag", rag_node)

    workflow.add_node(
        "summary",
        summary_node,
    )

    workflow.add_node(
        "research_gap",
        research_gap_node,
    )

    workflow.add_node(
        "literature",
        literature_node,
    )

    workflow.add_node(
        "novelty",
        novelty_node,
    )

    workflow.add_node(
        "datasets",
        dataset_node,
    )

    workflow.add_node(
        "experiments",
        experiment_node,
    )

    workflow.add_node(
        "comparison",
        comparison_node,
    )

    workflow.add_node(
        "final_report",
        final_report_node,
    )

    # ------------------------------------------------------
    # Graph Flow
    # ------------------------------------------------------

    workflow.add_edge(
        START,
        "rag",
    )

    workflow.add_edge(
        "rag",
        "summary",
    )

    workflow.add_edge(
        "summary",
        "research_gap",
    )

    workflow.add_edge(
        "research_gap",
        "literature",
    )

    workflow.add_edge(
        "literature",
        "novelty",
    )

    workflow.add_edge(
        "novelty",
        "datasets",
    )

    workflow.add_edge(
        "datasets",
        "experiments",
    )

    workflow.add_edge(
        "experiments",
        "comparison",
    )

    workflow.add_edge(
        "comparison",
        "final_report",
    )

    workflow.add_edge(
        "final_report",
        END,
    )

    return workflow.compile()


# ==========================================================
# Compiled Graph
# ==========================================================

research_graph = build_research_graph()