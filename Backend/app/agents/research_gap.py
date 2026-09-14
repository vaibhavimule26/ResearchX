import re
from typing import Any, Dict, List, Optional, Tuple, Union

from app.agents.coordinator import load_context_for_paper
from app.llm.multi_api_router import (
    call_cohere_api,
    call_mistral_api,
    call_groq_api,
    call_openrouter_api,
)


def clean_gap_output(text: str) -> str:
    """
    Clean LLM research-gap output while preserving valid Markdown tables, headers, and emphasis.
    """
    if not text:
        return ""

    result = text.strip()

    # Strip code block fences if any
    result = re.sub(
        r"^```(?:text|markdown|plain)?\s*",
        "",
        result,
        flags=re.IGNORECASE,
    )
    result = re.sub(r"\s*```$", "", result)

    # Handle literal escaped characters
    result = (
        result.replace("\\r\\n", "\n")
        .replace("\\n", "\n")
        .replace("\\r", "\n")
        .replace('\\"', '"')
        .replace("\\'", "'")
        .replace("\x00", "")
        .replace("\ufffd", "—")
    )

    # Ensure clean blank line before markdown headers
    result = re.sub(r'([^\n])\n(#{1,6}\s+)', r'\1\n\n\2', result)

    # Normalize excessive blank lines
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def run_gap_agent(
    topic: str,
    papers: List[Any],
) -> List[Dict[str, str]]:
    """
    Generate a research-gap comparison table for workspace papers.
    """

    if not papers:
        return [{
            "paper_name": "Research Gaps",
            "result": "No research papers were provided."
        }]

    paper_contexts = []
    paper_titles = []

    print(f"[Gap Agent] Processing {len(papers)} papers...")

    for idx, paper in enumerate(papers, start=1):

        if isinstance(paper, dict):
            title = (
                paper.get("title")
                or paper.get("paper_name")
                or f"Paper {idx}"
            )

            abstract = (
                paper.get("abstract")
                or paper.get("summary")
                or paper.get("why_chosen")
                or paper.get("key_contribution")
                or ""
            )

            authors = paper.get("authors") or ""
            published = paper.get("published") or ""
            venue = paper.get("venue") or ""
            pdf_url = paper.get("pdf_url") or paper.get("url")

        elif isinstance(paper, str):
            title = paper
            abstract = ""
            authors = ""
            published = ""
            venue = ""
            pdf_url = None

        else:
            title = (
                getattr(paper, "title", None)
                or getattr(paper, "paper_name", None)
                or f"Paper {idx}"
            )

            abstract = (
                getattr(paper, "abstract", None)
                or getattr(paper, "summary", None)
                or getattr(paper, "why_chosen", None)
                or getattr(paper, "key_contribution", None)
                or ""
            )

            authors = getattr(paper, "authors", "")
            published = getattr(paper, "published", "")
            venue = getattr(paper, "venue", "")
            pdf_url = getattr(paper, "pdf_url", None) or getattr(paper, "url", None)

        paper_titles.append(title)

        print(f"[Gap Agent] ({idx}/{len(papers)}) PAPER: {title}")

        # Retrieve actual paper evidence
        try:
            paper_context = load_context_for_paper(
                paper_name=title,
                query=topic,
                pdf_url=pdf_url,
            )
        except Exception as e:
            print(f"[Gap RAG Error - {title}]: {e}")
            paper_context = ""

        # Rich context construction
        if not paper_context or len(paper_context.strip()) < 100:
            context_lines = [f"Paper Title: {title}"]
            if authors:
                auth_str = authors if isinstance(authors, str) else ", ".join(map(str, authors))
                context_lines.append(f"Authors: {auth_str}")
            if venue:
                context_lines.append(f"Venue / Source: {venue}")
            if published:
                context_lines.append(f"Published: {published}")
            if abstract and "abstract not available" not in abstract.lower():
                context_lines.append(f"Abstract / Summary:\n{abstract}")
            else:
                context_lines.append(f"Research Focus: Investigates {topic} with specific contribution on {title}.")
            paper_context = "\n".join(context_lines)

        paper_contexts.append(
            f"""==================================================
PAPER {idx}: {title}
==================================================
Paper Context:
{paper_context[:12000]}
"""
        )

    combined_context = "\n\n".join(paper_contexts)
    paper_list_str = "\n".join([f"{i}. {t}" for i, t in enumerate(paper_titles, start=1)])

    print(
        f"[Gap Agent] Combined context length: {len(combined_context)} for {len(papers)} papers."
    )

    question = f"""You are the Research Gap Analysis Agent of ResearchX.

Research Topic: {topic}

You have been provided with {len(papers)} distinct research papers:
{paper_list_str}

Analyze ALL {len(papers)} supplied research papers and generate a comprehensive research-gap comparison table.

OUTPUT FORMAT:

| Paper | Research Gap | Explanation | Evidence |
| :--- | :--- | :--- | :--- |

Create EXACTLY {len(papers)} rows in the table — ONE row for each supplied paper in the list above, in that exact order.

RULES:
1. Every single row MUST have a meaningful, specific Research Gap, Explanation, and Evidence extracted from that paper's focus, methodology, or context.
2. Use the actual paper title in the Paper column.
3. Research Gap: State the primary unresolved challenge, methodological limitation, dataset constraint, or open question exposed or tackled by this paper.
4. Explanation: Explain why this is a research gap and its implications for future work.
5. Evidence: Mention the specific method, architectural constraint, evaluation setup, or task domain from the paper supporting this gap.
6. Do NOT write 'no abstract found' or 'not specified'. Synthesize the research gap from the paper's title, topic scope, and methodology context.
7. Include ALL {len(papers)} papers in the table ({len(papers)} total rows).
8. Keep every table cell concise and clear.
9. Return ONLY the Markdown table.
"""

    result = ""

    # Strategy 1: Cohere Command-R
    try:
        result = call_cohere_api(
            prompt=question,
            context=combined_context,
        )
    except Exception as e:
        print(f"[Gap Agent Cohere Error]: {e}")

    # Strategy 2: Mistral Fallback
    if not result or "| :---" not in result or "failed" in result.lower() or "no llm api" in result.lower():
        try:
            print("[Gap Agent] Falling back to Mistral...")
            result = call_mistral_api(
                prompt=question,
                context=combined_context,
            )
        except Exception as e:
            print(f"[Gap Agent Mistral Error]: {e}")

    # Strategy 3: Groq / OpenRouter Fallback
    if not result or "| :---" not in result or "failed" in result.lower() or "no llm api" in result.lower():
        try:
            print("[Gap Agent] Falling back to Groq / OpenRouter...")
            result = call_groq_api(
                prompt=question,
                context=combined_context,
            )
        except Exception as e:
            print(f"[Gap Agent Groq Error]: {e}")

    result = clean_gap_output(result)

    if not result or "| :---" not in result:
        rows = []
        for t in paper_titles:
            rows.append(f"| {t} | Not clearly established from context | General domain research gap | Evidence based on supplied summary |")
        result = (
            "| Paper | Research Gap | Explanation | Evidence |\n"
            "| :--- | :--- | :--- | :--- |\n" +
            "\n".join(rows)
        )

    return [{
        "paper_name": "Research Gaps",
        "result": result,
    }]


