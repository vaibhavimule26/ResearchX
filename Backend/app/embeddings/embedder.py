from sentence_transformers import SentenceTransformer


# Load embedding model only once
model = SentenceTransformer("all-MiniLM-L6-v2")


def create_embeddings(chunks):
    if not chunks:
        return []

    embeddings = model.encode(
        chunks,
        normalize_embeddings=True,
        show_progress_bar=False
    )

    return embeddings.tolist()


def create_query_embedding(query):
    if not query:
        return []

    embedding = model.encode(
        [query],
        normalize_embeddings=True,
        show_progress_bar=False
    )

    return embedding[0].tolist()