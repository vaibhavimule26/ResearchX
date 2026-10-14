from typing import List

from sentence_transformers import SentenceTransformer


# ==========================================================
# Embedding Model
# ==========================================================

_model = None


def get_embedding_model():
    """
    Load the embedding model only once.
    """
    global _model

    if _model is None:
        try:
            _model = SentenceTransformer(
                "all-MiniLM-L6-v2",
                local_files_only=True
            )
        except Exception:
            _model = SentenceTransformer(
                "all-MiniLM-L6-v2"
            )
        print("[RAG] Embedding model loaded.")

    return _model


# ==========================================================
# Create Embeddings
# ==========================================================

def create_embeddings(
    texts: List[str]
) -> List[List[float]]:
    """
    Convert text chunks into vector embeddings.
    """

    if not texts:
        return []

    model = get_embedding_model()

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    return embeddings.tolist()


# ==========================================================
# Create Single Query Embedding (with in-memory cache)
# ==========================================================

import threading

_QUERY_EMBEDDING_CACHE = {}
_QUERY_EMBEDDING_LOCK = threading.Lock()
_MAX_QUERY_EMBEDDINGS = 256


def create_query_embedding(
    query: str
) -> List[float]:
    """
    Convert a user query into a single embedding with LRU-style in-memory caching.
    """

    if not query or not query.strip():
        return []

    cache_key = query.strip()
    with _QUERY_EMBEDDING_LOCK:
        if cache_key in _QUERY_EMBEDDING_CACHE:
            return _QUERY_EMBEDDING_CACHE[cache_key]

    model = get_embedding_model()

    embedding = model.encode(
        query,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    result = embedding.tolist()

    with _QUERY_EMBEDDING_LOCK:
        if len(_QUERY_EMBEDDING_CACHE) >= _MAX_QUERY_EMBEDDINGS:
            _QUERY_EMBEDDING_CACHE.pop(next(iter(_QUERY_EMBEDDING_CACHE)))
        _QUERY_EMBEDDING_CACHE[cache_key] = result

    return result