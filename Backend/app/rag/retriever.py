import chromadb
from typing import List, Dict


# ==========================================================
# ChromaDB Client
# ==========================================================

client = chromadb.PersistentClient(
    path="./chroma_db"
)


# ==========================================================
# Get / Create Collection
# ==========================================================

def get_collection():
    return client.get_or_create_collection(
        name="research_papers"
    )


# ==========================================================
# Store Paper Chunks
# ==========================================================

def index_paper(
    paper_id: str,
    chunks: List[str],
    embeddings: List[List[float]],
    metadata: Dict = None
):
    """
    Store paper chunks and their embeddings in ChromaDB.
    """

    collection = get_collection()

    if not chunks:
        return

    ids = [
        f"{paper_id}_chunk_{i}"
        for i in range(len(chunks))
    ]

    metadatas = []

    for i in range(len(chunks)):
        item = {
            "paper_id": str(paper_id),
            "chunk_index": i
        }

        if metadata:
            item.update(metadata)

        metadatas.append(item)

    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas
    )

    print(
        f"[RAG] Indexed {len(chunks)} chunks "
        f"for paper: {paper_id}"
    )


# ==========================================================
# Retrieve Relevant Chunks
# ==========================================================

def retrieve_chunks(
    query_embedding: List[float],
    paper_id: str = None,
    top_k: int = 5
):
    """
    Retrieve the most relevant chunks for a query.
    """

    if not query_embedding:
        return []

    collection = get_collection()

    total = collection.count()

    if total == 0:
        return []

    top_k = min(top_k, total)

    where = None

    if paper_id:
        where = {
            "paper_id": str(paper_id)
        }

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where,
        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    retrieved = []

    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances
    ):
        retrieved.append({
            "text": document,
            "metadata": metadata or {},
            "distance": float(distance)
        })

    return retrieved