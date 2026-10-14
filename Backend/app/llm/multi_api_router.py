import os
import time
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
    context_limit: int = 24000
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

    t0 = time.time()
    try:
        co = _get_cohere_client(api_key=api_key)

        user_content = build_user_content(
            prompt,
            context,
            24000
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

        output = res.message.content[0].text.strip()
        print(f"[PERF] Cohere LLM call: {time.time() - t0:.2f}s")
        return output

    except Exception as e:
        print(f"[Cohere Error ({time.time() - t0:.2f}s)]: {e}")
        return "Cohere request failed."


# ==========================================================
# 2. Groq
# ==========================================================
def call_groq_api(prompt: str, context: str = "") -> str:

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        print("[Groq] API key missing. Using Cohere fallback.")
        return call_cohere_api(prompt, context)

    t0 = time.time()
    try:
        client = _get_groq_client(api_key=api_key)

        user_content = build_user_content(
            prompt,
            context,
            24000
        )

        # Active, verified high-speed models on Groq
        models = [
            "qwen/qwen3.8-27b",
            "openai/gpt-oss-20b",
            "openai/gpt-oss-120b",
        ]

        for model in models:
            t_model = time.time()
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
                    print(f"[PERF] Groq LLM call ({model}): {time.time() - t_model:.2f}s (total {time.time() - t0:.2f}s)")
                    return output.strip()

            except Exception as model_error:
                err_msg = str(model_error).lower()
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
        return call_groq_api(prompt, context)

    t0 = time.time()
    try:
        user_content = build_user_content(
            prompt,
            context,
            24000
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
            timeout=10
        )

        if res.status_code == 200:
            output = res.json()["choices"][0]["message"]["content"].strip()
            print(f"[PERF] Mistral LLM call: {time.time() - t0:.2f}s")
            return output

        print(
            f"[Mistral Error {res.status_code} ({time.time() - t0:.2f}s)]: {res.text[:200]}"
        )

    except Exception as e:
        print(f"[Mistral Error ({time.time() - t0:.2f}s)]: {e}")

    # Fast failover: Groq first (0.3s) then Cohere
    return call_groq_api(prompt, context)


# ==========================================================
# 4. OpenRouter
# ==========================================================
def call_openrouter_api(prompt: str, context: str = "") -> str:

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        return call_groq_api(prompt, context)

    t0 = time.time()
    try:
        user_content = build_user_content(
            prompt,
            context,
            24000
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
            timeout=12
        )

        if res.status_code == 200:
            output = res.json()["choices"][0]["message"]["content"].strip()
            print(f"[PERF] OpenRouter LLM call: {time.time() - t0:.2f}s")
            return output

        print(
            f"[OpenRouter Error {res.status_code} ({time.time() - t0:.2f}s)]: "
            f"{res.text[:200]}"
        )

    except Exception as e:
        print(f"[OpenRouter Error ({time.time() - t0:.2f}s)]: {e}")

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
        24000
    )

    t0 = time.time()
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
            output = response.text.strip()
            print(f"[PERF] Gemini LLM call: {time.time() - t0:.2f}s")
            return output

    except Exception as e:
        print(f"[Gemini API Error ({time.time() - t0:.2f}s)]: {e}")

    return call_groq_api(prompt, context)