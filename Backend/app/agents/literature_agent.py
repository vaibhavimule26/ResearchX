from app.llm.gemini import generate_answer


def generate_literature_survey(context: str) -> str:
    """
    Generate a structured literature survey for the uploaded research paper.
    """

    if not context or not context.strip():
        return (
            "Unable to generate literature survey because "
            "no research paper context was provided."
        )

    question = """
Analyze the provided research paper as an expert research scholar.

Generate a detailed Literature Survey Report with exactly these sections:

1. Introduction
- Briefly introduce the research domain.
- Explain the problem being addressed.

2. Existing Work
- Summarize the major existing methods discussed in the paper.
- Explain how previous approaches solve the problem.

3. Strengths of Existing Work
- Identify the strengths of existing approaches.
- Mention important contributions.

4. Limitations of Existing Work
- Explain the limitations or weaknesses of previous work.
- Mention challenges discussed in the paper.

5. Research Gap
- Identify the research gap addressed by this paper.
- Explain why existing work is insufficient.

6. Summary
- Summarize the complete literature survey.
- Explain how this paper advances the research area.

Important Rules:
- Base your answer only on the provided research paper context.
- Do not invent citations or research papers.
- If information is missing, clearly state that.
- Use formal academic language.
- Give a detailed structured answer.
"""

    return generate_answer(
        context=context,
        question=question,
    )


# ==========================================================
# Workspace Literature Survey Agent
# ==========================================================
def run_literature_survey_agent(topic: str, papers) -> str:
    """
    Execute the Literature Survey Agent.
    """

    print("Running Literature Survey Agent...")

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

    return generate_literature_survey(context)