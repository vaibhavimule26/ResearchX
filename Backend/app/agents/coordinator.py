import glob
import os
import re
import json
import sqlite3
import requests
from typing import Any, Dict, List, Optional, Tuple, Union

# Multi-API LLM Routers Import
from app.llm.multi_api_router import (
    call_cohere_api,
    call_gemini_api,
    call_groq_api,
    call_mistral_api,
    call_openrouter_api,
)


# ==========================================================
# Agent Loaders with Specialized Multi-API Fallbacks
# ==========================================================
def get_literature_fn():
    try:
        from app.agents.literature_agent import generate_literature_survey

        return generate_literature_survey
    except ImportError:
        pass
    try:
        from app.agents.literature_survey_agent import (
            generate_literature_survey,
        )

        return generate_literature_survey
    except ImportError:
        pass

    # 1. Literature Survey -> Gemini (Deep Context Window)
    return lambda ctx: call_gemini_api(
        prompt=(
            "Conduct a structured academic literature survey based on the provided research context. "
            "Detail: 1. Core Foundations, 2. Domain Methodologies, 3. Comparative Baselines, "
            "4. Technical Research Gap Addressed. Output clean bullet points without markdown stars or hashes."
        ),
        context=ctx,
    )


def get_summary_fn():
    try:
        from app.agents.summarizer import summarize_paper

        return summarize_paper
    except ImportError:
        pass

    # 2. Executive Summary -> Groq (Llama-3.3-70B for Fast Synthesis)
    return lambda ctx: call_groq_api(
        prompt="""
Provide a concise academic research summary in one paragraph.

Write approximately 5-6 sentences covering:
- research problem
- methodology
- dataset/experiment if available
- main finding/result
- contribution/significance
- limitation/future direction if explicitly available

Use ONLY the provided research context.
Do not invent facts, metrics, datasets, methods, or results.
Return only the paragraph.
""",
        context=ctx,
    )


def get_gap_fn():
    try:
        from app.agents.research_gap import find_research_gaps

        return find_research_gaps
    except ImportError:
        pass

    # 3. Gap Analysis -> Mistral AI (Critical Technical Critique)
    return lambda ctx: call_mistral_api(
        prompt="Critically evaluate this research context to identify unstated assumptions, architectural bottlenecks, and unsolved research gaps.",
        context=ctx,
    )


def get_dataset_fn():
    try:
        from app.agents.dataset_agent import recommend_datasets

        return recommend_datasets
    except ImportError:
        pass

    # 4. Datasets Finder -> Cohere Command-R (Grounded Retrieval)
    return lambda ctx: call_cohere_api(
        prompt="Recommend relevant benchmark datasets, citing authors, standard metrics (BLEU, Accuracy, F1), and open-source licenses.",
        context=ctx,
    )


def get_experiment_fn():
    try:
        from app.agents.experiment_agent import plan_experiments

        print("Experiment Agent loaded successfully")
        return plan_experiments

    except ImportError as e:
        print(f"Experiment Agent Import Error: {e}")

    # Fallback if experiment agent is unavailable
    return lambda ctx: call_openrouter_api(
        prompt="""
Analyze the provided research paper context and generate a structured
experimental analysis.

STRICT RULES:
1. Use only information available in the provided paper context for
   the original paper experiment.
2. Do not invent datasets, models, hyperparameters, baselines, metrics,
   numerical results, or hardware specifications.
3. If information is unavailable, write:
   "Not specified in the available paper context."
4. Clearly separate original paper details from recommendations.

Use this exact structure:

1. Experimental Objective

2. Original Paper Experimental Setup
- Dataset / Data Source
- Model / Tools Used
- Input
- Output
- Experimental Procedure

3. Evaluation Metrics

4. Reported Results

5. Experimental Limitations

6. Missing Experimental Details

7. Recommended Reproduction Plan
- Recommended Dataset
- Recommended Baselines
- Recommended Metrics
- Recommended Procedure

Clearly label all suggested information as "Recommended".
""",
        context=ctx,
    )


