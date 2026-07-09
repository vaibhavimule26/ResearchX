from app.llm.gemini import generate_answer


def generate_literature_survey(context):
    """
    Generate a literature survey from the uploaded research paper.
    """

    prompt = f"""
You are an expert AI Research Assistant.

Read the following research paper carefully.

Generate a professional Literature Survey containing:

1. Introduction
2. Existing Work
3. Strengths of Existing Work
4. Limitations of Existing Work
5. Research Gap
6. Summary

Write in formal academic language.

Research Paper:

{context}
"""

    return generate_answer(prompt, "")