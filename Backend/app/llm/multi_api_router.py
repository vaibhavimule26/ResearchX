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
# Reusable Client & Session Cache
# ==========================================================
_http_session = requests.Session()
_cohere_client = None
_groq_client = None


def _get_cohere_client(api_key: str):
    global _cohere_client
    if _cohere_client is None:
        import cohere
        _cohere_client = cohere.ClientV2(api_key=api_key)
    return _cohere_client


def _get_groq_client(api_key: str):
    global _groq_client
    if _groq_client is None:
        from groq import Groq
        _groq_client = Groq(api_key=api_key, max_retries=1)
    return _groq_client


# ==========================================================
# 1. Cohere
# ==========================================================
def call_cohere_api(prompt: str, context: str = "") -> str:

    api_key = os.getenv("COHERE_API_KEY")

    if not api_key:
        return "No LLM API key is available."

    try:
        co = _get_cohere_client(api_key=api_key)

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
        client = _get_groq_client(api_key=api_key)

        user_content = build_user_content(
            prompt,
            context,
            120000
        )

        # Active, verified high-speed models on Groq
        models = [
            "openai/gpt-oss-120b",
            "qwen/qwen3.8-27b",
            "openai/gpt-oss-20b",
            "qwen/qwen3.6-27b",
            "groq/compound",
        ]

        for model in models:

            try:
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
                    max_tokens=4096
                )

                output = res.choices[0].message.content

                if output and output.strip():
                    return output.strip()

            except Exception as model_error:
                err_msg = str(model_error).lower()
                # Fast failover on rate limit or missing model without stalling
                if "rate_limit" in err_msg or "429" in err_msg:
                    print(f"[Groq Rate Limit - {model}]: {model_error}")
                    break
                print(
                    f"[Groq Error - {model}]: {model_error}"
                )
                continue

    except Exception as e:
        print(f"[Groq Client Error]: {e}")

    print("[Groq] Using Cohere fallback.")
    return call_cohere_api(prompt, context)


# ==========================================================
# 3. Mistral
# ==========================================================
def call_mistral_api(prompt: str, context: str = "") -> str:

    api_key = os.getenv("MISTRAL_API_KEY")

    if not api_key:
        return call_cohere_api(prompt, context)

    try:
        user_content = build_user_content(
            prompt,
            context,
            120000
        )

        res = _http_session.post(
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
            timeout=15
        )

        if res.status_code == 200:
            return res.json()[
                "choices"
            ][0]["message"]["content"].strip()

        print(
            f"[Mistral Error {res.status_code}]: {res.text[:200]}"
        )

    except Exception as e:
        print(f"[Mistral Error]: {e}")

    return call_cohere_api(prompt, context)


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

        res = _http_session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "meta-llama/llama-3.3-70b-instruct",
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
            timeout=15
        )

        if res.status_code == 200:
            return res.json()[
                "choices"
            ][0]["message"]["content"].strip()

        print(
            f"[OpenRouter Error {res.status_code}]: "
            f"{res.text[:200]}"
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
        return call_cohere_api(prompt, context)

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

    return call_cohere_api(prompt, context)