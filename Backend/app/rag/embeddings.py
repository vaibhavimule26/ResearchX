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
        print("[RAG] Loading embedding model...")
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
# Create Single Query Embedding
# ==========================================================

def create_query_embedding(
    query: str
) -> List[float]:
    """
    Convert a user query into a single embedding.
    """

    if not query or not query.strip():
        return []

    model = get_embedding_model()

    embedding = model.encode(
        query,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    return embedding.tolist()