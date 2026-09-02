from typing import Any, Dict, List, Optional
from app.llm.multi_api_router import call_cohere_api
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
    Generate a factual literature-review summary for one paper.

    The summary is strictly grounded in the supplied paper context.
    """

    print("\n================ SUMMARY RETRIEVAL DEBUG ================")
    print(f"PAPER: {paper_name}")
    print(f"PDF URL: {pdf_url}")
    print(f"QUERY: {query}")

    # ------------------------------------------------------
    # Retrieve actual paper context when paper metadata exists
    # ------------------------------------------------------

    if paper_name:
        retrieved_context = load_context_for_paper(
            paper_name=paper_name,
            query=query,
            pdf_url=pdf_url,
        )

        print(
            f"RETRIEVED CONTEXT LENGTH: "
            f"{len(retrieved_context or '')}"
        )

        if retrieved_context:
            print(retrieved_context[:3000])

        if retrieved_context and len(retrieved_context.strip()) >= 100:
            context = f"""
Paper Title: {paper_name}

Retrieved Paper Evidence:
{retrieved_context}
"""

    print("==========================================================\n")

    if not context or not context.strip():
        return "Insufficient paper context available for summary."

    # ------------------------------------------------------
    # ONE FINAL PROMPT
    # ------------------------------------------------------

    question = """
You are an academic literature-review assistant.

Write ONE factual summary of the research paper using ONLY the supplied
paper context.

The supplied context is the complete evidence available to you.

Your highest priority is factual accuracy, not completeness, elegance,
length, or making the paper sound impressive.

STEP 1 — Extract only facts explicitly stated in the context:

- research problem or objective
- method or approach
- datasets, data, or experiments, if explicitly stated
- evaluation or comparison, if explicitly stated
- findings or results, if explicitly stated
- contribution, limitation, or future work ONLY if explicitly stated

STEP 2 — Write a short literature-review paragraph using only those facts.

STRICT EVIDENCE RULES:

1. Every sentence must be directly supported by the supplied context.

2. Do not infer anything.

3. Do not convert:
   "reviews" into "evaluates"
   "discusses" into "proposes"
   "categorizes" into "compares"
   "mentions datasets" into "uses datasets for experiments"
   "discusses challenges" into "solves challenges"

4. Do not invent:
   - methods
   - architectures
   - datasets
   - experiments
   - metrics
   - numerical results
   - comparisons
   - contributions
   - limitations
   - future work

5. Do not make claims based on absence.
   Never write:
   "does not report..."
   "does not propose..."
   "no experiments..."
   "no results..."
   unless the context explicitly says so.

6. Do not add implications or interpretation.
   Do not say that something is important, useful, effective, promising,
   significant, robust, relevant, or impactful unless the context
   explicitly supports that wording.

7. Do not add a sentence merely to reach a target word count.

8. If the context contains only a few facts, produce a short summary.

WRITING STYLE:

Write like a researcher making a factual note after reading a paper.

Use simple factual verbs such as:
examines, studies, reviews, categorizes, discusses, describes,
analyzes, reports, identifies, proposes, evaluates

Use these verbs only when the supplied context supports them.

Avoid repetitive openings such as:
"This paper presents..."
"This study provides..."
"The paper offers..."

Do NOT use promotional or generic academic wording.

NEVER USE these phrases:

"comprehensive survey"
"comprehensive review"
"comprehensive overview"
"insightful"
"valuable insights"
"provides an overview"
"offers an overview"
"delves into"
"plays a crucial role"
"paves the way"
"opens new avenues"
"promising"
"significant contribution"
"important contribution"
"robust solution"
"effective solution"
"highly relevant"
"advances the field"
"advancing the field"
"guides future work"
"enhances the development"
"demonstrates the potential"
"current state of the field"
"need for further research"
"need for improved methodologies"
"identified challenges"
unless those exact facts are explicitly stated in the context.

Do not replace these phrases with equivalent promotional wording.

NO FILLER:

Do not write sentences such as:

"The survey covers a range of topics."
"The paper provides an insightful evaluation."
"The study provides useful insights."
"The work highlights the importance of..."
"The research has important implications..."
"The paper contributes to the field..."

unless the context explicitly states those facts.

If all supported facts have already been stated, STOP.

LENGTH:

Aim for approximately 50–90 words when enough factual information is
available.

If fewer facts are available, write fewer words.

Never add information just to increase length.

FINAL SELF-CHECK:

Before returning the answer, silently check every sentence:

A. Can this entire sentence be supported by the supplied context?
B. Did I add any inference?
C. Did I add any generic academic filler?
D. Did I claim an experiment, result, contribution, limitation, or
   future direction that was not explicitly stated?
E. Did I use promotional wording?

If any answer is yes, remove or rewrite that sentence.

OUTPUT FORMAT:

Return exactly ONE continuous paragraph.

No heading.
No bullets.
No numbering.
No markdown.
No quotation marks.
No "Summary:" prefix.
No explanation.
No commentary.

Return ONLY the final paragraph.
"""

    try:
        result = call_cohere_api(
            prompt=question,
            context=context,
        )

        if not result or not result.strip():
            return "Unable to generate a summary for this paper."

        summary = result.strip()

        # --------------------------------------------------
        # Lightweight deterministic cleanup
        # --------------------------------------------------
        forbidden_phrases = [
            "comprehensive survey",
            "comprehensive review",
            "comprehensive overview",
            "insightful",
            "valuable insights",
            "provides an overview",
            "offers an overview",
            "delves into",
            "plays a crucial role",
            "paves the way",
            "opens new avenues",
            "promising",
            "significant contribution",
            "important contribution",
            "robust solution",
            "effective solution",
            "highly relevant",
            "advances the field",
            "advancing the field",
            "guides future work",
            "enhances the development",
            "demonstrates the potential",
            "current state of the field",
            "need for further research",
            "need for improved methodologies",
        ]

        # If the model violates the style rules, make one
        # controlled retry with the offending output shown to it.
        lowered = summary.lower()

        if any(
            phrase in lowered
            for phrase in forbidden_phrases
        ):
            retry_prompt = f"""
Rewrite the following paragraph.

Keep ONLY factual statements that are directly supported by the original
paper context.

Remove generic, promotional, interpretive, or filler wording.

Do not add any new information.

Return exactly one paragraph.

Original generated paragraph:
{summary}
"""

            retry = call_cohere_api(
                prompt=retry_prompt,
                context=context,
            )

            if retry and retry.strip():
                summary = retry.strip()

        return summary

    except Exception as e:
        print(f"[Summary Agent Error]: {e}")
        return "Unable to generate a summary for this paper."


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