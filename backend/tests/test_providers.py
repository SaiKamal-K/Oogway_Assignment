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


def test_provider_factory_anthropic_alias():
    """Verify 'anthropic' alias maps to ClaudeProvider."""
    provider = get_llm_provider("anthropic")
    assert isinstance(provider, ClaudeProvider)


def test_provider_factory_gpt4o_alias():
    """Verify 'gpt-4o' alias maps to OpenAIProvider."""
    provider = get_llm_provider("gpt-4o")
    assert isinstance(provider, OpenAIProvider)


def test_provider_factory_ollama_8b():
    """Verify 'ollama-8b' maps to OllamaProvider with 8b model."""
    provider = get_llm_provider("ollama-8b")
    assert isinstance(provider, OllamaProvider)
    assert provider.model == "llama3.1:8b"


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


@pytest.mark.asyncio
async def test_openai_missing_key_graceful_handling():
    """Verify that OpenAIProvider yields a clean notice when key is absent."""
    provider = OpenAIProvider(api_key="")
    tokens = []
    async for token in provider.generate_response([{"role": "user", "content": "hello"}], "system"):
        tokens.append(token)
    combined = "".join(tokens)
    assert "OPENAI_API_KEY" in combined
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
    assert '<artifact type=' in prompt


def test_ship30_prompt_empty_chunks():
    """Verify Ship 30 prompt handles empty chunks gracefully."""
    prompt = build_ship30_prompt("Test query", [])
    assert "No relevant podcast chunks found" in prompt


def test_ship30_prompt_multiple_chunks():
    """Verify Ship 30 prompt includes context from multiple chunks."""
    chunks = [
        {
            "episode": "Episode 1",
            "guest": "Guest One",
            "timestamp": "00:05:00",
            "text": "First insight about growth."
        },
        {
            "episode": "Episode 2",
            "guest": "Guest Two",
            "timestamp": "00:10:00",
            "text": "Second insight about retention."
        }
    ]
    prompt = build_ship30_prompt("Growth and retention", chunks)
    assert "Guest One" in prompt
    assert "Guest Two" in prompt
    assert "Context Source 1" in prompt
    assert "Context Source 2" in prompt


def test_ship30_system_prompt_structure():
    """Verify the Ship 30 system prompt contains key methodology elements."""
    assert "Hook" in SHIP_30_SYSTEM_PROMPT
    assert "1,250 words" in SHIP_30_SYSTEM_PROMPT
    assert "Bold Anchor" in SHIP_30_SYSTEM_PROMPT
    assert "artifact" in SHIP_30_SYSTEM_PROMPT
    assert "Checklist" in SHIP_30_SYSTEM_PROMPT


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
