from app.llm.gemini import generate_answer


def analyze_novelty(context: str) -> str:
    """
    Analyze the novelty and originality of the uploaded research paper.
    """

    if not context or not context.strip():
        return (
            "Unable to analyze novelty because "
            "no research paper context was provided."
        )

    question = """
Analyze the provided research paper as an expert research reviewer.

Generate a detailed Novelty Analysis Report with exactly these sections:

1. Novel Contributions
- Identify the key novel contributions of the paper.
- Explain why they are significant.

2. Comparison with Existing Work
- Compare the proposed approach with previous methods discussed in the paper.
- Highlight the major differences.

3. Innovation Score
- Give an innovation score from 1 to 10.
- Clearly justify the score using only the provided context.

4. Strengths
- List the strongest aspects of the proposed research.
- Explain why they are valuable.

5. Weaknesses
- Identify limitations or weaknesses discussed or implied in the paper.
- If insufficient information is available, clearly state that.

6. Suggestions for Improvement
- Suggest realistic improvements based on the paper.
- Do not invent unsupported claims.

Important Rules:
- Base your answer only on the provided research paper context.
- Do not invent citations, benchmark results, or comparisons.
- If information is missing, clearly state that.
- Use professional academic language.
- Give a detailed structured answer.
"""

    return generate_answer(
        context=context,
        question=question,
    )


# ==========================================================
# Workspace Novelty Analysis Agent
# ==========================================================

def run_novelty_agent(topic: str, papers) -> str:
    """
    Execute the Novelty Analysis Agent.
    """

    print("Running Novelty Analysis Agent...")

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

    return analyze_novelty(context)