from app.llm.multi_api_router import call_groq_api


def normalize_research_query(user_query: str) -> str:
    """
    Convert a natural-language research request into a clean
    academic search query.

    Handles:
    - Full sentences
    - Extra words such as 'find papers about'
    - Common spelling mistakes
    - Natural language questions
    - Technical research terminology
    """

    if not user_query or not user_query.strip():
        return ""

    user_query = user_query.strip()

    prompt = f"""
You are ResearchX Query Processor.

Convert the user's research request into a concise academic
search query.

USER QUERY:
{user_query}

RULES:

1. Understand the user's intended research topic.
2. Full sentences are allowed.
3. Remove conversational phrases such as:
   - find papers about
   - I want research on
   - show me papers
   - give me articles about
   - can you search for
4. Correct obvious spelling mistakes.
5. Preserve important technical terms.
6. Do NOT invent a new research topic.
7. Do NOT change the meaning of the user's request.
8. Keep important constraints such as:
   - healthcare
   - robotics
   - LLM
   - multimodal
   - 2024
   - medical diagnosis
   - reinforcement learning
9. Return ONLY the cleaned search query.
10. Do not add explanations.
11. Do not use quotation marks.

Examples:

USER:
genrative ai in healtcare

OUTPUT:
generative AI in healthcare

USER:
I want to find research papers about generative AI in healthcare

OUTPUT:
generative AI in healthcare

USER:
Can you find recent papers about multimodal LLMs for medical diagnosis?

OUTPUT:
multimodal LLMs medical diagnosis

USER:
research papers on robot navigation using deep reinforcement learning

OUTPUT:
robot navigation deep reinforcement learning

USER:
what are recent applications of retrieval augmented generation?

OUTPUT:
retrieval augmented generation applications

Now process the user's query.

Return ONLY the final search query.
"""

    try:
        result = call_groq_api(
            prompt=prompt,
            context=""
        )

        cleaned = (result or "").strip()

        # Remove accidental markdown/code formatting
        cleaned = cleaned.replace("```", "").strip()
        cleaned = cleaned.strip('"').strip("'").strip()

        if cleaned:
            return cleaned

    except Exception as e:
        print(
            f"[Query Processor Error]: {e}"
        )

    # Safe fallback: use original query
    return user_query