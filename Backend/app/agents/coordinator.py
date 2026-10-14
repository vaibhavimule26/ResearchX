import glob
import os
import re
import json
import sqlite3
import threading
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


def get_ppt_fn():
    try:
        from app.agents.ppt_agent import generate_presentation

        return generate_presentation
    except ImportError as e:
        print(f"PPT Agent Import Error: {e}")

    return lambda ctx, **kwargs: "Unable to load PPT Generator Agent."


def get_report_fn():
    try:
        from app.agents.report_agent import generate_ieee_report

        return generate_ieee_report
    except ImportError as e:
        print(f"IEEE Report Agent Import Error: {e}")

    return lambda ctx, **kwargs: "Unable to load IEEE Report Agent."



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
# In-Memory Paper Context Cache
# ==========================================================

_PAPER_CONTEXT_CACHE: Dict[Tuple[str, str, Optional[str]], str] = {}
_PAPER_CONTEXT_LOCK = threading.Lock()
_MAX_CONTEXT_CACHE = 128


def clear_context_cache():
    """Clear cached paper contexts (e.g. after fresh PDF upload or deletion)."""
    with _PAPER_CONTEXT_LOCK:
        _PAPER_CONTEXT_CACHE.clear()
    print("[Context Scanner] In-memory paper context cache cleared.")


def load_context_for_paper(
    paper_name: Optional[str],
    query: str = "",
    pdf_url: Optional[str] = None,
) -> str:
    """
    Cached facade for loading paper context across MongoDB, disk, and vector stores.
    """
    if not paper_name or not isinstance(paper_name, str):
        paper_name = str(paper_name) if paper_name else ""

    if not paper_name.strip():
        return ""

    cache_key = (
        paper_name.strip(),
        (query or "").strip(),
        pdf_url.strip() if pdf_url else None,
    )

    with _PAPER_CONTEXT_LOCK:
        if cache_key in _PAPER_CONTEXT_CACHE:
            cached_ctx = _PAPER_CONTEXT_CACHE[cache_key]
            if cached_ctx:
                print(f"[Context Cache Hit] Found cached context for paper: {paper_name} ({len(cached_ctx)} chars)")
                return cached_ctx

    context = _scan_context_for_paper(
        paper_name=paper_name,
        query=query,
        pdf_url=pdf_url,
    )

    if context and len(context.strip()) > 50:
        with _PAPER_CONTEXT_LOCK:
            if len(_PAPER_CONTEXT_CACHE) >= _MAX_CONTEXT_CACHE:
                _PAPER_CONTEXT_CACHE.pop(next(iter(_PAPER_CONTEXT_CACHE)))
            _PAPER_CONTEXT_CACHE[cache_key] = context

    return context


