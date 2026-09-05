import httpx
import json
import time

def test_stream():
    # 1. Create Session
    with httpx.Client(base_url="http://127.0.0.1:8000") as client:
        sess_resp = client.post("/api/sessions", json={"title": "SSE Test Session"})
        sess_data = sess_resp.json()
        session_id = sess_data["id"]
        print(f"Created Session ID: {session_id}")

        print("\nConnecting to SSE /api/chat with model 'ollama' (llama3.2:3b)...")
        start = time.time()
        with client.stream(
            "POST",
            "/api/chat",
            json={
                "session_id": session_id,
                "message": "What is the key takeaway from Elena Verna on product-led growth?",
                "provider": "ollama",
                "ship30_mode": False
            },
            timeout=120.0
        ) as response:
            print(f"Connection established (status {response.status_code}) in {time.time() - start:.2f}s")
            token_count = 0
            for line in response.iter_lines():
                if line.startswith("data: "):
                    payload = line[6:].strip()
                    if payload == "[DONE]":
                        print("\n[DONE event received]")
                        break
                    try:
                        event = json.loads(payload)
                        evt_type = event.get("type")
                        if evt_type == "status":
                            print(f"[STATUS] {event.get('content')}")
                        elif evt_type == "sources":
                            print(f"[SOURCES] Retrieved {len(event.get('sources', []))} chunks")
                        elif evt_type == "token":
                            print(event.get("content"), end="", flush=True)
                            token_count += 1
                        elif evt_type == "artifact":
                            print(f"\n[ARTIFACT] {event.get('artifact', {}).get('title')}")
                    except Exception as err:
                        print(f"[PARSE ERR]: {err} ({payload})")
        print(f"\n\nTotal tokens streamed: {token_count} in {time.time() - start:.2f}s")

if __name__ == "__main__":
    test_stream()
