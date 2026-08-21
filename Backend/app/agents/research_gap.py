import os
import re
from typing import List, Dict, Any
from app.llm.multi_api_router import call_mistral_api, call_groq_api


def clean_markdown_table_formatting(text: str) -> str:
    """Cleans up markdown table delimiters to ensure the frontend markdown parser renders the table correctly."""
    lines = text.split("\n")
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()
        # Ensure rows with pipe delimiters have proper spacing
        if stripped.startswith("|") and stripped.endswith("|"):
            cleaned_lines.append(stripped)
        elif "|" in stripped:
            # Add missing boundary pipes if LLM missed outer borders
            cleaned_lines.append(f"| {stripped} |")
        else:
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def run_gap_agent(topic: str, papers: List[Any]) -> List[Dict[str, str]]:
    """Runs gap analysis across selected research papers strictly using the provided context."""
    results = []

    for paper in papers:
        # Support both Pydantic models (paper.title) and standard dictionaries (paper["title"])
        title = getattr(paper, "title", None) or (paper.get("title") if isinstance(paper, dict) else "Untitled Paper")
        authors = getattr(paper, "authors", None) or (paper.get("authors") if isinstance(paper, dict) else "Not specified")
        summary = (
            getattr(paper, "summary", None)
            or getattr(paper, "abstract", None)
            or (paper.get("summary") or paper.get("abstract") if isinstance(paper, dict) else "Not specified in the paper.")
        )
        published = getattr(paper, "published", None) or (paper.get("published") if isinstance(paper, dict) else "Not specified")

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

        question = f"""
Analyze ONLY this research paper.

Research Topic: {topic}

Identify:
1. Research gaps
2. Limitations
3. Unresolved problems
4. Future research directions

Use only the provided paper context.
If something is missing, write:
"Not specified in the paper."
"""

        try:
            result = call_groq_api(
                prompt=question,
                context=paper_context
            )
        except Exception as e:
            print(f"[Gap Agent Groq Error for '{title}']: {e}")
            result = "Not specified in the paper."

        results.append({
            "paper_name": title,
            "result": result
        })

    return results


def analyze_research_gap(
    text: str = "",
    title: str = "Uploaded Research Paper",
    query: str = "",
    paper_name: str = "",
    **kwargs,
) -> str:
    """Dynamically extracts research gaps and constructs a peer-reviewed Gap Matrix strictly from the uploaded paper context."""
    content = text or query or kwargs.get("context", "")
    doc_title = title or paper_name or "Uploaded Research Paper"

    prompt = f"""You are a Principal AI Scientist and Senior IEEE/ACM Peer Reviewer.
Analyze the following research paper context: "{doc_title}".

Extract and synthesize the research gap strictly into the following 6 structured academic sections.

### 1. Limitations in Existing Systems
* **Architectural & Algorithmic Limitations:** 2-3 concrete technical points extracted from the paper.
* **Data & Representation Limitations:** 2-3 concrete points regarding data constraints or indexing bottlenecks.
* **Evaluation & Hardware Limitations:** 2-3 concrete points regarding benchmark or hardware evaluation gaps.

---

### 2. Missing & Unaddressed Research Areas
* **Overlooked Operational Scenarios:** 2 concise technical edge cases missing in the work.
* **Modality & Input Boundaries:** 2 concise points regarding input, sensor, or language boundaries.
* **Cross-Domain Scalability:** 2 concise points on cross-domain generalization constraints.

---

### 3. Technical & Real-World Impact
* **Academic Impact:** 2 concise sentences on theoretical or algorithmic implications.
* **Practical & End-User Impact:** 2 concise sentences on deployment, safety, and reliability implications.

---

### 4. Identified Research Gap Matrix
Construct a Markdown Table with strictly 3 columns and 4-5 dynamic technical rows extracted directly from the paper context.
You MUST use standard Markdown pipe syntax with header separators:

| Research Gap Area | Current Limitation in Existing Work | Unresolved Critical Bottleneck |
| :--- | :--- | :--- |

---

### 5. Formal Academic Research Gap Statement
* **[Dimension 1 - Core Algorithmic Gap]:** 1-sentence technical gap statement.
* **[Dimension 2 - Data & Scalability Gap]:** 1-sentence technical gap statement.
* **[Dimension 3 - Edge/System Deployment Gap]:** 1-sentence technical gap statement.

---

### 6. Core Research Question
Provide a single publication-ready research question enclosed in blockquotes:
> "Your formulated research question"

Strict Rules:
- Extract ALL findings dynamically from the context. Do not invent or assume unrelated domain details.
- Section 4 MUST be a valid Markdown table with '|' pipes and '| :--- | :--- | :--- |' separator.
- Do NOT output raw JSON or conversational greetings.
"""

    try:
        raw_output = call_mistral_api(prompt, context=content[:14000])
        return clean_markdown_table_formatting(raw_output)
    except Exception as e:
        print(f"[Research Gap Agent Error]: {e}")
        return "Unable to analyze research gaps for the provided context."


def find_research_gaps(*args, **kwargs):
    """Backwards-compatible alias for coordinator and report generators."""
    text_arg = args[0] if len(args) > 0 else kwargs.get("text", kwargs.get("query", ""))
    title_arg = (
        args[1]
        if len(args) > 1
        else kwargs.get("title", kwargs.get("paper_name", "Research Paper"))
    )
    return analyze_research_gap(text=text_arg, title=title_arg, **kwargs)