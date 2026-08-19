import os
import re
import time
import logging
from dotenv import load_dotenv
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, GoogleAPIError

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

# Parse multiple keys or single key
raw_keys = os.getenv("GEMINI_API_KEYS") or os.getenv("GEMINI_API_KEY", "")
API_KEYS = [k.strip() for k in raw_keys.split(",") if k.strip()]

if not API_KEYS:
    raise ValueError(
        f"No Gemini API key found in .env.\nExpected GEMINI_API_KEY or GEMINI_API_KEYS at: {ENV_PATH}"
    )

ACTIVE_MODEL_NAME = "gemini-3.6-flash"
current_key_index = 0

generation_config = genai.GenerationConfig(
    temperature=0.3,
    max_output_tokens=8192,
)


def get_configured_model():
    global current_key_index
    active_key = API_KEYS[current_key_index]

    genai.configure(api_key=active_key)
    return genai.GenerativeModel(
        model_name=ACTIVE_MODEL_NAME,
        generation_config=generation_config,
    )


def rotate_key() -> bool:
    global current_key_index
    if len(API_KEYS) > 1:
        current_key_index = (current_key_index + 1) % len(API_KEYS)
        logger.warning(
            f"🔄 Rate limit hit. Switched to API Key #{current_key_index + 1} of {len(API_KEYS)}"
        )
        return True
    return False


def parse_cooldown(error_str: str) -> float:
    match = re.search(r"retry in (\d+(\.\d+)?)s", error_str, re.IGNORECASE)
    if match:
        return float(match.group(1)) + 1.5
    return 20.0


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

    prompt = f"""
You are ResearchX, an AI Research Assistant.

Analyze the provided research paper and answer the question accurately.

IMPORTANT RULES:
1. Use ONLY the provided paper.
2. Never invent facts, datasets, metrics, or citations.
3. If information is unavailable, state: "Not specified in the paper."
4. Do NOT use emojis or special icon characters.
5. Provide a complete, structured academic answer.

RESEARCH PAPER:
{context}

QUESTION:
{question}
"""

    last_error = None

    for attempt in range(max_retries):
        try:
            model = get_configured_model()
            response = model.generate_content(prompt)

            if not response.candidates:
                return "Gemini returned no response."

            text = response.text
            if not text or not text.strip():
                return "Gemini returned an empty response."

            return text.strip()

        except ResourceExhausted as error:
            last_error = error
            error_str = str(error)

            # Rotate to next key if available
            if rotate_key():
                time.sleep(1)
                continue

            # If only 1 key exists, wait out the Google cooldown
            wait_time = parse_cooldown(error_str)
            logger.warning(
                f"⚠️ Rate limit on single API key. Pausing execution for {wait_time:.1f}s (Attempt {attempt + 1}/{max_retries})..."
            )
            time.sleep(wait_time)

        except GoogleAPIError as error:
            last_error = error
            logger.error(f"Google API Error: {str(error)}")
            if rotate_key():
                time.sleep(1)
            else:
                time.sleep(2)

        except Exception as error:
            raise RuntimeError(
                f"Gemini generation failed: {str(error)}"
            ) from error

    raise RuntimeError(
        f"Request failed after key rotation/cooldown: {str(last_error)}"
    )