from app.llm.multi_api_router import call_groq_api


# ==========================================================
# Comparison Agent
# ==========================================================

def compare_papers(context: str) -> str:
    """
    Compare multiple selected research papers using evidence-grounded
    scholarly synthesis and a comprehensive Markdown comparison table.
    """
    if not context or not context.strip():
        return (
            "Unable to compare papers because no research paper context was provided."
        )

    question = """
You are a senior academic peer reviewer and research domain expert.

Analyze and compare ONLY the selected research papers provided in the context.
Synthesize the technical trade-offs, methodological differences, and experimental outcomes in authentic, scholarly academic prose.

STRICT ACADEMIC WRITING & ANTI-PLAGIARISM RULES:
1. Paraphrase and synthesize conceptually; do NOT copy full sentences verbatim from abstracts.
2. Avoid generic AI cliché phrases (e.g., "delve into", "a testament to", "the tapestry of", "it is important to note", "pivotal role", "game-changer", "beacon").
3. Use precise, active scientific language.
4. Ground every comparison strictly in the provided paper context.

Generate the output using EXACTLY this structure:

### 1. Comparative Matrix

Generate a structured Markdown table comparing all analyzed papers:

| Paper | Core Objective | Methodology / Architecture | Datasets & Benchmarks | Key Findings & Metrics | Limitations & Gaps |
| :--- | :--- | :--- | :--- | :--- | :--- |

(Fill one complete row per paper. Keep cell entries concise and factual. If information is not available, write "Not specified".)

---

### 2. Methodological Trade-offs & Differences
Provide a concise 2-3 paragraph technical critique comparing how the proposed models/architectures differ in computational complexity, inductive biases, and architectural design choices.

---

### 3. Experimental & Empirical Comparison
Detail the benchmark datasets, evaluation criteria, and empirical outcomes reported across the papers. Highlight where approaches excel or fall short.

---

### 4. Cross-Study Synthesis & Future Vectors
Summarize the primary consensus, biggest unaddressed challenge across the papers, and the most promising future research vector in 3 crisp numbered takeaways:
1. **Consensus:** Primary shared insight or confirmed finding.
2. **Key Divergence:** Core technical trade-off between the approaches.
3. **Open Vector:** Most critical unaddressed problem requiring future investigation.
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

    if not papers:
        return "No research papers were provided for comparative analysis."

    print(
        f"Running Comparison Agent for {len(papers)} selected papers..."
    )

    context_parts = []

    for index, paper in enumerate(papers, start=1):

        if isinstance(paper, dict):
            title = paper.get("title", "Untitled Paper")
            authors = paper.get("authors", "Not specified")
            summary = paper.get("summary") or paper.get("abstract", "Not specified")
            published = paper.get("published", "Not specified")
            citation_count = paper.get("citation_count") or paper.get("citations", "Not specified")
            venue = paper.get("venue", "Not specified")
            source = paper.get("source", "Not specified")
        else:
            title = getattr(paper, "title", "Untitled Paper")
            authors = getattr(paper, "authors", "Not specified")
            summary = getattr(paper, "summary", None) or getattr(paper, "abstract", "Not specified")
            published = getattr(paper, "published", "Not specified")
            citation_count = getattr(paper, "citation_count", None) or getattr(paper, "citations", "Not specified")
            venue = getattr(paper, "venue", "Not specified")
            source = getattr(paper, "source", "Not specified")

        if isinstance(authors, list):
            authors = ", ".join(map(str, authors))

        context_parts.append(
            f"""
==========================================================
PAPER {index}
==========================================================

Title:
{title}

Authors:
{authors}

Abstract / Summary:
{summary}

Published:
{published}

Citation Count:
{citation_count}

Venue:
{venue}

Source:
{source}
"""
        )

    context = "\n".join(context_parts)

    return compare_papers(context)