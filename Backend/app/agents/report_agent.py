from app.llm.gemini import generate_answer


def generate_ieee_report(context: str) -> str:
    """
    Generate a professional IEEE-style research paper
    directly from the uploaded research paper.
    """

    if not context or not context.strip():
        return "No research paper context was provided."

    question = """
You are an IEEE Research Paper Writing Expert.

Analyze the uploaded research paper and generate a complete,
professional IEEE-style research paper.

Generate EXACTLY the following sections.

==================================================
Title
==================================================

Use the paper title exactly as available.

==================================================
Authors
==================================================

If authors are unavailable write:

"Authors not available in the provided paper."

==================================================
Abstract
==================================================

Write a professional academic abstract.

==================================================
Keywords
==================================================

Provide 4 to 6 keywords.

==================================================
I. Introduction
==================================================

Explain:
- Background
- Problem Statement
- Motivation
- Objectives
- Research Questions (if available)

==================================================
II. Related Work
==================================================

Summarize previous work discussed in the paper.

==================================================
III. Proposed Methodology
==================================================

Explain the proposed architecture,
workflow and methodology.

==================================================
IV. Dataset Description
==================================================

Include:

- Dataset Name
- Source
- Data Type
- Size (only if available)
- Purpose

If unavailable clearly mention it.

==================================================
V. Experimental Setup
==================================================

Include:

- Baselines
- Evaluation Metrics
- Experimental Configuration
- Hardware (if available)

==================================================
VI. Results and Discussion
==================================================

Explain:

- Experimental Results
- Performance
- Analysis
- Comparison
- Important observations

Preserve numerical values exactly.

==================================================
VII. Novel Contributions
==================================================

Clearly list the paper's original contributions.

==================================================
VIII. Limitations
==================================================

Explain all limitations discussed in the paper.

==================================================
IX. Future Work
==================================================

Explain future research directions.

==================================================
X. Conclusion
==================================================

Write a strong IEEE-style conclusion.

==================================================
References
==================================================

IMPORTANT

If the uploaded paper already contains a References
section, reproduce ONLY those references.

Do NOT invent references.

If some references are incomplete because they are
missing from the provided context, write:

"Reference details unavailable in the provided paper."

==================================================
STRICT RULES
==================================================

1. Use ONLY the uploaded paper.
2. Never invent citations.
3. Never invent references.
4. Never invent datasets.
5. Never invent numerical values.
6. Never invent authors.
7. Never invent institutions.
8. Never invent experimental results.
9. Clearly mention when information is unavailable.
10. Write like a real IEEE conference paper.
11. Use professional academic English.
12. Keep the formatting clean.
13. Produce a complete report.
14. Do not stop midway.
15. Preserve all technical details.
"""

    return generate_answer(
        context=context,
        question=question,
    )


# ==========================================================
# Workspace IEEE Report Agent
# ==========================================================

def run_ieee_report_agent(topic: str, papers) -> str:
    """
    Execute the IEEE Report Agent.
    """

    print("Running IEEE Report Agent...")

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

    return generate_ieee_report(context)

# Backward compatibility
generate_final_report = generate_ieee_report