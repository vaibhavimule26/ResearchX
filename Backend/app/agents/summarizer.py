import concurrent.futures
from typing import Any, Dict, List, Optional
from app.llm.multi_api_router import (
    call_cohere_api,
    call_mistral_api,
    call_groq_api,
    call_openrouter_api,
)
from app.agents.coordinator import load_context_for_paper


# ==========================================================
# Single Paper Summary Agent
# ==========================================================

def summarize_paper(
    context: str,
    paper_name: Optional[str] = None,
    query: str = "",
    pdf_url: Optional[str] = None,
) -> str:
    """
    Generate a factual, structured academic summary or query-focused analysis
    for one paper, strictly grounded in the supplied paper context.
    """

    print("\n================ SUMMARY RETRIEVAL DEBUG ================")
    print(f"PAPER: {paper_name}")
    print(f"PDF URL: {pdf_url}")
    print(f"QUERY: {query}")

    # ------------------------------------------------------
    # Retrieve actual paper context if not already provided
    # ------------------------------------------------------
    if paper_name and (not context or len(context.strip()) < 100):
        retrieved_context = load_context_for_paper(
            paper_name=paper_name,
            query=query,
            pdf_url=pdf_url,
        )

        print(
            f"RETRIEVED CONTEXT LENGTH: "
            f"{len(retrieved_context or '')}"
        )

        if retrieved_context and len(retrieved_context.strip()) >= 100:
            context = retrieved_context

    print("==========================================================\n")

    if not context or not context.strip():
        return "Insufficient paper context available for summary."

    # ------------------------------------------------------
    # Query vs. Standard Summary Prompt
    # ------------------------------------------------------
    q_clean = (query or "").strip().lower()
    is_plagiarism_query = any(
        k in q_clean
        for k in ["plagiar", "similarity", "originality", "integrity", "authenticity", "copy"]
    )
    is_custom_query = bool(
        q_clean
        and q_clean not in [
            "summary",
            "summarize",
            "summarize this paper",
            "executive summary",
            "executive_summary",
            "academic research topic",
        ]
    )

    if is_plagiarism_query:
        prompt = f"""You are ResearchX, an expert academic research intelligence and integrity assistant.
Analyze the provided research paper context to perform a brief, concise, and systematic PLAGIARISM & ORIGINALITY AUDIT along with an executive summary.

USER RESEARCH QUERY:
"{query.strip()}"

STRICT CITATION DIRECTIVE:
- DO NOT include citations, bracketed numbers, section tags (e.g. [Sec. 1], [Table 1], [Eq. 1]), or bibliography lists. Citations are explicitly NOT needed.
- Ground all findings strictly in the provided paper context. Be brief, concise, and systematic.

FORMAT YOUR RESPONSE IN CLEAN MARKDOWN WITH THESE SECTIONS:

### 1. Plagiarism & Originality Audit
- **Estimated Originality / Similarity Risk:** Provide an explicit risk assessment (e.g., Low Similarity Risk — Estimated Originality: 90-95%) with brief rationale.
- **Novelty vs. Prior Art Overlap:** Delineate genuine author innovations versus concepts, modules, or baselines adopted from existing academic literature.
- **Textual Uniqueness & Phrasing:** Evaluate whether the paper demonstrates authentic, original scholarly formulation or exhibits signs of boilerplate, repetitive formulas, or copied phrasing.
- **Attribution & Paraphrasing Integrity:** Check whether prior methods and benchmarks are properly framed rather than improperly claimed as the authors' own inventions.
- **Academic Integrity Verdict:** A clear scholarly verdict on publication readiness, originality, and plagiarism risk.

### 2. Executive Overview of Paper
- **Core Problem Addressed:** Concise 1-2 sentence explanation of the limitation or bottleneck targeted by the paper.
- **Proposed Solution & Architecture:** How the authors solve the problem and how the system operates.

### 3. Key Findings & Empirical Benchmarks
- **Evaluated Benchmarks & Models:** Datasets, task suites, and LLM backbones evaluated.
- **Reported Outcomes:** Concrete quantitative performance metrics and accuracy gains reported.

### 4. Core Contributions & Key Takeaways
- **Main Contributions:** 2-3 bullet points highlighting the primary technical and practical innovations.
- **Practical Takeaways:** The essential conclusions from the work.
"""
    elif is_custom_query:
        prompt = f"""You are ResearchX, an expert academic research intelligence assistant.
Provide a brief, concise, and systematic analysis of the provided research paper addressing the user's query, followed by an originality and plagiarism assessment.

USER RESEARCH QUERY:
"{query.strip()}"

STRICT CITATION DIRECTIVE:
- DO NOT include citations, bracketed numbers, section tags (e.g. [Sec. 1], [Table 1], [Eq. 1]), or bibliography lists. Citations are explicitly NOT needed.
- Ground every statement strictly in the context with high factual accuracy. Be brief, concise, and systematic.

FORMAT YOUR RESPONSE IN CLEAN MARKDOWN USING THESE SECTIONS:

### 1. Direct Synthesis & Core Findings
A brief, systematic direct answer to the query with explicit paper evidence, without any citation brackets or section markers.

### 2. Systematic Technical Architecture & Methodology
- **Core Mechanism & Design:** Concise breakdown of framework components, representations, and workflows relevant to the query.
- **Operational Workflow:** Step-by-step technical execution or protocol.
- **Key Technical Distinctions:** How this mechanism specifically differs from traditional baselines.

### 3. Empirical Evidence, Benchmarks & Metrics
- **Evaluated Benchmarks & Tasks:** Specific benchmark suites and domains evaluated.
- **Quantitative Metrics & Results:** Concrete numerical metrics, accuracy percentages, and comparisons reported.

### 4. Critical Takeaways & Limitations
- **Primary Advantages:** Key technical differentiators.
- **Reported Limitations:** Computational overhead or boundary constraints acknowledged by authors.

### 5. Plagiarism & Originality Audit
- **Estimated Originality / Similarity Risk:** Explicit risk level and estimated originality percentage (e.g., Low Similarity Risk — Estimated Originality: 90-95%).
- **Novelty vs. Prior Art Overlap:** Delineation of original mechanisms versus standard techniques adopted from prior literature.
- **Textual & Conceptual Authenticity:** Assessment of whether the methodology and explanations are genuinely original scholarly prose.
- **Academic Integrity Verdict:** Scholarly verdict evaluating proper framing of prior art and publication-grade originality.
"""
    else:
        prompt = """You are ResearchX, an expert academic research intelligence assistant.
Provide a brief, concise, and systematic research summary of this paper using ONLY the supplied paper context, followed by an originality and plagiarism assessment.

STRICT CITATION DIRECTIVE:
- DO NOT include citations, bracketed numbers, section tags (e.g. [Sec. 1], [Table 1], [Eq. 1]), or bibliography lists. Citations are explicitly NOT needed.
- Ground every claim, number, and finding strictly in the context. Be brief, concise, and systematic.

FORMAT YOUR RESPONSE IN CLEAN MARKDOWN USING THESE SECTIONS:

### 1. Research Problem, Motivation & Objectives
- **Problem Statement:** Concise 1-2 sentence statement of the core problem or limitation in prior work.
- **Core Research Objective:** The central thesis, proposed system, and high-level goal.

### 2. Methodology & Technical Architecture
- **Framework Architecture:** Concise overview of the system pipeline, modular roles, and communication channels.
- **Operational Mechanism:** Step-by-step breakdown of how the method executes.
- **Key Architectural Novelty:** Primary technical distinction from baseline methods.

### 3. Empirical Evaluation & Quantitative Findings
- **Task Domains & Datasets:** Specific benchmark suites and evaluation domains tested.
- **Quantitative Results & Gains:** Explicit accuracy numbers, percentage improvements, and metrics reported.

### 4. Core Contributions & Takeaways
- **Theoretical & Technical Innovations:** 2-3 concise bullet points highlighting primary contributions.
- **Practical Takeaways:** Key practical conclusions from the work.

### 5. Plagiarism & Originality Audit
- **Estimated Originality / Similarity Risk:** Explicit risk level and estimated originality percentage (e.g., Low Similarity Risk — Estimated Originality: 90-95%).
- **Novelty vs. Prior Art Overlap:** Delineation of original mechanisms versus standard techniques adopted from prior literature.
- **Textual & Conceptual Authenticity:** Assessment of whether the methodology and explanations are genuinely original scholarly prose.
- **Academic Integrity Verdict:** Scholarly verdict evaluating proper contextualization of prior art and publication-grade originality.
"""

    # ------------------------------------------------------
    # Execute LLM with multi-API fallback
    # ------------------------------------------------------
    summary = ""

    # Strategy 1: Cohere Command-R (Best for long-context research)
    try:
        summary = call_cohere_api(prompt=prompt, context=context)
    except Exception as e:
        print(f"[Summary Agent Cohere Error]: {e}")

    # Strategy 2: Mistral Fallback
    if not summary or not summary.strip() or "failed" in summary.lower() or "no llm api" in summary.lower():
        try:
            print("[Summary Agent] Cohere unavailable, falling back to Mistral...")
            summary = call_mistral_api(prompt=prompt, context=context)
        except Exception as e:
            print(f"[Summary Agent Mistral Error]: {e}")

    # Strategy 3: Groq / OpenRouter Fallback
    if not summary or not summary.strip() or "failed" in summary.lower() or "no llm api" in summary.lower():
        try:
            print("[Summary Agent] Falling back to Groq / OpenRouter...")
            summary = call_groq_api(prompt=prompt, context=context)
        except Exception as e:
            print(f"[Summary Agent Groq Error]: {e}")

    if not summary or not summary.strip():
        return "Unable to generate an accurate summary from the provided paper context."

    import re

    # Strip any LLM meta-disclaimers about placeholders if present
    cleaned = summary.strip()
    placeholder_phrases = [
        "Please note that the citations provided are placeholders and should be replaced with the actual references from the research paper.",
        "Please note that the citations provided are placeholders",
        "Note: Citations provided are placeholders",
    ]
    for phrase in placeholder_phrases:
        cleaned = cleaned.replace(phrase, "").strip()

    # Strictly strip any accidental bracketed citations or section markers
    cleaned = re.sub(r'\[\s*(?:Sec\.|Section|Table|Figure|Fig\.|Eq\.|Equation)\s*[\w\d\.\,\s\-]+\]', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\[[A-Z][a-zA-Z\s\.\-]+,\s*\d{4}[a-z]?\]', '', cleaned)
    cleaned = re.sub(r'\[\d+\]', '', cleaned)
    cleaned = re.sub(r'###\s*5?\.\s*Evidence\s*Map.*?(?=(###|$))', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = cleaned.replace("\x00", "").replace("\ufffd", "—")

    # Ensure markdown headers have clean blank lines before them
    cleaned = re.sub(r'([^\n])\n(#{1,6}\s+)', r'\1\n\n\2', cleaned)

    return cleaned.strip()


# ==========================================================
# Workspace Single Paper Summary
# ==========================================================

def summarize_paper_for_workspace(
    context: str,
    paper_name: Optional[str] = None,
    topic: str = "",
) -> str:
    """
    Generate a concise, factual executive summary for one paper inside AI Workspace.
    Tailored specifically for multi-paper comparative research without plagiarism audits.
    """
    topic_clean = (topic or "").strip()
    has_custom_topic = bool(
        topic_clean
        and topic_clean.lower() not in [
            "summary",
            "summarize",
            "executive summary",
            "academic research topic",
        ]
    )

    prompt = f"""You are ResearchX, an expert academic research assistant.
Analyze the provided research paper context to generate a concise, factual, and structured research summary.
{f'RESEARCH TOPIC FOCUS: {topic_clean}' if has_custom_topic else ''}

FORMAT YOUR RESPONSE IN CLEAN MARKDOWN FOLLOWING THIS EXACT STRUCTURE:

### Executive Overview
- **Research Problem:** Concise statement of the core problem, domain, and primary research objective.
- **Methodology & Framework:** The proposed approach, architecture, or algorithmic technique.

### Key Findings & Empirical Evaluation
- **Primary Performance:** Quantitative metrics, accuracy gain, or primary benchmark results.
- **Baseline Comparisons:** How the model compares to relevant baselines or prior work.

### Limitations & Open Challenges
- **Author Limitations:** Limitations explicitly acknowledged in the paper.
- **Future Directions:** Unresolved challenges and suggested future research directions.

### Core Takeaways
1. **[Key Innovation]:** Primary innovative takeaway.
2. **[Practical Utility]:** Practical implementation value.
3. **[Research Significance]:** Broader research significance.

STRICT RULES:
- Rely strictly on facts present in the paper context. Do NOT hallucinate.
- If information is missing, clearly write: "Not specified in the paper."
"""

    summary = ""
    try:
        summary = call_cohere_api(prompt=prompt, context=context)
    except Exception as e:
        print(f"[Workspace Summary Cohere Error]: {e}")

    if not summary or not summary.strip() or "failed" in summary.lower() or "no llm api" in summary.lower():
        try:
            summary = call_mistral_api(prompt=prompt, context=context)
        except Exception as e:
            print(f"[Workspace Summary Mistral Error]: {e}")

    if not summary or not summary.strip() or "failed" in summary.lower() or "no llm api" in summary.lower():
        try:
            summary = call_groq_api(prompt=prompt, context=context)
        except Exception as e:
            print(f"[Workspace Summary Groq Error]: {e}")

    if not summary or not summary.strip():
        return "Unable to generate paper summary from the available context."

    import re
    cleaned = summary.strip()
    cleaned = cleaned.replace("\x00", "").replace("\ufffd", "—")
    cleaned = re.sub(r'([^\n])\n(#{1,6}\s+)', r'\1\n\n\2', cleaned)
    return cleaned.strip()


# ==========================================================
# Workspace Summary
# ==========================================================

def summarize_workspace(topic: str, papers: List[Any]) -> List[Dict[str, str]]:
    """
    Generate one concise summary for every selected paper in the AI Workspace.
    Uses concurrent workers when multiple papers are selected.
    """
    if not papers:
        return []

    def _summarize_single(paper):
        if isinstance(paper, dict):
            title = paper.get("title") or "Untitled Paper"
            authors_raw = paper.get("authors") or "Not specified"
            published = paper.get("published") or "Not specified"
            citation_count = paper.get("citation_count") or 0
            venue = paper.get("venue") or "Not specified"
            source = paper.get("source") or "Not specified"
            pdf_url = paper.get("pdf_url")
            abstract = paper.get("abstract") or paper.get("summary")
        else:
            title = getattr(
                paper,
                "title",
                "Untitled Paper"
            )

            authors_raw = getattr(
                paper,
                "authors",
                "Not specified"
            )

            published = getattr(
                paper,
                "published",
                "Not specified"
            )

            citation_count = getattr(
                paper,
                "citation_count",
                0
            )

            venue = getattr(
                paper,
                "venue",
                "Not specified"
            )

            source = getattr(
                paper,
                "source",
                "Not specified"
            )

            pdf_url = getattr(
                paper,
                "pdf_url",
                None
            )

            abstract = (
                getattr(paper, "abstract", None)
                or getattr(paper, "summary", None)
            )

        if isinstance(authors_raw, list):
            authors = ", ".join(map(str, authors_raw))
        else:
            authors = str(authors_raw) if authors_raw else "Not specified"

        paper_context = load_context_for_paper(
            paper_name=title,
            query=topic,
            pdf_url=pdf_url,
        )

        print(
            "\n================ RAG SUMMARY CONTEXT ================"
        )
        print(f"PAPER: {title}")
        print(f"CONTEXT LENGTH: {len(paper_context or '')}")
        print((paper_context or "")[:3000])
        print("=====================================================\n")

        if not paper_context or len(paper_context.strip()) < 100:
            paper_context = (
                abstract
                or "Not specified in the available paper context."
            )

        full_context = f"""
Title: {title}

Authors: {authors}

Published: {published}

Citation Count: {citation_count}

Venue: {venue}

Source: {source}

Paper Content:
{paper_context}
"""

        summary = summarize_paper_for_workspace(
            context=full_context,
            paper_name=title,
            topic=topic,
        )

        return {
            "paper_name": title,
            "result": summary,
        }

    if len(papers) == 1:
        return [_summarize_single(papers[0])]

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, len(papers))) as executor:
        return list(executor.map(_summarize_single, papers))


# ==========================================================
# Workspace Summary Agent Entrypoint
# ==========================================================

def run_summary_agent(topic: str, papers: List[Any]) -> List[Dict[str, str]]:
    """
    Execute Summary Agent independently for every selected paper.
    """

    print(
        f"Running Summary Agent for "
        f"{len(papers)} selected papers..."
    )

    return summarize_workspace(
        topic=topic,
        papers=papers,
    )