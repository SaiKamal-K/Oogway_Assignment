import requests
import json
import time

def test_ollama():
    print("Testing direct Ollama llama3.2:3b...")
    start = time.time()
    try:
        res = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3.2:3b", "prompt": "Give 3 tips for SaaS onboarding in bullet points.", "stream": False},
            timeout=60
        )
        data = res.json()
        elapsed = time.time() - start
        print(f"Ollama Response ({elapsed:.2f}s):")
        print(data.get("response", "")[:300] + "...")
        print("Done!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_ollama()
