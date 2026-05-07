"""Otter.ai API client.

The Otter.ai enterprise REST API is used to list recent meetings and
retrieve AI-generated summaries. Requires an enterprise API key.

Base URL: https://api.otter.ai/v1
Auth: Bearer token via Authorization header.
"""

import os
import httpx

_BASE = "https://api.otter.ai/v1"
_KEY = os.environ.get("OTTER_API_KEY", "")

_HEADERS = {
    "Authorization": f"Bearer {_KEY}",
    "Accept": "application/json",
}


def _client() -> httpx.Client:
    return httpx.Client(headers=_HEADERS, timeout=20)


def list_speeches(limit: int = 10) -> list[dict]:
    """Return the most recent speeches/meetings for the authenticated user.

    Each item contains at minimum: otid, title, created_at.
    """
    with _client() as c:
        r = c.get(f"{_BASE}/speeches", params={"page_size": limit})
        r.raise_for_status()
        data = r.json()
        # API returns {"speeches": [...]} or a list directly
        if isinstance(data, dict):
            return data.get("speeches", data.get("items", []))
        return data


def get_speech_summary(otid: str) -> str:
    """Fetch the AI summary for a given speech (meeting).

    Returns the summary text, or the full transcript if no summary is present.
    """
    with _client() as c:
        r = c.get(f"{_BASE}/speeches/{otid}")
        r.raise_for_status()
        data = r.json()

    speech = data.get("speech", data)  # handle both envelope and flat shapes
    summary = speech.get("summary") or speech.get("ai_summary") or ""
    if not summary:
        # Fall back to concatenating transcript snippets
        snippets = speech.get("transcripts", [])
        summary = "\n".join(s.get("text", "") for s in snippets[:50])
    return summary.strip() or "(No summary available)"
