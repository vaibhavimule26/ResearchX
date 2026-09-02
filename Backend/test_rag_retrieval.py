from app.rag.embeddings import (
    create_embeddings,
    create_query_embedding,
)

from app.rag.retriever import (
    index_paper,
    retrieve_chunks,
)

from app.rag.context_builder import (
    build_rag_context,
)


# ==========================================================
# 1. Test Paper
# ==========================================================

paper_id = "robotics_test_1"

chunks = [
    """
    The proposed robotics system uses a vision-based object
    segmentation method to identify objects in real-time.
    The method improves perception efficiency for robotic tasks.
    """,

    """
    Experiments were conducted on a robotic manipulation dataset.
    The proposed approach was compared with existing segmentation
    methods and demonstrated improved segmentation performance.
    """,

    """
    The system has limitations related to computational cost and
    scalability when processing complex scenes with many objects.
    """,
]


# ==========================================================
# 2. Create Embeddings for Paper Chunks
# ==========================================================

print("\n[RAG TEST] Creating chunk embeddings...")

embeddings = create_embeddings(chunks)

print(
    f"[RAG TEST] Created embeddings for {len(embeddings)} chunks."
)


# ==========================================================
# 3. Store Paper in ChromaDB
# ==========================================================

print("\n[RAG TEST] Indexing paper...")

index_paper(
    paper_id=paper_id,
    chunks=chunks,
    embeddings=embeddings,
    metadata={
        "title": "Robotics Object Segmentation Test",
    },
)


# ==========================================================
# 4. User Query
# ==========================================================

query = """
What method was used for object segmentation
and what were the experimental results?
"""

print("\n[RAG TEST] Query:")
print(query)


# ==========================================================
# 5. Create Query Embedding
# ==========================================================

print("[RAG TEST] Creating query embedding...")

query_embedding = create_query_embedding(query)

print(
    f"[RAG TEST] Query embedding dimensions: "
    f"{len(query_embedding)}"
)


# ==========================================================
# 6. Retrieve Relevant Chunks
# ==========================================================

print("\n[RAG TEST] Retrieving relevant chunks...")

retrieved = retrieve_chunks(
    query_embedding=query_embedding,
    paper_id=paper_id,
    top_k=2,
)


# ==========================================================
# 7. Display Retrieved Chunks
# ==========================================================

print(
    f"[RAG TEST] Retrieved {len(retrieved)} chunks."
)

for i, item in enumerate(
    retrieved,
    start=1
):
    print("\n------------------------------")
    print(f"Retrieved Chunk {i}")
    print("------------------------------")
    print("Distance:", item.get("distance"))
    print("Metadata:", item.get("metadata"))
    print("Text:")
    print(item.get("text"))


# ==========================================================
# 8. Build Final LLM Context
# ==========================================================

context = build_rag_context(
    retrieved
)


# ==========================================================
# 9. Final RAG Context
# ==========================================================

print("\n")
print("==============================")
print("RAG RETRIEVED CONTEXT")
print("==============================")
print()

print(context)

print("\n")
print("==============================")
print("RAG TEST COMPLETED")
print("==============================")