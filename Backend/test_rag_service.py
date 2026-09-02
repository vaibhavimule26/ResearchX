from app.rag.rag_service import retrieve_rag_context


query = """
What method was used for object segmentation
and what were the experimental results?
"""


context = retrieve_rag_context(
    query=query,
    paper_id="robotics_test_1",
    top_k=2,
)


print("\n================ RAG SERVICE TEST ================\n")
print(context)
print("\n===================================================\n")