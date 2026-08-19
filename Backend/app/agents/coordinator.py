import os
import glob
import sqlite3
from typing import Optional, Any

# Multi-API LLM Routers Import
from app.llm.multi_api_router import (
    call_groq_api,
    call_mistral_api,
    call_cohere_api,
    call_openrouter_api,
    call_gemini_api,
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
        from app.agents.literature_survey_agent import generate_literature_survey
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
        context=ctx
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
        context=ctx
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
        context=ctx
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
        context=ctx
    )

def get_experiment_fn():
    try:
        from app.agents.experiment_agent import plan_experiments
        return plan_experiments
    except ImportError:
        pass
    
    # 5. Experiments / Protocol -> DeepSeek-R1 (Chain-of-Thought Replication)
    return lambda ctx: call_openrouter_api(
        prompt="Design a step-by-step experimental reproduction protocol with hyperparameters, baseline models, and compute requirements.",
        context=ctx
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
        pages_text = [p.extract_text() for p in reader.pages if p.extract_text()]
        if pages_text and len(" ".join(pages_text).strip()) > 100:
            return "\n".join(pages_text)
    except Exception:
        pass

    # Strategy 3: pdfplumber
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            pages_text = [p.extract_text() for p in pdf.pages if p.extract_text()]
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

    raw_clean_target = paper_name.lower().replace(".pdf", "").replace(".txt", "").replace("_", "").replace(" ", "").replace("(", "").replace(")", "").strip()

    # Step 1: Check SQLite Database
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
                            c_name = str(r_name).lower().replace(".pdf", "").replace("_", "").replace(" ", "").replace("(", "").replace(")", "")
                            if (raw_clean_target in c_name or c_name in raw_clean_target) and r_content and len(r_content.strip()) > 100:
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
                f_clean = f.lower().replace(".pdf", "").replace(".txt", "").replace("_", "").replace(" ", "").replace("(", "").replace(")", "")
                if raw_clean_target in f_clean or f_clean in raw_clean_target:
                    full_path = os.path.join(root, f)
                    extracted = extract_text_from_file_universal(full_path)
                    if extracted and len(extracted.strip()) > 100:
                        return extracted[:25000]

    # Step 3: Vector Store Fallback
    try:
        from app.search.vector_store import search_vector_db
        chunks = search_vector_db(query or "methodology architecture evaluation limitations", paper_name, top_k=12)
        if chunks:
            return "\n\n".join(chunks)
    except Exception:
        pass

    return ""


# ==========================================================
# Main Coordinator Function
# ==========================================================
def run_agent(query: str, paper_name: Optional[str] = None, context: Optional[str] = None, **kwargs: Any) -> dict:
    q_lower = query.lower() if query else ""

    # Route Intent
    if any(k in q_lower for k in ["literature", "survey", "related work", "prior work"]):
        agent_type = "literature_survey"
    elif any(k in q_lower for k in ["gap", "limitation", "weakness", "bottleneck"]):
        agent_type = "gaps"
    elif any(k in q_lower for k in ["dataset", "data", "benchmark"]):
        agent_type = "datasets"
    elif any(k in q_lower for k in ["experiment", "protocol", "metric", "reproduce"]):
        agent_type = "experiments"
    else:
        agent_type = "summary"

    active_context = context if (context and len(context.strip()) > 50) else load_context_for_paper(paper_name, query)

    # Dispatch to Multi-Agent Function
    if agent_type == "literature_survey":
        output = get_literature_fn()(active_context)
    elif agent_type == "gaps":
        output = get_gap_fn()(active_context)
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
        "results": {agent_type: {"output": output}}
    }