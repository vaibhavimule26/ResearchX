from app.llm.multi_api_router import call_cohere_api


# ==========================================================
# Single Paper Summary Agent
# ==========================================================

def summarize_paper(context: str) -> str:
    """
    Generate a clean, structured research summary for a single paper.
    """

    question = """
You are ResearchX, an expert academic research assistant.

Analyze ONLY the research paper provided in the context.

Generate a structured, professional research summary following this exact format:

### 📌 1. Research Snapshot
* **🎯 Problem:** Direct 1-2 sentence problem statement.
* **⚙️ Method:** Direct 1-2 sentence method/framework summary.
* **🌐 Domain:** Core research field/subfield.
* **🚀 Objective:** Main goal and focus of the study.

---

### 📊 2. Key Findings & Results
* **🏆 Main Performance:** Primary quantitative metric and benchmark outcome.
* **⚔️ Baseline Comparison:** Comparison against existing models/baselines.
* **🔬 Module Impact:** Key insight from ablation or architectural studies.

---

### ⚠️ 3. Limitations & Future Outlook
* **🛑 Limitation:** Explicit limitation mentioned in paper, or "Not specified in the paper."
* **🔭 Future Direction:** Explicit future direction mentioned in paper, or "Not specified in the paper."

---

### 💡 4. Core Takeaways
1. **[Key Insight 1 Title]:** Concise, high-value takeaway statement.
2. **[Key Insight 2 Title]:** Concise, high-value takeaway statement.
3. **[Key Insight 3 Title]:** Concise, high-value takeaway statement.

IMPORTANT RULES:
- Keep bullet markers (* or 1.) and bold titles on the same line as the text.
- Do NOT insert broken empty lines immediately after asterisks.
- Rely strictly on facts present in the paper. Do NOT hallucinate.
- If information is missing, clearly write: "Not specified in the paper."
"""

    return call_cohere_api(
        prompt=question,
        context=context,
    )


# ==========================================================
# Workspace Summary
# ==========================================================

def summarize_workspace(topic: str, papers) -> list:
    """
    Generate an individual structured summary for every selected paper.
    """

    results = []

    for paper in papers:
        title = getattr(paper, "title", "Untitled Paper")
        
        authors_raw = getattr(paper, "authors", "Not specified")
        authors = (
            ", ".join(authors_raw)
            if isinstance(authors_raw, list)
            else (authors_raw or "Not specified")
        )

        abstract = (
            getattr(paper, "summary", None)
            or getattr(paper, "abstract", None)
            or "Not specified in the available paper context."
        )

        published = getattr(paper, "published", "Not specified")
        citation_count = getattr(paper, "citation_count", "Not specified")
        venue = getattr(paper, "venue", "Not specified")
        source = getattr(paper, "source", "Not specified")

        paper_context = f"""
Title:
{title}

Authors:
{authors}

Abstract / Available Paper Content:
{abstract}

Published:
{published}

Citation Count:
{citation_count}

Venue:
{venue}

Source:
{source}
"""

        summary = summarize_paper(paper_context)

        results.append({
            "paper_name": title,
            "result": summary,
        })

    return results


# ==========================================================
# Workspace Summary Agent
# ==========================================================

def run_summary_agent(topic: str, papers) -> list:
    """
    Execute the Summary Agent separately for every selected paper.
    """

    print(f"Running Summary Agent for {len(papers)} selected papers...")

    return summarize_workspace(
        topic=topic,
        papers=papers,
    )