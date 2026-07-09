import os

import google.generativeai as genai


# ==========================
# Configure Gemini API
# ==========================
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY is not set in environment variables"
    )

genai.configure(
    api_key=api_key
)


# ==========================
# Generation Settings
# ==========================
generation_config = genai.GenerationConfig(
    temperature=0.3,
    max_output_tokens=4096,
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

Your task is to analyze the provided research paper context
and answer the user's question accurately.

IMPORTANT RULES:

1. Use ONLY information supported by the provided context.
2. Do not invent facts, datasets, results, metrics, or citations.
3. If information is missing, explicitly say that it is not
   available in the provided context.
4. Give a complete answer.
5. Do not stop in the middle of a sentence.
6. Use clear headings and structured formatting when useful.
7. Preserve important numerical results and technical details.
8. Distinguish clearly between:
   - paper claims
   - limitations
   - inferred observations
9. Avoid unnecessary repetition.
10. For research summaries, provide enough detail to understand
    the complete paper context.

RESEARCH PAPER CONTEXT:

{context}

USER QUESTION:

{question}

Now provide a complete, accurate, well-structured answer.
"""

    try:
        response = model.generate_content(
            prompt
        )

        if not response.candidates:
            return (
                "Gemini returned no response candidates."
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