import os
from dotenv import load_dotenv
import google.generativeai as genai


# ==========================
# Load Environment Variables
# ==========================
BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)
ENV_PATH = os.path.join(
    BASE_DIR,
    "..",
    "..",
    ".env"
)
load_dotenv(
    dotenv_path=ENV_PATH,
    override=True,
)


# ==========================
# Configure Gemini API
# ==========================
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        f"GEMINI_API_KEY not found.\nExpected .env at: {ENV_PATH}"
    )

genai.configure(
    api_key=api_key
)


# ==========================
# Generation Settings
# ==========================
generation_config = genai.GenerationConfig(
    temperature=0.3,
    max_output_tokens=8192,
)


# ==========================
# Load Gemini Model
# ==========================
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config=generation_config,
)


# ==========================
# Generate Research Answer
# ==========================
def generate_answer(
    context: str,
    question: str,
) -> str:

    if not context or not context.strip():
        return (
            "No research paper context was provided."
        )

    if not question or not question.strip():
        return (
            "No research question was provided."
        )

    prompt = f"""
You are ResearchX, an AI Research Assistant.

Your task is to analyze the provided research paper
and answer the user's question accurately.

IMPORTANT RULES

1. Use ONLY the provided paper.
2. Never invent facts.
3. Never invent datasets.
4. Never invent numerical values.
5. Never invent citations.
6. If information is unavailable,
   clearly state that.
7. Write professionally.
8. Never stop in the middle.
9. Produce complete answers.
10. Preserve technical details.

RESEARCH PAPER

{context}

QUESTION

{question}

Provide a complete answer.
"""

    try:

        response = model.generate_content(
            prompt
        )

        if not response.candidates:
            return (
                "Gemini returned no response."
            )

        text = response.text

        if not text or not text.strip():
            return (
                "Gemini returned an empty response."
            )

        return text.strip()

    except Exception as error:
        raise RuntimeError(
            f"Gemini generation failed: {str(error)}"
        ) from error


# =====================================================
# Generate Large Answer (Multiple Gemini Calls)
# =====================================================
def generate_large_answer(
    context: str,
    question_part1: str,
    question_part2: str,
) -> str:

    part1 = generate_answer(
        context=context,
        question=question_part1,
    )

    part2 = generate_answer(
        context=context,
        question=question_part2,
    )

    return (
        part1
        + "\n\n"
        + part2
    )