from app.llm.gemini import generate_answer


def compare_papers(context: str) -> str:
    """
    Compare multiple selected research papers.
    """

    if not context or not context.strip():
        return (
            "Unable to compare papers because "
            "no research paper context was provided."
        )

    question = """
Analyze the provided research papers as an expert research reviewer.

Generate a detailed Research Paper Comparison Report with exactly these sections:

1. Paper Titles
- List all selected paper titles.

2. Main Objectives
- Compare the research objectives of each paper.

3. Methodology
- Compare the methodologies used.

4. Datasets Used
- Compare the datasets or benchmarks used.
- If a paper does not mention datasets, clearly state that.

5. Models / Algorithms
- Compare the proposed models, architectures, or algorithms.

6. Key Contributions
- Compare the major contributions of each paper.

7. Experimental Results
- Compare the reported experimental findings.

8. Strengths
- Highlight the strengths of each paper.

9. Weaknesses
- Highlight the limitations of each paper.

10. Future Work
- Compare the future research directions.

11. Final Comparison Summary
- Summarize the similarities and differences.
- Identify which paper appears strongest for its intended objective.

Important Rules:
- Base the comparison only on the provided research paper context.
- Do not invent datasets, experiments, results, or citations.
- If only one paper is available, clearly state that meaningful comparison requires at least two papers.
- If information is missing, clearly state that.
- Use professional academic language.
- Give a detailed structured answer.
"""

    return generate_answer(
        context=context,
        question=question,
    )


# ==========================================================
# Workspace Comparison Agent
# ==========================================================

def run_comparison_agent(topic: str, papers) -> str:
    """
    Execute the Comparison Agent.
    """

    print("Running Comparison Agent...")

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

    return compare_papers(context)