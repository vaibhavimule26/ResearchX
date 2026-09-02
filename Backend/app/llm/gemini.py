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

def get_configured_model():
    """Initializes high-accuracy LLM using active working keys from .env."""
    mistral_key = os.getenv("MISTRAL_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")

    if mistral_key:
        return ChatMistralAI(
            model="mistral-small-latest",
            mistral_api_key=mistral_key,
            temperature=0.1
        )
    elif groq_key:
        return ChatGroq(
            model_name="llama-3.1-8b-instant",
            groq_api_key=groq_key,
            temperature=0.1
        )
    elif openrouter_key:
        return ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key,
            model="deepseek/deepseek-chat",
            temperature=0.1
        )
    else:
        raise ValueError("No active API keys found in .env (Mistral, Groq, or OpenRouter required).")


# ==========================
# Generate Research Answer
# ==========================
def generate_answer(
    context: str,
    question: str,
    max_retries: int = 3,
) -> str:
    if not context or not context.strip():
        return "No research paper context was provided."

    if not question or not question.strip():
        return "No research question was provided."

    prompt = f"""You are ResearchX, an advanced AI Academic Research Assistant.

Analyze the provided research paper context thoroughly and synthesize an accurate, detailed, and scholarly answer.

GUIDELINES:
1. Ground your analysis in the provided paper context (title, abstract, methodology, results, and problem formulation).
2. Synthesize concrete academic insights. Avoid generic placeholders like "Not specified", "N/A", or "Not available".
3. Provide a complete, well-structured scholarly answer with clear technical reasoning.
4. Do NOT use emojis or informal commentary.

RESEARCH PAPER:
{context}

QUESTION / TASK:
{question}
"""

    last_error = None

    for attempt in range(max_retries):
        try:
            model = get_configured_model()
            response = model.invoke(prompt)

            text = response.content if hasattr(response, "content") else str(response)
            if not text or not text.strip():
                return "LLM returned an empty response."

            return text.strip()

        except Exception as error:
            last_error = error
            logger.warning(f"Generation attempt {attempt + 1} failed: {str(error)}")
            time.sleep(1.5)

    raise RuntimeError(f"Request failed after retries: {str(last_error)}")