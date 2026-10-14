import numpy as np
from typing import Dict, Any, Optional

_SENTENCE_TRANSFORMER_MODEL = None


def get_embedding_model():
    """
    Reuse the singleton SentenceTransformer instance loaded in app.embeddings.embedder
    to eliminate duplicate model loads and optimize latency.
    """
    global _SENTENCE_TRANSFORMER_MODEL
    if _SENTENCE_TRANSFORMER_MODEL is not None:
        return _SENTENCE_TRANSFORMER_MODEL

    try:
        from app.embeddings.embedder import model
        _SENTENCE_TRANSFORMER_MODEL = model
        return _SENTENCE_TRANSFORMER_MODEL
    except Exception:
        from sentence_transformers import SentenceTransformer
        _SENTENCE_TRANSFORMER_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        return _SENTENCE_TRANSFORMER_MODEL


def calculate_semantic_similarity(reference_text: str, generated_text: str) -> Dict[str, Any]:
    """
    Computes cosine similarity between reference content and agent output using all-MiniLM-L6-v2.
    Returns the exact score (0.0 to 1.0) and percentage, explicitly labeled as 'Semantic Similarity Score'.
    Never mislabels cosine similarity as pure accuracy.
    """
    ref = (reference_text or "").strip()
    gen = (generated_text or "").strip()

    if not ref or not gen:
        return {
            "semantic_similarity_score": 0.0,
            "semantic_similarity_percentage": 0.0,
            "label": "Semantic Similarity Score",
            "metric_type": "cosine_similarity",
            "model": "all-MiniLM-L6-v2",
            "explanation": "Insufficient text provided for semantic similarity comparison."
        }

    try:
        model = get_embedding_model()
        ref_sample = ref[:8000]
        gen_sample = gen[:8000]

        embeddings = model.encode(
            [ref_sample, gen_sample],
            normalize_embeddings=True,
            show_progress_bar=False
        )

        ref_vec = np.array(embeddings[0], dtype=np.float32)
        gen_vec = np.array(embeddings[1], dtype=np.float32)

        raw_cosine = float(np.dot(ref_vec, gen_vec))
        similarity_score = max(0.0, min(1.0, raw_cosine))
        similarity_percentage = round(similarity_score * 100.0, 2)

        return {
            "semantic_similarity_score": round(similarity_score, 4),
            "semantic_similarity_percentage": similarity_percentage,
            "label": "Semantic Similarity Score",
            "metric_type": "cosine_similarity",
            "model": "all-MiniLM-L6-v2",
            "explanation": f"Semantic vector alignment between reference content and generated output is {similarity_percentage}%."
        }
    except Exception as e:
        print(f"[SemanticEvaluator Error]: {e}")
        return {
            "semantic_similarity_score": 0.0,
            "semantic_similarity_percentage": 0.0,
            "label": "Semantic Similarity Score",
            "metric_type": "cosine_similarity",
            "model": "all-MiniLM-L6-v2",
            "error": str(e),
            "explanation": "Could not calculate semantic similarity due to embedding failure."
        }
