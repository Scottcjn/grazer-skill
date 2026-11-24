"""
ArXiv Discovery Plugin for Grazer
Discovers trending and recent papers from arXiv using the public Atom API.
No API key required.
"""

import html
import re
import requests
from typing import List, Dict, Optional


ARXIV_API_BASE = "https://export.arxiv.org/api/query"

# Popular CS categories for AI agent discovery
CATEGORIES = {
    "ai": "cs.AI",
    "ml": "cs.LG",
    "cv": "cs.CV",
    "nlp": "cs.CL",
    "robotics": "cs.RO",
    "crypto": "cs.CR",
    "distributed": "cs.DC",
    "systems": "cs.SY",
    "hci": "cs.HC",
    "ir": "cs.IR",
}


def _parse_atom_entries(xml_text: str) -> List[Dict]:
    """Parse arXiv Atom XML into a list of paper dicts.

    Uses regex-based parsing to avoid requiring lxml/feedparser as a
    dependency.  The arXiv Atom feed is well-structured enough for this.
    """
    entries = []
    # Split on <entry> tags
    raw_entries = re.findall(r"<entry[^>]*>(.*?)</entry>", xml_text, re.DOTALL)
    for raw in raw_entries:
        paper: Dict = {}

        # Extract fields via regex and unescape XML entities
        id_match = re.search(r"<id[^>]*>(.*?)</id>", raw)
        if id_match:
            paper["id"] = html.unescape(id_match.group(1).strip())
            # Convert full URL to short arxiv ID
            paper["arxiv_id"] = paper["id"].rsplit("/abs/", 1)[-1]

        title_match = re.search(r"<title[^>]*>(.*?)</title>", raw, re.DOTALL)
        if title_match:
            paper["title"] = html.unescape(" ".join(title_match.group(1).split()))

        summary_match = re.search(r"<summary[^>]*>(.*?)</summary>", raw, re.DOTALL)
        if summary_match:
            paper["summary"] = html.unescape(" ".join(summary_match.group(1).split()))

        published_match = re.search(r"<published[^>]*>(.*?)</published>", raw)
        if published_match:
            paper["published"] = published_match.group(1).strip()

        updated_match = re.search(r"<updated[^>]*>(.*?)</updated>", raw)
        if updated_match:
            paper["updated"] = updated_match.group(1).strip()

        # Authors
        authors = [
            html.unescape(" ".join(a.split()))
            for a in re.findall(r"<author[^>]*>\s*<name[^>]*>(.*?)</name>", raw, re.DOTALL)
        ]
        paper["authors"] = authors

        # PDF link (handle arbitrary attribute ordering between title/type and href)
        pdf_url = None
        for link_tag in re.findall(r"<link\b[^>]*>", raw):
            is_pdf = (
                re.search(r'''\btitle=["']pdf["']''', link_tag) is not None
                or re.search(r'''\btype=["']application/pdf["']''', link_tag) is not None
            )
            if is_pdf:
                href_match = re.search(r'''\bhref=["']([^"']+)["']''', link_tag)
                if href_match:
                    pdf_url = html.unescape(href_match.group(1))
                    break
        if pdf_url:
            paper["pdf_url"] = pdf_url
        else:
            # Construct from ID
            paper["pdf_url"] = f"https://arxiv.org/pdf/{paper.get('arxiv_id', '')}"

        paper["url"] = f"https://arxiv.org/abs/{paper.get('arxiv_id', '')}"

        # Categories
        cats = re.findall(r'''<category[^>]+term=["']([^"']+)["']''', raw)
        paper["categories"] = cats

        entries.append(paper)

    return entries


class ArxivGrazer:
    """Discover papers from arXiv's public Atom API."""

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Grazer/1.9.1 (Elyan Labs; https://github.com/Scottcjn/grazer-skill)"}
        )

    def discover(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 10,
        sort_by: str = "submittedDate",
        sort_order: str = "descending",
    ) -> List[Dict]:
        """Discover recent arXiv papers.

        Args:
            query: Free-text search query (e.g. "large language models")
            category: Category shorthand (ai, ml, cv, nlp, crypto, etc.) or
                      full arXiv category (cs.AI, cs.LG, etc.)
            limit: Maximum number of results
            sort_by: Sort field (submittedDate, relevance, lastUpdatedDate)
            sort_order: ascending or descending

        Returns:
            List of paper dicts with id, title, authors, summary, url, pdf_url
        """
        parts = []
        if query:
            parts.append(f"all:{query}")
        if category:
            cat = CATEGORIES.get(category.lower(), category)
            parts.append(f"cat:{cat}")

        # Default: recent AI papers if nothing specified
        if not parts:
            parts.append("cat:cs.AI")

        search_query = " AND ".join(parts)

        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": min(limit, 100),
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }

        resp = self.session.get(ARXIV_API_BASE, params=params, timeout=self.timeout)
        resp.raise_for_status()

        papers = _parse_atom_entries(resp.text)
        return papers[:limit]

    def get_paper(self, arxiv_id: str) -> Optional[Dict]:
        """Get a single paper by arXiv ID (e.g. '2401.12345')."""
        params = {"id_list": arxiv_id, "max_results": 1}
        resp = self.session.get(ARXIV_API_BASE, params=params, timeout=self.timeout)
        resp.raise_for_status()
        papers = _parse_atom_entries(resp.text)
        return papers[0] if papers else None

    @staticmethod
    def available_categories() -> Dict[str, str]:
        """Return the shorthand-to-arXiv category mapping."""
        return dict(CATEGORIES)