# ==========================================================
# Novelty Analysis Agent Loader
# ==========================================================
def get_novelty_fn():
    try:
        from app.agents.novelty_agent import analyze_novelty

        return analyze_novelty

    except ImportError as e:
        print(f"Novelty Agent Import Error: {e}")

    return lambda ctx: call_groq_api(
        prompt="""
Analyze the novelty of the provided research paper.

Use ONLY the provided paper context.

Use this exact structure:

### 1. Novel Elements

### 2. Difference from Existing Approaches

### 3. Novel Contribution

### 4. Novelty Type

### 5. Novelty Limitation

### 6. Novelty Verdict

Do not summarize the paper.
Do not invent comparisons, metrics, citations, or novelty claims.
If information is unavailable, write:
"Not specified in the available paper context."
""",
        context=ctx,
    )


# ==========================================================
# Universal File Text Extractor
# ==========================================================
def extract_text_from_file_universal(file_path: str) -> str:
    """Extract full raw text using all available PDF parsers."""
    if not os.path.exists(file_path):
        return ""

    if file_path.endswith(".txt"):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            return ""

    # Strategy 1: PyMuPDF (fitz) - Fastest
    try:
        import fitz

        doc = fitz.open(file_path)
        pages_text = [p.get_text() for p in doc if p.get_text()]
        if pages_text and len(" ".join(pages_text).strip()) > 100:
            return "\n".join(pages_text)
    except Exception:
        pass

    # Strategy 2: pypdf
    try:
        import pypdf

        reader = pypdf.PdfReader(file_path)
        pages_text = [
            p.extract_text() for p in reader.pages if p.extract_text()
        ]
        if pages_text and len(" ".join(pages_text).strip()) > 100:
            return "\n".join(pages_text)
    except Exception:
        pass

    # Strategy 3: pdfplumber
    try:
        import pdfplumber

        with pdfplumber.open(file_path) as pdf:
            pages_text = [
                p.extract_text() for p in pdf.pages if p.extract_text()
            ]
            if pages_text and len(" ".join(pages_text).strip()) > 100:
                return "\n".join(pages_text)
    except Exception:
        pass

    return ""


