import re
import concurrent.futures
from typing import Any, Dict, List, Optional
from app.llm.multi_api_router import (
    call_cohere_api,
    call_mistral_api,
    call_groq_api,
    call_openrouter_api,
)
from app.agents.coordinator import load_context_for_paper


def strip_plagiarism_section(text: str) -> str:
    """
    Remove any Plagiarism & Originality Audit section, originality scores,
    similarity risk, novelty overlap, academic integrity verdicts, or plagiarism-related analysis
    from Summary Agent output while preserving all other summary sections.
    """
    if not text:
        return ""
    # Strip any section with heading containing Plagiarism, Originality, Similarity, Academic Integrity
    cleaned = re.sub(
        r'(?i)###\s*\d*\.?\s*(?:Plagiarism|Originality|Similarity|Academic\s*Integrity)\b[^\n]*\n[\s\S]*?(?=(?:\n###|\Z))',
        '',
        text,
    )
    # Strip any individual bullet points related to plagiarism, originality scores, similarity risk, or academic integrity verdict
    cleaned = re.sub(
        r'(?im)^\s*[-*]\s+\*\*(?:Estimated\s+Originality|Similarity\s+Risk|Novelty\s+vs|Academic\s+Integrity\s+Verdict|Textual\s+(?:&|and)\s+Conceptual\s+Authenticity|Textual\s+Uniqueness|Attribution\s+(?:&|and)\s+Paraphrasing)[^*]*\*\*:[^\n]*\n?',
        '',
        cleaned,
    )
    # If section 1 was removed and section 2 is now first, renumber 2,3,4 to 1,2,3
    if re.search(r'^\s*###\s*2\.', cleaned):
        cleaned = re.sub(r'###\s*2\.', '### 1.', cleaned)
        cleaned = re.sub(r'###\s*3\.', '### 2.', cleaned)
        cleaned = re.sub(r'###\s*4\.', '### 3.', cleaned)
        cleaned = re.sub(r'###\s*5\.', '### 4.', cleaned)
    return cleaned.strip()


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

    if is_custom_query:
        prompt = f"""You are ResearchX, an expert academic research intelligence assistant.
Provide a brief, concise, and systematic analysis of the provided research paper addressing the user's query.

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
"""
    else:
        prompt = """You are ResearchX, an expert academic research intelligence assistant.
Provide a brief, concise, and systematic research summary of this paper using ONLY the supplied paper context.

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
    cleaned = strip_plagiarism_section(cleaned)
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
    cleaned = strip_plagiarism_section(cleaned)
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