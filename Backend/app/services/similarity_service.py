from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Load model only once
model = SentenceTransformer("all-MiniLM-L6-v2")


def calculate_similarity(query, papers):
    """
    Calculate semantic similarity between the user query
    and each paper using title + abstract + key contribution.
    """

    if not papers:
        return papers

    query_text = str(query or "").strip()

    if not query_text:
        for paper in papers:
            paper["semantic_score"] = 0.0
        return papers

    paper_texts = []

    for paper in papers:
        title = str(paper.get("title") or "")
        abstract = str(
            paper.get("abstract")
            or paper.get("summary")
            or ""
        )
        contribution = str(
            paper.get("key_contribution")
            or ""
        )

        combined_text = (
            f"Title: {title}. "
            f"Abstract: {abstract}. "
            f"Contribution: {contribution}"
        )

        paper_texts.append(combined_text)

    query_embedding = model.encode(
        [query_text],
        normalize_embeddings=True
    )

    paper_embeddings = model.encode(
        paper_texts,
        normalize_embeddings=True
    )

    similarities = cosine_similarity(
        query_embedding,
        paper_embeddings
    )[0]

    for paper, score in zip(papers, similarities):
        # Cosine similarity is normally [-1, 1].
        # Convert to a clean [0, 1] relevance score.
        normalized_score = (float(score) + 1.0) / 2.0

        paper["semantic_score"] = normalized_score

    return papers