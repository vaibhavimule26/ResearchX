from app.llm.gemini import generate_answer


def analyze_novelty(context):
    """
    Analyze the novelty of the uploaded research paper.
    """

    prompt = f"""
You are an expert AI Research Reviewer.

Analyze the following research paper.

Provide:

1. Novel Contributions
2. Comparison with Existing Work
3. Innovation Score (1-10)
4. Strengths
5. Weaknesses
6. Suggestions for Improvement

Research Paper:

{context}
"""

    return generate_answer(prompt, "")