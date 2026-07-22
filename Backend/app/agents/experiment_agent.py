from app.llm.gemini import generate_answer


def recommend_experiments(context: str) -> str:
    """
    Recommend research experiments for the uploaded paper.
    """

    if not context or not context.strip():
        return (
            "Unable to recommend experiments because "
            "no research paper context was provided."
        )

    question = """
Analyze the provided research paper as an expert research scientist.

Generate a detailed Experiment Recommendation Report with exactly these sections:

1. Suggested Experiments
- List the most important experiments to perform.
- Explain why each experiment is useful.

2. Experiment Setup
- Experimental methodology
- Required datasets
- Models
- Baselines
- Training strategy

3. Evaluation Metrics
- Appropriate evaluation metrics
- Explain why each metric is suitable.

4. Expected Outcomes
- Expected observations
- Possible improvements
- Potential limitations

5. Best Experiment Plan
- Recommend the best complete experiment.
- Explain how it should be implemented.

Important Rules:
- Base your answer only on the provided research paper context.
- Do not invent results.
- If information is missing, clearly state that.
- Give a detailed structured answer.
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
    Execute the Experiment Recommendation Agent.
    """

    print("Running Experiment Recommendation Agent...")

    context = "\n\n".join(
        [
            f"""
Title: {paper.title}
Authors: {", ".join(paper.authors)}
Summary: {paper.summary}
Published: {paper.published}
"""
            for paper in papers
        ]
    )

    return recommend_experiments(context)