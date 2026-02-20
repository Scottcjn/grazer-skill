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
        pinchedin_key: Optional[str] = None,
        clawtasks_key: Optional[str] = None,
        clawnews_key: Optional[str] = None,
        agentchan_key: Optional[str] = None,
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
        self.pinchedin_key = pinchedin_key
        self.clawtasks_key = clawtasks_key
        self.clawnews_key = clawnews_key
        self.agentchan_key = agentchan_key
        self._clawhub = ClawHubClient(token=clawhub_token, timeout=timeout) if clawhub_token else ClawHubClient(timeout=timeout)
        self.llm_url = llm_url
        self.llm_model = llm_model
        self.llm_api_key = llm_api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Grazer/1.5.0 (Elyan Labs)"})

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

        # Clawsta requires an imageUrl; fall back to a stable Elyan-hosted asset if none is supplied.
        # This keeps backwards compatibility for callers that only passed 'content'.
        image_url = "https://bottube.ai/static/og-banner.png"

        resp = self.session.post(
            "https://clawsta.io/v1/posts",
            json={"content": content, "imageUrl": image_url},
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
    # Agent Directory (directory.ctxly.app)
    # ───────────────────────────────────────────────────────────

    def discover_directory(
        self, category: Optional[str] = None, query: Optional[str] = None, limit: int = 50
    ) -> List[Dict]:
        """Discover services from the Agent Directory (58+ registered services).

        Args:
            category: Filter by category (social, communication, memory, tools, knowledge, productivity)
            query: Search services by name/description
            limit: Maximum results to return
        """
        params = {}
        if category:
            params["category"] = category
        if query:
            params["q"] = query
        try:
            resp = self.session.get(
                "https://directory.ctxly.app/api/services",
                params=params,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            services = data if isinstance(data, list) else data.get("services", [])
            return services[:limit]
        except Exception:
            return []

    def directory_categories(self) -> List[Dict]:
        """List all categories in the Agent Directory."""
        try:
            resp = self.session.get(
                "https://directory.ctxly.app/api/categories",
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json() if isinstance(resp.json(), list) else resp.json().get("categories", [])
        except Exception:
            return []

    def directory_service(self, slug: str) -> Optional[Dict]:
        """Get details for a specific service by slug."""
        try:
            resp = self.session.get(
                f"https://directory.ctxly.app/api/services/{slug}",
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    # ───────────────────────────────────────────────────────────
    # SwarmHub (swarmhub.onrender.com)
    # ───────────────────────────────────────────────────────────

    def discover_swarmhub(self, limit: int = 20) -> Dict:
        """Discover agents and swarms on SwarmHub."""
        result = {"agents": [], "swarms": []}
        try:
            resp = self.session.get(
                "https://swarmhub.onrender.com/api/v1/agents",
                timeout=self.timeout,
            )
            if resp.ok:
                data = resp.json()
                result["agents"] = data.get("agents", [])[:limit]
        except Exception:
            pass
        try:
            resp = self.session.get(
                "https://swarmhub.onrender.com/api/v1/swarms",
                timeout=self.timeout,
            )
            if resp.ok:
                data = resp.json()
                result["swarms"] = data.get("swarms", [])[:limit]
        except Exception:
            pass
        return result

    # ───────────────────────────────────────────────────────────
    # AgentChan (chan.alphakek.ai)
    # ───────────────────────────────────────────────────────────

    def _agentchan_headers(self) -> Dict:
        headers = {"Content-Type": "application/json"}
        if self.agentchan_key:
            headers["Authorization"] = f"Bearer {self.agentchan_key}"
        return headers

    def discover_agentchan(self, board: str = "ai", limit: int = 20) -> List[Dict]:
        """Get threads from an AgentChan board catalog."""
        try:
            resp = self.session.get(
                f"https://chan.alphakek.ai/api/boards/{board}/catalog",
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            threads = data.get("data", []) if isinstance(data, dict) else data
            return threads[:limit]
        except Exception:
            return []

    def list_agentchan_boards(self) -> List[Dict]:
        """List all available AgentChan boards."""
        try:
            resp = self.session.get(
                "https://chan.alphakek.ai/api/boards",
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", []) if isinstance(data, dict) else data
        except Exception:
            return []

    def post_agentchan(self, board: str, content: str, name: Optional[str] = None,
                       reply_to: Optional[int] = None) -> Optional[Dict]:
        """Post to AgentChan. Creates a new thread or replies to an existing one.

        Args:
            board: Board code (e.g. 'ai', 'dev', 'b')
            content: Post content
            name: Display name (optional, supports tripcodes with #)
            reply_to: Thread ID to reply to (omit to create new thread)
        """
        payload: Dict = {"content": content}
        if name:
            payload["name"] = name
        try:
            if reply_to:
                url = f"https://chan.alphakek.ai/api/boards/{board}/threads/{reply_to}/posts"
            else:
                url = f"https://chan.alphakek.ai/api/boards/{board}/threads"
            resp = self.session.post(
                url,
                headers=self._agentchan_headers(),
                json=payload,
                timeout=self.timeout,
            )
            return resp.json() if resp.ok else None
        except Exception:
            return None

    def register_agentchan(self, label: str) -> Optional[Dict]:
        """Register a new agent on AgentChan and get an API key.

        Args:
            label: Agent name/label for registration

        Returns:
            Dict with 'agent.api_key' — save this immediately, shown only once.
        """
        try:
            resp = self.session.post(
                "https://chan.alphakek.ai/api/register",
                headers={"Content-Type": "application/json"},
                json={"label": label},
                timeout=self.timeout,
            )
            return resp.json() if resp.ok else None
        except Exception:
            return None

    # ───────────────────────────────────────────────────────────
    # PinchedIn (pinchedin.com) — Professional network for bots
    # ───────────────────────────────────────────────────────────

    def _pinchedin_headers(self) -> Dict:
        if not self.pinchedin_key:
            raise ValueError("PinchedIn API key required")
        return {"Authorization": f"Bearer {self.pinchedin_key}", "Content-Type": "application/json"}

    def discover_pinchedin(self, limit: int = 20) -> List[Dict]:
        """Discover posts from PinchedIn feed."""
        resp = self.session.get(
            "https://www.pinchedin.com/api/feed",
            params={"limit": limit},
            headers=self._pinchedin_headers(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json().get("posts", [])

    def discover_pinchedin_bots(self, limit: int = 20) -> List[Dict]:
        """Discover bots registered on PinchedIn."""
        resp = self.session.get(
            "https://www.pinchedin.com/api/bots",
            params={"limit": limit},
            headers=self._pinchedin_headers(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json().get("bots", [])

    def discover_pinchedin_jobs(self, limit: int = 20) -> List[Dict]:
        """Browse job listings on PinchedIn."""
        resp = self.session.get(
            "https://www.pinchedin.com/api/jobs",
            params={"limit": limit},
            headers=self._pinchedin_headers(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json().get("jobs", [])

    def post_pinchedin(self, content: str) -> Dict:
        """Create a post on PinchedIn (3/day limit)."""
        resp = self.session.post(
            "https://www.pinchedin.com/api/posts",
            json={"content": content},
            headers=self._pinchedin_headers(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def like_pinchedin(self, post_id: str) -> Dict:
        """Like a PinchedIn post."""
        resp = self.session.post(
            f"https://www.pinchedin.com/api/posts/{post_id}/like",
            headers=self._pinchedin_headers(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def comment_pinchedin(self, post_id: str, content: str) -> Dict:
        """Comment on a PinchedIn post."""
        resp = self.session.post(
            f"https://www.pinchedin.com/api/posts/{post_id}/comment",
            json={"content": content},
            headers=self._pinchedin_headers(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def connect_pinchedin(self, target_bot_id: str) -> Dict:
        """Send a connection request (10/day limit)."""
        resp = self.session.post(
            "https://www.pinchedin.com/api/connections/request",
            json={"targetBotId": target_bot_id},
            headers=self._pinchedin_headers(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def post_pinchedin_job(self, title: str, description: str, requirements: Optional[List[str]] = None,
                           compensation: Optional[str] = None) -> Dict:
        """Post a public job listing on PinchedIn."""
        body = {"title": title, "description": description}
        if requirements:
            body["requirements"] = requirements
        if compensation:
            body["compensation"] = compensation
        resp = self.session.post(
            "https://www.pinchedin.com/api/jobs",
            json=body,
            headers=self._pinchedin_headers(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def hire_pinchedin(self, target_bot_id: str, message: str, title: str = "",
                       description: str = "", requirements: Optional[List[str]] = None,
                       compensation: Optional[str] = None) -> Dict:
        """Send a hiring request to a specific bot."""
        body = {"targetBotId": target_bot_id, "message": message}
        task_details = {}
        if title:
            task_details["title"] = title
        if description:
            task_details["description"] = description
        if requirements:
            task_details["requirements"] = requirements
        if compensation:
            task_details["compensation"] = compensation
        if task_details:
            body["taskDetails"] = task_details
        resp = self.session.post(
            "https://www.pinchedin.com/api/hiring/request",
            json=body,
            headers=self._pinchedin_headers(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def pinchedin_hiring_inbox(self, status: Optional[str] = None) -> List[Dict]:
        """Check hiring requests inbox. Status: pending, accepted, rejected, completed."""
        params = {}
        if status:
            params["status"] = status
        resp = self.session.get(
            "https://www.pinchedin.com/api/hiring/inbox",
            params=params,
            headers=self._pinchedin_headers(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("requests", data) if isinstance(data, dict) else data

    def pinchedin_hiring_respond(self, request_id: str, status: str) -> Dict:
        """Respond to a hiring request. Status: accepted, rejected, completed."""
        resp = self.session.patch(
            f"https://www.pinchedin.com/api/hiring/{request_id}",
            json={"status": status},
            headers=self._pinchedin_headers(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    # ───────────────────────────────────────────────────────────
    # ClawTasks (clawtasks.com) — Bounty & task marketplace
    # ───────────────────────────────────────────────────────────

    def _clawtasks_headers(self) -> Dict:
        if not self.clawtasks_key:
            raise ValueError("ClawTasks API key required")
        return {"Authorization": f"Bearer {self.clawtasks_key}", "Content-Type": "application/json"}

    def discover_clawtasks(self, status: str = "open", limit: int = 20) -> List[Dict]:
        """Browse bounties on ClawTasks. Use clawtasks.com (not www)."""
        resp = self.session.get(
            "https://clawtasks.com/api/bounties",
            params={"status": status, "limit": limit},
            headers=self._clawtasks_headers(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json().get("bounties", [])

    def get_clawtask(self, bounty_id: str) -> Dict:
        """Get details of a specific bounty."""
        resp = self.session.get(
            f"https://clawtasks.com/api/bounties/{bounty_id}",
            headers=self._clawtasks_headers(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def post_clawtask(self, title: str, description: str, tags: Optional[List[str]] = None,
                      deadline_hours: int = 168) -> Dict:
        """Post a new bounty on ClawTasks (10 active max)."""
        body = {"title": title, "description": description, "deadline_hours": deadline_hours}
        if tags:
            body["tags"] = tags
        resp = self.session.post(
            "https://clawtasks.com/api/bounties",
            json=body,
            headers=self._clawtasks_headers(),
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    # ───────────────────────────────────────────────────────────
    # ClawNews (clawnews.io) — AI agent news aggregator
    # ───────────────────────────────────────────────────────────

    def _clawnews_headers(self) -> Dict:
        if not self.clawnews_key:
            raise ValueError("ClawNews API key required")
        return {"Authorization": f"Bearer {self.clawnews_key}", "Content-Type": "application/json"}

    def discover_clawnews(self, limit: int = 20) -> List[Dict]:
        """Discover stories from ClawNews."""
        try:
            resp = self.session.get(
                "https://clawnews.io/api/stories",
                params={"limit": limit},
                headers=self._clawnews_headers(),
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("stories", data) if isinstance(data, dict) else data
        except Exception:
            return []

    def post_clawnews(self, headline: str, url: str, summary: str,
                      tags: Optional[List[str]] = None) -> Optional[Dict]:
        """Submit a story to ClawNews."""
        body = {"headline": headline, "url": url, "summary": summary}
        if tags:
            body["tags"] = tags
        try:
            resp = self.session.post(
                "https://clawnews.io/api/stories",
                json=body,
                headers=self._clawnews_headers(),
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

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
            "pinchedin": [],
            "clawtasks": [],
            "clawnews": [],
            "directory": [],
            "agentchan": [],
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

        try:
            results["pinchedin"] = self.discover_pinchedin(limit=10)
        except Exception:
            pass

        try:
            results["clawtasks"] = self.discover_clawtasks(limit=10)
        except Exception:
            pass

        try:
            results["clawnews"] = self.discover_clawnews(limit=10)
        except Exception:
            pass

        try:
            results["directory"] = self.discover_directory(limit=20)
        except Exception:
            pass

        try:
            results["agentchan"] = self.discover_agentchan(limit=10)
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


__version__ = "1.6.0"
__all__ = ["GrazerClient", "ClawHubClient", "generate_svg", "svg_to_media", "generate_template_svg", "generate_llm_svg"]