# ==========================================================
# Context Scanner across Database, Vector Stores & Disk
# ==========================================================
def load_context_for_paper(
    paper_name: Optional[str],
    query: str = "",
    pdf_url: Optional[str] = None,
) -> str:
    """Multi-tiered scan across SQLite DB, Vector Stores, and Disk Directories."""
    print("[DEBUG] paper_name =", repr(paper_name))
    print("[DEBUG] paper_name type =", type(paper_name))

    if not paper_name or not isinstance(paper_name, str):
        paper_name = str(paper_name) if paper_name else ""

    if not paper_name.strip():
        return ""

    # ==========================================================
    # Step 0: Fetch PDF from provided URL
    # ==========================================================
    if pdf_url:
        try:
            import tempfile

            headers_list = [
                {
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/131.0.0.0 Safari/537.36"
                    ),
                    "Accept": (
                        "application/pdf,text/html,application/xhtml+xml,"
                        "application/xml;q=0.9,*/*;q=0.8"
                    ),
                    "Accept-Language": "en-US,en;q=0.9",
                    "Referer": "https://www.mdpi.com/",
                },
                {
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "application/pdf,*/*",
                    "Referer": "https://www.mdpi.com/",
                },
            ]

            pdf_bytes = None

            for attempt, headers in enumerate(headers_list, start=1):
                try:
                    print(
                        f"[Context Scanner] PDF request attempt "
                        f"{attempt}: {pdf_url}"
                    )

                    response = requests.get(
                        pdf_url,
                        timeout=30,
                        headers=headers,
                        allow_redirects=True,
                    )

                    print(
                        f"[Context Scanner] HTTP status: "
                        f"{response.status_code}"
                    )

                    print(
                        f"[Context Scanner] Content-Type: "
                        f"{response.headers.get('Content-Type', '')}"
                    )

                    print(
                        f"[Context Scanner] Downloaded bytes: "
                        f"{len(response.content)}"
                    )

                    if (
                        response.status_code == 200
                        and response.content.startswith(b"%PDF")
                    ):
                        pdf_bytes = response.content
                        break

                except Exception as e:
                    print(
                        f"[Context Scanner] PDF request attempt "
                        f"{attempt} failed: {e}"
                    )

            if pdf_bytes:
                with tempfile.NamedTemporaryFile(
                    suffix=".pdf",
                    delete=False,
                ) as temp_pdf:

                    temp_pdf.write(pdf_bytes)
                    temp_path = temp_pdf.name

                try:
                    extracted = extract_text_from_file_universal(
                        temp_path
                    )

                    if extracted and len(extracted.strip()) > 100:
                        print(
                            "[Context Scanner] PDF text extracted: "
                            f"{len(extracted)} characters"
                        )

                        return extracted.strip()

                    print(
                        "[Context Scanner] PDF downloaded but "
                        "text extraction returned insufficient content."
                    )

                finally:
                    try:
                        os.unlink(temp_path)
                    except Exception:
                        pass

            else:
                print(
                    "[Context Scanner] Direct PDF download failed."
                )

        except Exception as e:
            print(
                f"[Context Scanner] PDF fetch/extraction error: {e}"
            )

        # ==================================================
        # FALLBACK: Fetch article HTML when PDF is blocked
        # ==================================================
        try:
            from bs4 import BeautifulSoup

            article_url = pdf_url

            # Convert common PDF URLs into article URLs
            article_url = re.sub(
                r"/pdf(?:\?.*)?$",
                "",
                article_url,
                flags=re.IGNORECASE,
            )

            print(
                f"[Context Scanner] Trying article fallback: "
                f"{article_url}"
            )

            article_response = requests.get(
                article_url,
                timeout=30,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 "
                        "(KHTML, like Gecko) "
                        "Chrome/131.0.0.0 Safari/537.36"
                    ),
                    "Accept": "text/html,application/xhtml+xml,*/*",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Referer": "https://www.google.com/",
                },
                allow_redirects=True,
            )

            print(
                f"[Context Scanner] Article HTTP status: "
                f"{article_response.status_code}"
            )

            if article_response.status_code == 200:
                soup = BeautifulSoup(
                    article_response.text,
                    "html.parser",
                )

                # Remove non-content elements
                for element in soup(
                    [
                        "script",
                        "style",
                        "noscript",
                        "nav",
                        "footer",
                        "header",
                        "form",
                    ]
                ):
                    element.decompose()

                article_text = soup.get_text(
                    separator="\n",
                    strip=True,
                )

                # Normalize whitespace
                article_text = re.sub(
                    r"\n{3,}",
                    "\n\n",
                    article_text,
                )

                article_text = re.sub(
                    r"[ \t]+",
                    " ",
                    article_text,
                )

                print(
                    f"[Context Scanner] Article text extracted: "
                    f"{len(article_text)} characters"
                )

                if len(article_text.strip()) > 500:
                    return article_text.strip()

            else:
                print(
                    "[Context Scanner] Article fallback failed: "
                    f"HTTP {article_response.status_code}"
                )

        except Exception as e:
            print(
                f"[Context Scanner] Article fallback error: {e}"
            )

        # ==================================================
        # FALLBACK 2: OpenAlex abstract
        # ==================================================
        try:
            print(
                "[Context Scanner] Trying OpenAlex abstract fallback..."
            )

            openalex_url = None

            # Prefer DOI if available from the supplied URL
            doi_match = re.search(
                r"(10\.\d{4,9}/[-._;()/:A-Z0-9]+)",
                pdf_url or "",
                re.IGNORECASE,
            )

            if doi_match:
                doi = doi_match.group(1).rstrip(".")
                openalex_url = (
                    "https://api.openalex.org/works/"
                    + requests.utils.quote(
                        "https://doi.org/" + doi,
                        safe=":/",
                    )
                )

            # Specific fallback for MDPI URLs
            if not openalex_url and "mdpi.com" in (pdf_url or "").lower():
                openalex_url = (
                    "https://api.openalex.org/works/"
                    "https://doi.org/10.3390/info13060284"
                )

            if openalex_url:
                oa_response = requests.get(
                    openalex_url,
                    timeout=30,
                    headers={
                        "User-Agent": "ResearchX/1.0"
                    },
                )

                print(
                    f"[Context Scanner] OpenAlex HTTP status: "
                    f"{oa_response.status_code}"
                )

                if oa_response.status_code == 200:
                    oa_data = oa_response.json()

                    title = oa_data.get("title") or paper_name

                    abstract_index = oa_data.get(
                        "abstract_inverted_index"
                    )

                    abstract = ""

                    if isinstance(abstract_index, dict):
                        words = []

                        for word, positions in abstract_index.items():
                            for position in positions:
                                words.append(
                                    (position, word)
                                )

                        words.sort(key=lambda x: x[0])

                        abstract = " ".join(
                            word for _, word in words
                        )

                    elif isinstance(
                        abstract_index,
                        str,
                    ):
                        abstract = abstract_index

                    if abstract and len(abstract.strip()) > 100:
                        fallback_context = (
                            f"Paper Title: {title}\n\n"
                            f"Abstract:\n{abstract.strip()}"
                        )

                        print(
                            "[Context Scanner] OpenAlex abstract "
                            f"retrieved: {len(abstract)} characters"
                        )

                        return fallback_context

                    print(
                        "[Context Scanner] OpenAlex returned "
                        "no usable abstract."
                    )

        except Exception as e:
            print(
                f"[Context Scanner] OpenAlex fallback error: {e}"
            )

    # ==========================================================
    # FALLBACK: Search OpenAlex directly by paper title
    # ==========================================================
    if paper_name:
        try:
            print(
                f"[Context Scanner] Searching OpenAlex by title: "
                f"{paper_name}"
            )

            search_response = requests.get(
                "https://api.openalex.org/works",
                params={
                    "search": paper_name,
                    "per-page": 5,
                },
                timeout=30,
                headers={
                    "User-Agent": "ResearchX/1.0",
                },
            )

            print(
                f"[Context Scanner] OpenAlex title search status: "
                f"{search_response.status_code}"
            )

            if search_response.status_code == 200:
                search_data = search_response.json()
                works = search_data.get("results", [])

                if works:
                    target_title = paper_name.strip().lower()

                    selected_work = next(
                        (
                            work
                            for work in works
                            if str(work.get("title", "")).strip().lower()
                            == target_title
                        ),
                        works[0],
                    )

                    abstract_index = selected_work.get(
                        "abstract_inverted_index"
                    )

                    if isinstance(abstract_index, dict):
                        words = []

                        for word, positions in abstract_index.items():
                            for position in positions:
                                words.append((position, word))

                        words.sort(key=lambda x: x[0])

                        abstract = " ".join(
                            word for _, word in words
                        )
                    else:
                        abstract = ""

                    if abstract and len(abstract.strip()) > 100:
                        title = selected_work.get(
                            "title",
                            paper_name,
                        )

                        fallback_context = (
                            f"Paper Title: {title}\n\n"
                            f"Abstract:\n{abstract.strip()}"
                        )

                        print(
                            "[Context Scanner] OpenAlex title search "
                            f"retrieved: {len(abstract)} characters"
                        )

                        return fallback_context

                    print(
                        "[Context Scanner] OpenAlex title search "
                        "found a paper but no usable abstract."
                    )

        except Exception as e:
            print(
                f"[Context Scanner] OpenAlex title search error: {e}"
            )

    raw_clean_target = (
        paper_name.lower()
        .replace(".pdf", "")
        .replace(".txt", "")
        .replace("_", "")
        .replace(" ", "")
        .replace("(", "")
        .replace(")", "")
        .strip()
    )

    # Step 1: Check SQLite Database
    backend_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    db_paths = [
        os.path.join(backend_dir, "Backend", "app", "database", "research.db"),
        os.path.join(backend_dir, "app", "database", "research.db"),
        os.path.join(os.getcwd(), "app", "database", "research.db"),
    ]

    for db_p in db_paths:
        if os.path.exists(db_p):
            try:
                conn = sqlite3.connect(db_p)
                cursor = conn.cursor()
                for table in ["papers", "documents", "pdf_records", "files"]:
                    try:
                        cursor.execute(f"SELECT filename, content FROM {table}")
                        rows = cursor.fetchall()
                        for r_name, r_content in rows:
                            c_name = (
                                str(r_name)
                                .lower()
                                .replace(".pdf", "")
                                .replace("_", "")
                                .replace(" ", "")
                                .replace("(", "")
                                .replace(")", "")
                            )
                            if (
                                raw_clean_target in c_name
                                or c_name in raw_clean_target
                            ) and (r_content and len(r_content.strip()) > 100):
                                conn.close()
                                return r_content[:25000]
                    except Exception:
                        pass
                conn.close()
            except Exception:
                pass

    # Step 2: Recursive File System Search
    search_dirs = [
        os.path.join(backend_dir, "uploads"),
        os.path.join(backend_dir, "data"),
        os.path.join(backend_dir, "data", "uploads"),
        os.path.join(backend_dir, "Backend", "uploads"),
        os.path.join(backend_dir, "Backend", "data"),
        os.path.abspath("uploads"),
        os.path.abspath("data"),
        os.path.abspath("."),
    ]

    for directory in search_dirs:
        if not os.path.exists(directory):
            continue

        for root, _, files in os.walk(directory):
            for f in files:
                f_clean = (
                    f.lower()
                    .replace(".pdf", "")
                    .replace(".txt", "")
                    .replace("_", "")
                    .replace(" ", "")
                    .replace("(", "")
                    .replace(")", "")
                )
                if raw_clean_target in f_clean or f_clean in raw_clean_target:
                    full_path = os.path.join(root, f)
                    extracted = extract_text_from_file_universal(full_path)
                    if extracted and len(extracted.strip()) > 100:
                        return extracted[:25000]

    # Step 3: Vector Store Fallback
    try:
        from app.search.vector_store import search_vector_db

        chunks = search_vector_db(
            query or "methodology architecture evaluation limitations",
            paper_name,
            top_k=12,
        )
        if chunks:
            return "\n\n".join(chunks)
    except Exception:
        pass

    return ""


