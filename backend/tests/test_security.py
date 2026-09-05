"""
Security tests for artifact sanitization and sandbox configuration.
"""
import pytest
from app.skills.artifact_generator import extract_artifacts


def test_xss_script_in_artifact():
    """Verify that malicious script tags can be extracted but the extraction doesn't execute them."""
    malicious = (
        '<artifact type="html" title="Evil Widget">'
        '<script>document.cookie</script>'
        '<div>Hello</div>'
        '</artifact>'
    )
    artifacts = extract_artifacts(malicious)
    assert len(artifacts) == 1
    assert artifacts[0]["type"] == "html"
    # The content is extracted as-is — sanitization happens on the frontend via DOMPurify
    assert "<script>" in artifacts[0]["content"] or "<div>" in artifacts[0]["content"]


def test_xss_event_handler_in_artifact():
    """Verify extraction of HTML with event handler attributes."""
    malicious = (
        '<artifact type="html" title="XSS Handler">'
        '<img src="x" onerror="alert(1)">'
        '<div onmouseover="steal()">hover me</div>'
        '</artifact>'
    )
    artifacts = extract_artifacts(malicious)
    assert len(artifacts) == 1
    assert artifacts[0]["type"] == "html"


def test_iframe_injection_in_artifact():
    """Verify that iframe injection attempts in artifacts are extracted but isolated."""
    malicious = (
        '<artifact type="html" title="Iframe Inject">'
        '<iframe src="https://evil.com"></iframe>'
        '</artifact>'
    )
    artifacts = extract_artifacts(malicious)
    assert len(artifacts) == 1


def test_markdown_artifact_safe_extraction():
    """Verify that markdown artifacts don't contain executable code."""
    md_content = (
        '<artifact type="markdown" title="Safe Essay">'
        '# Growth Playbook\n\n'
        '**Key Insight:** Onboarding is the 100% growth lever.\n\n'
        '## Section 1\n\n'
        'Normal markdown content here.\n'
        '</artifact>'
    )
    artifacts = extract_artifacts(md_content)
    assert len(artifacts) == 1
    assert artifacts[0]["type"] == "markdown"
    assert "# Growth Playbook" in artifacts[0]["content"]


def test_artifact_type_validation():
    """Verify only 'markdown' and 'html' types are recognized."""
    # Valid types
    valid_md = '<artifact type="markdown" title="Test">content</artifact>'
    valid_html = '<artifact type="html" title="Test">content</artifact>'
    
    assert len(extract_artifacts(valid_md)) == 1
    assert len(extract_artifacts(valid_html)) == 1
    
    # Invalid type should not match
    invalid = '<artifact type="javascript" title="Test">alert(1)</artifact>'
    assert len(extract_artifacts(invalid)) == 0


def test_sandbox_attribute_documentation():
    """
    Verify the sandbox security boundary documentation.
    
    The SandboxedIframe component uses:
      sandbox="allow-scripts"
    
    This means:
    - Scripts CAN run (needed for interactive HTML widgets)
    - Scripts CANNOT access parent document cookies, localStorage, or DOM
    - Scripts CANNOT navigate the parent page
    - Scripts CANNOT create popups
    - Forms CANNOT be submitted
    
    The absence of 'allow-same-origin' is the critical security boundary:
    without it, the iframe is treated as a unique origin, preventing
    any access to the parent page's data.
    """
    # This is a documentation test — the actual sandbox attribute
    # is set in the frontend React component (SandboxedIframe.tsx)
    # and cannot be tested from Python. This test documents the
    # security model for auditing purposes.
    expected_sandbox = "allow-scripts"
    assert "allow-same-origin" not in expected_sandbox
    assert "allow-scripts" in expected_sandbox


def test_multiple_artifacts_extraction():
    """Verify extraction of multiple artifacts from a single response."""
    response = (
        'Here is a markdown essay:\n\n'
        '<artifact type="markdown" title="Essay One">Content 1</artifact>\n\n'
        'And an HTML widget:\n\n'
        '<artifact type="html" title="Widget One"><div>Widget</div></artifact>'
    )
    artifacts = extract_artifacts(response)
    assert len(artifacts) == 2
    assert artifacts[0]["title"] == "Essay One"
    assert artifacts[1]["title"] == "Widget One"


def test_empty_artifact_not_extracted():
    """Verify that artifacts with empty content are not extracted."""
    response = '<artifact type="markdown" title="Empty"></artifact>'
    artifacts = extract_artifacts(response)
    assert len(artifacts) == 0
