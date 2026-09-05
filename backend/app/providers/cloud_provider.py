import os
import json
import logging
import httpx
from typing import AsyncGenerator, Dict, Any, List
from .base import BaseLLMProvider
from .ollama_provider import OllamaProvider
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class ClaudeProvider(BaseLLMProvider):
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model or settings.CLAUDE_MODEL

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.3
    ) -> AsyncGenerator[str, None]:
        if not self.api_key:
            yield (
                "\n[Notice: `ANTHROPIC_API_KEY` is not configured in .env. "
                "Switch to the local 'Ollama (llama3.1:8b)' provider in the header selector for instant offline inference, "
                "or provide your Anthropic API key in .env.]"
            )
            return

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        # Format messages for Anthropic Messages API
        formatted_messages = []
        for m in messages:
            role = "user" if m.get("role") in ["user", "system"] else "assistant"
            formatted_messages.append({"role": role, "content": m.get("content", "")})

        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "temperature": temperature,
            "system": system_prompt,
            "messages": formatted_messages,
            "stream": True
        }

        url = "https://api.anthropic.com/v1/messages"
        logger.info(f"Streaming from Anthropic Claude ({self.model})")

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    if response.status_code != 200:
                        err = await response.aread()
                        logger.error(f"Anthropic returned {response.status_code}: {err.decode('utf-8', errors='ignore')}")
                        yield f"\n[Anthropic API Error {response.status_code}: {err.decode('utf-8', errors='ignore')}]"
                        return

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            raw_data = line[6:].strip()
                            if raw_data == "[DONE]":
                                break
                            try:
                                event = json.loads(raw_data)
                                if event.get("type") == "content_block_delta":
                                    delta = event.get("delta", {})
                                    if delta.get("type") == "text_delta":
                                        yield delta.get("text", "")
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error(f"ClaudeProvider streaming error: {e}")
            yield f"\n[Error communicating with Anthropic Claude: {str(e)}]"

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.3
    ) -> AsyncGenerator[str, None]:
        if not self.api_key:
            yield (
                "\n[Notice: `OPENAI_API_KEY` is not configured in .env. "
                "Switch to the local 'Ollama (llama3.1:8b)' provider in the header selector for offline execution, "
                "or supply an OpenAI key in .env.]"
            )
            return

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        full_messages = [{"role": "system", "content": system_prompt}] + messages
        payload = {
            "model": self.model,
            "messages": full_messages,
            "stream": True,
            "temperature": temperature
        }

        url = "https://api.openai.com/v1/chat/completions"
        logger.info(f"Streaming from OpenAI ({self.model})")

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    if response.status_code != 200:
                        err = await response.aread()
                        logger.error(f"OpenAI returned {response.status_code}: {err.decode('utf-8', errors='ignore')}")
                        yield f"\n[OpenAI API Error {response.status_code}: {err.decode('utf-8', errors='ignore')}]"
                        return

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            raw_data = line[6:].strip()
                            if raw_data == "[DONE]":
                                break
                            try:
                                chunk = json.loads(raw_data)
                                choices = chunk.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error(f"OpenAIProvider error: {e}")
            yield f"\n[Error communicating with OpenAI: {str(e)}]"

def get_llm_provider(provider_name: str = None) -> BaseLLMProvider:
    """Factory creating the designated LLM provider instance."""
    name = (provider_name or settings.DEFAULT_PROVIDER).lower()
    if name == "claude" or name == "anthropic":
        return ClaudeProvider()
    elif name == "openai" or name == "gpt-4o":
        return OpenAIProvider()
    elif name == "ollama-8b" or "8b" in name:
        return OllamaProvider(model="llama3.1:8b")
    else:
        # Default: use the configured Ollama model (defaults to llama3.1:8b)
        return OllamaProvider(model=settings.OLLAMA_MODEL)

