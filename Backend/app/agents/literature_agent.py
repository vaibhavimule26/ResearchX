from typing import Any, Dict, List

from app.llm.gemini import generate_answer
from app.llm.multi_api_router import call_groq_api


# ==========================================================
# SINGLE PAPER LITERATURE SURVEY AGENT
# ==========================================================


def generate_literature_survey(context: str) -> str:
    """
    Generate a concise, evidence-grounded literature survey
    for one research paper.
    """

    if not context or not context.strip():
        return (
            "Unable to generate literature survey because "
            "no research paper context was provided."
        )

    question = """
Analyze ONLY the provided research paper context.

Act as a research literature survey assistant.

Generate a SHORT and ACCURATE literature survey for THIS
single paper only.

Use EXACTLY this Markdown structure:

### 1. Research Area
- **Domain:** State the research domain mentioned or clearly
  supported by the paper.
- **Problem:** State the main problem addressed by the paper.

---

### 2. Main Approach
- Briefly describe the main method, model, system, or approach
  proposed or discussed in the paper.
- If unavailable, write: Not specified in paper.

---

### 3. Key Contribution
- State the main contribution or purpose of the paper.
- Do not claim novelty unless explicitly supported by the paper.

---

### 4. Related Work / Research Direction
- Mention ONLY previous approaches, systems, methods, or research
  directions explicitly mentioned in the paper context.
- If no previous work is clearly mentioned, write:
  Not specified in paper.

---

### 5. Research Gap / Limitation
- State ONLY limitations, gaps, or unresolved problems explicitly
  mentioned or clearly supported by the paper.
- Do NOT invent future problems or limitations.
- If unavailable, write: Not specified in paper.

---

### 6. Paper Position
- In 1-2 short sentences, explain how this paper addresses
  the identified problem or research direction.
- If unavailable, write: Not specified in paper.

---

### 7. Quick Takeaway
- Write ONE concise sentence summarizing the paper.

STRICT RULES:
- Analyze ONLY the provided paper.
- Do NOT use external knowledge.
- Do NOT compare with other selected papers.
- Do NOT invent authors, citations, publication years, datasets,
  models, methods, tools, experiments, metrics, or results.
- Do NOT mention famous systems or examples unless explicitly
  present in the paper context.
- Do NOT infer specific prior work from general domain knowledge.
- If information is missing, write exactly:
  Not specified in paper.
- Keep the TOTAL response under 250 words.
- Keep every section concise.
- Do not add any sections outside the required format.
"""

    try:
        return generate_answer(
            context=context,
            question=question,
        )

    except Exception as e:
        print(f"[Literature Survey Agent Error]: {e}")
        return "Unable to generate literature survey."


# ==========================================================
# MULTI-PAPER WORKSPACE LITERATURE AGENT
# ==========================================================


def run_literature_agent(
    topic: str, papers: List[Any]
) -> List[Dict[str, str]]:
    """
    Generate one concise literature survey for each selected paper.

    Each paper is analyzed independently.
    No comparison is made between selected papers.
    """

    results = []

    for paper in papers:

        # --------------------------------------------------
        # GET PAPER TITLE
        # --------------------------------------------------

        if isinstance(paper, dict):
            title = paper.get("title", "Untitled Paper")
        else:
            title = getattr(paper, "title", "Untitled Paper")

        # --------------------------------------------------
        # GET AUTHORS
        # --------------------------------------------------

        if isinstance(paper, dict):
            authors = paper.get("authors", "Not specified")
        else:
            authors = getattr(paper, "authors", "Not specified")

        if isinstance(authors, list):
            authors = ", ".join(map(str, authors))

        # --------------------------------------------------
        # GET ABSTRACT / SUMMARY
        # --------------------------------------------------

        if isinstance(paper, dict):
            summary = (
                paper.get("abstract")
                or paper.get("summary")
                or "Not specified in paper."
            )
        else:
            summary = (
                getattr(paper, "abstract", None)
                or getattr(paper, "summary", None)
                or "Not specified in paper."
            )

        # --------------------------------------------------
        # GET PUBLISHED DATE
        # --------------------------------------------------

        if isinstance(paper, dict):
            published = paper.get("published", "Not specified")
        else:
            published = getattr(paper, "published", "Not specified")

        # --------------------------------------------------
        # CREATE PAPER CONTEXT
        # --------------------------------------------------

        paper_context = f"""
Title:
{title}

Authors:
{authors}

Abstract:
{summary}

Published:
{published}
"""

        # --------------------------------------------------
        # PROMPT
        # --------------------------------------------------

        question = f"""
Analyze ONLY this selected research paper.

Research Topic: {topic}

Generate a SHORT and ACCURATE literature survey using ONLY
the provided paper title, abstract, and context.

Use EXACTLY this format:

### 1. Research Area
- Domain:
- Problem:

### 2. Main Approach
Briefly explain the method, system, model, framework, or
solution proposed in the paper.

### 3. Key Contribution
State the main contribution of the paper in 1-2 concise points.

### 4. Related Work / Research Direction
Mention previous methods, systems, concepts, or research
directions ONLY if they are present in the paper context.
If unavailable, write:
"Not specified in the available paper context."

### 5. Research Gap / Limitation
Identify the gap, limitation, challenge, or unmet need that
motivates this paper.

You may infer the gap ONLY when it is directly supported by
the problem statement or motivation in the provided context.
Do not invent unsupported limitations.

### 6. Paper Position
Explain in one concise statement how this paper addresses
the identified problem or gap.

### 7. Quick Takeaway
Give one short, simple academic takeaway.

STRICT RULES:
- Keep the complete analysis SHORT and focused.
- Maximum approximately 250-350 words per paper.
- Do not generate a long 13-section literature review.
- Do not compare this paper with other selected papers.
- Do not invent authors, citations, papers, methods, results,
  datasets, or limitations.
- Use only information supported by the available paper context.
- If information is missing, clearly state:
  "Not specified in the available paper context."
- Keep the same EXACT structure for every selected paper.
"""

        # --------------------------------------------------
        # CALL LLM
        # --------------------------------------------------

        try:
            result = call_groq_api(
                prompt=question,
                context=paper_context,
            )

        except Exception as e:
            print(f"[Literature Agent Groq Error for '{title}']: {e}")

            result = """### 1. Research Area
- Domain: Not specified in the available paper context.
- Problem: Not specified in the available paper context.

### 2. Main Approach
Not specified in the available paper context.

### 3. Key Contribution
Not specified in the available paper context.

### 4. Related Work / Research Direction
Not specified in the available paper context.

### 5. Research Gap / Limitation
Not specified in the available paper context.

### 6. Paper Position
Not specified in the available paper context.

### 7. Quick Takeaway
Unable to generate literature survey."""

        # --------------------------------------------------
        # SAVE RESULT
        # --------------------------------------------------

        results.append({"paper_name": title, "result": result})

    return results


# ==========================================================
# BACKWARD-COMPATIBLE ALIAS
# ==========================================================

run_literature_survey_agent = run_literature_agent