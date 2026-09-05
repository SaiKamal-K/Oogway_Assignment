import httpx
import json
import logging
from typing import AsyncGenerator, Dict, Any, List
from .base import BaseLLMProvider
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class OllamaProvider(BaseLLMProvider):
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.3
    ) -> AsyncGenerator[str, None]:
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "num_ctx": 4096
            }
        }

        url = f"{self.base_url}/api/chat"
        logger.info(f"Streaming from Ollama provider ({self.model}) at {url}")

        try:
            timeout_config = httpx.Timeout(connect=15.0, read=180.0, write=15.0, pool=15.0)
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        err_text = await response.aread()
                        logger.error(f"Ollama returned {response.status_code}: {err_text.decode('utf-8', errors='ignore')}")
                        yield f"\n[Error: Ollama service returned status {response.status_code}. Ensure model '{self.model}' is downloaded via 'ollama run {self.model}']"
                        return

                    async for line in response.aiter_lines():
                        if line:
                            try:
                                chunk = json.loads(line)
                                content = chunk.get("message", {}).get("content", "")
                                if content:
                                    yield content
                                if chunk.get("done", False):
                                    break
                            except json.JSONDecodeError:
                                continue
        except httpx.ConnectError:
            logger.error(f"Cannot connect to Ollama at {self.base_url}")
            yield f"\n[Connection Error: Unable to connect to local Ollama daemon at {self.base_url}. Please ensure Ollama is running ('ollama serve').]"
        except httpx.TimeoutException:
            logger.error(f"Ollama request timed out after 180s for model {self.model}")
            yield f"\n[Timeout Error: Local model '{self.model}' took too long to respond. You can switch to Claude 3.5 Sonnet or GPT-4o from the model selector, or verify Ollama status via 'ollama ps'.]"
        except Exception as e:
            err_msg = str(e).strip() or type(e).__name__
            logger.error(f"Unexpected error in OllamaProvider: {err_msg}")
            yield f"\n[Error generating response from local model: {err_msg}]"
