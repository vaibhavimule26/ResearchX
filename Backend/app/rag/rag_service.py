from typing import Optional

from app.rag.embeddings import create_query_embedding
from app.rag.retriever import retrieve_chunks
from app.rag.context_builder import build_rag_context


def retrieve_rag_context(
    query: str,
    paper_id: Optional[str] = None,
    top_k: int = 5,
) -> str:
    """
    Retrieve relevant evidence from indexed paper content
    and convert it into LLM-ready RAG context.
    """

    if not query or not query.strip():
        return "No relevant evidence was retrieved from the paper."

    query_embedding = create_query_embedding(query)

    if not query_embedding:
        return "No relevant evidence was retrieved from the paper."

    retrieved_chunks = retrieve_chunks(
        query_embedding=query_embedding,
        paper_id=paper_id,
        top_k=top_k,
    )

    return build_rag_context(retrieved_chunks)