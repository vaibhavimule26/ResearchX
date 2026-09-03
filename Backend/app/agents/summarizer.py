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
        prompt = f"""You are ResearchX, an expert academic research assistant.
Analyze the provided research paper context and provide a comprehensive, accurate, evidence-backed answer to the user's specific query.

USER RESEARCH QUERY:
"{query.strip()}"

GUIDELINES:
1. Ground every statement strictly in the provided paper context. Do not invent methods, benchmarks, numbers, or conclusions.
2. Structure your response in clean, professional Markdown:
   - **Direct Answer & Key Findings**: Directly address the query with evidence from the paper.
   - **Methodological & Technical Context**: Detail the relevant architectural, algorithmic, or theoretical mechanisms from the paper.
   - **Empirical Evidence & Benchmarks**: Cite the datasets, metrics, and quantitative or qualitative outcomes reported.
   - **Key Implications & Takeaways**: Highlight the significance and practical takeaways.
3. If specific aspects of the query are not mentioned in the context, explicitly state: "Not specified in the available paper context."
"""
    else:
        prompt = """You are ResearchX, an expert academic research assistant.
Provide a high-quality, comprehensive, and accurately structured research summary of this paper using ONLY the supplied paper context.

Format your response in clean, professional Markdown with these exact sections:

### Executive Overview
Explain the core research problem, domain motivation, and the primary objective addressed by the authors.

### Methodology & Technical Architecture
Detail the proposed framework, system design, key algorithms, models, and workflows described in the paper.

### Experimental Findings & Evaluation
State the datasets, benchmark tasks, evaluation metrics, and reported empirical outcomes or comparisons directly mentioned in the paper.

### Core Contributions & Key Takeaways
List the main innovations, claimed advantages, and primary takeaways in concise bullet points.

STRICT EVIDENCE RULES:
1. Every claim must be grounded in the supplied context. Do not invent methods, numbers, or baselines.
2. If specific details (e.g. dataset numbers or baselines) are not mentioned in the excerpt, summarize what is provided without guessing.
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

    return summary.strip()


# ==========================================================
# Workspace Summary
# ==========================================================

def summarize_workspace(topic: str, papers: List[Any]) -> List[Dict[str, str]]:
    """
    Generate one concise summary for every selected paper.
    """

    results = []

    for paper in papers:

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

        summary = summarize_paper(
            context=full_context,
            paper_name=title,
            query=topic,
            pdf_url=pdf_url,
        )

        results.append({
            "paper_name": title,
            "result": summary,
        })

    return results


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