import os
import json
import requests
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)
load_dotenv(os.path.join(os.getcwd(), ".env"), override=True)

# 1. Cohere
def call_cohere_api(prompt: str, context: str = "") -> str:
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        return "Cohere API key missing."
    try:
        import cohere
        co = cohere.ClientV2(api_key=api_key)
        res = co.chat(
            model="command-r-08-2024",
            messages=[{"role": "user", "content": f"Context:\n{context[:12000]}\n\nTask:\n{prompt}" if context else prompt}]
        )
        return res.message.content[0].text.strip()
    except Exception as e:
        print(f"[Cohere Error]: {e}")
        return "Cohere request failed."

# 2. Groq
def call_groq_api(prompt: str, context: str = "") -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return call_cohere_api(prompt, context)

    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        user_content = f"Context:\n{context[:12000]}\n\nTask:\n{prompt}" if context else prompt
        
        for model in ["llama-3.1-8b-instant", "openai/gpt-oss-20b", "gemma2-9b-it"]:
            try:
                res = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are an expert AI research scientist. Always format tables using standard Markdown with '|' pipes."},
                        {"role": "user", "content": user_content}
                    ],
                    temperature=0.2,
                    max_tokens=2500
                )
                return res.choices[0].message.content.strip()
            except Exception:
                continue
    except Exception as e:
        print(f"[Groq Error]: {e}")

    return call_cohere_api(prompt, context)

# 3. Mistral
def call_mistral_api(prompt: str, context: str = "") -> str:
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        return call_groq_api(prompt, context)
    try:
        res = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "mistral-small-latest",
                "messages": [
                    {"role": "system", "content": "You are a senior academic reviewer. Always format tables using Markdown pipe syntax with '|'."},
                    {"role": "user", "content": f"Context:\n{context[:12000]}\n\nTask:\n{prompt}" if context else prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 2500
            },
            timeout=25
        )
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[Mistral Error]: {e}")
    return call_groq_api(prompt, context)

# 4. OpenRouter
def call_openrouter_api(prompt: str, context: str = "") -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return call_groq_api(prompt, context)
    try:
        res = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "meta-llama/llama-3.3-70b-instruct:free",
                "messages": [{"role": "user", "content": f"Context:\n{context[:12000]}\n\nTask:\n{prompt}" if context else prompt}],
                "max_tokens": 2500
            },
            timeout=25
        )
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[OpenRouter Error]: {e}")
    return call_groq_api(prompt, context)

# 5. Gemini Router
def call_gemini_api(prompt: str, context: str = "") -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    user_content = f"Context:\n{context[:15000]}\n\nTask:\n{prompt}" if context else prompt

    if api_key and api_key.startswith("AIzaSy"):
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash-latest")
            return model.generate_content(user_content).text.strip()
        except Exception as e:
            print(f"[Gemini API Error]: {e}")

    return call_groq_api(prompt, context)