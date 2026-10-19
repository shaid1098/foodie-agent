"""LLM client with automatic failover: Groq (primary) -> Gemini (backup).
Both expose OpenAI-compatible chat endpoints, so one code path serves both."""
import os, time, requests
from dotenv import load_dotenv
load_dotenv()

def providers():
    return [
        {"name": "groq", "key": os.getenv("GROQ_API_KEY"),
         "url": "https://api.groq.com/openai/v1/chat/completions",
         "model": os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")},
        {"name": "gemini", "key": os.getenv("GEMINI_API_KEY"),
         "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
         "model": os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")},
    ]

def llm_call(messages, tools, retries=2):
    """Returns (provider_name, assistant_message, errors). Raises if all providers fail."""
    errors = []
    for p in providers():
        if not p["key"]:
            errors.append(f"{p['name']}: no API key set"); continue
        for attempt in range(retries):
            try:
                r = requests.post(p["url"], timeout=40,
                    headers={"Authorization": f"Bearer {p['key']}"},
                    json={"model": p["model"], "messages": messages,
                          "tools": tools, "tool_choice": "auto", "temperature": 0.4})
                r.raise_for_status()
                return p["name"], r.json()["choices"][0]["message"], errors
            except Exception as e:
                errors.append(f"{p['name']} attempt {attempt+1}: {e}")
                time.sleep(1)
    raise RuntimeError("All LLM providers failed: " + " | ".join(errors))
