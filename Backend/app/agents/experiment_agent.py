from app.llm.gemini import generate_answer


def recommend_experiments(context):
    """
    Recommend experiments for the uploaded research paper.
    """

    prompt = f"""
You are an expert AI Research Assistant.

Analyze the following research paper and recommend experiments.

For each experiment provide:

1. Experiment Name
2. Objective
3. Methodology
4. Expected Outcome
5. Evaluation Metrics

Research Paper:

{context}
"""

    return generate_answer(prompt, "")