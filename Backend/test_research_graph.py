from app.workflow.research_graph import research_graph


test_state = {
    "topic": "AI in healthcare",
    "papers": [],
    "paper_id": "robotics_test_1",
}


print("\n================ LANGGRAPH TEST ================\n")

result = research_graph.invoke(test_state)

print("\n================ GRAPH COMPLETED ================\n")

print("Status:")
print(result.get("status"))

print("\nRAG Context:")
print(result.get("rag_context", "")[:1000])

print("\nSummary:")
print(result.get("summary"))

print("\nResearch Gap:")
print(result.get("research_gap"))

print("\nLiterature:")
print(result.get("literature"))

print("\nNovelty:")
print(result.get("novelty"))

print("\nDatasets:")
print(result.get("datasets"))

print("\nExperiments:")
print(result.get("experiments"))

print("\nComparison:")
print(result.get("comparison"))

print("\nFinal Report:")
print(result.get("final_report"))

print("\n=================================================\n")