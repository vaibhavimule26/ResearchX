from app.agents.report_agent import generate_final_report
from app.agents.summarizer import summarize_paper
from app.agents.research_gap import find_research_gaps
from app.agents.dataset_agent import recommend_datasets
from app.agents.experiment_agent import recommend_experiments
from app.agents.literature_agent import generate_literature_survey
from app.agents.novelty_agent import analyze_novelty
from app.agents.comparison_agent import compare_papers


def run_agent(query, context):
    """
    Intelligent Coordinator Agent

    Routes user queries to the appropriate AI agent based on intent.
    """

    query = query.lower().strip()

    # ==========================================================
    # Complete Research Analysis
    # ==========================================================
    if (
        "complete analysis" in query
        or "full analysis" in query
        or "analyze completely" in query
        or "analyze this paper completely" in query
        or "complete report" in query
        or "detailed analysis" in query
    ):

        summary = summarize_paper(context)
        gaps = find_research_gaps(context)
        datasets = recommend_datasets(context)
        experiments = recommend_experiments(context)
        literature = generate_literature_survey(context)
        novelty = analyze_novelty(context)

        return generate_final_report(
            summary,
            gaps,
            datasets,
            experiments,
            literature,
            novelty,
        )

    # ==========================================================
    # Summarizer Agent
    # ==========================================================
    elif (
        "summarize" in query
        or "summary" in query
        or "explain" in query
        or "overview" in query
        or "describe" in query
        or "what is this paper about" in query
        or "brief" in query
    ):
        return summarize_paper(context)

    # ==========================================================
    # Research Gap Agent
    # ==========================================================
    elif (
        "research gap" in query
        or "research gaps" in query
        or "gap" in query
        or "limitations" in query
        or "limitation" in query
        or "future work" in query
        or "weakness" in query
        or "weaknesses" in query
    ):
        return find_research_gaps(context)

    # ==========================================================
    # Dataset Recommendation Agent
    # ==========================================================
    elif (
        "dataset" in query
        or "datasets" in query
        or "recommend dataset" in query
        or "recommend datasets" in query
        or "suggest dataset" in query
        or "suggest datasets" in query
        or "training data" in query
        or "data source" in query
    ):
        return recommend_datasets(context)

    # ==========================================================
    # Experiment Recommendation Agent
    # ==========================================================
    elif (
        "experiment" in query
        or "experiments" in query
        or "recommend experiment" in query
        or "recommend experiments" in query
        or "suggest experiment" in query
        or "suggest experiments" in query
        or "implementation" in query
        or "evaluation" in query
    ):
        return recommend_experiments(context)

    # ==========================================================
    # Literature Survey Agent
    # ==========================================================
    elif (
        "literature survey" in query
        or "literature review" in query
        or "related work" in query
        or "survey" in query
        or "review papers" in query
    ):
        return generate_literature_survey(context)

    # ==========================================================
    # Novelty Analysis Agent
    # ==========================================================
    elif (
        "novelty" in query
        or "novel" in query
        or "innovation" in query
        or "innovative" in query
        or "unique contribution" in query
        or "originality" in query
    ):
        return analyze_novelty(context)

    # ==========================================================
    # Paper Comparison Agent
    # ==========================================================
    elif (
        "compare" in query
        or "comparison" in query
        or "compare papers" in query
        or "difference" in query
        or "difference between papers" in query
        or "compare research papers" in query
    ):
        return compare_papers(context)

    # ==========================================================
    # Default
    # ==========================================================
    return None