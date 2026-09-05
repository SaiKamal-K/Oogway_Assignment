import re
from typing import Optional, Dict, Any, List

ARTIFACT_REGEX = re.compile(
    r'<artifact\s+type=[\'"](?P<type>markdown|html)[\'"]\s+title=[\'"](?P<title>[^\'"]+)[\'"]>(?P<content>.*?)(?:</artifact>|$)',
    re.DOTALL | re.IGNORECASE
)

def extract_artifacts(text: str) -> List[Dict[str, str]]:
    """
    Extract all <artifact type="..." title="...">...</artifact> tags from text.
    Returns list of dicts: {'type': ..., 'title': ..., 'content': ...}
    """
    artifacts = []
    for match in ARTIFACT_REGEX.finditer(text):
        art_type = match.group("type").strip().lower()
        title = match.group("title").strip()
        content = match.group("content").strip()
        if content:
            artifacts.append({
                "type": art_type,
                "title": title,
                "content": content
            })
    return artifacts

def sanitize_response_text(text: str) -> str:
    """Optional helper to cleanly separate chat response text from artifact blocks."""
    return ARTIFACT_REGEX.sub("", text).strip()
