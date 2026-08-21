from app.llm.multi_api_router import call_groq_api


# ==========================================================
# Comparison Agent
# ==========================================================

def compare_papers(context: str) -> str:
    """
    Compare multiple selected research papers using only
    the provided paper context.
    """

    if not context or not context.strip():
        return (
            "Unable to compare papers because "
            "no research paper context was provided."
        )

    question = """
You are ResearchX, an expert academic research assistant.

Analyze and compare ONLY the selected research papers provided
in the context.

Generate a clean and structured comparison in the following format:

### 📄 1. Papers Compared

List the titles of all selected papers.

---

### 🎯 2. Research Objectives

For each paper, briefly explain its main research objective.

---

### ⚙️ 3. Methodology Comparison

Compare the methods, frameworks, architectures, models, or
algorithms used by the selected papers.

Clearly mention important similarities and differences.

---

### 📊 4. Datasets and Evaluation

For each paper:
- Mention datasets or benchmarks used.
- Mention evaluation metrics if available.
- If not specified, write: "Not specified in the paper."

---

### 🔬 5. Key Findings

For each paper, briefly state its important findings or
reported results.

Then identify the major differences between the findings.

---

### 💪 6. Strengths and Limitations

For each paper:

**Paper: [Paper Title]**
* **Strength:** Brief strength based only on the provided context.
* **Limitation:** Brief limitation, or "Not specified in the paper."

---

### 🔮 7. Future Research Directions

Compare future work or research directions mentioned across
the selected papers.

If unavailable, write:
"Not specified in the provided papers."

---

### 💡 8. Final Comparison Summary

Provide 3 concise comparison insights:

1. **[Main Similarity]:** Key similarity across the papers.
2. **[Main Difference]:** Most important difference between the papers.
3. **[Overall Insight]:** Which approach appears most suitable for
   its stated objective, based only on the provided information.

IMPORTANT RULES:
- Analyze ONLY the provided paper context.
- Do NOT ask the user for additional information.
- Do NOT invent datasets, metrics, results, methods, or citations.
- If information is missing, write:
  "Not specified in the paper."
- Keep the output concise, structured, and professional.
- Use proper Markdown headings and bullet points.
- If fewer than two papers are provided, clearly state that
  meaningful comparison requires at least two papers.
"""

    return call_groq_api(
        prompt=question,
        context=context,
    )


# ==========================================================
# Workspace Comparison Agent
# ==========================================================

def run_comparison_agent(topic: str, papers) -> str:
    """
    Execute the Comparison Agent for all selected papers.
    """

    print(
        f"Running Comparison Agent for {len(papers)} selected papers..."
    )

    context_parts = []

    for index, paper in enumerate(papers, start=1):

        authors = (
            ", ".join(paper.authors)
            if isinstance(paper.authors, list)
            else (paper.authors or "Not specified")
        )

        context_parts.append(
            f"""
==========================================================
PAPER {index}
==========================================================

Title:
{paper.title}

Authors:
{authors}

Abstract / Summary:
{paper.summary or "Not specified"}

Published:
{paper.published or "Not specified"}

Citation Count:
{getattr(paper, "citation_count", "Not specified")}

Venue:
{getattr(paper, "venue", "Not specified")}

Source:
{getattr(paper, "source", "Not specified")}
"""
        )

    context = "\n".join(context_parts)

    return compare_papers(context)