# ==========================================================
# Context Scanner across Database, Vector Stores & Disk
# ==========================================================
def _scan_context_for_paper(
    paper_name: Optional[str],
    query: str = "",
    pdf_url: Optional[str] = None,
) -> str:
    """
    Multi-tiered scan across MongoDB, Local Disk/Uploads, Vector Stores, and Fallback Web APIs.
    Prioritizes locally uploaded documents and MongoDB records first.
    """
    print("[DEBUG] paper_name =", repr(paper_name))
    print("[DEBUG] query =", repr(query))

    if not paper_name or not isinstance(paper_name, str):
        paper_name = str(paper_name) if paper_name else ""

    if not paper_name.strip():
        return ""

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

    # ==========================================================
    # Tier 1: Check MongoDB Uploaded Papers (HIGHEST PRIORITY)
    # ==========================================================
    try:
        from app.database.mongodb import papers_collection

        # Query MongoDB for exact or regex match
        mongo_paper = (
            papers_collection.find_one({"filename": paper_name})
            or papers_collection.find_one({"title": paper_name})
            or papers_collection.find_one({
                "filename": {"$regex": re.escape(paper_name.strip()), "$options": "i"}
            })
            or papers_collection.find_one({
                "title": {"$regex": re.escape(paper_name.strip()), "$options": "i"}
            })
        )

        if not mongo_paper and raw_clean_target:
            for cand in papers_collection.find({"text": {"$exists": True}}).limit(30):
                c_fn = (cand.get("filename") or cand.get("title") or "").lower()
                c_clean = (
                    c_fn.replace(".pdf", "")
                    .replace(".txt", "")
                    .replace("_", "")
                    .replace(" ", "")
                    .replace("(", "")
                    .replace(")", "")
                    .strip()
                )
                if raw_clean_target in c_clean or c_clean in raw_clean_target:
                    mongo_paper = cand
                    break

        if mongo_paper:
            p_text = mongo_paper.get("text", "")
            p_title = mongo_paper.get("title") or mongo_paper.get("filename") or paper_name

            # Retrieve RAG chunks from ChromaDB if query is provided
            rag_context = ""
            if query and query.strip() and query.lower() not in ["summary", "summarize", "summarize this paper"]:
                try:
                    from app.rag.rag_service import retrieve_rag_context
                    rag_paper_id = mongo_paper.get("filename") or paper_name
                    rag_context = retrieve_rag_context(query=query, paper_id=rag_paper_id, top_k=6)
                except Exception as rag_err:
                    print(f"[Context Scanner] RAG context error: {rag_err}")

            if p_text and len(p_text.strip()) > 100:
                print(f"[Context Scanner] Found paper in MongoDB: {p_title} ({len(p_text)} chars)")
                if rag_context and "No relevant evidence" not in rag_context:
                    return f"Paper Title: {p_title}\n\nKey Relevant Evidence:\n{rag_context}\n\nFull Paper Content:\n{p_text[:150000]}"
                return f"Paper Title: {p_title}\n\n{p_text[:150000]}"

    except Exception as mongo_err:
        print(f"[Context Scanner] MongoDB lookup error: {mongo_err}")

    # ==========================================================
    # Tier 2: Recursive Local File System Search (Uploads & Disk)
    # ==========================================================
    backend_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    search_dirs = [
        os.path.join(backend_dir, "uploads"),
        os.path.join(backend_dir, "Backend", "uploads"),
        os.path.join(os.getcwd(), "uploads"),
        os.path.join(os.getcwd(), "Backend", "uploads"),
        os.path.join(backend_dir, "data"),
        os.path.join(backend_dir, "data", "uploads"),
        os.path.abspath("uploads"),
        os.path.abspath("."),
    ]

    for directory in search_dirs:
        if not os.path.exists(directory):
            continue

        for root, _, files in os.walk(directory):
            for f in files:
                if not f.lower().endswith((".pdf", ".txt")):
                    continue
                f_clean = (
                    f.lower()
                    .replace(".pdf", "")
                    .replace(".txt", "")
                    .replace("_", "")
                    .replace(" ", "")
                    .replace("(", "")
                    .replace(")", "")
                )
                if (raw_clean_target and (raw_clean_target in f_clean or f_clean in raw_clean_target)) or (f.lower() == paper_name.lower()):
                    full_path = os.path.join(root, f)
                    extracted = extract_text_from_file_universal(full_path)
                    if extracted and len(extracted.strip()) > 100:
                        print(f"[Context Scanner] Extracted text from local file: {full_path} ({len(extracted)} chars)")
                        return f"Paper Title: {f}\n\n{extracted[:150000]}"

    # ==========================================================
    # Tier 3: Vector Store / ChromaDB RAG Search
    # ==========================================================
    try:
        from app.rag.rag_service import retrieve_rag_context
        rag_ctx = retrieve_rag_context(
            query=query or "abstract methodology key contributions experimental results",
            paper_id=paper_name,
            top_k=8,
        )
        if rag_ctx and len(rag_ctx.strip()) > 100 and "No relevant evidence" not in rag_ctx:
            print(f"[Context Scanner] Retrieved RAG context from ChromaDB ({len(rag_ctx)} chars)")
            return rag_ctx
    except Exception as rag_err:
        print(f"[Context Scanner] ChromaDB RAG error: {rag_err}")

    # ==========================================================
    # Tier 4: SQLite Database (Legacy fallback)
    # ==========================================================
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
                                return r_content[:30000]
                    except Exception:
                        pass
                conn.close()
            except Exception:
                pass

    # ==========================================================
    # Tier 5: Fetch PDF from provided URL (Online Paper Search)
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
                    extracted = extract_text_from_file_universal(temp_path)
                    if extracted and len(extracted.strip()) > 100:
                        return extracted.strip()
                finally:
                    try:
                        os.unlink(temp_path)
                    except Exception:
                        pass

        except Exception as e:
            print(f"[Context Scanner] PDF fetch/extraction error: {e}")

        # Fallback to article HTML
        try:
            from bs4 import BeautifulSoup
            article_url = re.sub(r"/pdf(?:\?.*)?$", "", pdf_url, flags=re.IGNORECASE)
            article_response = requests.get(
                article_url,
                timeout=30,
                headers={"User-Agent": "Mozilla/5.0"},
                allow_redirects=True,
            )
            if article_response.status_code == 200:
                soup = BeautifulSoup(article_response.text, "html.parser")
                for element in soup(["script", "style", "noscript", "nav", "footer", "header", "form"]):
                    element.decompose()
                article_text = soup.get_text(separator="\n", strip=True)
                article_text = re.sub(r"\n{3,}", "\n\n", article_text)
                if len(article_text.strip()) > 500:
                    return article_text.strip()
        except Exception as e:
            print(f"[Context Scanner] Article fallback error: {e}")

    # ==========================================================
    # Tier 6: OpenAlex by Title (ONLY for Online Paper Search, NOT for local/uploaded files)
    # ==========================================================
    is_local_file_pattern = (
        paper_name.lower().endswith(".pdf")
        or paper_name.lower().endswith(".txt")
        or "research paper" in paper_name.lower()
        or paper_name.lower().startswith("paper")
    )

    if paper_name and not is_local_file_pattern:
        try:
            print(f"[Context Scanner] Searching OpenAlex by title: {paper_name}")
            search_response = requests.get(
                "https://api.openalex.org/works",
                params={"search": paper_name, "per-page": 5},
                timeout=30,
                headers={"User-Agent": "ResearchX/1.0"},
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
                            if str(work.get("title", "")).strip().lower() == target_title
                        ),
                        works[0],
                    )
                    abstract_index = selected_work.get("abstract_inverted_index")
                    abstract = ""
                    if isinstance(abstract_index, dict):
                        words = []
                        for word, positions in abstract_index.items():
                            for position in positions:
                                words.append((position, word))
                        words.sort(key=lambda x: x[0])
                        abstract = " ".join(word for _, word in words)
                    elif isinstance(abstract_index, str):
                        abstract = abstract_index

                    if abstract and len(abstract.strip()) > 100:
                        title = selected_work.get("title", paper_name)
                        return f"Paper Title: {title}\n\nAbstract:\n{abstract.strip()}"
        except Exception as e:
            print(f"[Context Scanner] OpenAlex title search error: {e}")

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
    explicit_agent = (kwargs.get("analysis_type") or kwargs.get("agent_type") or "").strip().lower()

    if explicit_agent in ["summary", "executive_summary"]:
        agent_type = "summary"
    elif explicit_agent in ["literature", "literature_survey", "survey"]:
        agent_type = "literature_survey"
    elif explicit_agent in ["gaps", "gap", "research_gap"]:
        agent_type = "gaps"
    elif explicit_agent in ["novelty", "novelty_analysis"]:
        agent_type = "novelty"
    elif explicit_agent in ["datasets", "dataset", "dataset_recommendation"]:
        agent_type = "datasets"
    elif explicit_agent in ["experiments", "experiment", "experiment_recommendation"]:
        agent_type = "experiments"
    elif explicit_agent in ["ppt", "presentation", "slides", "powerpoint"]:
        agent_type = "presentation"
    elif explicit_agent in ["report", "ieee", "ieee_report", "manuscript", "ieee_paper"]:
        agent_type = "report"

    elif any(
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

    elif any(
        k in q_lower for k in ["presentation", "powerpoint", "slide deck", "generate ppt", "make slides"]
    ):
        agent_type = "presentation"

    elif any(
        k in q_lower
        for k in [
            "ieee report",
            "generate report",
            "ieee paper",
            "ieee format",
            "research report",
            "full report",
            "manuscript",
            "compile report",
        ]
    ):
        agent_type = "report"

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
        and len(paper_list) > 1
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
        lit_fn = get_literature_fn()
        try:
            output = lit_fn(
                context=active_context,
                paper_name=paper_name,
                query=query,
                pdf_url=pdf_url,
            )
        except TypeError:
            try:
                output = lit_fn(
                    active_context,
                    paper_name=paper_name or "Uploaded Research Paper",
                )
            except TypeError:
                output = lit_fn(active_context)

    elif agent_type == "gaps":
        try:
            if isinstance(paper_list, list) and len(paper_list) > 1:
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
                gap_fn = get_gap_fn()
                try:
                    output = gap_fn(
                        context=active_context,
                        paper_name=paper_name,
                        query=query,
                        pdf_url=pdf_url,
                    )
                except TypeError:
                    try:
                        output = gap_fn(
                            active_context,
                            paper_name=paper_name or "Uploaded Research Paper",
                        )
                    except TypeError:
                        output = gap_fn(active_context)

        except Exception as e:
            print(f"[Gap Agent Error]: {e}")
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
        try:
            if isinstance(paper_list, list) and len(paper_list) > 1:
                from app.agents.experiment_agent import run_experiment_agent

                exp_results = run_experiment_agent(
                    topic=query,
                    papers=paper_list,
                )

                combined_output = []
                for index, item in enumerate(exp_results, start=1):
                    paper_title = item.get(
                        "paper_name",
                        "Untitled Paper",
                    )
                    paper_result = item.get(
                        "result",
                        "No sufficient paper evidence was provided to design accurate experiments.",
                    )
                    combined_output.append(
                        f"\n\n{'=' * 70}\n"
                        f"PAPER {index}: {paper_title}\n"
                        f"{'=' * 70}\n\n"
                        f"{paper_result}"
                    )
                output = "\n".join(combined_output)

            else:
                exp_fn = get_experiment_fn()
                try:
                    output = exp_fn(
                        context=active_context,
                        paper_name=paper_name,
                        query=query,
                        pdf_url=pdf_url,
                    )
                except TypeError:
                    try:
                        output = exp_fn(
                            active_context,
                            paper_name=paper_name or "Uploaded Research Paper",
                        )
                    except TypeError:
                        output = exp_fn(active_context)

        except Exception as e:
            print(f"[Experiment Agent Error]: {e}")
            output = get_experiment_fn()(active_context)
    elif agent_type == "presentation":
        try:
            ppt_fn = get_ppt_fn()
            try:
                output = ppt_fn(
                    context=active_context,
                    paper_name=paper_name,
                    query=query,
                    pdf_url=pdf_url,
                )
            except TypeError:
                try:
                    output = ppt_fn(
                        active_context,
                        paper_name=paper_name or "Uploaded Research Paper",
                    )
                except TypeError:
                    output = ppt_fn(active_context)
        except Exception as e:
            print(f"[Presentation Agent Error]: {e}")
            output = get_ppt_fn()(active_context)

    elif agent_type == "report":
        try:
            report_fn = get_report_fn()
            try:
                output = report_fn(
                    context=active_context,
                    paper_name=paper_name,
                    query=query,
                    pdf_url=pdf_url,
                )
            except TypeError:
                try:
                    output = report_fn(
                        active_context,
                        paper_name=paper_name or "Uploaded Research Paper",
                    )
                except TypeError:
                    output = report_fn(active_context)
        except Exception as e:
            print(f"[IEEE Report Agent Error]: {e}")
            output = get_report_fn()(active_context)

    else:
        summary_fn = get_summary_fn()
        try:
            output = summary_fn(
                context=active_context,
                paper_name=paper_name,
                query=query,
                pdf_url=pdf_url,
            )
        except TypeError:
            try:
                output = summary_fn(active_context, query=query)
            except TypeError:
                output = summary_fn(active_context)

    return {
        "intent": agent_type,
        "status": "success",
        "results": {agent_type: {"output": output}},
    }