from llm_router import get_agent_llm

def test_all_agents():
    print("==================================================")
    print("1. Testing Summarizer Agent (Mistral Small)...")
    summarizer = get_agent_llm("summarizer")
    res_sum = summarizer.invoke("Summarize the importance of Multi-Agent Systems in 1 sentence.")
    print("Output:\n", res_sum.content)

    print("\n==================================================")
    print("2. Testing Research Gap Agent (OpenRouter / DeepSeek)...")
    gap_agent = get_agent_llm("research_gap")
    res_gap = gap_agent.invoke("Identify 1 major research challenge in Multi-Agent AI in 1 sentence.")
    print("Output:\n", res_gap.content)

    print("\n==================================================")
    print("3. Testing Dataset Agent (Mistral Small)...")
    dataset_agent = get_agent_llm("dataset")
    res_data = dataset_agent.invoke("List 2 popular benchmark datasets for NLP.")
    print("Output:\n", res_data.content)
    print("==================================================")

if __name__ == "__main__":
    test_all_agents()