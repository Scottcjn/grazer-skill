"""
Nostr Discovery Plugin for Grazer
Discovers Nostr events via the nostr.band REST API.
No WebSocket needed, no API key required.
"""

import requests
from typing import List, Dict, Optional


NOSTR_BAND_API = "https://api.nostr.band"


class NostrGrazer:
    """Discover Nostr events via the nostr.band REST search API."""

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Grazer/1.9.1 (Elyan Labs; https://github.com/Scottcjn/grazer-skill)"}
        )

    def discover(
        self,
        query: str = "AI",
        limit: int = 10,
    ) -> List[Dict]:
        """Search Nostr events via nostr.band.

        Args:
            query: Free-text search query
            limit: Maximum number of results

        Returns:
            List of event dicts with content, author pubkey, timestamps
        """
        params = {
            "q": query,
            "limit": min(limit, 100),
        }

        resp = self.session.get(
            f"{NOSTR_BAND_API}/v0/search",
            params=params,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        events = []
        for item in data.get("events", []):
            event = _normalize_event(item)
            events.append(event)

        return events[:limit]

    def trending(self, limit: int = 10) -> List[Dict]:
        """Get trending Nostr notes.

        Args:
            limit: Maximum number of results

        Returns:
            List of trending event dicts
        """
        resp = self.session.get(
            f"{NOSTR_BAND_API}/v0/trending/notes",
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        events = []
        for item in data.get("notes", []):
            # Trending endpoint may nest event data differently
            event_data = item.get("event", item)
            event = _normalize_event(event_data)
            events.append(event)

        return events[:limit]

    def profile(self, pubkey: str) -> Optional[Dict]:
        """Get a Nostr user profile by public key.

        Args:
            pubkey: Hex public key or npub

        Returns:
            Profile dict or None if not found
        """
        resp = self.session.get(
            f"{NOSTR_BAND_API}/v0/profiles",
            params={"pubkey": pubkey},
            timeout=self.timeout,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()

        profiles = data.get("profiles", [])
        if not profiles:
            return None

        p = profiles[0] if isinstance(profiles[0], dict) else {}
        meta = p.get("profile", p.get("content", {}))
        if isinstance(meta, str):
            import json as _json
            try:
                meta = _json.loads(meta)
            except (ValueError, TypeError):
                meta = {}

        return {
            "pubkey": p.get("pubkey", pubkey),
            "name": meta.get("name", ""),
            "display_name": meta.get("display_name", meta.get("name", "")),
            "about": meta.get("about", ""),
            "picture": meta.get("picture", ""),
            "nip05": meta.get("nip05", ""),
            "url": f"https://nostr.band/{pubkey}",
        }


def _normalize_event(item: dict) -> Dict:
    """Normalize a Nostr event object into a consistent dict."""
    event_id = item.get("id", "")
    pubkey = item.get("pubkey", "")
    created_at = item.get("created_at", 0)
    content = item.get("content", "")
    kind = item.get("kind", 1)

    # Extract hashtags from tags array
    tags = item.get("tags", [])
    hashtags = []
    for tag in tags if isinstance(tags, list) else []:
        if isinstance(tag, list) and len(tag) >= 2 and tag[0] == "t":
            hashtags.append(tag[1])

    return {
        "id": event_id,
        "pubkey": pubkey,
        "content": content,
        "kind": kind,
        "created_at": created_at,
        "hashtags": hashtags,
        "url": f"https://nostr.band/note{event_id[:8]}" if event_id else "",
        "author_url": f"https://nostr.band/{pubkey}" if pubkey else "",
    }
