import threading
from typing import Dict, Optional, Tuple

from app.rag.embeddings import create_query_embedding
from app.rag.retriever import retrieve_chunks
from app.rag.context_builder import build_rag_context

_RAG_CACHE: Dict[Tuple[str, Optional[str], int], str] = {}
_RAG_CACHE_LOCK = threading.Lock()
_MAX_RAG_CACHE = 256


def clear_rag_cache():
    """Clear cached RAG contexts."""
    with _RAG_CACHE_LOCK:
        _RAG_CACHE.clear()


def retrieve_rag_context(
    query: str,
    paper_id: Optional[str] = None,
    top_k: int = 5,
) -> str:
    """
    Retrieve relevant evidence from indexed paper content
    and convert it into LLM-ready RAG context with in-memory caching.
    """

    if not query or not query.strip():
        return "No relevant evidence was retrieved from the paper."

    norm_query = query.strip()
    norm_paper_id = paper_id.strip() if paper_id else None
    cache_key = (norm_query, norm_paper_id, top_k)

    with _RAG_CACHE_LOCK:
        if cache_key in _RAG_CACHE:
            return _RAG_CACHE[cache_key]

    query_embedding = create_query_embedding(norm_query)

    if not query_embedding:
        return "No relevant evidence was retrieved from the paper."

    retrieved_chunks = retrieve_chunks(
        query_embedding=query_embedding,
        paper_id=norm_paper_id,
        top_k=top_k,
    )

    result = build_rag_context(retrieved_chunks)

    with _RAG_CACHE_LOCK:
        if len(_RAG_CACHE) >= _MAX_RAG_CACHE:
            _RAG_CACHE.pop(next(iter(_RAG_CACHE)))
        _RAG_CACHE[cache_key] = result

    return result