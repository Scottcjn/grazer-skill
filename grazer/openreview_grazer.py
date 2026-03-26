"""
OpenReview Discovery Plugin for Grazer
Discovers conference papers and submissions via the OpenReview API v2.
No API key required for public venues.
"""

import requests
from typing import List, Dict, Optional


OPENREVIEW_API_BASE = "https://api2.openreview.net"


class OpenReviewGrazer:
    """Discover papers from OpenReview conference venues."""

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Grazer/1.9.1 (Elyan Labs; https://github.com/Scottcjn/grazer-skill)"}
        )

    def discover(
        self,
        query: str = "large language models",
        venue: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict]:
        """Search OpenReview notes/papers.

        Args:
            query: Free-text search query
            venue: Venue group ID (e.g. 'ICLR.cc/2025/Conference')
            limit: Maximum results (max 1000)

        Returns:
            List of paper dicts
        """
        params = {
            "query": query,
            "limit": min(limit, 1000),
        }
        if venue:
            params["content.venue"] = venue

        resp = self.session.get(
            f"{OPENREVIEW_API_BASE}/notes/search",
            params=params,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        papers = []
        for item in data.get("notes", []):
            paper = _normalize_note(item)
            papers.append(paper)

        return papers[:limit]

    def venue_submissions(
        self,
        venue_id: str,
        limit: int = 10,
    ) -> List[Dict]:
        """Get submissions for a specific venue.

        Args:
            venue_id: OpenReview venue group ID
                      (e.g. 'ICLR.cc/2025/Conference', 'NeurIPS.cc/2024/Conference')
            limit: Maximum results

        Returns:
            List of paper dicts from the venue
        """
        params = {
            "content.venue": venue_id,
            "limit": min(limit, 1000),
        }

        resp = self.session.get(
            f"{OPENREVIEW_API_BASE}/notes",
            params=params,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        papers = []
        for item in data.get("notes", []):
            paper = _normalize_note(item)
            papers.append(paper)

        return papers[:limit]


def _normalize_note(item: dict) -> Dict:
    """Normalize an OpenReview note into a consistent paper dict."""
    content = item.get("content", {})

    # Authors can be in content.authors or content.authors.value (API v2 format)
    authors_raw = content.get("authors", {})
    if isinstance(authors_raw, dict):
        authors = authors_raw.get("value", [])
    elif isinstance(authors_raw, list):
        authors = authors_raw
    else:
        authors = []

    # Title can be string or {"value": "..."}
    title_raw = content.get("title", "(untitled)")
    title = title_raw.get("value", title_raw) if isinstance(title_raw, dict) else title_raw

    # Abstract
    abstract_raw = content.get("abstract", "")
    abstract = abstract_raw.get("value", abstract_raw) if isinstance(abstract_raw, dict) else abstract_raw

    # Venue
    venue_raw = content.get("venue", "")
    venue = venue_raw.get("value", venue_raw) if isinstance(venue_raw, dict) else venue_raw

    note_id = item.get("id", "")
    forum = item.get("forum", note_id)

    return {
        "id": note_id,
        "title": title,
        "abstract": (abstract or "")[:500],
        "authors": authors if isinstance(authors, list) else [],
        "venue": venue,
        "url": f"https://openreview.net/forum?id={forum}" if forum else "",
        "pdf_url": f"https://openreview.net/pdf?id={forum}" if forum else "",
        "created": item.get("cdate", ""),
        "modified": item.get("mdate", ""),
    }
