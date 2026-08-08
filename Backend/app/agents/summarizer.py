from app.llm.gemini import generate_answer


# ==========================================================
# Single Paper Summary Agent
# ==========================================================

def summarize_paper(context: str) -> str:
    """
    Generate a structured and comprehensive summary
    of a single research paper.
    """

    question = """
You are ResearchX, an expert academic research assistant.

Analyze ONLY the research paper provided in the context.

Generate a professional, structured research summary using
the following sections:

1. Paper Overview
   - Research problem
   - Research domain
   - Main objective

2. Problem Statement
   - What problem does the paper attempt to solve?
   - Why is the problem important?

3. Proposed Methodology
   - Approach used
   - Models / algorithms / techniques
   - System architecture or framework, if mentioned

4. Dataset / Data
   - Dataset name
   - Data source
   - Dataset size
   - Important characteristics
   - If not mentioned, explicitly say "Not specified in the paper."

5. Key Contributions
   - List the major contributions made by the authors.

6. Experimental Setup
   - Experimental procedure
   - Baselines
   - Evaluation metrics
   - Hardware/software details if provided

7. Results
   - Important findings
   - Performance values
   - Comparisons with existing methods

8. Limitations
   - Limitations explicitly mentioned by the authors
   - Do not invent limitations.

9. Future Work
   - Future directions explicitly mentioned in the paper.

10. Conclusion
   - Overall conclusion of the research.

11. Key Takeaways
   - Provide 3–5 concise points that capture the most important
     information from the paper.

IMPORTANT RULES:

- Use ONLY information available in the provided paper.
- Do NOT invent facts.
- Do NOT invent datasets.
- Do NOT invent numerical results.
- Do NOT invent citations.
- Do NOT assume missing information.
- If information is unavailable, write:
  "Not specified in the paper."
- Preserve important technical terminology.
- Clearly distinguish results from claims.
- Use professional academic language.
- Make the answer complete.
- Do not stop in the middle of a section.
"""

    return generate_answer(
        context=context,
        question=question,
    )


# ==========================================================
# Workspace Summary
# ==========================================================

def summarize_workspace(topic: str, papers) -> str:
    """
    Generate a structured research summary from
    multiple papers selected in the AI Workspace.
    """

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

Abstract:
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

    context = "\n".join(context_parts)

    question = f"""
You are ResearchX, an expert academic research assistant.

Research Topic:
{topic}

The user has selected multiple research papers.

Analyze ONLY the information provided in the papers.

Generate a structured multi-paper research synthesis.

Include:

1. Overall Research Overview
   - What is the overall research area?
   - What problems are being investigated?

2. Paper-wise Contributions
   - Briefly explain the contribution of each paper.

3. Common Research Trends
   - Identify recurring methods, approaches, models,
     datasets, or research directions.

4. Methodology Comparison
   - Compare the major approaches used across the papers.

5. Key Findings
   - Identify important findings supported by the papers.

6. Common Challenges
   - Identify challenges supported by the provided papers.

7. Research Gaps
   - Mention gaps that can reasonably be identified from
     the provided papers.
   - Do not invent unsupported claims.

8. Future Research Directions
   - Summarize future directions supported by the papers.

9. Overall Takeaways
   - Provide 5 concise research-level takeaways.

IMPORTANT RULES:

- Use ONLY the provided paper information.
- Do NOT invent facts.
- Do NOT invent numerical results.
- Do NOT invent datasets or citations.
- If information is unavailable, write:
  "Not specified in the provided papers."
- Do not treat assumptions as facts.
- Use professional academic language.
- Preserve technical terminology.
- Compare papers based only on available information.
- Produce a complete answer.
"""

    return generate_answer(
        context=context,
        question=question,
    )


# ==========================================================
# Workspace Summary Agent
# ==========================================================

def run_summary_agent(topic: str, papers) -> str:
    """
    Execute the Summary Agent for multiple selected papers.
    """

    print("Running Summary Agent...")

    return summarize_workspace(
        topic,
        papers,
    )