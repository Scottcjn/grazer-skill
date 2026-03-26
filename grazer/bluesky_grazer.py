"""
Bluesky Discovery Plugin for Grazer
Discovers posts via the AT Protocol public API.
No API key required for public reads.
"""

import requests
from typing import List, Dict, Optional


BSKY_API_BASE = "https://public.api.bsky.app/xrpc"


class BlueskyGrazer:
    """Discover posts from Bluesky's public AT Protocol API."""

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Grazer/1.9.1 (Elyan Labs; https://github.com/Scottcjn/grazer-skill)"}
        )

    def discover(
        self,
        query: str = "AI agents",
        limit: int = 10,
        sort: str = "latest",
    ) -> List[Dict]:
        """Search Bluesky posts via app.bsky.feed.searchPosts.

        Args:
            query: Free-text search query
            limit: Maximum number of results (max 100)
            sort: Sort order — 'top' or 'latest'

        Returns:
            List of post dicts with author, text, url, timestamps, metrics
        """
        params = {
            "q": query,
            "limit": min(limit, 100),
            "sort": sort,
        }

        resp = self.session.get(
            f"{BSKY_API_BASE}/app.bsky.feed.searchPosts",
            params=params,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        posts = []
        for item in data.get("posts", []):
            post = _normalize_post(item)
            posts.append(post)

        return posts[:limit]

    def timeline(
        self,
        actor: str,
        limit: int = 10,
    ) -> List[Dict]:
        """Get an actor's feed (public posts).

        Args:
            actor: DID or handle (e.g. 'alice.bsky.social')
            limit: Maximum number of results (max 100)

        Returns:
            List of post dicts
        """
        params = {
            "actor": actor,
            "limit": min(limit, 100),
        }

        resp = self.session.get(
            f"{BSKY_API_BASE}/app.bsky.feed.getAuthorFeed",
            params=params,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        posts = []
        for item in data.get("feed", []):
            post_data = item.get("post", item)
            post = _normalize_post(post_data)
            posts.append(post)

        return posts[:limit]

    def get_profile(self, actor: str) -> Dict:
        """Get a Bluesky user profile.

        Args:
            actor: DID or handle (e.g. 'alice.bsky.social')

        Returns:
            Profile dict with handle, displayName, description, follower counts
        """
        params = {"actor": actor}
        resp = self.session.get(
            f"{BSKY_API_BASE}/app.bsky.actor.getProfile",
            params=params,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        return {
            "did": data.get("did", ""),
            "handle": data.get("handle", ""),
            "display_name": data.get("displayName", ""),
            "description": data.get("description", ""),
            "followers_count": data.get("followersCount", 0),
            "follows_count": data.get("followsCount", 0),
            "posts_count": data.get("postsCount", 0),
            "avatar": data.get("avatar", ""),
            "url": f"https://bsky.app/profile/{data.get('handle', '')}",
        }


def _normalize_post(item: dict) -> Dict:
    """Normalize a Bluesky post object into a consistent dict."""
    author_data = item.get("author", {})
    record = item.get("record", {})
    uri = item.get("uri", "")

    # Build web URL from AT URI: at://did/app.bsky.feed.post/rkey
    handle = author_data.get("handle", "")
    rkey = uri.rsplit("/", 1)[-1] if "/" in uri else ""
    web_url = f"https://bsky.app/profile/{handle}/post/{rkey}" if handle and rkey else ""

    return {
        "uri": uri,
        "cid": item.get("cid", ""),
        "text": record.get("text", ""),
        "created_at": record.get("createdAt", ""),
        "author_handle": handle,
        "author_name": author_data.get("displayName", handle),
        "author_did": author_data.get("did", ""),
        "url": web_url,
        "likes": item.get("likeCount", 0),
        "reposts": item.get("repostCount", 0),
        "replies": item.get("replyCount", 0),
        "language": record.get("langs", [""])[0] if record.get("langs") else "",
    }
