import glob
import os
import sqlite3
from typing import Any, List, Optional

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
        from app.agents.summary_agent import generate_summary

        return generate_summary
    except ImportError:
        pass

    # 2. Executive Summary -> Groq (Llama-3.3-70B for Fast Synthesis)
    return lambda ctx: call_groq_api(
        prompt="Provide a comprehensive executive research summary covering problem statement, methodology, quantitative findings, and key takeaways.",
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
def load_context_for_paper(paper_name: Optional[str], query: str = "") -> str:
    """Multi-tiered scan across SQLite DB, Vector Stores, and Disk Directories."""
    if not paper_name or not paper_name.strip():
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
            # Use the actual Summary Agent
            from app.agents.summary_agent import run_summary_agent

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
        else load_context_for_paper(paper_name, query)
    )

    # ======================================================
    # Dispatch to Multi-Agent Function
    # ======================================================
    if agent_type == "literature_survey":
        output = get_literature_fn()(active_context)

    elif agent_type == "gaps":
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