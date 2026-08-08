from app.llm.gemini import generate_answer


# ==========================================================
# Experiment Recommendation Agent
# ==========================================================

def recommend_experiments(context: str) -> str:
    """
    Analyze a research paper and recommend
    evidence-grounded experiments for reproduction,
    validation, and research extension.
    """

    if not context or not context.strip():
        return (
            "Unable to recommend experiments because "
            "no research paper context was provided."
        )

    question = """
You are ResearchX, an expert research scientist and
experimental research planner.

Analyze ONLY the research paper provided in the context.

Your goal is to design meaningful experiments that can:
1. Reproduce the original research.
2. Validate the reported methodology.
3. Test weaknesses and limitations.
4. Extend the research toward a potential new contribution.

Produce a structured Experiment Recommendation Report.

1. Research Objective

Explain:

- What research question the paper investigates.
- What hypothesis or claim should be tested.
- What the experiment should demonstrate.

2. Reproduction Experiment

Design an experiment that attempts to reproduce the
paper's core methodology.

Include:

- Dataset
- Input
- Output
- Model / Algorithm
- Training procedure
- Important parameters
- Train / validation / test strategy
- Baselines
- Evaluation metrics

Only specify details supported by the paper.

If a required detail is unavailable, write:
"Not specified in the paper."

3. Validation Experiments

Recommend experiments that independently validate
the paper's main claims.

For each experiment provide:

- Experiment objective
- Setup
- Variables
- Baseline
- Evaluation
- What the result would tell the researcher

4. Ablation Study

Identify components of the proposed methodology that
could be tested through ablation.

For each ablation provide:

- Component being removed or changed
- Reason for testing it
- Expected research insight

Do NOT claim an expected numerical improvement.

5. Baseline Comparison

Recommend appropriate baseline categories.

Compare:

- Original approach
- Traditional baseline
- Strong modern baseline
- Proposed extension

Only recommend baselines that are logically relevant
to the paper's task.

6. Dataset Experiments

Recommend experiments involving:

- Different datasets
- Cross-dataset validation
- Larger datasets
- Diverse datasets
- Domain shifts

Only recommend these when relevant to the research.

7. Robustness Experiments

When applicable, evaluate:

- Noise
- Input variations
- Distribution shifts
- Missing data
- Perturbations
- Different environments

Explain why each robustness test matters.

8. Generalization Experiments

Design experiments to determine whether the proposed
method generalizes beyond the original experimental setup.

Consider:

- Unseen data
- Different populations
- Different domains
- Different environments
- External datasets

9. Evaluation Metrics

Identify the most appropriate evaluation metrics.

For each metric explain:

- What it measures
- Why it is relevant
- What limitation it has

Do NOT invent metric values.

10. Experimental Variables

Clearly identify:

- Independent variables
- Dependent variables
- Control variables

If the paper does not provide enough information,
state that explicitly.

11. Expected Outcomes

Describe qualitative outcomes that the experiments
are designed to observe.

IMPORTANT:

Do NOT predict specific numerical results.

Instead explain possible outcomes such as:

- improved performance
- similar performance
- reduced performance
- better robustness
- improved generalization
- failure under certain conditions

12. Potential Failure Cases

Identify situations where the proposed approach
may fail or perform poorly.

Only infer these when logically supported by the
paper's methodology and clearly label them as:

"Inferred"

13. Best Experiment Plan

Select the single most valuable experiment.

Provide a complete plan:

- Objective
- Dataset
- Model
- Baseline
- Procedure
- Evaluation metrics
- Comparison strategy
- Expected research insight

14. Research Extension Experiment

Design ONE experiment that could potentially produce
a meaningful research contribution beyond the original paper.

Explain:

- Existing limitation
- Proposed change
- Experimental setup
- Evaluation
- Research value

15. Final Experiment Roadmap

Provide an ordered roadmap:

Phase 1 — Reproduction
Phase 2 — Validation
Phase 3 — Ablation
Phase 4 — Robustness / Generalization
Phase 5 — Research Extension

IMPORTANT RULES:

- Use ONLY information supported by the paper context
  when describing the original research.
- Clearly distinguish paper facts from proposed experiments.
- Never invent original experimental results.
- Never invent dataset usage.
- Never claim that the authors performed an experiment
  unless the context explicitly states it.
- Do not invent numerical outcomes.
- Do not invent hyperparameters.
- If information is unavailable, say:
  "Not specified in the paper."
- Label logical assumptions as "Inferred".
- Keep recommendations specific to the paper.
- Avoid generic experiment advice.
- Produce a complete academic research plan.
"""

    return generate_answer(
        context=context,
        question=question,
    )


# ==========================================================
# Workspace Experiment Agent
# ==========================================================

def run_experiment_agent(topic: str, papers) -> str:
    """
    Execute the Experiment Recommendation Agent
    for multiple selected papers.
    """

    print("Running Experiment Recommendation Agent...")

    context_parts = []

    for i, paper in enumerate(papers, start=1):

        context_parts.append(
            f"""
==========================================================
Paper {i}
==========================================================

Title:
{paper.title}

Authors:
{", ".join(paper.authors)}

Abstract / Summary:
{paper.summary}

Published:
{paper.published}

Citation Count:
{getattr(paper, "citation_count", "Not specified")}

Venue:
{getattr(paper, "venue", "Not specified")}

Source:
{getattr(paper, "source", "Not specified")}
"""
        )

    context = "\n\n".join(context_parts)

    workspace_question = f"""
You are ResearchX, an expert experimental research planner.

Research Topic:
{topic}

The context contains multiple research papers.

Analyze the papers collectively and create an experimental
research strategy.

Include:

1. Common experimental methodologies
2. Reproduction experiments
3. Validation experiments
4. Important baseline comparisons
5. Dataset experiments
6. Ablation opportunities
7. Robustness experiments
8. Generalization experiments
9. Common evaluation metrics
10. Major experimental limitations
11. Highest-value experiment
12. Potential research extension experiment
13. Ordered experiment roadmap

IMPORTANT:

- Clearly separate what the papers actually performed from
  what you recommend.
- Do not invent results.
- Do not invent dataset usage.
- Do not invent numerical outcomes.
- Label inferred conclusions as "Inferred".
- If information is unavailable, write:
  "Not specified in the provided papers."
- Keep recommendations relevant to the provided papers.
- Produce a detailed academic experimental strategy.
"""

    return generate_answer(
        context=context,
        question=workspace_question,
    )