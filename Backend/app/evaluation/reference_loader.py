import os
import re
from typing import Optional, Dict, Any, List
from app.database.mongodb import papers_collection
from app.pdf.extractor import extract_text_from_pdf

BASE_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EVALUATION_DATA_DIR = os.path.join(BASE_BACKEND_DIR, "evaluation_data")
UPLOADS_DIR = os.path.join(BASE_BACKEND_DIR, "uploads")


def normalize_paper_slug(filename: str) -> str:
    """Normalize paper name to directory slug."""
    if not filename:
        return ""
    slug = re.sub(r"\.pdf$", "", filename, flags=re.IGNORECASE)
    slug = re.sub(r"[^a-zA-Z0-9_\-]+", "_", slug).strip("_").lower()
    return slug


def get_ground_truth_reference(paper_name: str, agent_name: str) -> Optional[Dict[str, Any]]:
    """
    Search evaluation_data/ for a verified reference benchmark file for THIS SPECIFIC PAPER.
    Example: evaluation_data/{paper_slug}/reference_{agent_name}.txt
    
    CRITICAL: Never fall back to sample_nlp_paper for unrelated papers!
    The benchmark must correspond to the SAME paper being evaluated.
    """
    if not os.path.isdir(EVALUATION_DATA_DIR) or not paper_name:
        return None

    agent_clean = (agent_name or "").lower().strip()
    slug = normalize_paper_slug(paper_name)

    agent_alias_map = {
        "summary": "summary",
        "summarizer": "summary",
        "summarization": "summary",
        "gaps": "gaps",
        "gap": "gaps",
        "research_gap": "gaps",
        "datasets": "datasets",
        "dataset": "datasets",
        "dataset_recommendation": "datasets",
        "experiments": "experiments",
        "experiment": "experiments",
        "experiment_recommendation": "experiments",
        "literature": "literature",
        "literature_survey": "literature",
        "retrieval": "literature",
        "novelty": "novelty",
        "novelty_analysis": "novelty",
        "comparison": "comparison",
        "paper_comparison": "comparison",
        "report": "report",
        "ieee_report": "report",
        "ppt": "ppt",
        "presentation": "ppt",
        "chat": "chat",
        "idea": "chat",
        "research_idea": "chat"
    }

    canonical_agent = agent_alias_map.get(agent_clean, agent_clean)

    # ONLY check the directory for THIS specific paper slug.
    # NEVER fall back to sample_nlp_paper unless the paper itself is sample_nlp_paper!
    if not slug:
        return None

    cand_dir = os.path.join(EVALUATION_DATA_DIR, slug)
    if not os.path.isdir(cand_dir):
        return None

    possible_filenames = [
        f"reference_{canonical_agent}.txt",
        f"reference_{canonical_agent}.md",
        f"reference_{canonical_agent}.json",
        f"ground_truth_{canonical_agent}.txt",
        f"reference.txt"
    ]

    for pfile in possible_filenames:
        full_path = os.path.join(cand_dir, pfile)
        if os.path.exists(full_path):
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                if content:
                    rel_path = os.path.relpath(full_path, BASE_BACKEND_DIR)
                    return {
                        "reference_text": content,
                        "source_label": f"Ground-Truth Benchmark ({rel_path})",
                        "is_ground_truth": True
                    }
            except Exception as e:
                print(f"[ReferenceLoader Error reading {full_path}]: {e}")

    return None


def get_paper_source_text(paper_name: str, max_chars: int = 15000) -> Optional[Dict[str, Any]]:
    """
    Extract original research paper content from disk or MongoDB as ground source context.
    """
    if not paper_name:
        return None

    # Check disk uploads
    pdf_path = os.path.join(UPLOADS_DIR, paper_name)
    if os.path.exists(pdf_path) and pdf_path.lower().endswith(".pdf"):
        try:
            extracted = extract_text_from_pdf(pdf_path)
            if extracted and len(extracted.strip()) > 50:
                return {
                    "source_text": extracted[:max_chars].strip(),
                    "source_label": f"Source Paper Document ({paper_name})",
                    "is_ground_truth": False
                }
        except Exception as e:
            print(f"[ReferenceLoader PDF extract error]: {e}")

    # Check MongoDB papers_collection
    try:
        doc = papers_collection.find_one({"filename": paper_name})
        if not doc:
            doc = papers_collection.find_one({"title": {"$regex": re.escape(paper_name), "$options": "i"}})
        
        if doc:
            text = doc.get("full_text") or doc.get("content") or ""
            if not text:
                parts = []
                if doc.get("title"):
                    parts.append(f"Title: {doc['title']}")
                if doc.get("abstract"):
                    parts.append(f"\nAbstract: {doc['abstract']}")
                if doc.get("summary"):
                    parts.append(f"\nSummary: {doc['summary']}")
                if doc.get("key_contribution"):
                    parts.append(f"\nContributions: {doc['key_contribution']}")
                text = "\n".join(parts)

            if text and len(text.strip()) > 50:
                return {
                    "source_text": text[:max_chars].strip(),
                    "source_label": f"Indexed Paper Context ({paper_name})",
                    "is_ground_truth": False
                }
    except Exception as e:
        print(f"[ReferenceLoader MongoDB query error]: {e}")

    return None


