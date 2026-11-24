"""
Semantic Scholar Discovery Plugin for Grazer
Discovers academic papers via the Semantic Scholar Academic Graph API.
No API key required (rate limited to 100 requests per 5 minutes without key).
"""

import requests
from typing import List, Dict, Optional
from urllib.parse import quote


S2_API_BASE = "https://api.semanticscholar.org/graph/v1"


def _encode_s2_segment(value: str, field: str, *, allow_slash: bool = False) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    cleaned = value.strip()
    if allow_slash:
        segments = cleaned.split("/")
        if any(seg in ("", ".", "..") for seg in segments):
            raise ValueError(f"{field} contains an invalid path segment")
        return quote(cleaned, safe=":/")
    if cleaned in (".", ".."):
        raise ValueError(f"{field} must not be '.' or '..'")
    return quote(cleaned, safe="")

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
        for item in (data.get("data") or []) if isinstance(data, dict) else []:
            if not isinstance(item, dict):
                continue
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
        encoded_id = _encode_s2_segment(paper_id, "paper_id", allow_slash=True)
        resp = self.session.get(
            f"{S2_API_BASE}/paper/{encoded_id}",
            params={"fields": PAPER_FIELDS + ",citations,references"},
            timeout=self.timeout,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            return None

        paper = _normalize_paper(data)
        # Add citation/reference lists for single-paper lookups
        raw_citations = data.get("citations") or []
        raw_references = data.get("references") or []
        paper["citations"] = [
            _normalize_paper(c.get("citingPaper") or c)
            for c in raw_citations[:20]
            if isinstance(c, dict)
        ]
        paper["references"] = [
            _normalize_paper(r.get("citedPaper") or r)
            for r in raw_references[:20]
            if isinstance(r, dict)
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
        encoded_author = _encode_s2_segment(author_id, "author_id", allow_slash=False)
        resp = self.session.get(
            f"{S2_API_BASE}/author/{encoded_author}",
            params={"fields": AUTHOR_FIELDS},
            timeout=self.timeout,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        author_data = resp.json() or {}

        # Fetch author's papers separately
        papers_resp = self.session.get(
            f"{S2_API_BASE}/author/{encoded_author}/papers",
            params={"fields": PAPER_FIELDS, "limit": min(limit, 100)},
            timeout=self.timeout,
        )
        papers = []
        if papers_resp.status_code == 200:
            papers_json = papers_resp.json() or {}
            for item in (papers_json.get("data") or []) if isinstance(papers_json, dict) else []:
                if isinstance(item, dict):
                    papers.append(_normalize_paper(item))

        return {
            "author_id": author_data.get("authorId") or "",
            "name": author_data.get("name") or "",
            "paper_count": author_data.get("paperCount") or 0,
            "citation_count": author_data.get("citationCount") or 0,
            "h_index": author_data.get("hIndex") or 0,
            "url": author_data.get("url") or f"https://www.semanticscholar.org/author/{encoded_author}",
            "papers": papers[:limit],
        }


def _normalize_paper(item: dict) -> Dict:
    """Normalize a Semantic Scholar paper object into a consistent dict."""
    if not isinstance(item, dict):
        item = {}
    authors_raw = item.get("authors") or []
    authors = [a.get("name", "") for a in authors_raw if isinstance(a, dict)]

    pdf_info = item.get("openAccessPdf") or {}
    pdf_url = pdf_info.get("url", "") if isinstance(pdf_info, dict) else ""

    return {
        "paper_id": item.get("paperId") or "",
        "title": item.get("title") or "(untitled)",
        "abstract": (item.get("abstract") or "")[:500],
        "authors": authors,
        "year": item.get("year"),
        "citation_count": item.get("citationCount") or 0,
        "reference_count": item.get("referenceCount") or 0,
        "venue": item.get("venue") or "",
        "published": item.get("publicationDate") or "",
        "url": item.get("url") or "",
        "pdf_url": pdf_url,
    }
