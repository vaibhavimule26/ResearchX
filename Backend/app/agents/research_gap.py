import re
from typing import Any, Dict, List, Optional, Tuple, Union

from app.agents.coordinator import load_context_for_paper
from app.llm.multi_api_router import call_mistral_api


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

    # Handle literal escaped newlines from raw string outputs
    result = result.replace("\\r\\n", "\n")
    result = result.replace("\\n", "\n")
    result = result.replace("\\r", "\n")

    # Normalize excessive blank lines
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def run_gap_agent(
    topic: str,
    papers: List[Any],
) -> List[Dict[str, str]]:
    """
    Generate one combined research-gap table for all workspace papers.
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
            if pdf_url and str(pdf_url).startswith("http"):
                paper_context = load_context_for_paper(
                    paper_name=title,
                    query=topic,
                    pdf_url=pdf_url,
                )
            else:
                paper_context = ""
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

    question = f"""
You are the Research Gap Analysis Agent of ResearchX.

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
6. Do NOT write 'no abstract found' or 'not specified'. If full text is limited, synthesize the research gap from the paper's title, topic scope, and methodology.
7. Include ALL {len(papers)} papers in the table ({len(papers)} total rows).
8. Keep every table cell concise and clear.
9. Return ONLY the Markdown table.
"""

    try:
        result = call_mistral_api(
            prompt=question,
            context=combined_context,
        )

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

    except Exception as e:
        print(f"[Gap Agent Error]: {e}")
        rows = []
        for t in paper_titles:
            rows.append(f"| {t} | Not clearly established | Unable to analyze full evidence | Standard domain challenge |")
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
    **kwargs,
) -> str:
    """
    Analyze research gaps from directly supplied paper text.

    This function is kept for backward compatibility.
    """

    content = (
        text
        or query
        or kwargs.get("context", "")
    )

    doc_title = (
        title
        or paper_name
        or "Uploaded Research Paper"
    )

    if not content or len(content.strip()) < 50:
        return (
            "No sufficient paper evidence was provided "
            "to identify reliable research gaps."
        )

    paper_context = content[:12000]

    prompt = f"""
You are the Research Gap Analysis Agent of ResearchX.

Research Topic: {query or doc_title}

Paper Title: {doc_title}

Paper Context:
{paper_context}

Analyze ONLY the supplied research paper context.

Your task is to identify the MOST RELEVANT research gaps
that are directly supported by the paper.

VERY IMPORTANT:
Do NOT treat every unmentioned experiment, dataset, architecture,
modality, attack, or future possibility as a research gap.

A research gap is valid ONLY when:
1. The paper explicitly states it as a limitation, challenge,
   unresolved issue, or future work; OR
2. The supplied context clearly shows that the paper leaves a
   specific research question unanswered.

Do NOT create a gap merely because the paper did not mention
something.

Do NOT generate "unseen fake news types", "adversarial attacks",
"temporal dynamics", "source credibility", "other domains",
"other datasets", or similar future possibilities unless the
supplied context explicitly supports them.

If only 1 or 2 evidence-supported gaps can be established,
return only 1 or 2 gaps. Do NOT force exactly 3 gaps.

OUTPUT FORMAT:

Research Gap 1: [Short academic title]
Explanation: [2-3 concise sentences explaining the gap using
only evidence from the supplied paper context.]

Research Gap 2: [Short academic title]
Explanation: [2-3 concise sentences.]

Research Gap 3: [Short academic title]
Explanation: [2-3 concise sentences.]

(Only include Research Gap 2 or 3 if genuinely supported by the context.)

IMPORTANT RULES:

- Return ONLY the research gaps.
- Generate 1 to 3 gaps maximum.
- Prioritize the MOST RELEVANT gaps.
- Do not generate generic future research ideas.
- A missing feature is NOT automatically a research gap.
- Do not assume that something was not studied merely because
  it is not present in the abstract.
- Prefer gaps explicitly stated by the paper.
- Do not claim that a limitation exists without evidence.
- Do not compare with papers that are not present in the context.
- Do not use outside knowledge.
- Do not invent citations, authors, datasets, metrics,
  experiments, or results.
- Do not invent numerical values.
- Do not use Markdown headings.
- Do not use Markdown bullets.
- Do not use asterisks.
- Do not use JSON.
- Do not use tables.
- Do not add greetings or explanations.
- Keep the complete answer under 350 words.

If the supplied context is insufficient to establish a gap,
write:

Research Gap: Not clearly established from the available paper context.
"""

    try:

        raw_output = call_mistral_api(
            prompt=prompt,
            context=paper_context,
        )

        cleaned_output = clean_gap_output(raw_output)

        if not cleaned_output:
            return (
                "Research Gap: Not clearly established from the available paper context."
            )

        return cleaned_output

    except Exception as e:

        print(f"[Research Gap Agent Error]: {e}")

        return (
            "Unable to analyze research gaps for "
            "the provided paper context."
        )


def find_research_gaps(*args, **kwargs):
    """
    Backwards-compatible alias used by coordinator.py
    and other report-generation components.
    """

    text_arg = (
        args[0]
        if len(args) > 0
        else kwargs.get(
            "text",
            kwargs.get("query", ""),
        )
    )

    title_arg = (
        args[1]
        if len(args) > 1
        else kwargs.get(
            "title",
            kwargs.get(
                "paper_name",
                "Research Paper",
            ),
        )
    )

    return analyze_research_gap(
        text=text_arg,
        title=title_arg,
        **kwargs,
    )