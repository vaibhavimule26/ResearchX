from app.llm.gemini import generate_answer


def find_research_gaps(context: str) -> str:
    """
    Analyze a research paper context and identify
    evidence-grounded research gaps and future directions.
    """

    if not context or not context.strip():
        return (
            "Unable to analyze research gaps because "
            "no research paper context was provided."
        )

    question = """
Analyze the provided research paper context as an expert
research analyst.

Produce a detailed Research Gap Analysis with exactly these
sections:

1. Research Gaps
- Identify unresolved research problems.
- Explain what the paper does not fully address.
- Distinguish explicit gaps from inferred gaps.

2. Limitations
- Identify methodological limitations.
- Identify dataset or data limitations.
- Identify evaluation limitations.
- Identify scalability, generalization, reproducibility,
  computational, or practical limitations when supported
  by the paper context.

3. Future Work Opportunities
- Identify realistic future research directions.
- Explain why each direction matters.
- Connect each opportunity to a limitation or gap.

4. Possible Improvements
- Propose concrete technical or methodological improvements.
- Include stronger experiments, datasets, baselines, metrics,
  architecture changes, or validation strategies when relevant.

5. High-Priority Research Opportunity
- Select the single most promising future research direction.
- Explain why it has high research value.
- Suggest a concise testable research question.

Important rules:
- Use only evidence available in the provided paper context.
- Do not invent datasets, results, experiments, or claims.
- If a limitation is inferred rather than explicitly stated,
  clearly label it as "Inferred".
- Be specific to this paper.
- Avoid generic statements.
- Give a detailed answer.
"""

    return generate_answer(
        context=context,
        question=question,
    )