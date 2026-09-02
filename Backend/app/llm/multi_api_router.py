import os
import requests
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

load_dotenv(
    os.path.join(BASE_DIR, ".env"),
    override=True
)

load_dotenv(
    os.path.join(os.getcwd(), ".env"),
    override=True
)


# ==========================================================
# Helper: Safe context limit
# ==========================================================
def build_user_content(
    prompt: str,
    context: str = "",
    context_limit: int = 120000
) -> str:

    if context:
        return (
            "Research Paper Context:\n"
            f"{context[:context_limit]}\n\n"
            "Task:\n"
            f"{prompt}"
        )

    return prompt


# ==========================================================
# 1. Cohere
# ==========================================================
def call_cohere_api(prompt: str, context: str = "") -> str:

    api_key = os.getenv("COHERE_API_KEY")

    if not api_key:
        return "No LLM API key is available."

    try:
        import cohere

        co = cohere.ClientV2(api_key=api_key)

        user_content = build_user_content(
            prompt,
            context,
            120000
        )

        res = co.chat(
            model="command-r-08-2024",
            messages=[
                {
                    "role": "user",
                    "content": user_content
                }
            ]
        )

        return res.message.content[0].text.strip()

    except Exception as e:
        print(f"[Cohere Error]: {e}")
        return "Cohere request failed."


# ==========================================================
# 2. Groq
# ==========================================================
def call_groq_api(prompt: str, context: str = "") -> str:

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        print("[Groq] API key missing. Using Mistral / Cohere fallback.")
        return call_mistral_api(prompt, context)

    try:
        from groq import Groq

        client = Groq(
            api_key=api_key,
            max_retries=1,
        )

        user_content = build_user_content(
            prompt,
            context,
            120000
        )

        # Active, high-speed Groq models
        models = [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ]

        for model in models:

            try:
                print(f"[Groq] Trying model: {model}")

                res = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are ResearchX, an expert academic "
                                "research assistant. Analyze the provided "
                                "research paper context thoroughly. Synthesize "
                                "concrete, scholarly, evidence-grounded insights "
                                "from the paper's title, abstract, methodology, "
                                "and domain focus. Avoid generic placeholders "
                                "like 'Not specified' or 'N/A' whenever the "
                                "technical problem, approach, domain, or "
                                "limitations can be synthesized from context."
                            )
                        },
                        {
                            "role": "user",
                            "content": user_content
                        }
                    ],
                    temperature=0.2,
                    max_tokens=2500
                )

                output = res.choices[0].message.content

                if output and output.strip():
                    print(
                        f"[Groq] Success with model: {model}"
                    )
                    return output.strip()

            except Exception as model_error:
                print(
                    f"[Groq Error - {model}]: {model_error}"
                )
                continue

    except Exception as e:
        print(f"[Groq Client Error]: {e}")

    print("[Groq] All models failed. Using Mistral fallback.")
    return call_mistral_api(prompt, context)


# ==========================================================
# 3. Mistral
# ==========================================================
def call_mistral_api(prompt: str, context: str = "") -> str:

    api_key = os.getenv("MISTRAL_API_KEY")

    if not api_key:
        return call_groq_api(prompt, context)

    try:
        user_content = build_user_content(
            prompt,
            context,
            120000
        )

        res = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "mistral-small-latest",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a senior academic reviewer. "
                            "Analyze only the supplied research context. "
                            "Do not invent missing information."
                        )
                    },
                    {
                        "role": "user",
                        "content": user_content
                    }
                ],
                "temperature": 0.2,
                "max_tokens": 2500
            },
            timeout=60
        )

        if res.status_code == 200:
            return res.json()[
                "choices"
            ][0]["message"]["content"].strip()

        print(
            f"[Mistral Error {res.status_code}]: {res.text}"
        )

    except Exception as e:
        print(f"[Mistral Error]: {e}")

    return call_groq_api(prompt, context)


# ==========================================================
# 4. OpenRouter
# ==========================================================
def call_openrouter_api(prompt: str, context: str = "") -> str:

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        return call_groq_api(prompt, context)

    try:
        user_content = build_user_content(
            prompt,
            context,
            120000
        )

        res = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "meta-llama/llama-3.3-70b-instruct:free",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are ResearchX, an academic research "
                            "assistant. Use only the provided context."
                        )
                    },
                    {
                        "role": "user",
                        "content": user_content
                    }
                ],
                "temperature": 0.2,
                "max_tokens": 2500
            },
            timeout=60
        )

        if res.status_code == 200:
            return res.json()[
                "choices"
            ][0]["message"]["content"].strip()

        print(
            f"[OpenRouter Error {res.status_code}]: "
            f"{res.text}"
        )

    except Exception as e:
        print(f"[OpenRouter Error]: {e}")

    return call_groq_api(prompt, context)


# ==========================================================
# 5. Gemini
# ==========================================================
def call_gemini_api(prompt: str, context: str = "") -> str:

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return call_groq_api(prompt, context)

    user_content = build_user_content(
        prompt,
        context,
        120000
    )

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)

        model = genai.GenerativeModel(
            "gemini-1.5-flash-latest"
        )

        response = model.generate_content(
            user_content
        )

        if response.text:
            return response.text.strip()

    except Exception as e:
        print(f"[Gemini API Error]: {e}")

    return call_groq_api(prompt, context)