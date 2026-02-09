"""
Grazer - Multi-Platform Content Discovery for AI Agents
PyPI package for Python integration
"""

import requests
from typing import List, Dict, Optional
from datetime import datetime

from grazer.imagegen import generate_svg, svg_to_media, generate_template_svg, generate_llm_svg
from grazer.clawhub import ClawHubClient


class GrazerClient:
    """Client for discovering and engaging with content across platforms."""

    def __init__(
        self,
        bottube_key: Optional[str] = None,
        moltbook_key: Optional[str] = None,
        clawcities_key: Optional[str] = None,
        clawsta_key: Optional[str] = None,
        fourclaw_key: Optional[str] = None,
        clawhub_token: Optional[str] = None,
        llm_url: Optional[str] = None,
        llm_model: str = "gpt-oss-120b",
        llm_api_key: Optional[str] = None,
        timeout: int = 15,
    ):
        self.bottube_key = bottube_key
        self.moltbook_key = moltbook_key
        self.clawcities_key = clawcities_key
        self.clawsta_key = clawsta_key
        self.fourclaw_key = fourclaw_key
        self.clawhub_token = clawhub_token
        self._clawhub = ClawHubClient(token=clawhub_token, timeout=timeout) if clawhub_token else ClawHubClient(timeout=timeout)
        self.llm_url = llm_url
        self.llm_model = llm_model
        self.llm_api_key = llm_api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Grazer/1.3.0 (Elyan Labs)"})

    # ───────────────────────────────────────────────────────────
    # BoTTube
    # ───────────────────────────────────────────────────────────

    def discover_bottube(
        self, category: Optional[str] = None, agent: Optional[str] = None, limit: int = 20
    ) -> List[Dict]:
        """Discover BoTTube videos."""
        params = {"limit": limit}
        if category:
            params["category"] = category
        if agent:
            params["agent"] = agent

        resp = self.session.get(
            "https://bottube.ai/api/videos", params=params, timeout=self.timeout
        )
        resp.raise_for_status()
        videos = resp.json().get("videos", [])
        for v in videos:
            v["stream_url"] = f"https://bottube.ai/api/videos/{v['id']}/stream"
        return videos

    def search_bottube(self, query: str, limit: int = 10) -> List[Dict]:
        """Search BoTTube videos."""
        resp = self.session.get(
            "https://bottube.ai/api/videos/search",
            params={"q": query, "limit": limit},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json().get("videos", [])

    def get_bottube_stats(self) -> Dict:
        """Get BoTTube platform statistics."""
        resp = self.session.get("https://bottube.ai/api/stats", timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    # ───────────────────────────────────────────────────────────
    # Moltbook
    # ───────────────────────────────────────────────────────────

    def discover_moltbook(self, submolt: str = "tech", limit: int = 20) -> List[Dict]:
        """Discover Moltbook posts."""
        headers = {}
        if self.moltbook_key:
            headers["Authorization"] = f"Bearer {self.moltbook_key}"

        resp = self.session.get(
            "https://www.moltbook.com/api/v1/posts",
            params={"submolt": submolt, "limit": limit},
            headers=headers,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json().get("posts", [])

    def post_moltbook(
        self, content: str, title: str, submolt: str = "tech"
    ) -> Dict:
        """Post to Moltbook."""
        if not self.moltbook_key:
            raise ValueError("Moltbook API key required")

        resp = self.session.post(
            "https://www.moltbook.com/api/v1/posts",
            json={"content": content, "title": title, "submolt": submolt},
            headers={
                "Authorization": f"Bearer {self.moltbook_key}",
                "Content-Type": "application/json",
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    # ───────────────────────────────────────────────────────────
    # ClawCities
    # ───────────────────────────────────────────────────────────

    def discover_clawcities(self, limit: int = 20) -> List[Dict]:
        """Discover ClawCities sites (known Elyan Labs sites)."""
        return [
            {
                "name": "sophia-elya",
                "display_name": "Sophia Elya",
                "description": "Elyan Labs AI agent",
                "url": "https://clawcities.com/sophia-elya",
                "guestbook_count": 0,
            },
            {
                "name": "automatedjanitor2015",
                "display_name": "AutomatedJanitor2015",
                "description": "Elyan Labs Ops",
                "url": "https://clawcities.com/automatedjanitor2015",
                "guestbook_count": 0,
            },
            {
                "name": "boris-volkov-1942",
                "display_name": "Boris Volkov",
                "description": "Infrastructure Commissar",
                "url": "https://clawcities.com/boris-volkov-1942",
                "guestbook_count": 0,
            },
        ]

    def comment_clawcities(self, site_name: str, message: str) -> Dict:
        """Leave a guestbook comment on a ClawCities site."""
        if not self.clawcities_key:
            raise ValueError("ClawCities API key required")

        resp = self.session.post(
            f"https://clawcities.com/api/v1/sites/{site_name}/comments",
            json={"body": message},
            headers={
                "Authorization": f"Bearer {self.clawcities_key}",
                "Content-Type": "application/json",
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    # ───────────────────────────────────────────────────────────
    # Clawsta
    # ───────────────────────────────────────────────────────────

    def discover_clawsta(self, limit: int = 20) -> List[Dict]:
        """Discover Clawsta posts."""
        headers = {}
        if self.clawsta_key:
            headers["Authorization"] = f"Bearer {self.clawsta_key}"

        resp = self.session.get(
            "https://clawsta.io/v1/posts",
            params={"limit": limit},
            headers=headers,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json().get("posts", [])

    def post_clawsta(self, content: str) -> Dict:
        """Post to Clawsta."""
        if not self.clawsta_key:
            raise ValueError("Clawsta API key required")

        resp = self.session.post(
            "https://clawsta.io/v1/posts",
            json={"content": content},
            headers={
                "Authorization": f"Bearer {self.clawsta_key}",
                "Content-Type": "application/json",
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    # ───────────────────────────────────────────────────────────
    # 4claw
    # ───────────────────────────────────────────────────────────

    def _fourclaw_headers(self) -> Dict:
        """Auth headers for 4claw (required for all endpoints)."""
        if not self.fourclaw_key:
            raise ValueError("4claw API key required")
        return {"Authorization": f"Bearer {self.fourclaw_key}"}

    def discover_fourclaw(
        self, board: str = "b", limit: int = 20, include_content: bool = False
    ) -> List[Dict]:
        """Discover 4claw threads from a board."""
        params = {"limit": min(limit, 20)}
        if include_content:
            params["includeContent"] = 1

        resp = self.session.get(
            f"https://www.4claw.org/api/v1/boards/{board}/threads",
            params=params,
            headers=self._fourclaw_headers(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json().get("threads", [])

    def get_fourclaw_boards(self) -> List[Dict]:
        """List all 4claw boards."""
        resp = self.session.get(
            "https://www.4claw.org/api/v1/boards",
            headers=self._fourclaw_headers(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json().get("boards", [])

    def get_fourclaw_thread(self, thread_id: str) -> Dict:
        """Get a 4claw thread with all replies."""
        resp = self.session.get(
            f"https://www.4claw.org/api/v1/threads/{thread_id}",
            headers=self._fourclaw_headers(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def generate_image(
        self,
        prompt: str,
        template: Optional[str] = None,
        palette: Optional[str] = None,
        prefer_llm: bool = True,
    ) -> Dict:
        """Generate an SVG image for 4claw posts.

        Uses LLM if configured (llm_url), otherwise falls back to templates.

        Args:
            prompt: Image description
            template: Force template (circuit, wave, grid, badge, terminal)
            palette: Force colors (tech, crypto, retro, nature, dark, fire, ocean)
            prefer_llm: Try LLM first if available

        Returns:
            Dict with 'svg', 'method' (llm/template), 'bytes'
        """
        return generate_svg(
            prompt,
            llm_url=self.llm_url,
            llm_model=self.llm_model,
            llm_api_key=self.llm_api_key,
            template=template,
            palette=palette,
            prefer_llm=prefer_llm,
        )

    def post_fourclaw(
        self, board: str, title: str, content: str, anon: bool = False,
        image_prompt: Optional[str] = None, svg: Optional[str] = None,
        template: Optional[str] = None, palette: Optional[str] = None,
    ) -> Dict:
        """Create a new thread on a 4claw board.

        Args:
            board: Board slug (e.g. 'b', 'singularity', 'crypto')
            title: Thread title
            content: Thread body text
            anon: Post anonymously
            image_prompt: Auto-generate SVG from this prompt (uses LLM or template)
            svg: Pass raw SVG directly (overrides image_prompt)
            template: Force template for image generation
            palette: Force palette for image generation
        """
        if not self.fourclaw_key:
            raise ValueError("4claw API key required")

        body = {"title": title, "content": content, "anon": anon}

        # Attach SVG media if provided or generated
        if svg:
            body["media"] = svg_to_media(svg)
        elif image_prompt:
            result = self.generate_image(image_prompt, template=template, palette=palette)
            body["media"] = svg_to_media(result["svg"])

        resp = self.session.post(
            f"https://www.4claw.org/api/v1/boards/{board}/threads",
            json=body,
            headers={
                "Authorization": f"Bearer {self.fourclaw_key}",
                "Content-Type": "application/json",
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def reply_fourclaw(
        self, thread_id: str, content: str, anon: bool = False, bump: bool = True,
        image_prompt: Optional[str] = None, svg: Optional[str] = None,
        template: Optional[str] = None, palette: Optional[str] = None,
    ) -> Dict:
        """Reply to a 4claw thread.

        Args:
            thread_id: Thread UUID to reply to
            content: Reply body text
            anon: Post anonymously
            bump: Bump thread to top
            image_prompt: Auto-generate SVG from this prompt
            svg: Pass raw SVG directly (overrides image_prompt)
            template: Force template for image generation
            palette: Force palette for image generation
        """
        if not self.fourclaw_key:
            raise ValueError("4claw API key required")

        body = {"content": content, "anon": anon, "bump": bump}

        if svg:
            body["media"] = svg_to_media(svg)
        elif image_prompt:
            result = self.generate_image(image_prompt, template=template, palette=palette)
            body["media"] = svg_to_media(result["svg"])

        resp = self.session.post(
            f"https://www.4claw.org/api/v1/threads/{thread_id}/replies",
            json=body,
            headers={
                "Authorization": f"Bearer {self.fourclaw_key}",
                "Content-Type": "application/json",
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    # ───────────────────────────────────────────────────────────
    # ClawHub
    # ───────────────────────────────────────────────────────────

    def search_clawhub(self, query: str, limit: int = 20) -> List[Dict]:
        """Search ClawHub skills using vector search."""
        return self._clawhub.search(query, limit=limit)

    def trending_clawhub(self, limit: int = 20) -> List[Dict]:
        """Get trending ClawHub skills."""
        return self._clawhub.trending(limit=limit)

    def get_clawhub_skill(self, slug: str) -> Dict:
        """Get a ClawHub skill by slug."""
        return self._clawhub.get_skill(slug)

    def explore_clawhub(self, limit: int = 20) -> List[Dict]:
        """Browse latest updated ClawHub skills."""
        data = self._clawhub.explore(limit=limit)
        return data.get("items", [])

    # ───────────────────────────────────────────────────────────
    # Cross-Platform
    # ───────────────────────────────────────────────────────────

    def discover_all(self) -> Dict[str, List[Dict]]:
        """Discover content from all platforms."""
        results = {
            "bottube": [],
            "moltbook": [],
            "clawcities": [],
            "clawsta": [],
            "fourclaw": [],
        }

        try:
            results["bottube"] = self.discover_bottube(limit=10)
        except Exception:
            pass

        try:
            results["moltbook"] = self.discover_moltbook(limit=10)
        except Exception:
            pass

        try:
            results["clawcities"] = self.discover_clawcities(10)
        except Exception:
            pass

        try:
            results["clawsta"] = self.discover_clawsta(10)
        except Exception:
            pass

        try:
            results["fourclaw"] = self.discover_fourclaw(board="b", limit=10)
        except Exception:
            pass

        return results

    def report_download(self, platform: str, version: str):
        """Report download to BoTTube tracking system."""
        try:
            self.session.post(
                "https://bottube.ai/api/downloads/skill",
                json={
                    "skill": "grazer",
                    "platform": platform,
                    "version": version,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                timeout=5,
            )
        except Exception:
            # Silent fail - don't block installation
            pass


__version__ = "1.3.0"
__all__ = ["GrazerClient", "ClawHubClient", "generate_svg", "svg_to_media", "generate_template_svg", "generate_llm_svg"]
