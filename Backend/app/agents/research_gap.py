from app.llm.gemini import generate_answer


def find_research_gaps(context: str) -> str:
    """
    Identify research gaps, limitations,
    future work opportunities, and improvements.
    """

    if not context or not context.strip():
        return "No research paper context was provided."

    question = """
Analyze the provided research paper context as an expert
research analyst.

Provide a complete and well-structured analysis with these
sections:

1. Research Gaps
- Identify unresolved problems.
- Identify missing research areas.
- Identify unanswered questions.
- Explain why each gap matters.

2. Limitations
- Identify methodological limitations.
- Identify dataset or data limitations.
- Identify evaluation limitations.
- Identify scalability or generalization limitations.
- Identify implementation or deployment limitations.
- Include only limitations supported by the paper context.

3. Future Work Opportunities
- Identify realistic future research directions.
- Connect each direction to a limitation or unresolved problem.
- Explain how future work could extend the current research.

4. Possible Improvements
- Suggest concrete methodological improvements.
- Suggest stronger evaluation strategies.
- Suggest improvements to datasets and experiments.
- Suggest robustness or reproducibility improvements where relevant.

5. Priority Research Opportunities
- Rank the three most important research opportunities.
- Explain why each opportunity is important.
- Explain what could be investigated.
- Explain the expected research impact.

Important rules:
- Use only information supported by the provided context.
- Do not invent facts, datasets, metrics, or citations.
- Clearly separate explicit paper limitations from inferred gaps.
- If evidence is insufficient, state that clearly.
- Provide a complete answer.
- Do not stop in the middle of a sentence.
"""

    return generate_answer(
        context,
        question,
    )