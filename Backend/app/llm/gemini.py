import os
import re
import time
import logging
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ResearchX-LLM")

# ==========================
# Load Environment Variables
# ==========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, "..", "..", ".env")

load_dotenv(
    dotenv_path=ENV_PATH,
    override=True,
)

_cached_model = None

def get_configured_model():
    """Initializes high-accuracy LLM using active working keys from .env with client caching."""
    global _cached_model
    if _cached_model is not None:
        return _cached_model

    groq_key = os.getenv("GROQ_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    mistral_key = os.getenv("MISTRAL_API_KEY")

    if groq_key:
        _cached_model = ChatGroq(
            model_name="qwen/qwen3.8-27b",
            groq_api_key=groq_key,
            temperature=0.1,
            max_tokens=4096,
        )
    elif openrouter_key:
        _cached_model = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
            model="meta-llama/llama-3.3-70b-instruct",
            temperature=0.1,
            max_tokens=4096,
        )
    elif mistral_key:
        _cached_model = ChatMistralAI(
            model="mistral-small-latest",
            mistral_api_key=mistral_key,
            temperature=0.1,
            max_tokens=4096,
        )
    else:
        raise ValueError("No active API keys found in .env (Groq, OpenRouter, or Mistral required).")

    return _cached_model


# ==========================
# Generate Research Answer
# ==========================
def generate_answer(
    context: str,
    question: str,
    max_retries: int = 2,
) -> str:
    if not context or not context.strip():
        return "No research paper context was provided."

    if not question or not question.strip():
        return "No research question was provided."

    t0 = time.time()

    # 1. Fast Primary: Groq API with verified ultra-fast models (sub-second)
    try:
        from app.llm.multi_api_router import call_groq_api
        groq_resp = call_groq_api(prompt=question, context=context)
        if groq_resp and len(groq_resp.strip()) > 50 and not groq_resp.startswith("Groq"):
            print(f"[PERF] generate_answer via Groq: {time.time() - t0:.2f}s")
            return groq_resp.strip()
    except Exception as g_err:
        logger.warning(f"Groq primary failed: {g_err}")

    # 2. Secondary: Cohere API
    try:
        from app.llm.multi_api_router import call_cohere_api
        cohere_resp = call_cohere_api(prompt=question, context=context)
        if cohere_resp and len(cohere_resp.strip()) > 50 and not cohere_resp.startswith("Cohere"):
            print(f"[PERF] generate_answer via Cohere: {time.time() - t0:.2f}s")
            return cohere_resp.strip()
    except Exception as c_err:
        logger.warning(f"Cohere secondary failed: {c_err}")

    # 3. Tertiary: OpenRouter API
    try:
        from app.llm.multi_api_router import call_openrouter_api
        or_resp = call_openrouter_api(prompt=question, context=context)
        if or_resp and len(or_resp.strip()) > 50:
            print(f"[PERF] generate_answer via OpenRouter: {time.time() - t0:.2f}s")
            return or_resp.strip()
    except Exception as or_err:
        logger.warning(f"OpenRouter tertiary failed: {or_err}")

    # 4. Fallback: LangChain configured model
    for attempt in range(max_retries):
        try:
            model = get_configured_model()
            prompt = f"Research Paper Context:\n{context[:24000]}\n\nTask / Question:\n{question}"
            response = model.invoke(prompt)
            text = response.content if hasattr(response, "content") else str(response)
            if text and text.strip():
                print(f"[PERF] generate_answer via LangChain fallback: {time.time() - t0:.2f}s")
                return text.strip()
        except Exception as error:
            logger.warning(f"LangChain attempt {attempt + 1} failed: {error}")
            if "429" in str(error) or "rate" in str(error).lower():
                break

    raise RuntimeError("All LLM providers failed to generate an answer.")