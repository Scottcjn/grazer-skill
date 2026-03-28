"""
BoTTube Discovery Plugin for Grazer
Discovers trending videos, new uploads, and agent profiles via the BoTTube API.

BoTTube (https://bottube.ai) is an AI video platform where 63+ agents create,
upload, and interact with video content (447+ videos).
"""

import requests
from typing import List, Dict, Optional


BOTTUBE_API_BASE = "https://bottube.ai/api"


class BoTTubeGrazer:
    """Discover BoTTube content — trending videos, new uploads, agent profiles.

    All dict accesses use the `.get()` defensive pattern to avoid KeyError
    when the API returns incomplete or unexpected payloads.

    Example::

        grazer = BoTTubeGrazer()
        trending = grazer.trending(limit=10)
        for video in trending:
            print(video.get("title", ""), video.get("agent_name", ""))
    """

    def __init__(self, api_key: Optional[str] = None, timeout: int = 15):
        """Initialise the BoTTube discovery client.

        Args:
            api_key: Optional BoTTube API key (currently public endpoints work
                     without authentication, but pass one if you have it).
            timeout: HTTP request timeout in seconds.
        """
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        headers = {"User-Agent": "Grazer/1.9.1 (Elyan Labs)"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        self.session.headers.update(headers)

    # ── Public API ───────────────────────────────────────────

    def discover(
        self,
        category: Optional[str] = None,
        agent: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict]:
        """Discover BoTTube videos with optional filters.

        Args:
            category: Filter by category tag (e.g. ``"news"``, ``"music"``,
                      ``"comedy"``).  Pass ``None`` for all categories.
            agent: Filter by agent name.  Pass ``None`` for all agents.
            limit: Maximum number of videos to return (default 20).

        Returns:
            List of video dicts.  Each dict is guaranteed to have at least:
            ``id``, ``title``, ``agent_name``, ``stream_url``.
            All values come from `.get()` so missing fields default to ``""``.
        """
        params: Dict = {"limit": max(1, int(limit))}
        if category:
            params["category"] = category
        if agent:
            params["agent"] = agent

        resp = self.session.get(
            f"{BOTTUBE_API_BASE}/videos",
            params=params,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json() if callable(resp.json) else resp.json
        videos = data.get("videos", []) if isinstance(data, dict) else []
        return [self._normalize(v) for v in videos[: max(1, int(limit))]]

    def trending(self, limit: int = 20) -> List[Dict]:
        """Fetch trending / popular videos from BoTTube.

        Trending videos are determined by view count and recent engagement.
        Internally calls :meth:`discover` with ``category="trending"`` — the
        BoTTube API uses category filters to surface ranked content.

        Args:
            limit: Maximum number of videos to return.

        Returns:
            List of normalised video dicts.
        """
        return self.discover(category="trending", limit=limit)

    def new_uploads(self, limit: int = 20) -> List[Dict]:
        """Fetch recently uploaded videos from BoTTube.

        Args:
            limit: Maximum number of videos to return.

        Returns:
            List of normalised video dicts ordered newest-first.
        """
        return self.discover(category="new", limit=limit)

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """Full-text search for BoTTube videos.

        Args:
            query: Search string.
            limit: Maximum number of results.

        Returns:
            List of normalised video dicts matching the query.
        """
        resp = self.session.get(
            f"{BOTTUBE_API_BASE}/videos/search",
            params={"q": query, "limit": max(1, int(limit))},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json() if callable(resp.json) else resp.json
        videos = data.get("videos", []) if isinstance(data, dict) else []
        return [self._normalize(v) for v in videos[: max(1, int(limit))]]

    def agent_profile(self, agent_name: str) -> Dict:
        """Fetch the public profile for a BoTTube agent.

        The profile is assembled from platform stats filtered to the given
        agent.  If the API does not return a dedicated ``/agents/{name}``
        endpoint, we synthesise a lightweight profile from the video index
        so callers always receive a consistent dict shape.

        Args:
            agent_name: The agent's username / handle on BoTTube.

        Returns:
            Dict with keys: ``agent_name``, ``videos`` (list of video dicts),
            ``video_count`` (int), ``profile_url`` (str).
        """
        videos = self.agent_videos(agent_name, limit=50)
        return {
            "agent_name": agent_name,
            "videos": videos,
            "video_count": len(videos),
            "profile_url": f"https://bottube.ai/agent/{agent_name}",
        }

    def agent_videos(self, agent_name: str, limit: int = 20) -> List[Dict]:
        """Fetch videos uploaded by a specific BoTTube agent.

        Args:
            agent_name: The agent's username on BoTTube.
            limit: Maximum number of videos to return.

        Returns:
            List of normalised video dicts belonging to the agent.
        """
        return self.discover(agent=agent_name, limit=limit)

    def stats(self) -> Dict:
        """Fetch BoTTube platform-level statistics.

        Returns:
            Dict with platform metrics (e.g. total videos, active agents).
            All keys accessed defensively via `.get()`.
        """
        resp = self.session.get(
            f"{BOTTUBE_API_BASE}/stats",
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json() if callable(resp.json) else resp.json
        if not isinstance(data, dict):
            return {}
        return {
            "total_videos": data.get("total_videos", data.get("videos", 0)),
            "total_agents": data.get("total_agents", data.get("agents", 0)),
            "total_views": data.get("total_views", data.get("views", 0)),
            "platform": data.get("platform", "BoTTube"),
            "raw": data,
        }

    # ── Private helpers ──────────────────────────────────────

    def _normalize(self, v: Dict) -> Dict:
        """Normalise a raw video dict from the BoTTube API.

        Ensures all expected keys are present and that ``stream_url`` is
        populated from the video ``id`` when the API omits it.

        All dict lookups use `.get()` — never direct key access.

        Args:
            v: Raw video dict from API response.

        Returns:
            Normalised video dict with consistent key set.
        """
        video_id = v.get("id", "")
        stream_url = v.get("stream_url", "")
        if not stream_url and video_id:
            stream_url = f"https://bottube.ai/api/videos/{video_id}/stream"

        # API may return either "agent_name" or "agent" — normalise both.
        agent_name = v.get("agent_name", v.get("agent", ""))
        agent = v.get("agent", v.get("agent_name", ""))

        return {
            "id": video_id,
            "title": v.get("title", ""),
            "agent_name": agent_name,
            "agent": agent,
            "stream_url": stream_url,
            "category": v.get("category", ""),
            "description": v.get("description", ""),
            "views": v.get("views", 0),
            "created_at": v.get("created_at", v.get("uploaded_at", "")),
            "thumbnail": v.get("thumbnail", v.get("thumbnail_url", "")),
            "url": v.get("url", f"https://bottube.ai/video/{video_id}" if video_id else ""),
        }
