from app.agents.report_agent import generate_final_report
from app.agents.summarizer import summarize_paper
from app.agents.research_gap import find_research_gaps
from app.agents.dataset_agent import recommend_datasets
from app.agents.experiment_agent import recommend_experiments
from app.agents.literature_agent import generate_literature_survey
from app.agents.novelty_agent import analyze_novelty
from app.agents.comparison_agent import compare_papers

# ==========================================================
# Dynamic Agent Registry
# ==========================================================
AGENTS = {
    "summary": summarize_paper,
    "gaps": find_research_gaps,
    "datasets": recommend_datasets,
    "experiments": recommend_experiments,
    "literature": generate_literature_survey,
    "novelty": analyze_novelty,
    "comparison": compare_papers,
}


def execute_workflow(workflow, context):
    """Executes a list of agent tasks dynamically with deduplication and structured results."""
    results = {}
    completed = set()

    for step in workflow:
        if step in completed:
            continue

        if step not in AGENTS:
            continue

        try:
            print(f"Running {step} Agent...")
            output = AGENTS[step](context)
            results[step] = {
                "status": "success",
                "agent": step,
                "output": output,
            }
            completed.add(step)
        except Exception as e:
            print(f"{step} failed:", e)
            results[step] = {
                "status": "failed",
                "agent": step,
                "error": str(e),
            }

    return results


def calculate_confidence(results):
    """Calculates the execution success rate as a confidence percentage."""
    total = len(results)
    success = 0

    for value in results.values():
        if value and value.get("status") == "success":
            success += 1

    if total == 0:
        return 0

    return round((success / total) * 100, 2)


def is_complex_query(query: str):
    """Determines if query complexity exceeds basic keyword processing threshold."""
    query = query.lower()
    complex_keywords = [
        "complete",
        "full",
        "research",
        "publish",
        "ieee",
        "workflow",
        "novel",
        "survey",
        "roadmap",
        "analysis",
        "project",
        "future",
        "compare",
        "recommend",
    ]

    score = 0
    for word in complex_keywords:
        if word in query:
            score += 1

    return score >= 2


def detect_intent(query: str):
    """Detects intent from query string using keyword mapping."""
    query = query.lower().strip()

    intent_map = {
        "complete_analysis": [
            "complete analysis",
            "full analysis",
            "complete report",
            "analyze completely",
            "analyze this paper completely",
        ],
        "summary": [
            "summary",
            "summarize",
            "overview",
            "brief",
            "explain",
            "describe",
            "what is this paper about",
        ],
        "gaps": [
            "gap",
            "research gap",
            "limitations",
            "future work",
            "weakness",
        ],
        "datasets": [
            "dataset",
            "datasets",
            "training data",
            "recommend dataset",
            "suggest dataset",
        ],
        "experiments": [
            "experiment",
            "experiments",
            "implementation",
            "evaluation",
            "benchmark",
        ],
        "literature": [
            "literature",
            "survey",
            "review",
            "related work",
        ],
        "novelty": [
            "novelty",
            "innovation",
            "originality",
            "unique",
        ],
        "comparison": [
            "compare",
            "comparison",
            "difference",
        ],
    }

    for intent, keywords in intent_map.items():
        for keyword in keywords:
            if keyword in query:
                return intent

    return "unknown"


def build_workflow(intent: str):
    """Maps a detected intent to its corresponding ordered agent execution steps."""
    workflows = {
        "summary": [
            "summary",
        ],
        "gaps": [
            "summary",
            "gaps",
        ],
        "datasets": [
            "summary",
            "datasets",
        ],
        "experiments": [
            "summary",
            "datasets",
            "experiments",
        ],
        "literature": [
            "summary",
            "literature",
        ],
        "novelty": [
            "summary",
            "novelty",
        ],
        "comparison": [
            "comparison",
        ],
        "complete_analysis": [
            "summary",
            "gaps",
            "datasets",
            "experiments",
            "novelty",
            "literature",
        ],
    }

    return workflows.get(intent, [])


def run_agent(query, context):
    """
    Intelligent Coordinator Agent

    Routes user queries to an agent workflow planner based on complexity and intent,
    executes workflows, and formats structured outputs.
    """
    complex_query = is_complex_query(query)

    if complex_query:
        print("Using Intelligent Planning...")
        intent = detect_intent(query)
    else:
        intent = detect_intent(query)

    workflow = build_workflow(intent)
    if not workflow:
        return None

    results = execute_workflow(workflow, context)

    confidence = calculate_confidence(results)
    print(f"Coordinator Confidence: {confidence}%")

    final_response = {
        "intent": intent,
        "workflow": workflow,
        "confidence": confidence,
        "agents_used": len(workflow),
        "results": results,
    }

    if intent == "complete_analysis":
        def get_agent_output(step_name):
            res = results.get(step_name)
            if res and res.get("status") == "success":
                return res.get("output", "")
            return ""

        return generate_final_report(
            get_agent_output("summary"),
            get_agent_output("gaps"),
            get_agent_output("datasets"),
            get_agent_output("experiments"),
            get_agent_output("literature"),
            get_agent_output("novelty"),
        )

    return final_response