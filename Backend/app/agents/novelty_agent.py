from app.llm.gemini import generate_answer


# ==========================================================
# Novelty Analysis Agent
# ==========================================================

def analyze_novelty(context: str) -> str:
    """
    Analyze the novelty, originality, and research contribution
    of the provided research paper.
    """

    if not context or not context.strip():
        return (
            "Unable to analyze novelty because "
            "no research paper context was provided."
        )

    question = """
You are ResearchX, an expert academic peer reviewer.

Analyze ONLY the research paper context provided.

Your goal is to determine what is genuinely novel,
what is established from prior work, and where the paper's
contribution appears original.

Produce a structured Novelty Analysis Report with these sections:

1. Research Contribution

Identify:

- Main research problem
- Proposed approach
- Main contribution
- Claimed contribution
- Technical contribution
- Practical contribution

Clearly distinguish what the authors CLAIM from what can
actually be supported by the provided context.

2. Novel Contributions

For every potentially novel contribution explain:

- What is new
- What problem it addresses
- Why it may be valuable
- Evidence from the provided paper context

If novelty cannot be established from the context, write:

"Novelty cannot be conclusively established from the
provided context."

3. Existing vs Proposed Approach

Compare:

- Existing approach
- Proposed approach
- Main difference
- Technical difference
- Expected advantage

DO NOT introduce external papers or methods unless they are
explicitly mentioned in the provided context.

4. Novelty Evidence

Classify each contribution as:

- Explicitly claimed by authors
- Supported by provided context
- Inferred
- Cannot be established

For every "Inferred" conclusion, clearly label it:

"Inferred"

5. Innovation Dimensions

Evaluate novelty across:

- Problem novelty
- Methodological novelty
- Architectural novelty
- Dataset novelty
- Experimental novelty
- Application novelty
- Practical novelty

For each dimension provide:

- Rating: High / Medium / Low / Not established
- Explanation

Do not assume novelty simply because something is not mentioned.

6. Innovation Score

Give an overall innovation score from 1 to 10.

IMPORTANT:

The score represents the apparent novelty based ONLY on the
provided context.

Clearly explain:

- Why the score was given
- What evidence supports it
- What information is missing

If the context is insufficient, reduce confidence in the score
and explicitly state:

"Low confidence due to limited evidence."

7. Strengths of the Contribution

Identify the strongest aspects of the research.

Consider:

- Technical contribution
- Problem relevance
- Methodological design
- Practical value
- Potential impact

Only discuss aspects supported by the context.

8. Novelty Risks / Weaknesses

Identify factors that may reduce the originality of the work.

Consider:

- Similarity to existing methods mentioned in the paper
- Limited methodological differentiation
- Limited validation
- Limited datasets
- Weak experimental evidence
- Narrow application scope

Clearly label inferred weaknesses as:

"Inferred"

9. Research Differentiation

Explain what would make this work clearly distinguishable
from existing research.

Suggest improvements such as:

- New methodology
- Stronger architecture
- New dataset
- Cross-domain validation
- Better evaluation
- New application
- New theoretical insight

Only suggest directions logically connected to the paper.

10. Novelty Improvement Opportunities

Provide the top 5 opportunities to make the research
more original.

For each provide:

- Opportunity
- Current limitation
- Proposed change
- Expected research value

Do NOT claim that the improvement will definitely succeed.

11. Highest-Value Novelty Opportunity

Select ONE improvement with the strongest potential
research value.

Explain:

- Existing limitation
- Proposed innovation
- Why it is different
- What experiment could validate it

12. Potential Research Contribution

Write one concise statement describing the strongest
potential contribution that could emerge from extending
this work.

13. Novelty Verdict

Give one final verdict:

- Strongly Novel
- Moderately Novel
- Limited Novelty
- Novelty Not Established

Explain the verdict using only evidence from the context.

IMPORTANT RULES:

- Use ONLY the provided research paper context.
- Never invent citations.
- Never invent external comparisons.
- Never claim a method is novel merely because it is not
  mentioned in the context.
- Clearly distinguish author claims from your analysis.
- Clearly label inferred conclusions as "Inferred".
- Do not invent benchmark results.
- Do not invent datasets.
- Do not invent numerical performance values.
- If information is unavailable, write:
  "Not specified in the paper."
- Do not treat an innovation score as an objective truth.
- Keep the analysis specific to the provided research.
- Produce a complete academic peer-review style analysis.
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
    Execute the Novelty Analysis Agent
    for multiple selected papers.
    """

    print("Running Novelty Analysis Agent...")

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
You are ResearchX, an expert academic novelty analyst.

Research Topic:
{topic}

The context contains multiple research papers.

Analyze them collectively and identify:

1. Common research contributions
2. Paper-specific novel contributions
3. Similarities between approaches
4. Differences between approaches
5. Methodological novelty
6. Dataset novelty
7. Experimental novelty
8. Application novelty
9. Research areas with limited originality
10. Underexplored opportunities
11. Top 5 novelty improvement opportunities
12. Highest-value potential innovation
13. Potential research contribution
14. Overall novelty assessment

IMPORTANT:

- Compare papers ONLY using information present in the
  provided context.
- Do not invent external comparisons.
- Clearly separate author claims from your analysis.
- Label inferred conclusions as "Inferred".
- Do not invent results, datasets, citations, or metrics.
- If evidence is insufficient, say:
  "Not established from the provided papers."
- Do not automatically assume that a newer paper is more novel.
- Produce a detailed academic analysis.
"""

    return generate_answer(
        context=context,
        question=workspace_question,
    )