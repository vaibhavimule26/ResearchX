import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pymupdf
from bson import ObjectId
from rapidfuzz import fuzz

from app.database.mongodb import papers_collection

# In-memory result cache: target_identifier -> (cache_timestamp, result_dict)
_PLAGIARISM_CACHE: Dict[str, Tuple[str, Dict[str, Any]]] = {}


def normalize_text_for_comparison(text: str) -> str:
    """
    Normalize text: lowercasing, removing punctuation,
    collapsing multiple whitespace characters.
    """
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def segment_text_into_passages(text: str, min_words: int = 7) -> List[str]:
    """
    Split text into distinct academic sentences or meaningful clauses.
    Filters out headers, citations, and trivial snippets.
    """
    if not text:
        return []

    # Clean whitespace
    clean_text = " ".join(text.split())

    # Split on sentence boundaries (. ! ? or newline)
    raw_sentences = re.split(r"(?<=[.!?])\s+|\n+", clean_text)
    passages = []

    for s in raw_sentences:
        s_clean = s.strip()
        words = s_clean.split()
        if len(words) >= min_words:
            # Skip pure metadata or equation snippets
            if re.match(r"^[\d\W_]+$", s_clean):
                continue
            passages.append(s_clean)

    return passages


def extract_document_passages(paper: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract text passages mapped to exact PDF page numbers.
    Prefers reading from disk via PyMuPDF; falls back to MongoDB chunks/text.
    """
    passages: List[Dict[str, Any]] = []
    filepath = paper.get("filepath")

    # Method 1: PyMuPDF per-page extraction
    if filepath and os.path.exists(filepath):
        try:
            doc = pymupdf.open(filepath)
            for page_idx, page in enumerate(doc, start=1):
                page_text = page.get_text()
                if not page_text or not page_text.strip():
                    continue

                page_sentences = segment_text_into_passages(page_text)
                for sentence in page_sentences:
                    norm = normalize_text_for_comparison(sentence)
                    words = sentence.split()
                    if norm and len(words) >= 6:
                        passages.append({
                            "page": page_idx,
                            "text": sentence,
                            "normalized": norm,
                            "word_count": len(words),
                        })
            doc.close()
            if passages:
                return passages
        except Exception as e:
            print(f"[Plagiarism Service] PyMuPDF extraction error for {filepath}: {e}")

    # Method 2: Chunks from MongoDB document
    chunks = paper.get("chunks") or []
    if chunks:
        for idx, chunk in enumerate(chunks, start=1):
            # Estimate page: approx 2-3 chunks per page
            est_page = max(1, (idx + 1) // 2)
            for sentence in segment_text_into_passages(chunk):
                norm = normalize_text_for_comparison(sentence)
                words = sentence.split()
                if norm and len(words) >= 6:
                    passages.append({
                        "page": est_page,
                        "text": sentence,
                        "normalized": norm,
                        "word_count": len(words),
                    })
        if passages:
            return passages

    # Method 3: Raw text from MongoDB
    raw_text = paper.get("text", "")
    if raw_text:
        for sentence in segment_text_into_passages(raw_text):
            norm = normalize_text_for_comparison(sentence)
            words = sentence.split()
            if norm and len(words) >= 6:
                passages.append({
                    "page": 1,
                    "text": sentence,
                    "normalized": norm,
                    "word_count": len(words),
                })

    return passages


def find_similarity_matches(
    target_passages: List[Dict[str, Any]],
    corpus_papers: List[Dict[str, Any]],
    similarity_threshold: float = 72.0,
) -> Tuple[List[Dict[str, Any]], int, int]:
    """
    Perform multi-level similarity detection between target passages and corpus papers:
    - Level A: Exact Phrase Match (100% similarity)
    - Level B: Near-Exact / Fuzzy Match (RapidFuzz token_sort_ratio >= 85%)
    - Level C: Similar Text / Paraphrased (RapidFuzz >= 72%)

    Returns:
    - List of structured match records
    - Total words in target passages
    - Total matching words in target passages
    """
    # Pre-extract passages for all corpus papers
    corpus_passages: List[Dict[str, Any]] = []
    for c_paper in corpus_papers:
        c_title = c_paper.get("title") or c_paper.get("filename") or "Unknown Document"
        c_passages = extract_document_passages(c_paper)
        for cp in c_passages:
            corpus_passages.append({
                "source_name": c_title,
                "source_page": cp.get("page", 1),
                "text": cp["text"],
                "normalized": cp["normalized"],
                "word_count": cp["word_count"],
            })

    total_target_words = sum(p["word_count"] for p in target_passages)
    matched_word_indices = set()
    matches: List[Dict[str, Any]] = []
    seen_target_texts = set()

    for t_idx, t_pass in enumerate(target_passages):
        t_norm = t_pass["normalized"]
        t_text = t_pass["text"]
        t_words = t_pass["word_count"]

        # Avoid duplicate match cards for identical sentences in target
        if t_norm in seen_target_texts:
            continue

        best_match = None
        best_score = 0.0
        best_type = ""

        # Step 1: Compare against all corpus passages
        for c_pass in corpus_passages:
            c_norm = c_pass["normalized"]

            # Exact match check
            if t_norm == c_norm:
                best_match = c_pass
                best_score = 100.0
                best_type = "exact_match"
                break

            # If lengths are reasonably comparable, run rapidfuzz
            len_ratio = len(t_norm) / (len(c_norm) or 1)
            if 0.4 < len_ratio < 2.5:
                ratio = fuzz.token_sort_ratio(t_norm, c_norm)
                if ratio > best_score and ratio >= similarity_threshold:
                    best_score = ratio
                    best_match = c_pass
                    if ratio >= 88.0:
                        best_type = "near_exact"
                    else:
                        best_type = "similar_text"

        if best_match and best_score >= similarity_threshold:
            seen_target_texts.add(t_norm)
            matched_word_indices.add(t_idx)

            m_id = len(matches) + 1
            matches.append({
                "id": m_id,
                "match_id": m_id,
                "page": t_pass.get("page", 1),
                "matched_text": t_text,
                "source_passage": best_match["text"],
                "source_document": best_match["source_name"],
                "source_page": best_match.get("source_page", 1),
                "similarity": round(best_score, 1),
                "similarity_percentage": round(best_score, 1),
                "match_type": best_type,
            })

    # Calculate non-overlapping matched words
    matched_words_count = sum(
        target_passages[idx]["word_count"]
        for idx in matched_word_indices
        if idx < len(target_passages)
    )

    # Sort matches by similarity score descending
    matches.sort(key=lambda m: m["similarity"], reverse=True)

    return matches, total_target_words, matched_words_count


def analyze_paper_similarity(
    pdf_id: str,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    """
    Main entry point for similarity/plagiarism analysis for a given PDF.
    - Validates paper existence in MongoDB.
    - Compares against all other uploaded documents in the ResearchX repository.
    - Computes authentic similarity percentage and returns structured findings.
    """
    clean_id = str(pdf_id).strip()

    # Check in-memory cache if not forced
    if not force_refresh and clean_id in _PLAGIARISM_CACHE:
        cache_time, cached_result = _PLAGIARISM_CACHE[clean_id]
        res = dict(cached_result)
        res["cached"] = True
        return res

    # Locate target paper in MongoDB by ObjectId or filename
    query: Dict[str, Any] = {}
    if ObjectId.is_valid(clean_id):
        query = {"$or": [{"_id": ObjectId(clean_id)}, {"filename": clean_id}]}
    else:
        query = {"filename": clean_id}

    target_paper = papers_collection.find_one(query)
    if not target_paper:
        raise ValueError(f"Research paper with identifier '{pdf_id}' was not found in the database.")

    target_filename = target_paper.get("filename") or "Uploaded Paper"
    target_title = target_paper.get("title") or target_filename

    # Extract target passages
    target_passages = extract_document_passages(target_paper)
    if not target_passages:
        # Check if text is present
        raw_text = target_paper.get("text", "")
        if not raw_text or not raw_text.strip():
            raise ValueError(
                f"Paper '{target_filename}' contains no extracted readable text. "
                "The PDF may be image-only or corrupt."
            )
        target_passages = [{"page": 1, "text": raw_text[:500], "normalized": normalize_text_for_comparison(raw_text[:500]), "word_count": len(raw_text[:500].split())}]

    # Retrieve all comparison papers from MongoDB (excluding target)
    corpus_query: Dict[str, Any] = {"filename": {"$ne": target_filename}}
    if "_id" in target_paper:
        corpus_query = {"_id": {"$ne": target_paper["_id"]}, "filename": {"$ne": target_filename}}

    corpus_papers = list(papers_collection.find(corpus_query))

    matches: List[Dict[str, Any]] = []
    total_words = sum(p["word_count"] for p in target_passages)
    matched_words = 0

    if corpus_papers:
        matches, total_words, matched_words = find_similarity_matches(
            target_passages=target_passages,
            corpus_papers=corpus_papers,
        )
        scope_note = f"Compared against {len(corpus_papers)} uploaded research document(s) in ResearchX repository."
    else:
        # No other papers in repository: Check for self-similarity / internal duplicates
        internal_matches: List[Dict[str, Any]] = []
        seen_norms: Dict[str, Dict[str, Any]] = {}

        for p_idx, p in enumerate(target_passages):
            norm = p["normalized"]
            if norm in seen_norms:
                prev = seen_norms[norm]
                if prev.get("page") != p.get("page"):
                    m_id = len(internal_matches) + 1
                    internal_matches.append({
                        "id": m_id,
                        "match_id": m_id,
                        "page": p.get("page", 1),
                        "matched_text": p["text"],
                        "source_passage": prev["text"],
                        "source_document": f"{target_filename} (Page {prev.get('page', 1)})",
                        "source_page": prev.get("page", 1),
                        "similarity": 100.0,
                        "similarity_percentage": 100.0,
                        "match_type": "exact_match",
                    })
            else:
                seen_norms[norm] = p

        matches = internal_matches
        matched_words = sum(m.get("word_count", 15) for m in matches)
        scope_note = "Only 1 document available in ResearchX repository. Evaluated for internal passage duplication."

    # Compute aggregate similarity percentage
    if total_words > 0 and matched_words > 0:
        raw_score = (matched_words / total_words) * 100.0
        similarity_score = round(min(100.0, max(0.0, raw_score)), 1)
    else:
        similarity_score = 0.0

    original_content = round(max(0.0, 100.0 - similarity_score), 1)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    result: Dict[str, Any] = {
        "pdf_id": str(target_paper.get("_id", clean_id)),
        "filename": target_filename,
        "title": target_title,
        "similarity_score": similarity_score,
        "original_content": original_content,
        "originality_score": original_content,
        "potential_matches_count": len(matches),
        "matches_count": len(matches),
        "comparison_sources_count": len(corpus_papers),
        "total_compared_documents": len(corpus_papers),
        "comparison_scope": scope_note,
        "comparison_corpus": scope_note,
        "total_words_analyzed": total_words,
        "matches": matches[:50],  # Limit to top 50 matches for performance
        "checked_at": now_str,
        "analyzed_at": now_str,
        "cached": False,
    }

    # Store in memory cache
    _PLAGIARISM_CACHE[clean_id] = (result["checked_at"], result)
    if target_filename != clean_id:
        _PLAGIARISM_CACHE[target_filename] = (result["checked_at"], result)

    return result


def clear_plagiarism_cache():
    """Clear all cached plagiarism analysis results."""
    global _PLAGIARISM_CACHE
    _PLAGIARISM_CACHE.clear()