def analyze_research_gap(
    text: str = "",
    title: str = "Uploaded Research Paper",
    query: str = "",
    paper_name: str = "",
    context: str = "",
    pdf_url: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """
    Analyze research gaps from an uploaded research paper context.
    Identifies evidence-grounded research gaps, explicit author limitations,
    and actionable future research directions based specifically on the paper content.
    """

    doc_title = (
        paper_name
        or title
        or kwargs.get("filename", "")
        or "Uploaded Research Paper"
    )

    content = (
        context
        or text
        or kwargs.get("paper_context", "")
        or ""
    )

    # If context is not passed directly, retrieve it from the uploaded paper
    if not content or len(content.strip()) < 100:
        retrieved = load_context_for_paper(
            paper_name=doc_title,
            query=query or "research gaps and limitations",
            pdf_url=pdf_url,
        )
        if retrieved and len(retrieved.strip()) >= 100:
            content = retrieved

    if not content or len(content.strip()) < 50:
        return "Insufficient paper context available to identify reliable research gaps. Please verify the uploaded document."

    paper_context = content[:30000]

    prompt = f"""You are ResearchX, an expert academic research intelligence assistant specializing in rigorous gap analysis.
Analyze the provided research paper context to identify authentic, evidence-grounded RESEARCH GAPS and limitations.

PAPER TITLE: {doc_title}
{f'RESEARCH FOCUS / QUERY: {query.strip()}' if query and query.strip().lower() not in ['gaps', 'research_gap', 'gap', 'summary'] else ''}

STRICT EVIDENCE DIRECTIVES:
1. Every research gap MUST be grounded specifically in the supplied research paper context.
2. Differentiate between:
   - Explicit limitations directly acknowledged by the authors in the paper.
   - Genuine unresolved methodological, algorithmic, or empirical boundaries exposed by the paper's design or evaluation setup.
3. Do NOT invent hypothetical scenarios, unrelated benchmarks, or imaginary attack vectors unless explicitly discussed in the paper.
4. Output in clean, professional Markdown.

FORMAT YOUR RESPONSE USING THESE EXACT SECTIONS:

### 1. Research Scope & Problem Overview
- **Domain & Core Focus:** Specific academic domain and the central research objective addressed by this paper.
- **Target Bottleneck:** The specific technical bottleneck, algorithmic limitation, or inefficiency the authors set out to resolve.
- **Foundational Assumptions:** Key operating assumptions made by the proposed methodology.

### 2. Primary Research Gaps & Limitations
#### Research Gap 1: [Concise Technical Title of the Gap]
- **Gap Category:** [e.g., Algorithmic Complexity / Generalization Boundary / Empirical Scope / Scalability Constraint / Hardware Dependency]
- **Core Limitation:** 2-3 precise sentences explaining the gap and why it presents a bottleneck.
- **Evidence from Paper:** Concrete evidence, mechanism, metric, or boundary condition stated in the uploaded text.
- **Open Research Challenge:** What remains unresolved for subsequent researchers.

#### Research Gap 2: [Concise Technical Title of the Gap]
- **Gap Category:** [e.g., Algorithmic Complexity / Generalization Boundary / Empirical Scope / Scalability Constraint / Hardware Dependency]
- **Core Limitation:** 2-3 precise sentences explaining the gap.
- **Evidence from Paper:** Concrete evidence or limitation from the paper context.
- **Open Research Challenge:** What remains unresolved for subsequent researchers.

#### Research Gap 3: [Concise Technical Title of the Gap]
- **Gap Category:** [e.g., Algorithmic Complexity / Generalization Boundary / Empirical Scope / Scalability Constraint / Hardware Dependency]
- **Core Limitation:** 2-3 precise sentences explaining the gap.
- **Evidence from Paper:** Concrete evidence or limitation from the paper context.
- **Open Research Challenge:** What remains unresolved for subsequent researchers.

### 3. Author-Acknowledged Limitations vs. Unresolved Boundaries
- **Explicit Limitations Acknowledged by Authors:** Direct limitations, failure modes, or computational bounds admitted by the authors.
- **Implicit Architectural & Empirical Boundaries:** Inherent constraints evident from the framework design, dataset diversity, or evaluation scope.

### 4. Actionable Future Research Directions
1. **[Future Direction 1]:** Concrete, high-impact research vector to address Research Gap 1.
2. **[Future Direction 2]:** Concrete, high-impact research vector to address Research Gap 2.
3. **[Future Direction 3]:** Concrete, high-impact research vector to address Research Gap 3.

### 5. Research Gap Summary Matrix
| Identified Gap | Category | Paper Evidence / Limitation | Future Research Opportunity |
| :--- | :--- | :--- | :--- |
| [Short title 1] | [Category] | [Brief paper evidence] | [Opportunity] |
| [Short title 2] | [Category] | [Brief paper evidence] | [Opportunity] |
| [Short title 3] | [Category] | [Brief paper evidence] | [Opportunity] |
"""

    raw_output = ""

    # Strategy 1: Cohere Command-R (Exceptional for factual grounding & structured reasoning)
    try:
        raw_output = call_cohere_api(prompt=prompt, context=paper_context)
    except Exception as e:
        print(f"[Research Gap Cohere Error]: {e}")

    # Strategy 2: Mistral Fallback
    if not raw_output or not raw_output.strip() or "failed" in raw_output.lower() or "no llm api" in raw_output.lower():
        try:
            print("[Research Gap] Cohere unavailable, falling back to Mistral...")
            raw_output = call_mistral_api(prompt=prompt, context=paper_context)
        except Exception as e:
            print(f"[Research Gap Mistral Error]: {e}")

    # Strategy 3: Groq / OpenRouter Fallback
    if not raw_output or not raw_output.strip() or "failed" in raw_output.lower() or "no llm api" in raw_output.lower():
        try:
            print("[Research Gap] Falling back to Groq / OpenRouter...")
            raw_output = call_groq_api(prompt=prompt, context=paper_context)
        except Exception as e:
            print(f"[Research Gap Groq Error]: {e}")

    cleaned_output = clean_gap_output(raw_output)

    if not cleaned_output:
        return "Unable to analyze research gaps for the provided paper context."

    return cleaned_output


def find_research_gaps(*args: Any, **kwargs: Any) -> str:
    """
    Backwards-compatible alias used by coordinator.py, report.py, and workflow graph.
    """
    kw = dict(kwargs)
    text_arg = (
        args[0]
        if len(args) > 0
        else kw.pop("context", kw.pop("text", kw.get("query", "")))
    )

    title_arg = (
        args[1]
        if len(args) > 1
        else kw.pop("paper_name", kw.pop("title", "Uploaded Research Paper"))
    )

    kw.pop("context", None)
    kw.pop("text", None)
    kw.pop("title", None)
    kw.pop("paper_name", None)

    return analyze_research_gap(
        text=text_arg,
        title=title_arg,
        context=text_arg,
        paper_name=title_arg,
        **kw,
    )