"""
YouTube Discovery Plugin for Grazer
Discovers videos via the YouTube Data API v3 (when key is available)
or via lightweight RSS feed parsing (no key required).
"""

import re
import requests
from typing import List, Dict, Optional
from urllib.parse import quote


YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
YOUTUBE_RSS_BASE = "https://www.youtube.com/feeds/videos.xml"


def _parse_youtube_rss(xml_text: str) -> List[Dict]:
    """Parse YouTube RSS/Atom feed into video dicts.

    YouTube channel/playlist feeds are public Atom XML.  We parse them
    with regex to avoid a feedparser dependency.
    """
    entries = []
    raw_entries = re.findall(r"<entry>(.*?)</entry>", xml_text, re.DOTALL)
    for raw in raw_entries:
        video: Dict = {}

        vid_match = re.search(r"<yt:videoId>(.*?)</yt:videoId>", raw)
        if vid_match:
            video["id"] = vid_match.group(1).strip()
            video["url"] = f"https://www.youtube.com/watch?v={video['id']}"

        title_match = re.search(r"<title>(.*?)</title>", raw, re.DOTALL)
        if title_match:
            video["title"] = " ".join(title_match.group(1).split())

        author_match = re.search(r"<author>\s*<name>(.*?)</name>", raw)
        if author_match:
            video["channel"] = author_match.group(1).strip()

        published_match = re.search(r"<published>(.*?)</published>", raw)
        if published_match:
            video["published"] = published_match.group(1).strip()

        # Media group has description and thumbnail
        desc_match = re.search(
            r"<media:description>(.*?)</media:description>", raw, re.DOTALL
        )
        if desc_match:
            video["description"] = " ".join(desc_match.group(1).split())

        thumb_match = re.search(r'<media:thumbnail[^>]+url="([^"]+)"', raw)
        if thumb_match:
            video["thumbnail"] = thumb_match.group(1)

        views_match = re.search(r'<media:statistics[^>]+views="(\d+)"', raw)
        if views_match:
            video["views"] = int(views_match.group(1))

        entries.append(video)

    return entries


class YouTubeGrazer:
    """Discover YouTube videos via API or public RSS feeds."""

    def __init__(self, api_key: Optional[str] = None, timeout: int = 15):
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Grazer/1.9.1 (Elyan Labs; https://github.com/Scottcjn/grazer-skill)"}
        )

    def discover(
        self,
        query: str = "AI agents",
        limit: int = 10,
    ) -> List[Dict]:
        """Discover YouTube videos by search query.

        Uses the Data API v3 when an API key is configured, otherwise
        falls back to scraping search result page for video IDs.

        Args:
            query: Search terms
            limit: Maximum results

        Returns:
            List of video dicts with id, title, channel, url, etc.
        """
        if self.api_key:
            return self._discover_api(query, limit)
        return self._discover_scrape(query, limit)

    def channel_videos(self, channel_id: str, limit: int = 10) -> List[Dict]:
        """Get recent videos from a YouTube channel via its public RSS feed.

        No API key needed -- uses the public Atom feed.

        Args:
            channel_id: YouTube channel ID (e.g. 'UC...')
            limit: Maximum results
        """
        url = f"{YOUTUBE_RSS_BASE}?channel_id={channel_id}"
        resp = self.session.get(url, timeout=self.timeout)
        resp.raise_for_status()
        videos = _parse_youtube_rss(resp.text)
        return videos[:limit]

    def playlist_videos(self, playlist_id: str, limit: int = 10) -> List[Dict]:
        """Get videos from a YouTube playlist via its public RSS feed.

        No API key needed.

        Args:
            playlist_id: YouTube playlist ID
            limit: Maximum results
        """
        url = f"{YOUTUBE_RSS_BASE}?playlist_id={playlist_id}"
        resp = self.session.get(url, timeout=self.timeout)
        resp.raise_for_status()
        videos = _parse_youtube_rss(resp.text)
        return videos[:limit]

    # ── Private helpers ──────────────────────────────────────

    def _discover_api(self, query: str, limit: int) -> List[Dict]:
        """Search via YouTube Data API v3."""
        resp = self.session.get(
            f"{YOUTUBE_API_BASE}/search",
            params={
                "part": "snippet",
                "q": query,
                "maxResults": min(limit, 50),
                "type": "video",
                "key": self.api_key,
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])

        videos = []
        for item in items:
            snippet = item.get("snippet", {})
            vid_id = item.get("id", {}).get("videoId", "")
            videos.append(
                {
                    "id": vid_id,
                    "title": snippet.get("title", ""),
                    "channel": snippet.get("channelTitle", ""),
                    "description": snippet.get("description", ""),
                    "published": snippet.get("publishedAt", ""),
                    "url": f"https://www.youtube.com/watch?v={vid_id}",
                    "thumbnail": snippet.get("thumbnails", {})
                    .get("high", {})
                    .get("url", ""),
                }
            )
        return videos[:limit]

    def _discover_scrape(self, query: str, limit: int) -> List[Dict]:
        """Lightweight scrape fallback -- extracts video IDs from search page."""
        search_url = (
            f"https://www.youtube.com/results?search_query={quote(query)}"
        )
        resp = self.session.get(
            search_url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
                )
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()

        video_ids = re.findall(r"/watch\?v=([a-zA-Z0-9_-]{11})", resp.text)
        unique_ids = list(dict.fromkeys(video_ids))[:limit]

        return [
            {
                "id": vid,
                "title": "(scraped -- use API key for metadata)",
                "channel": "",
                "description": "",
                "published": "",
                "url": f"https://www.youtube.com/watch?v={vid}",
            }
            for vid in unique_ids
        ]
