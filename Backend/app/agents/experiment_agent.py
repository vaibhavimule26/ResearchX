from typing import Any, Dict, List, Optional, Tuple, Union

from app.llm.gemini import generate_answer
from app.llm.multi_api_router import call_groq_api


# ==========================================================
# SINGLE PAPER EXPERIMENT PLANNING AGENT
# ==========================================================

def plan_experiments(context: str) -> str:
    """
    Generate a concise, high-impact experiment recommendation and validation protocol
    for one research paper based on its research problem, methodology, and objectives.
    """

    if not context or not context.strip():
        return (
            "Unable to generate experiment protocol because "
            "no research paper context was provided."
        )

    question = """
You are the Senior Experimental Design & Evaluation Architect at ResearchX.

MOTIVE & OBJECTIVE:
Identify and recommend appropriate experiments and evaluation techniques for this research paper based on its research problem, methodology, and objectives. Provide a concise, high-impact experimental plan.

STRICT CONCISENESS RULE: Keep the total output under 180 words. Focus strictly on essential experimental steps and metrics.

Use EXACTLY this structure:

### 1. Core Hypothesis & Validation Objective
- **Primary Hypothesis:** One crisp sentence predicting the advantage of the proposed approach.
- **Key Evaluation Metrics:** Primary quantitative metrics (e.g. Accuracy, F1 Score, Latency/Throughput, BLEU/ROUGE).

---

### 2. Recommended Experiments Matrix

| Phase | Experimental Objective | Proposed Method vs Baseline | Target Evaluation Metric | Expected Validation Outcome |
| :--- | :--- | :--- | :--- | :--- |
| **1. Comparative Benchmark** | Primary comparative evaluation | Proposed model vs SOTA baselines | Primary accuracy/performance metrics | Demonstrates statistically significant gain |
| **2. Ablation & Efficiency** | Component contribution & speed | Proposed system with/without key modules | Latency (ms) / FLOPs / Memory | Quantifies efficiency vs accuracy trade-offs |

---

### 3. Key Execution Protocol
- **Data & Split:** Standard 70/15/15 train/val/test or official benchmark split with uniform preprocessing.
- **Validation Protocol:** 5-fold cross-validation or paired statistical significance testing under controlled hardware settings.
"""

    try:
        return generate_answer(
            context=context,
            question=question,
        )

    except Exception as e:
        print(f"[Experiment Agent Error]: {e}")
        return "Unable to generate experiment recommendations."


# ==========================================================
# MULTI-PAPER WORKSPACE EXPERIMENT AGENT
# ==========================================================

def run_experiment_agent(
    topic: str,
    papers: List[Any]
) -> List[Dict[str, str]]:
    """
    Generate concise, high-impact experiment recommendations and evaluation techniques
    for each selected research paper.
    """

    results = []

    for paper in papers:

        # --------------------------------------------------
        # GET PAPER TITLE
        # --------------------------------------------------

        if isinstance(paper, dict):
            title = paper.get("title", "Untitled Paper")
        else:
            title = getattr(paper, "title", "Untitled Paper")

        # --------------------------------------------------
        # GET ABSTRACT / SUMMARY
        # --------------------------------------------------

        if isinstance(paper, dict):
            summary = (
                paper.get("abstract")
                or paper.get("summary")
                or paper.get("why_chosen")
                or paper.get("key_contribution")
                or f"Research investigation on {topic} focusing on {title}."
            )
            venue = paper.get("venue") or ""
        else:
            summary = (
                getattr(paper, "abstract", None)
                or getattr(paper, "summary", None)
                or getattr(paper, "why_chosen", None)
                or getattr(paper, "key_contribution", None)
                or f"Research investigation on {topic} focusing on {title}."
            )
            venue = getattr(paper, "venue", "")

        # --------------------------------------------------
        # GET PUBLISHED DATE
        # --------------------------------------------------

        if isinstance(paper, dict):
            published = paper.get("published", "Not specified")
        else:
            published = getattr(paper, "published", "Not specified")

        # --------------------------------------------------
        # CREATE PAPER CONTEXT
        # --------------------------------------------------

        paper_context = f"""
Title:
{title}

Abstract / Focus:
{summary}

Venue / Source:
{venue}

Published:
{published}
"""

        # --------------------------------------------------
        # PROMPT
        # --------------------------------------------------

        question = f"""
You are the Senior Experimental Design & Evaluation Architect at ResearchX.

MOTIVE & OBJECTIVE:
Identify and recommend appropriate experiments and evaluation techniques for this research paper based on its research problem, methodology, and objectives.

Paper Title: {title}
Research Topic: {topic}

STRICT CONCISENESS RULE: Keep the entire output under 140 words. Focus strictly on key validation experiments and metrics.

Use EXACTLY this format:

### 1. Core Validation Objective
- **Hypothesis:** 1 crisp sentence stating the primary testable claim and expected performance gain.
- **Key Metrics:** Primary evaluation metrics (e.g. Accuracy, F1 Score, Latency/Throughput, BLEU/ROUGE).

---

### 2. Recommended Experiment & Validation Matrix

| Phase | Objective | Proposed Setup vs Baseline | Validation Metric | Target Outcome |
| :--- | :--- | :--- | :--- | :--- |
| **1. Comparative Benchmark** | Primary comparative evaluation | Proposed model vs standard baselines | Primary task metrics | Statistically significant improvement |
| **2. Ablation & Efficiency** | Component contribution & speed | Proposed system with/without key components | Latency (ms) / Memory (MB) | Quantifies efficiency-accuracy trade-off |

---

### 3. Execution Notes
- **Data & Protocol:** Benchmark split (e.g. 70/15/15) with standard task preprocessing.
- **Validation:** 5-fold cross-validation or paired significance testing under controlled hyperparameters.
"""

        # --------------------------------------------------
        # CALL LLM WITH RESILIENT CASCADE
        # --------------------------------------------------

        result = ""
        try:
            result = call_groq_api(
                prompt=question,
                context=paper_context
            )
        except Exception as e:
            print(f"[Experiment Agent Groq Error for '{title}']: {e}")

        if not result or len(result.strip()) < 50:
            try:
                result = generate_answer(
                    context=paper_context,
                    question=question
                )
            except Exception as e:
                print(f"[Experiment Agent Gemini Error for '{title}']: {e}")

        # --------------------------------------------------
        # SAVE RESULT
        # --------------------------------------------------

        results.append({
            "paper_name": title,
            "result": result.strip() if result else "Unable to generate experiment recommendation for this paper."
        })

    return results


# ==========================================================
# BACKWARD-COMPATIBLE FUNCTION ALIASES
# ==========================================================

recommend_experiments = plan_experiments
run_experiments = run_experiment_agent