from app.llm.gemini import generate_answer


# ==========================================================
# Research Gap Agent
# ==========================================================

def find_research_gaps(context: str) -> str:
    """
    Analyze a research paper and identify
    evidence-grounded research gaps, limitations,
    and future research opportunities.
    """

    if not context or not context.strip():
        return (
            "Unable to analyze research gaps because "
            "no research paper context was provided."
        )

    question = """
You are ResearchX, an expert academic research analyst.

Analyze ONLY the research paper provided in the context.

Your goal is to identify genuine research gaps and opportunities
that can help a researcher design meaningful future work.

Produce a structured Research Gap Analysis using these sections:

1. Research Problem
   - What problem does the paper address?
   - What aspect of the problem remains unresolved?

2. Explicit Research Gaps
   - Identify gaps explicitly mentioned by the authors.
   - Connect each gap to the relevant statement or limitation
     in the paper.

3. Inferred Research Gaps
   - Identify gaps that can logically be inferred from the
     methodology, experiments, dataset, evaluation, or discussion.
   - Clearly label every such gap as "Inferred".
   - Explain the reasoning behind the inference.

4. Methodological Limitations
   Analyze whether the paper has limitations related to:
   - methodology
   - model or algorithm
   - experimental design
   - assumptions
   - baseline selection

5. Dataset / Data Limitations
   Analyze:
   - dataset size
   - dataset diversity
   - data quality
   - class imbalance
   - data source
   - missing data
   - generalization to other datasets

   Only discuss these when supported by the paper.

6. Evaluation Limitations
   Analyze:
   - evaluation metrics
   - baseline comparisons
   - validation strategy
   - experimental coverage
   - statistical validation
   - reproducibility

7. Generalization and Practical Limitations
   Analyze, when supported:
   - scalability
   - computational requirements
   - real-world deployment
   - robustness
   - generalization
   - interpretability
   - reproducibility

8. Future Research Directions
   For each direction:
   - Describe the proposed direction.
   - Explain which gap or limitation it addresses.
   - Explain why it is valuable.

9. Concrete Improvements
   Suggest technically meaningful improvements such as:
   - stronger datasets
   - additional baselines
   - improved evaluation metrics
   - ablation studies
   - cross-dataset validation
   - architecture improvements
   - robustness testing
   - real-world validation

   Only suggest improvements that logically follow from
   the identified gaps.

10. Priority Ranking
   Rank the top 3 research opportunities.

   For each opportunity provide:
   - Priority
   - Research opportunity
   - Gap addressed
   - Expected research value

11. Highest-Priority Research Opportunity
   Select ONE opportunity that appears most promising.

   Explain:
   - Why it is important.
   - What gap it addresses.
   - Why it could lead to meaningful research.
   - What experiment could validate it.

12. Potential Research Question
   Formulate ONE concise and testable research question
   based on the highest-priority opportunity.

IMPORTANT RULES:

- Use ONLY information supported by the provided paper.
- Never invent facts, datasets, results, metrics, citations,
  experiments, or claims.
- Clearly distinguish explicit gaps from inferred gaps.
- Use the label "Inferred" whenever a gap is not explicitly
  stated by the authors.
- Do not assume that something is a limitation simply because
  it is not mentioned.
- If the paper does not provide enough information for a section,
  write:
  "Not specified in the paper."
- Avoid generic research advice.
- Keep the analysis specific to the paper.
- Preserve important technical terminology.
- Do not confuse future work with an already completed contribution.
- Produce a complete academic analysis.
"""

    return generate_answer(
        context=context,
        question=question,
    )


# ==========================================================
# Workspace Research Gap Agent
# ==========================================================

def run_research_gap_agent(topic: str, papers) -> str:
    """
    Execute the Research Gap Agent for multiple selected papers.
    """

    print("Running Research Gap Agent...")

    context_parts = []

    for i, paper in enumerate(papers, start=1):

        context_parts.append(
            f"""
==========================================================
Paper {i}
==========================================================

Title:
{paper.title}

Authors:
{", ".join(paper.authors)}

Abstract / Summary:
{paper.summary}

Published:
{paper.published}

Citation Count:
{getattr(paper, "citation_count", "Not specified")}

Venue:
{getattr(paper, "venue", "Not specified")}

Source:
{getattr(paper, "source", "Not specified")}
"""
        )

    context = "\n\n".join(context_parts)

    workspace_question = f"""
You are ResearchX, an expert research gap analyst.

Research Topic:
{topic}

The context contains multiple research papers.

Analyze the papers collectively and identify:

1. Common Research Gaps
2. Paper-Specific Research Gaps
3. Common Methodological Limitations
4. Dataset / Data Gaps
5. Evaluation Gaps
6. Generalization Gaps
7. Conflicting or Inconsistent Findings
8. Underexplored Research Areas
9. Top 5 Future Research Opportunities
10. Highest-Priority Research Direction
11. One Potential Research Question

IMPORTANT:

- Use ONLY the provided papers.
- Clearly distinguish explicit information from inference.
- Label inferred conclusions as "Inferred".
- Do not invent information.
- Do not invent datasets, metrics, results, or citations.
- If information is unavailable, say:
  "Not specified in the provided papers."
- Avoid generic statements.
- Compare the papers based only on the information provided.
- Produce a detailed academic analysis.
"""

    return generate_answer(
        context=context,
        question=workspace_question,
    )