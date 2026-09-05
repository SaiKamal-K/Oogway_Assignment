import pytest
from app.providers.cloud_provider import get_llm_provider, ClaudeProvider, OpenAIProvider
from app.providers.ollama_provider import OllamaProvider
from app.skills.ship30_writer import build_ship30_prompt, SHIP_30_SYSTEM_PROMPT
from app.skills.artifact_generator import extract_artifacts

def test_provider_factory():
    """Verify that provider factory instantiates the expected classes."""
    ollama = get_llm_provider("ollama")
    assert isinstance(ollama, OllamaProvider)

    claude = get_llm_provider("claude")
    assert isinstance(claude, ClaudeProvider)

    openai = get_llm_provider("openai")
    assert isinstance(openai, OpenAIProvider)

    # Default fallback
    default_p = get_llm_provider()
    assert isinstance(default_p, OllamaProvider)

@pytest.mark.asyncio
async def test_claude_missing_key_graceful_handling():
    """Verify that ClaudeProvider yields a clean configuration guide instead of crashing when key is absent."""
    provider = ClaudeProvider(api_key="")
    tokens = []
    async for token in provider.generate_response([{"role": "user", "content": "hello"}], "system"):
        tokens.append(token)
    combined = "".join(tokens)
    assert "ANTHROPIC_API_KEY" in combined
    assert "not configured" in combined

def test_ship30_prompt_construction():
    """Verify that Ship 30 for 30 prompt incorporates guest metadata and heuristics."""
    chunks = [
        {
            "episode": "How to build a high-performing growth team",
            "guest": "Adam Fishman",
            "timestamp": "00:05:00",
            "text": "Onboarding is the only experience 100% of users see."
        }
    ]
    prompt = build_ship30_prompt("Explain onboarding leverage", chunks)
    assert "Adam Fishman" in prompt
    assert "00:05:00" in prompt
    assert "1,250-word" in prompt
    assert "<artifact type=" in prompt

def test_artifact_extraction():
    """Verify extraction of <artifact> tags from model response."""
    raw_response = (
        "Here is the requested tactical guide:\n\n"
        "<artifact type=\"markdown\" title=\"The Onboarding Masterclass\">\n"
        "# The Onboarding Masterclass\n"
        "**The First Touch:** Never waste day zero.\n"
        "</artifact>\n\n"
        "Let me know if you want any edits!"
    )
    artifacts = extract_artifacts(raw_response)
    assert len(artifacts) == 1
    assert artifacts[0]["type"] == "markdown"
    assert artifacts[0]["title"] == "The Onboarding Masterclass"
    assert "# The Onboarding Masterclass" in artifacts[0]["content"]

    # Test HTML artifact
    html_response = (
        "<artifact type=\"html\" title=\"Growth Calculator\">\n"
        "<div class=\"card\"><h1>Growth Rate</h1></div>\n"
        "</artifact>"
    )
    html_artifacts = extract_artifacts(html_response)
    assert len(html_artifacts) == 1
    assert html_artifacts[0]["type"] == "html"
    assert html_artifacts[0]["title"] == "Growth Calculator"
