from app.llm.gemini import generate_answer


# ==========================================================
# Single Paper Summary
# ==========================================================
def summarize_paper(context: str) -> str:
    """
    Summarize a single uploaded research paper.
    """

    question = """
Summarize this research paper in a professional and complete way.

Include:

1. Main Objective

2. Methodology

3. Key Contributions

4. Results

5. Conclusion

Provide a complete answer.
Do not stop mid-sentence.
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
    Summarize multiple papers selected in the AI Workspace.
    """

    context_parts = []

    for i, paper in enumerate(papers, start=1):
        context_parts.append(
            f"""
Paper {i}

Title:
{paper.title}

Authors:
{", ".join(paper.authors)}

Abstract:
{paper.summary}

Published:
{paper.published}

----------------------------------------
"""
        )

    context = "\n".join(context_parts)

    question = f"""
You are an expert AI Research Assistant.

The research topic is:

{topic}

The user has selected multiple research papers.

Generate a structured summary containing:

1. Overall Summary

2. Main Contributions

3. Common Research Trends

4. Key Challenges

5. Future Research Directions

Write in professional academic language.
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
    Execute the Summary Agent for the selected papers.
    Called from /analysis/run-agent.
    """

    print("Running Summary Agent...")

    return summarize_workspace(
        topic,
        papers,
    )