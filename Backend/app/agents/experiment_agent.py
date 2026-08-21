from typing import List, Dict, Any

from app.llm.gemini import generate_answer
from app.llm.multi_api_router import call_groq_api


# ==========================================================
# SINGLE PAPER EXPERIMENT PLANNING AGENT
# ==========================================================

def plan_experiments(context: str) -> str:
    """
    Generate a detailed experiment and validation protocol
    for one research paper.
    """

    if not context or not context.strip():
        return (
            "Unable to generate experiment protocol because "
            "no research paper context was provided."
        )

    question = """
Analyze ONLY the provided research paper context.

Act as a research experiment planning assistant.

Create a practical experimental replication and validation protocol.

Use EXACTLY this Markdown structure:

### 1. Experimental Objective
- **Objective:** State the main experiment objective based only on the paper.
- **Hypothesis:** State one testable hypothesis.
- If unavailable, write: Not specified in paper.

---

### 2. Experiment Setup
- **Dataset:** Use the dataset explicitly mentioned in the paper.
- **Model/Method:** Use the model, method, or system mentioned in the paper.
- **Configuration:** Include important settings only if specified.
- Do NOT invent datasets or model configurations.

---

### 3. Evaluation Metrics
- List ONLY metrics explicitly named in the paper.
- Do NOT convert objectives, claims, expected benefits, features,
or general concepts into metrics.
- If no explicit metric is named, write exactly:
Not specified in paper.

---

### 4. Step-by-Step Experiment
Generate steps ONLY from an experiment, procedure, workflow,
validation process, or methodology explicitly described in the paper.

Do NOT create new experimental steps.

For each missing step, write exactly:
Not specified in paper.

Use this format:

1. Prepare the data or input:
   - Extract only explicitly described preparation steps.
   - Otherwise: Not specified in paper.

2. Set up the model/method:
   - Extract only explicitly described setup steps.
   - Otherwise: Not specified in paper.

3. Run the experiment:
   - Extract only explicitly described execution steps.
   - Otherwise: Not specified in paper.

4. Measure the specified metrics:
   - Use only explicitly named metrics.
   - Otherwise: Not specified in paper.

5. Compare the result:
   - Extract only explicitly described comparison or validation procedures.
   - Otherwise: Not specified in paper.

---

### 5. Expected Result
- Extract only an expected result, finding, or conclusion explicitly
reported in the paper.
- Do NOT predict a new result.
- Do NOT say "expected to show" unless the paper itself describes this.
- If unavailable, write exactly: Not specified in paper.

STRICT RULES:
- Analyze ONLY the provided paper context.
- Do NOT recommend external datasets.
- Do NOT recommend datasets not named in the paper.
- Do NOT invent hypotheses.
- Do NOT invent baselines or comparisons.
- Do NOT invent traditional methods.
- Do NOT invent teacher feedback, human evaluation, peer review,
or Turing tests.
- Do NOT invent environments, dynamic obstacles, uncertainty levels,
or simulation procedures.
- Do NOT invent metrics from general objectives.
- Do NOT invent dataset splits.
- Do NOT invent hyperparameters.
- Do NOT invent hardware or software.
- Do NOT infer that a model "improves", "outperforms", or is
"effective" unless explicitly reported in the paper.
- When information is missing, write exactly:
Not specified in paper.
- Prefer "Not specified in paper" over making an inference.
- Keep the response concise and based strictly on extracted evidence.
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
    Generate one short experiment recommendation
    for each research paper.
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
                or "Not specified in paper."
            )
        else:
            summary = (
                getattr(paper, "abstract", None)
                or getattr(paper, "summary", None)
                or "Not specified in paper."
            )

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

Abstract:
{summary}

Published:
{published}
"""

        # --------------------------------------------------
        # PROMPT
        # --------------------------------------------------

        question = f"""
Analyze ONLY this research paper.

Research Topic:
{topic}

Generate ONE small and practical experiment that can be
performed to validate or reproduce the main idea of this paper.

Use EXACTLY this format:

### Small Experiment
- **Objective:** One short sentence based on the paper.
- **Setup:** Mention only the dataset, model, method, or input explicitly described in the paper. If unavailable, write "Not specified in paper".
- **Metrics:** Maximum 3 metrics. Use only metrics mentioned in the paper. If unavailable, write "Not specified in paper".
- **Expected Output:** One short sentence based on the paper.

STRICT RULES:
- Maximum 100 words total.
- Exactly 4 bullet points.
- Analyze ONLY this paper.
- Do NOT recommend external datasets.
- Do NOT recommend multiple datasets.
- Do NOT invent dataset names.
- Do NOT invent model names.
- Do NOT invent metrics.
- Do NOT invent train/test splits.
- Do NOT add baselines.
- Do NOT add implementation details.
- Do NOT add explanations outside the required format.
- If exact information is unavailable, write "Not specified in paper".
"""

        # --------------------------------------------------
        # CALL LLM
        # --------------------------------------------------

        try:
            result = call_groq_api(
                prompt=question,
                context=paper_context
            )

        except Exception as e:
            print(
                f"[Experiment Agent Groq Error for '{title}']: {e}"
            )

            result = """### Small Experiment
- **Objective:** Not specified in paper.
- **Setup:** Not specified in paper.
- **Metrics:** Not specified in paper.
- **Expected Output:** Unable to generate experiment recommendation."""

        # --------------------------------------------------
        # SAVE RESULT
        # --------------------------------------------------

        results.append({
            "paper_name": title,
            "result": result
        })

    return results


# ==========================================================
# BACKWARD-COMPATIBLE FUNCTION ALIASES
# ==========================================================

recommend_experiments = plan_experiments
run_experiments = run_experiment_agent