def resolve_multi_paper_context(papers: List[Any], max_chars_per_paper: int = 4000) -> Dict[str, Any]:
    """
    Build multi-paper benchmark context for AI Workspace evaluations.
    Combines each selected paper's title and key text with clear attribution boundaries
    to enable cross-paper synthesis and cross-paper contamination auditing.
    """
    if not papers:
        return {
            "comparison_text": "",
            "is_ground_truth": False,
            "evaluation_mode": "Multi-Paper Workspace Evaluation",
            "source_label": "No Selected Papers"
        }

    parts = []
    titles = []
    for idx, p in enumerate(papers):
        p_title = ""
        p_text = ""
        if isinstance(p, dict):
            p_title = p.get("title") or p.get("filename") or f"Paper {idx + 1}"
            p_text = p.get("abstract") or p.get("summary") or p.get("full_text") or p.get("content") or ""
        elif hasattr(p, "title"):
            p_title = getattr(p, "title", None) or getattr(p, "filename", None) or f"Paper {idx + 1}"
            p_text = getattr(p, "abstract", "") or getattr(p, "summary", "") or ""
        else:
            p_title = str(p)

        titles.append(p_title)
        parts.append(f"=== PAPER {idx + 1}: {p_title} ===\n{p_text[:max_chars_per_paper].strip()}\n")

    combined_text = "\n\n".join(parts)
    title_summary = ", ".join(titles[:2]) + (f" and {len(titles) - 2} more" if len(titles) > 2 else "")
    return {
        "comparison_text": combined_text,
        "is_ground_truth": False,
        "evaluation_mode": "Multi-Paper Workspace Evaluation",
        "source_label": f"Multi-Paper Workspace ({len(titles)} papers: {title_summary})",
        "paper_titles": titles
    }


def resolve_evaluation_context(
    paper_name: Optional[str],
    agent_name: str,
    explicit_context: Optional[str] = None,
    explicit_reference: Optional[str] = None,
    papers: Optional[List[Any]] = None
) -> Dict[str, Any]:
    """
    Resolve the benchmark context against which the agent output should be evaluated.
    Prioritizes:
    1. Multi-paper workspace context (when multiple papers or workspace mode is active)
    2. Explicit reference provided by caller (ground truth)
    3. evaluation_data/{paper_slug}/reference_{agent}.txt (ground truth for that specific paper ONLY)
    4. Source research paper extracted content (source-grounded)
    5. Explicit context provided by caller (source-grounded)
    """
    # 1. Multi-Paper Workspace Context
    if (papers and len(papers) > 1) or (agent_name == "workspace" and papers):
        return resolve_multi_paper_context(papers)

    # 2. Explicit reference
    if explicit_reference and explicit_reference.strip():
        return {
            "comparison_text": explicit_reference.strip(),
            "is_ground_truth": True,
            "evaluation_mode": "Ground-Truth Benchmark Evaluation",
            "source_label": "User-Supplied Reference Ground-Truth Benchmark"
        }

    # 3. Paper-specific Benchmark data folder (ONLY for matching slug!)
    if paper_name:
        gt = get_ground_truth_reference(paper_name, agent_name)
        if gt:
            return {
                "comparison_text": gt["reference_text"],
                "is_ground_truth": True,
                "evaluation_mode": "Ground-Truth Benchmark Evaluation",
                "source_label": gt["source_label"]
            }

    # 4. Source paper content (extracted from PDF or MongoDB)
    if paper_name:
        src = get_paper_source_text(paper_name)
        if src:
            return {
                "comparison_text": src["source_text"],
                "is_ground_truth": False,
                "evaluation_mode": "Source-Grounded Paper Evaluation",
                "source_label": src["source_label"]
            }

    # 5. Explicit context provided by caller
    if explicit_context and explicit_context.strip():
        return {
            "comparison_text": explicit_context.strip(),
            "is_ground_truth": False,
            "evaluation_mode": "Source-Grounded Paper Evaluation",
            "source_label": "Caller Provided Research Paper Context"
        }

    return {
        "comparison_text": "",
        "is_ground_truth": False,
        "evaluation_mode": "Source-Grounded Paper Evaluation",
        "source_label": "No Reference Context Available"
    }


def load_reference_or_paper_context(
    paper_name: Optional[str],
    agent_name: str,
    fallback_context: Optional[str] = None,
    explicit_reference: Optional[str] = None,
    papers: Optional[List[Any]] = None
) -> Dict[str, Any]:
    """Adapter wrapper returning comparison context details."""
    return resolve_evaluation_context(
        paper_name=paper_name,
        agent_name=agent_name,
        explicit_context=fallback_context,
        explicit_reference=explicit_reference,
        papers=papers
    )
