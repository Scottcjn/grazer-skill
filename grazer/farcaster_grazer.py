"""
Farcaster Discovery Plugin for Grazer
Discovers casts via the Neynar API.
Optional API key for higher rate limits; public endpoints work without auth.
"""

import requests
from typing import List, Dict, Optional


NEYNAR_API_BASE = "https://api.neynar.com/v2/farcaster"


class FarcasterGrazer:
    """Discover casts from Farcaster via the Neynar API."""

    def __init__(self, api_key: Optional[str] = None, timeout: int = 15):
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        headers = {
            "User-Agent": "Grazer/1.9.1 (Elyan Labs; https://github.com/Scottcjn/grazer-skill)",
            "Accept": "application/json",
        }
        if api_key:
            headers["x-api-key"] = api_key
        self.session.headers.update(headers)

    def discover(
        self,
        query: str = "AI agents",
        limit: int = 10,
    ) -> List[Dict]:
        """Search Farcaster casts.

        Args:
            query: Free-text search query
            limit: Maximum number of results (max 100)

        Returns:
            List of cast dicts with author, text, url, timestamps, metrics
        """
        params = {
            "q": query,
            "limit": min(limit, 100),
        }

        resp = self.session.get(
            f"{NEYNAR_API_BASE}/cast/search",
            params=params,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        casts = []
        result_field = data.get("result", data)
        raw_casts = result_field.get("casts", []) if isinstance(result_field, dict) else []

        for item in raw_casts:
            cast = _normalize_cast(item)
            casts.append(cast)

        return casts[:limit]

    def trending(self, limit: int = 10) -> List[Dict]:
        """Get trending casts on Farcaster.

        Args:
            limit: Maximum number of results

        Returns:
            List of cast dicts
        """
        params = {
            "limit": min(limit, 100),
        }

        resp = self.session.get(
            f"{NEYNAR_API_BASE}/feed/trending",
            params=params,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        casts = []
        for item in data.get("casts", []):
            cast = _normalize_cast(item)
            casts.append(cast)

        return casts[:limit]

    def channel(self, channel_id: str, limit: int = 10) -> List[Dict]:
        """Get casts from a specific Farcaster channel.

        Args:
            channel_id: Channel identifier (e.g. 'ai', 'dev', 'crypto')
            limit: Maximum results

        Returns:
            List of cast dicts from the channel
        """
        params = {
            "channel_id": channel_id,
            "limit": min(limit, 100),
        }

        resp = self.session.get(
            f"{NEYNAR_API_BASE}/feed/channels",
            params=params,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        casts = []
        for item in data.get("casts", []):
            cast = _normalize_cast(item)
            casts.append(cast)

        return casts[:limit]


def _normalize_cast(item: dict) -> Dict:
    """Normalize a Farcaster cast object into a consistent dict."""
    author_data = item.get("author", {})
    reactions = item.get("reactions", {})

    fid = author_data.get("fid", "")
    hash_val = item.get("hash", "")
    username = author_data.get("username", "")

    # Warpcast URL
    url = f"https://warpcast.com/{username}/{hash_val[:10]}" if username and hash_val else ""

    return {
        "hash": hash_val,
        "text": item.get("text", ""),
        "timestamp": item.get("timestamp", ""),
        "author_fid": fid,
        "author_username": username,
        "author_name": author_data.get("display_name", username),
        "author_pfp": author_data.get("pfp_url", ""),
        "url": url,
        "likes": reactions.get("likes_count", reactions.get("likes", 0)),
        "recasts": reactions.get("recasts_count", reactions.get("recasts", 0)),
        "replies": item.get("replies", {}).get("count", 0),
        "channel": item.get("channel", {}).get("id", "") if isinstance(item.get("channel"), dict) else "",
    }