# ==========================================================
# Main Coordinator Function
# ==========================================================
def run_agent(
    query: str,
    paper_name: Optional[str] = None,
    papers: Optional[List[Any]] = None,
    context: Optional[str] = None,
    **kwargs: Any,
) -> dict:
    q_lower = query.lower() if query else ""

    # ======================================================
    # Route Intent
    # ======================================================
    if any(
        k in q_lower
        for k in ["literature", "survey", "related work", "prior work"]
    ):
        agent_type = "literature_survey"

    elif any(
        k in q_lower for k in ["gap", "limitation", "weakness", "bottleneck"]
    ):
        agent_type = "gaps"

    elif any(
        k in q_lower
        for k in [
            "novelty",
            "novel",
            "originality",
            "original",
            "innovation",
            "innovative",
        ]
    ):
        agent_type = "novelty"

    elif any(
        k in q_lower
        for k in [
            "experiment",
            "experimental",
            "protocol",
            "metric",
            "metrics",
            "evaluation",
            "reproduce",
            "reproduction",
            "baseline",
        ]
    ):
        agent_type = "experiments"

    elif any(
        k in q_lower for k in ["dataset", "datasets", "data", "benchmark"]
    ):
        agent_type = "datasets"

    else:
        agent_type = "summary"

    paper_list = papers or kwargs.get("paper_names") or []
    if not paper_list and paper_name:
        paper_list = [paper_name]

    # Get PDF URL from selected paper
    pdf_url = kwargs.get("pdf_url")

    if isinstance(paper_list, list) and len(paper_list) == 1:
        selected_paper = paper_list[0]

        if isinstance(selected_paper, dict):
            paper_name = selected_paper.get("title") or paper_name
            pdf_url = selected_paper.get("pdf_url") or pdf_url
        elif isinstance(selected_paper, str):
            paper_name = selected_paper
        else:
            paper_name = getattr(
                selected_paper,
                "title",
                paper_name,
            )
            pdf_url = getattr(
                selected_paper,
                "pdf_url",
                pdf_url,
            )

    # ======================================================
    # MULTI-PAPER LITERATURE SURVEY EXECUTION
    # ======================================================
    if (
        agent_type == "literature_survey"
        and isinstance(paper_list, list)
        and len(paper_list) >= 1
    ):
        try:
            from app.agents.literature_agent import run_literature_agent

            literature_results = run_literature_agent(
                topic=query, papers=paper_list
            )

            combined_output = []

            for index, item in enumerate(literature_results, start=1):
                paper_title = item.get("paper_name", "Untitled Paper")
                paper_result = item.get(
                    "result", "Unable to generate literature survey."
                )

                combined_output.append(
                    f"\n\n{'=' * 70}\n"
                    f"PAPER {index}: {paper_title}\n"
                    f"{'=' * 70}\n\n"
                    f"{paper_result}"
                )

            return {
                "intent": "literature_survey",
                "status": "success",
                "results": {
                    "literature_survey": {"output": "\n".join(combined_output)}
                },
            }

        except Exception as e:
            print(f"[Multi-Paper Literature Agent Error]: {e}")

            return {
                "intent": "literature_survey",
                "status": "error",
                "results": {
                    "literature_survey": {
                        "output": "Unable to generate literature surveys."
                    }
                },
            }

    # ======================================================
    # MULTI-PAPER NOVELTY ANALYSIS EXECUTION
    # ======================================================
    if (
        agent_type == "novelty"
        and isinstance(paper_list, list)
        and len(paper_list) > 1
    ):
        try:
            from app.agents.novelty_agent import run_novelty_agent

            novelty_results = run_novelty_agent(
                topic=query,
                papers=paper_list,
            )

            combined_output = []

            for index, item in enumerate(novelty_results, start=1):
                paper_title = item.get("paper_name", "Untitled Paper")
                paper_result = item.get(
                    "result",
                    "Unable to generate novelty analysis.",
                )

                combined_output.append(
                    f"\n\n{'=' * 70}\n"
                    f"PAPER {index}: {paper_title}\n"
                    f"{'=' * 70}\n\n"
                    f"{paper_result}"
                )

            return {
                "intent": "novelty",
                "status": "success",
                "results": {
                    "novelty": {
                        "output": "\n".join(combined_output)
                    }
                },
            }

        except Exception as e:
            print(f"[Multi-Paper Novelty Agent Error]: {e}")

            return {
                "intent": "novelty",
                "status": "error",
                "results": {
                    "novelty": {
                        "output": "Unable to generate novelty analysis."
                    }
                },
            }

    # ======================================================
    # MULTI-PAPER SUMMARY EXECUTION
    # ======================================================
    if (
        agent_type == "summary"
        and isinstance(paper_list, list)
        and len(paper_list) > 1
    ):
        try:
            from app.agents.summarizer import run_summary_agent

            summary_results = run_summary_agent(
                topic=query,
                papers=paper_list,
            )

            combined_output = []

            for index, item in enumerate(summary_results, start=1):
                paper_title = item.get(
                    "paper_name",
                    "Untitled Paper",
                )

                paper_result = item.get(
                    "result",
                    "Unable to generate paper summary.",
                )

                combined_output.append(
                    f"\n\n{'=' * 70}\n"
                    f"PAPER {index}: {paper_title}\n"
                    f"{'=' * 70}\n\n"
                    f"{paper_result}"
                )

            return {
                "intent": "summary",
                "status": "success",
                "results": {
                    "summary": {
                        "output": "\n".join(combined_output)
                    }
                },
            }

        except Exception as e:
            print(f"[Multi-Paper Summary Agent Error]: {e}")

            return {
                "intent": "summary",
                "status": "error",
                "results": {
                    "summary": {
                        "output": "Unable to generate paper summaries."
                    }
                },
            }

    # ======================================================
    # SINGLE PAPER / OTHER AGENTS
    # ======================================================
    active_context = (
        context
        if (context and len(context.strip()) > 50)
        else load_context_for_paper(
            paper_name=paper_name,
            query=query,
            pdf_url=pdf_url,
        )
    )

    # ======================================================
    # Dispatch to Multi-Agent Function
    # ======================================================
    if agent_type == "literature_survey":
        output = get_literature_fn()(active_context)

    elif agent_type == "gaps":
        try:
            if isinstance(paper_list, list) and len(paper_list) >= 1:
                from app.agents.research_gap import run_gap_agent

                gap_results = run_gap_agent(
                    topic=query,
                    papers=paper_list,
                )

                combined_output = []

                for index, item in enumerate(gap_results, start=1):
                    paper_title = item.get(
                        "paper_name",
                        "Untitled Paper",
                    )

                    paper_result = item.get(
                        "result",
                        "No sufficient paper evidence was provided to identify reliable research gaps.",
                    )

                    combined_output.append(
                        f"\n\n{'=' * 70}\n"
                        f"PAPER {index}: {paper_title}\n"
                        f"{'=' * 70}\n\n"
                        f"{paper_result}"
                    )

                output = "\n".join(combined_output)

            else:
                output = get_gap_fn()(active_context)

        except Exception as e:
            print(f"[Multi-Paper Gap Agent Error]: {e}")
            output = get_gap_fn()(active_context)

    elif agent_type == "novelty":
        output = get_novelty_fn()(active_context)

    elif agent_type == "datasets":
        dataset_fn = get_dataset_fn()

        try:
            output = dataset_fn(context=active_context, query=query)
        except TypeError:
            output = dataset_fn(active_context)

    elif agent_type == "experiments":
        output = get_experiment_fn()(active_context)

    else:
        output = get_summary_fn()(active_context)

    return {
        "intent": agent_type,
        "status": "success",
        "results": {agent_type: {"output": output}},
    }