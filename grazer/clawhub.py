"""
ClawHub Integration - Skill Registry with Vector Search
Python SDK for https://clawhub.ai
"""

import requests
from typing import List, Dict, Optional


class ClawHubClient:
    """Client for the ClawHub skill registry API."""

    BASE_URL = "https://clawhub.ai/api/v1"

    def __init__(self, token: Optional[str] = None, timeout: int = 15):
        self.token = token
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Grazer/1.3.0 (Elyan Labs)"})
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

    def search(self, query: str, limit: int = 20) -> List[Dict]:
        """Search skills using vector search."""
        resp = self.session.get(
            f"{self.BASE_URL}/skills",
            params={"search": query, "limit": limit},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("items", [])

    def explore(self, limit: int = 20, cursor: Optional[str] = None) -> Dict:
        """Browse latest updated skills."""
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        resp = self.session.get(
            f"{self.BASE_URL}/skills",
            params=params,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def get_skill(self, slug: str) -> Dict:
        """Get skill details by slug."""
        resp = self.session.get(
            f"{self.BASE_URL}/skills/{slug}",
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def trending(self, limit: int = 20) -> List[Dict]:
        """Get trending/popular skills (sorted by downloads)."""
        data = self.explore(limit=limit)
        items = data.get("items", [])
        return sorted(items, key=lambda x: x.get("stats", {}).get("downloads", 0), reverse=True)
