from app.evaluation.agent_evaluators.summary_evaluator import evaluate_summary
from app.evaluation.agent_evaluators.gap_evaluator import evaluate_gaps
from app.evaluation.agent_evaluators.dataset_evaluator import evaluate_datasets
from app.evaluation.agent_evaluators.experiment_evaluator import evaluate_experiments
from app.evaluation.agent_evaluators.literature_evaluator import evaluate_literature
from app.evaluation.agent_evaluators.novelty_evaluator import evaluate_novelty
from app.evaluation.agent_evaluators.comparison_evaluator import evaluate_comparison
from app.evaluation.agent_evaluators.report_evaluator import evaluate_report
from app.evaluation.agent_evaluators.ppt_evaluator import evaluate_ppt
from app.evaluation.agent_evaluators.chat_evaluator import evaluate_chat_or_idea
from app.evaluation.agent_evaluators.workspace_evaluator import evaluate_workspace

AGENT_EVALUATOR_MAP = {
    "summary": evaluate_summary,
    "summarization": evaluate_summary,
    "gaps": evaluate_gaps,
    "research_gap": evaluate_gaps,
    "gap": evaluate_gaps,
    "datasets": evaluate_datasets,
    "dataset": evaluate_datasets,
    "dataset_recommendation": evaluate_datasets,
    "experiments": evaluate_experiments,
    "experiment": evaluate_experiments,
    "experiment_recommendation": evaluate_experiments,
    "literature": evaluate_literature,
    "literature_survey": evaluate_literature,
    "retrieval": evaluate_literature,
    "novelty": evaluate_novelty,
    "novelty_analysis": evaluate_novelty,
    "comparison": evaluate_comparison,
    "paper_comparison": evaluate_comparison,
    "report": evaluate_report,
    "ieee_report": evaluate_report,
    "ppt": evaluate_ppt,
    "presentation": evaluate_ppt,
    "chat": evaluate_chat_or_idea,
    "idea": evaluate_chat_or_idea,
    "research_idea": evaluate_chat_or_idea,
    "workspace": evaluate_workspace,
    "ai_workspace": evaluate_workspace,
}

__all__ = [
    "AGENT_EVALUATOR_MAP",
    "evaluate_summary",
    "evaluate_gaps",
    "evaluate_datasets",
    "evaluate_experiments",
    "evaluate_literature",
    "evaluate_novelty",
    "evaluate_comparison",
    "evaluate_report",
    "evaluate_ppt",
    "evaluate_chat_or_idea",
    "evaluate_workspace",
]
