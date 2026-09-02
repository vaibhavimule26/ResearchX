from app.chunking.chunker import chunk_text
from app.embeddings.embedder import create_embeddings
from app.rag.retriever import index_paper, retrieve_chunks
from app.rag.context_builder import build_rag_context


paper_id = "test_paper_1"

text = """
Generative AI can support researchers by helping with
literature analysis, summarization, and knowledge discovery.
However, hallucination and lack of reliable evidence remain
important challenges. Retrieval augmented generation can
improve factual grounding by retrieving relevant information
before generating an answer.
"""


# 1. Chunk the paper text
chunks = chunk_text(
    text,
    chunk_size=500
)

print("Chunks:", len(chunks))


# 2. Create embeddings
embeddings = create_embeddings(chunks)

print(
    "Embeddings created:",
    len(embeddings)
)


# 3. Store chunks in ChromaDB
index_paper(
    paper_id=paper_id,
    chunks=chunks,
    embeddings=embeddings,
    metadata={
        "title": "Test Research Paper"
    }
)


# 4. Create query
query = "What are the challenges of Generative AI?"

query_embedding = create_embeddings(
    [query]
)[0]


# 5. Retrieve relevant chunks
results = retrieve_chunks(
    query_embedding=query_embedding,
    paper_id=paper_id,
    top_k=3
)


# 6. Build RAG context
context = build_rag_context(results)


print("\n================ RAG CONTEXT ================\n")
print(context)