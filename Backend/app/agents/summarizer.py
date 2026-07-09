from app.llm.gemini import generate_answer


def summarize_paper(context):
    """
    Summarize the uploaded research paper.
    """

    question = """
Summarize this research paper in a professional and complete way.

Include:
1. Main objective
2. Methodology
3. Key contributions
4. Results
5. Conclusion

Provide a complete answer.
Do not stop mid-sentence.
"""

    return generate_answer(
        context,
        question
    )