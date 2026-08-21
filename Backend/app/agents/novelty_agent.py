from typing import List, Dict, Any

from app.llm.multi_api_router import call_groq_api


# ==========================================================
# 5. Novelty Analysis Agent
# File: app/agents/novelty_agent.py
# ==========================================================

def analyze_novelty(context: str) -> str:
    """
    Generate a concise, evidence-grounded novelty analysis
    for a single research paper.
    """

    if not context or not context.strip():
        return (
            "Insufficient paper context available for novelty analysis."
        )

    question = """
You are ResearchX, an expert academic peer reviewer.

Analyze ONLY the provided research paper context.

Your task is to determine what is genuinely NEW or DISTINCTIVE
about the current paper.

IMPORTANT:
This is a NOVELTY ANALYSIS, not a paper summary.
Do not simply repeat the problem statement, methodology,
or findings.

Use EXACTLY this format:

### 1. Novel Elements
Identify the specific ideas, methods, systems, combinations,
applications, or perspectives that appear new or distinctive.

### 2. Difference from Existing Approaches
Explain how the paper differs from previous approaches,
methods, systems, or research directions mentioned in the
provided context.

If previous approaches are not available, write:
"Not clearly established from the available paper context."

### 3. Novel Contribution
State the main original contribution of the paper in
1-2 concise points.

### 4. Novelty Type
Classify the novelty as one or more of:
- Methodological novelty
- System / Integration novelty
- Application novelty
- Theoretical / Conceptual novelty
- Not clearly established

Briefly explain why.

### 5. Novelty Limitation
State what cannot be confidently claimed as novel based on
the available paper context.

IMPORTANT:
Do not assume that using Generative AI, LLMs, ChatGPT,
LangChain, LangGraph, SLAM, or any existing technology is
automatically novel.

A paper may be novel because of:
- a new method
- a new architecture
- a new combination of existing methods
- a new application of an existing method
- a new theoretical perspective

Clearly distinguish between these cases.

### 6. Novelty Verdict
Give a final novelty verdict in 1-2 concise sentences.

STRICT RULES:
- Use ONLY information supported by the provided paper context.
- Do not invent citations, authors, prior papers, datasets,
  baselines, experimental results, percentages, accuracy values,
  or metrics.
- Never invent performance numbers.
- Do not claim "state-of-the-art" unless explicitly supported.
- Do not claim a method is completely new unless the context
  clearly supports it.
- Clearly distinguish explicit evidence from reasonable inference.
- If novelty cannot be confirmed from the context, explicitly say so.
- If information is missing, write:
  "Not specified in the available paper context."
- Keep the complete analysis SHORT and focused.
- Maximum approximately 250-350 words per paper.
"""

    return call_groq_api(
        prompt=question,
        context=context,
    )


# ==========================================================
# Multi-Paper Novelty Analysis Agent
# ==========================================================

def run_novelty_agent(
    topic: str,
    papers: List[Any]
) -> List[Dict[str, str]]:
    """
    Execute novelty analysis for each selected paper separately.

    Each paper receives the same short and consistent
    6-section novelty analysis format.
    """

    results = []

    for paper in papers:

        # Support both object and dictionary paper formats
        if isinstance(paper, dict):
            title = paper.get("title", "Untitled Paper")
            summary = (
                paper.get("summary")
                or paper.get("abstract")
                or "Not specified in the available paper context."
            )
            published = paper.get("published", "Not specified")
        else:
            title = getattr(paper, "title", "Untitled Paper")
            summary = (
                getattr(paper, "summary", None)
                or getattr(paper, "abstract", None)
                or "Not specified in the available paper context."
            )
            published = getattr(
                paper,
                "published",
                "Not specified"
            )

        paper_context = f"""
Title:
{title}

Abstract:
{summary}

Published:
{published}
"""

        question = f"""
You are ResearchX, an expert academic peer reviewer.

Analyze ONLY this selected research paper.

Research Topic: {topic}

Your task is to identify what is genuinely NEW or DISTINCTIVE
about this paper.

This is NOT a summary of the paper.

Use EXACTLY this format:

### 1. Novel Elements
Identify what appears new or distinctive in this paper.

### 2. Difference from Existing Approaches
Explain how this paper differs from previous approaches
ONLY if such approaches are supported by the provided context.

If unavailable, write:
"Not clearly established from the available paper context."

### 3. Novel Contribution
State the main original contribution in 1-2 concise points.

### 4. Novelty Type
Choose one or more:
- Methodological novelty
- System / Integration novelty
- Application novelty
- Theoretical / Conceptual novelty
- Not clearly established

Briefly explain the classification.

### 5. Novelty Limitation
Explain what cannot be confidently claimed as novel based
on the available context.

Do not assume that simply using an existing technology such
as Generative AI, LLMs, ChatGPT, LangChain, SLAM, or another
existing tool is itself novel.

### 6. Novelty Verdict
Give one concise final verdict about the paper's novelty.

STRICT RULES:
- Analyze this paper independently.
- Do not compare it with other selected papers.
- Use ONLY the title, abstract, and provided paper context.
- Do not invent novelty claims.
- Do not invent citations, prior papers, authors, datasets,
  metrics, accuracy values, percentages, or experimental results.
- Never generate unsupported numerical findings.
- If the context is insufficient, clearly say so.
- Keep the complete output short and focused.
- Maximum approximately 250-350 words.
"""

        try:
            result = call_groq_api(
                prompt=question,
                context=paper_context,
            )
        except Exception as e:
            print(
                f"[Novelty Agent Error for '{title}']: {e}"
            )
            result = (
                "Unable to generate novelty analysis for this paper."
            )

        results.append({
            "paper_name": title,
            "result": result,
        })

    return results


# ==========================================================
# Backward-Compatible Alias
# ==========================================================

generate_novelty_analysis = analyze_novelty