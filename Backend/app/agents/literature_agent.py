from app.llm.gemini import generate_answer


# ==========================================================
# Literature Survey Agent
# ==========================================================

def generate_literature_survey(context: str) -> str:
    """
    Generate an evidence-grounded literature survey
    for the provided research paper.
    """

    if not context or not context.strip():
        return (
            "Unable to generate literature survey because "
            "no research paper context was provided."
        )

    question = """
You are ResearchX, an expert academic literature-review
researcher.

Analyze ONLY the research paper context provided.

Your goal is to understand the research landscape described
by the paper and explain how the work relates to previous
research.

Produce a structured Literature Survey Report with these sections:

1. Research Domain Overview

Explain:

- Research domain
- Main research problem
- Importance of the problem
- Research context

2. Existing Work Mentioned in the Paper

Identify the previous approaches, methods, systems, or
research directions explicitly mentioned in the context.

For each one explain:

- Approach
- Purpose
- Main contribution
- Relevance to the current paper

IMPORTANT:
Do not invent authors, papers, citations, or methods that
are not present in the provided context.

3. Existing Methodology Landscape

Organize the previous approaches into meaningful categories.

For example:

- Traditional approaches
- Machine learning approaches
- Deep learning approaches
- Hybrid approaches
- Other approaches

Only create categories supported by the context.

4. Strengths of Existing Work

Identify strengths of the previous approaches explicitly
supported by the paper.

Explain why each strength is valuable.

5. Limitations of Existing Work

Identify limitations explicitly discussed by the paper.

Clearly distinguish:

- Explicit limitation
- Inferred limitation

Use the label "Inferred" whenever a limitation is derived
rather than directly stated.

6. Research Gap

Explain:

- What existing work does not adequately solve
- What remains unresolved
- What motivates the current paper
- How the paper attempts to address the gap

Do not assume a research gap merely because information
is missing.

7. Position of the Current Paper

Explain how the current paper positions itself relative
to previous research.

Include:

- What it continues
- What it changes
- What it improves
- What it introduces

Clearly distinguish author claims from analysis.

8. Comparative Analysis

Compare the major approaches mentioned in the context.

Use dimensions such as:

- Method
- Strength
- Limitation
- Application
- Contribution
- Relation to current paper

Do not introduce external methods.

9. Evolution of the Research Area

Based ONLY on the provided context, explain how the research
appears to have progressed from earlier approaches toward
the current work.

If the context is insufficient, write:

"Research evolution cannot be established from the provided
context."

10. Open Research Problems

Identify unresolved problems that are supported by the
provided context.

For each problem explain why it remains important.

11. Future Literature Directions

Identify research directions that logically follow from
the literature discussed in the paper.

Clearly label proposed directions as:

"Proposed"

Do not present proposed directions as established facts.

12. Literature Survey Conclusion

Summarize:

- Major existing approaches
- Important strengths
- Major limitations
- Research gap
- Position of the current paper
- Remaining opportunities

13. Researcher's Quick Takeaways

Provide 5 concise academic takeaways that a researcher
should remember after reading this literature survey.

IMPORTANT RULES:

- Use ONLY information supported by the provided context.
- Do not invent citations.
- Do not invent paper titles.
- Do not invent authors.
- Do not invent publication years.
- Do not introduce external research papers.
- Clearly distinguish explicit information from inference.
- Label inferred conclusions as "Inferred".
- Label proposed future directions as "Proposed".
- If information is unavailable, write:
  "Not specified in the paper."
- Do not claim that the current paper is superior unless
  the provided context supports that conclusion.
- Do not confuse the paper's claimed contribution with
  independently verified novelty.
- Use formal academic language.
- Produce a complete literature survey.
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
    Execute the Literature Survey Agent for multiple
    selected research papers.
    """

    print("Running Literature Survey Agent...")

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
You are ResearchX, an expert academic literature analyst.

Research Topic:
{topic}

The context contains multiple research papers.

Generate a comparative literature survey covering:

1. Research domain
2. Major approaches across the papers
3. Paper-specific contributions
4. Common strengths
5. Common limitations
6. Methodological differences
7. Research gaps
8. Conflicting or complementary approaches
9. Evolution of the research area
10. Underexplored research problems
11. Proposed future research directions
12. Overall literature conclusion

IMPORTANT:

- Use ONLY the provided papers.
- Do not invent citations, papers, authors, or results.
- Clearly distinguish paper facts from inference.
- Label inferred conclusions as "Inferred".
- Label proposed future directions as "Proposed".
- If information is unavailable, write:
  "Not specified in the provided papers."
- Do not use external literature.
- Produce a detailed academic literature synthesis.
"""

    return generate_answer(
        context=context,
        question=workspace_question,
    )