from app.llm.gemini import generate_answer


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

    return generate_answer(
        context=context,
        question=question,
    )


# ==========================================================
# Workspace Summary
# ==========================================================

def summarize_workspace(topic: str, papers) -> str:
    """
    Generate a structured multi-paper research synthesis.
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

Analyze ONLY the information provided in the papers. Generate a structured multi-paper research synthesis.

Include:

### 📚 1. Research Overview & Problems
* **🔍 Overview & Core Problems:** Briefly state the core area and primary challenges addressed across the papers.

---

### 🔗 2. Common Methods & Trends
* **⚙️ Methodological Trends:** Highlight recurring approaches, architectures, or benchmark datasets used across the papers.

---

### 📈 3. Key Findings & Limitations
* **📊 Synthesis Findings:** Summarize collective breakthroughs and recurring limitations.

---

### 💡 4. Overall Takeaways
1. **[Synthesis Insight 1]:** High-level takeaway across all reviewed papers.
2. **[Synthesis Insight 2]:** High-level takeaway across all reviewed papers.
3. **[Synthesis Insight 3]:** High-level takeaway across all reviewed papers.

IMPORTANT RULES:
- Keep bullet markers and bold headings properly formatted on the same line.
- Base every point strictly on the provided papers.
- Do not invent facts or metrics.
- If information is unavailable, write: "Not specified in the provided papers."
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