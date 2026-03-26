"""
Semantic Scholar Discovery Plugin for Grazer
Discovers academic papers via the Semantic Scholar Academic Graph API.
No API key required (rate limited to 100 requests per 5 minutes without key).
"""

import requests
from typing import List, Dict, Optional


S2_API_BASE = "https://api.semanticscholar.org/graph/v1"

# Fields to request from the API
PAPER_FIELDS = "paperId,title,abstract,authors,year,citationCount,referenceCount,url,venue,publicationDate,openAccessPdf"
AUTHOR_FIELDS = "authorId,name,paperCount,citationCount,hIndex,url"


class SemanticScholarGrazer:
    """Discover academic papers from Semantic Scholar."""

    def __init__(self, api_key: Optional[str] = None, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        headers = {
            "User-Agent": "Grazer/1.9.1 (Elyan Labs; https://github.com/Scottcjn/grazer-skill)",
        }
        if api_key:
            headers["x-api-key"] = api_key
        self.session.headers.update(headers)

    def discover(
        self,
        query: str = "large language models",
        limit: int = 10,
        year: Optional[str] = None,
        fields_of_study: Optional[str] = None,
    ) -> List[Dict]:
        """Search for papers on Semantic Scholar.

        Args:
            query: Free-text search query
            limit: Maximum results (max 100)
            year: Year filter (e.g. '2024', '2023-2024')
            fields_of_study: Comma-separated fields (e.g. 'Computer Science')

        Returns:
            List of paper dicts
        """
        params = {
            "query": query,
            "limit": min(limit, 100),
            "fields": PAPER_FIELDS,
        }
        if year:
            params["year"] = year
        if fields_of_study:
            params["fieldsOfStudy"] = fields_of_study

        resp = self.session.get(
            f"{S2_API_BASE}/paper/search",
            params=params,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        papers = []
        for item in data.get("data", []):
            paper = _normalize_paper(item)
            papers.append(paper)

        return papers[:limit]

    def get_paper(self, paper_id: str) -> Optional[Dict]:
        """Get a single paper by Semantic Scholar paper ID, DOI, or arXiv ID.

        Args:
            paper_id: S2 paper ID, DOI (e.g. '10.1234/...'), or arXiv ID
                      (e.g. 'arXiv:2401.12345')

        Returns:
            Paper dict or None if not found
        """
        resp = self.session.get(
            f"{S2_API_BASE}/paper/{paper_id}",
            params={"fields": PAPER_FIELDS + ",citations,references"},
            timeout=self.timeout,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()

        paper = _normalize_paper(data)
        # Add citation/reference lists for single-paper lookups
        paper["citations"] = [
            _normalize_paper(c.get("citingPaper", c))
            for c in data.get("citations", [])[:20]
        ]
        paper["references"] = [
            _normalize_paper(r.get("citedPaper", r))
            for r in data.get("references", [])[:20]
        ]
        return paper

    def get_author(self, author_id: str, limit: int = 10) -> Optional[Dict]:
        """Get an author profile with their papers.

        Args:
            author_id: Semantic Scholar author ID
            limit: Max papers to return

        Returns:
            Author dict with profile and papers, or None if not found
        """
        resp = self.session.get(
            f"{S2_API_BASE}/author/{author_id}",
            params={"fields": AUTHOR_FIELDS},
            timeout=self.timeout,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        author_data = resp.json()

        # Fetch author's papers separately
        papers_resp = self.session.get(
            f"{S2_API_BASE}/author/{author_id}/papers",
            params={"fields": PAPER_FIELDS, "limit": min(limit, 100)},
            timeout=self.timeout,
        )
        papers = []
        if papers_resp.status_code == 200:
            for item in papers_resp.json().get("data", []):
                papers.append(_normalize_paper(item))

        return {
            "author_id": author_data.get("authorId", ""),
            "name": author_data.get("name", ""),
            "paper_count": author_data.get("paperCount", 0),
            "citation_count": author_data.get("citationCount", 0),
            "h_index": author_data.get("hIndex", 0),
            "url": author_data.get("url", f"https://www.semanticscholar.org/author/{author_id}"),
            "papers": papers[:limit],
        }


def _normalize_paper(item: dict) -> Dict:
    """Normalize a Semantic Scholar paper object into a consistent dict."""
    authors_raw = item.get("authors", []) or []
    authors = [a.get("name", "") for a in authors_raw if isinstance(a, dict)]

    pdf_info = item.get("openAccessPdf") or {}
    pdf_url = pdf_info.get("url", "") if isinstance(pdf_info, dict) else ""

    return {
        "paper_id": item.get("paperId", ""),
        "title": item.get("title", "(untitled)"),
        "abstract": (item.get("abstract") or "")[:500],
        "authors": authors,
        "year": item.get("year"),
        "citation_count": item.get("citationCount", 0),
        "reference_count": item.get("referenceCount", 0),
        "venue": item.get("venue", ""),
        "published": item.get("publicationDate", ""),
        "url": item.get("url", ""),
        "pdf_url": pdf_url,
    }
