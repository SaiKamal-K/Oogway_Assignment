import httpx
import time

print("Testing Ollama /api/chat...")
start = time.time()
try:
    with httpx.Client(timeout=180.0) as client:
        payload = {
            "model": "llama3.1:8b",
            "messages": [{"role": "user", "content": "Reply with 'Growth Assistant Ready' in 3 words."}],
            "stream": False
        }
        res = client.post("http://localhost:11434/api/chat", json=payload)
        print("Status code:", res.status_code)
        if res.status_code == 200:
            print("Response:", res.json().get("message", {}).get("content"))
            print(f"Elapsed time: {time.time() - start:.2f}s")
        else:
            print("Error:", res.text)
except Exception as e:
    print("Exception:", e)
