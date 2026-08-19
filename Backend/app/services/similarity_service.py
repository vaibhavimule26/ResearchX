from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Load model only once
model = SentenceTransformer("all-MiniLM-L6-v2")


def calculate_similarity(query, papers):
    """
    Calculate semantic similarity between user query and paper titles.
    """

    if not papers:
        return papers

    titles = [paper.get("title", "") for paper in papers]

    query_embedding = model.encode([query])

    title_embeddings = model.encode(titles)

    similarities = cosine_similarity(
        query_embedding,
        title_embeddings
    )[0]

    for paper, score in zip(papers, similarities):
        paper["semantic_score"] = float(score)

    return papers