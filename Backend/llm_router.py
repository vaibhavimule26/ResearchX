import os
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from langchain_openai import ChatOpenAI

load_dotenv()

def get_agent_llm(agent_name: str):
    agent = agent_name.lower().strip()
    mistral_key = os.getenv("MISTRAL_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    
    # 1. Mistral Small - High Precision, Structured Extraction, Fast (Summarizer, Coordinator, Dataset)
    if agent in ["summarizer", "coordinator", "dataset", "comparison", "report"]:
        return ChatMistralAI(
            model="mistral-small-latest",
            mistral_api_key=mistral_key,
            temperature=0.1
        )

    # 2. OpenRouter Free DeepSeek / Qwen - Complex Reasoning & Research Gap
    elif agent in ["research_gap", "novelty", "experiment", "ppt"]:
        return ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
            model="deepseek/deepseek-chat",  # Top reasoning, free tier compatible
            temperature=0.1
        )

    # Default Fallback
    else:
        return ChatMistralAI(
            model="mistral-small-latest",
            mistral_api_key=mistral_key,
            temperature=0.1
        )