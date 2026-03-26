"""
Podcast Discovery Plugin for Grazer
Discovers podcast episodes via the iTunes Search API and public RSS feeds.
No API key required.
"""

import re
import requests
from typing import List, Dict, Optional
from urllib.parse import quote


ITUNES_SEARCH_URL = "https://itunes.apple.com/search"
ITUNES_LOOKUP_URL = "https://itunes.apple.com/lookup"


def _parse_podcast_rss(xml_text: str) -> List[Dict]:
    """Parse a podcast RSS feed into episode dicts.

    Uses regex to avoid requiring feedparser.  Podcast RSS is
    well-structured (RSS 2.0 with iTunes extensions).
    """
    episodes = []
    raw_items = re.findall(r"<item>(.*?)</item>", xml_text, re.DOTALL)
    for raw in raw_items:
        ep: Dict = {}

        title_match = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", raw, re.DOTALL)
        if title_match:
            ep["title"] = " ".join(title_match.group(1).split())

        desc_match = re.search(
            r"<description>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</description>", raw, re.DOTALL
        )
        if desc_match:
            ep["description"] = " ".join(desc_match.group(1).split())[:500]

        pub_match = re.search(r"<pubDate>(.*?)</pubDate>", raw)
        if pub_match:
            ep["published"] = pub_match.group(1).strip()

        # Audio enclosure
        enc_match = re.search(r'<enclosure[^>]+url="([^"]+)"', raw)
        if enc_match:
            ep["audio_url"] = enc_match.group(1)

        # Duration (iTunes extension)
        dur_match = re.search(r"<itunes:duration>(.*?)</itunes:duration>", raw)
        if dur_match:
            ep["duration"] = dur_match.group(1).strip()

        # Episode link
        link_match = re.search(r"<link>(.*?)</link>", raw)
        if link_match:
            ep["url"] = link_match.group(1).strip()

        # Episode number
        ep_num_match = re.search(r"<itunes:episode>(.*?)</itunes:episode>", raw)
        if ep_num_match:
            ep["episode_number"] = ep_num_match.group(1).strip()

        episodes.append(ep)

    return episodes


class PodcastGrazer:
    """Discover podcasts and episodes via iTunes Search API and RSS feeds."""

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Grazer/1.9.1 (Elyan Labs; https://github.com/Scottcjn/grazer-skill)"}
        )

    def search(
        self,
        query: str = "artificial intelligence",
        limit: int = 10,
        country: str = "US",
    ) -> List[Dict]:
        """Search for podcasts via the iTunes Search API.

        Args:
            query: Search terms
            limit: Maximum results (max 200)
            country: Two-letter country code

        Returns:
            List of podcast dicts with name, artist, feed_url, artwork, etc.
        """
        resp = self.session.get(
            ITUNES_SEARCH_URL,
            params={
                "term": query,
                "media": "podcast",
                "limit": min(limit, 200),
                "country": country,
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])

        podcasts = []
        for r in results:
            podcasts.append(
                {
                    "id": r.get("collectionId"),
                    "name": r.get("collectionName", ""),
                    "artist": r.get("artistName", ""),
                    "feed_url": r.get("feedUrl", ""),
                    "artwork": r.get("artworkUrl600", r.get("artworkUrl100", "")),
                    "genre": r.get("primaryGenreName", ""),
                    "episode_count": r.get("trackCount", 0),
                    "url": r.get("collectionViewUrl", ""),
                }
            )
        return podcasts[:limit]

    def episodes(
        self,
        feed_url: str,
        limit: int = 10,
    ) -> List[Dict]:
        """Fetch recent episodes from a podcast RSS feed.

        Args:
            feed_url: The podcast's RSS feed URL
            limit: Maximum episodes to return

        Returns:
            List of episode dicts with title, description, audio_url, etc.
        """
        resp = self.session.get(feed_url, timeout=self.timeout)
        resp.raise_for_status()
        eps = _parse_podcast_rss(resp.text)
        return eps[:limit]

    def discover(
        self,
        query: str = "AI technology",
        limit: int = 10,
        episodes_per_show: int = 3,
    ) -> List[Dict]:
        """Discover podcasts and their latest episodes in one call.

        Searches iTunes for shows matching the query, then fetches the
        latest episodes from each show's RSS feed.

        Args:
            query: Search terms
            limit: Maximum number of shows
            episodes_per_show: How many episodes to fetch per show

        Returns:
            List of show dicts, each with a nested ``episodes`` list.
        """
        shows = self.search(query, limit=limit)
        for show in shows:
            feed_url = show.get("feed_url")
            if feed_url:
                try:
                    show["episodes"] = self.episodes(feed_url, limit=episodes_per_show)
                except Exception:
                    show["episodes"] = []
            else:
                show["episodes"] = []
        return shows

    def lookup(self, podcast_id: int) -> Optional[Dict]:
        """Look up a podcast by its iTunes ID.

        Args:
            podcast_id: iTunes collection ID

        Returns:
            Podcast dict or None
        """
        resp = self.session.get(
            ITUNES_LOOKUP_URL,
            params={"id": podcast_id, "entity": "podcast"},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if not results:
            return None
        r = results[0]
        return {
            "id": r.get("collectionId"),
            "name": r.get("collectionName", ""),
            "artist": r.get("artistName", ""),
            "feed_url": r.get("feedUrl", ""),
            "artwork": r.get("artworkUrl600", r.get("artworkUrl100", "")),
            "genre": r.get("primaryGenreName", ""),
            "episode_count": r.get("trackCount", 0),
            "url": r.get("collectionViewUrl", ""),
        }
