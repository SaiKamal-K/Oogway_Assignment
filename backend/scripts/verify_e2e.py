import httpx
import json
import sys

API_BASE = "http://127.0.0.1:8000"

def run_verification():
    print("=== 1. Health Diagnostic Probe ===")
    r = httpx.get(f"{API_BASE}/api/health", timeout=5.0)
    print(f"Health response ({r.status_code}):", json.dumps(r.json(), indent=2))

    print("\n=== 2. Creating New Chat Session ===")
    r = httpx.post(f"{API_BASE}/api/sessions", json={"title": "Adam Fishman Onboarding Verification"}, timeout=5.0)
    print(f"Session response ({r.status_code}):", json.dumps(r.json(), indent=2))
    session_id = r.json()["id"]

    print("\n=== 3. Streaming Grounded QA with Local Ollama (llama3.1:8b) ===")
    chat_payload = {
        "session_id": session_id,
        "message": "What is Adam Fishman's view on onboarding and why is it a 100% growth lever?",
        "mode": "default",
        "provider": "ollama"
    }

    tokens = []
    sources = []
    with httpx.stream("POST", f"{API_BASE}/api/chat", json=chat_payload, timeout=180.0) as resp:
        for line in resp.iter_lines():
            if line.startswith("data: "):
                data_str = line[6:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    event = json.loads(data_str)
                    ev_type = event.get("type")
                    if ev_type == "status":
                        print(f"  [STATUS]: {event.get('content')}", flush=True)
                    elif ev_type == "sources":
                        sources = event.get("sources", [])
                        print(f"  [SOURCES RETRIEVED]: {len(sources)} sources", flush=True)
                        for s in sources[:2]:
                            print(f"    - {s.get('guest')} ({s.get('timestamp')}): {s.get('episode')}", flush=True)
                    elif ev_type == "token":
                        tok = event.get("content", "")
                        tokens.append(tok)
                        print(tok, end="", flush=True)
                except Exception:
                    pass

    print("\n\n=== Streaming Finished ===")
    print(f"Total tokens received: {len(tokens)}")
    print(f"Total sources retrieved: {len(sources)}")

    if len(tokens) > 0:
        print("\n[SUCCESS] Grounded QA with Ollama is fully functional!")
    else:
        print("\n[WARNING] No tokens received.")

if __name__ == "__main__":
    run_verification()
