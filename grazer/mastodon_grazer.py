"""
Mastodon / ActivityPub Fediverse Discovery Plugin for Grazer
Discovers posts, trending hashtags, and public timelines from any Mastodon instance.
No API key required for public reads.
"""

import requests
from typing import List, Dict, Optional


DEFAULT_INSTANCE = "mastodon.social"


class MastodonGrazer:
    """Discover posts from the Mastodon fediverse."""

    def __init__(self, instance: str = DEFAULT_INSTANCE, timeout: int = 15):
        self.instance = instance.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Grazer/1.9.1 (Elyan Labs; https://github.com/Scottcjn/grazer-skill)"}
        )

    def _api_url(self, instance: Optional[str] = None) -> str:
        inst = (instance or self.instance).rstrip("/")
        if not inst.startswith("http"):
            inst = f"https://{inst}"
        return f"{inst}/api/v1"

    def discover(
        self,
        query: str = "AI",
        instance: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict]:
        """Search public posts on a Mastodon instance.

        Args:
            query: Free-text search query
            instance: Instance hostname (default: mastodon.social)
            limit: Maximum results (max 40)

        Returns:
            List of post dicts
        """
        base = self._api_url(instance)
        params = {
            "q": query,
            "type": "statuses",
            "limit": min(limit, 40),
        }

        resp = self.session.get(
            f"{base}/search",
            params=params,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        posts = []
        for item in data.get("statuses", []):
            post = _normalize_status(item)
            posts.append(post)

        return posts[:limit]

    def trending_tags(self, instance: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Get trending hashtags on a Mastodon instance.

        Args:
            instance: Instance hostname (default: mastodon.social)
            limit: Maximum results

        Returns:
            List of trending hashtag dicts
        """
        base = self._api_url(instance)
        params = {"limit": min(limit, 40)}

        resp = self.session.get(
            f"{base}/trends/tags",
            params=params,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        tags = []
        for item in data if isinstance(data, list) else []:
            tag = {
                "name": item.get("name", ""),
                "url": item.get("url", ""),
                "uses_today": 0,
                "accounts_today": 0,
            }
            history = item.get("history", [])
            if history and isinstance(history[0], dict):
                tag["uses_today"] = int(history[0].get("uses", 0))
                tag["accounts_today"] = int(history[0].get("accounts", 0))
            tags.append(tag)

        return tags[:limit]

    def trending_posts(self, instance: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Get trending posts on a Mastodon instance.

        Args:
            instance: Instance hostname (default: mastodon.social)
            limit: Maximum results

        Returns:
            List of trending post dicts
        """
        base = self._api_url(instance)
        params = {"limit": min(limit, 40)}

        resp = self.session.get(
            f"{base}/trends/statuses",
            params=params,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        posts = []
        for item in data if isinstance(data, list) else []:
            post = _normalize_status(item)
            posts.append(post)

        return posts[:limit]

    def public_timeline(
        self,
        instance: Optional[str] = None,
        limit: int = 10,
        local: bool = False,
    ) -> List[Dict]:
        """Get the public timeline of a Mastodon instance.

        Args:
            instance: Instance hostname (default: mastodon.social)
            limit: Maximum results (max 40)
            local: If True, only show local posts (not federated)

        Returns:
            List of post dicts
        """
        base = self._api_url(instance)
        params = {
            "limit": min(limit, 40),
            "local": "true" if local else "false",
        }

        resp = self.session.get(
            f"{base}/timelines/public",
            params=params,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        posts = []
        for item in data if isinstance(data, list) else []:
            post = _normalize_status(item)
            posts.append(post)

        return posts[:limit]


def _normalize_status(item: dict) -> Dict:
    """Normalize a Mastodon status object into a consistent dict."""
    account = item.get("account", {})

    # Strip HTML tags from content for plain-text display
    content = item.get("content", "")
    # Simple tag stripping (avoid requiring BeautifulSoup)
    import re
    plain_text = re.sub(r"<[^>]+>", "", content).strip()

    return {
        "id": item.get("id", ""),
        "text": plain_text,
        "content_html": content,
        "created_at": item.get("created_at", ""),
        "author_acct": account.get("acct", ""),
        "author_name": account.get("display_name", account.get("acct", "")),
        "author_url": account.get("url", ""),
        "url": item.get("url", ""),
        "favourites": item.get("favourites_count", 0),
        "reblogs": item.get("reblogs_count", 0),
        "replies": item.get("replies_count", 0),
        "language": item.get("language", ""),
        "visibility": item.get("visibility", "public"),
    }
