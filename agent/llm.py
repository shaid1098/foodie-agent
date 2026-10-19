"""LLM client with automatic failover: Groq (primary) -> Gemini (backup).
Both expose OpenAI-compatible chat endpoints, with provider-specific payload harmonization."""
import os, time, requests, json
from dotenv import load_dotenv
load_dotenv()

FALLBACK_THOUGHT_SIGNATURE = "EmAKXgFpFH0TOQw0JycEUw8CUhHluvBG8LX7QppQKEZ4neUXt2yZ50UFxLaSe1aaoAUHNTzRmviN5xA/ZfOTudBABr0CSjlnX2TnpSNyTJpxSSiN77dXCoq+89B/sKuhtYM="

def providers():
    # Groq primary (with fallback models on 429) -> Gemini backup
    groq_models = [
        os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        "openai/gpt-oss-20b",
        "qwen/qwen3.8-27b"
    ]
    # Remove duplicates while preserving order
    seen = set()
    groq_unique = [m for m in groq_models if not (m in seen or seen.add(m))]
    
    list_providers = []
    groq_key = os.getenv("GROQ_API_KEY")
    for m in groq_unique:
        list_providers.append({
            "name": f"groq ({m.split('/')[-1]})",
            "provider_type": "groq",
            "key": groq_key,
            "url": "https://api.groq.com/openai/v1/chat/completions",
            "model": m
        })

    gemini_key = os.getenv("GEMINI_API_KEY")
    list_providers.append({
        "name": "gemini",
        "provider_type": "gemini",
        "key": gemini_key,
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "model": os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    })
    
    return list_providers

def adapt_messages_for_provider(messages, provider_type):
    """Ensures cross-provider compatibility (e.g. Gemini thought signatures and non-empty user content)."""
    adapted = []
    has_user = False
    
    for m in messages:
        entry = dict(m)
        role = entry.get("role")
        if role == "user" and entry.get("content"):
            has_user = True
            
        if provider_type == "gemini":
            # 1. Gemini requires thought_signature for any functionCall in history
            if role == "assistant" and entry.get("tool_calls"):
                new_calls = []
                for tc in entry["tool_calls"]:
                    tc_copy = dict(tc)
                    extra = tc_copy.get("extra_content")
                    if not extra or not isinstance(extra, dict) or not extra.get("google", {}).get("thought_signature"):
                        tc_copy["extra_content"] = {"google": {"thought_signature": FALLBACK_THOUGHT_SIGNATURE}}
                    new_calls.append(tc_copy)
                entry["tool_calls"] = new_calls
                
            # 2. If assistant content is None/empty and no tool_calls, ensure non-empty string
            if role == "assistant" and not entry.get("content") and not entry.get("tool_calls"):
                entry["content"] = "Thinking..."
        
        adapted.append(entry)
    
    # Gemini requires at least one user message (cannot have only system messages)
    if provider_type == "gemini" and not has_user:
        adapted.append({"role": "user", "content": "Hello"})
        
    return adapted

def llm_call(messages, tools, retries=1):
    """Returns (provider_name, assistant_message, errors). Raises if all providers fail."""
    errors = []
    for p in providers():
        if not p["key"]:
            errors.append(f"{p['name']}: no API key set")
            continue
            
        payload_messages = adapt_messages_for_provider(messages, p["provider_type"])
        body = {
            "model": p["model"],
            "messages": payload_messages,
            "temperature": 0.4
        }
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"
            
        headers = {
            "Authorization": f"Bearer {p['key']}",
            "Content-Type": "application/json"
        }
        
        for attempt in range(retries):
            try:
                r = requests.post(p["url"], timeout=35, headers=headers, json=body)
                if r.status_code == 200:
                    resp_json = r.json()
                    msg = resp_json["choices"][0]["message"]
                    return p["name"], msg, errors
                
                # Check for rate limit / 429
                err_text = r.text[:250]
                errors.append(f"{p['name']} HTTP {r.status_code}: {err_text}")
                if r.status_code == 429:
                    # On rate limit, don't waste time retrying the same locked endpoint; fail over immediately!
                    break
            except Exception as e:
                errors.append(f"{p['name']} attempt {attempt+1}: {e}")
                time.sleep(0.5)
                
    raise RuntimeError("All LLM providers failed: " + " | ".join(errors))
