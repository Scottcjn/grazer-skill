import logging
import requests
from typing import Dict, List, Optional, Union
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from grazer.base import GrazerBase

logger = logging.getLogger(__name__)

class BoTTubeGrazer(GrazerBase):
    """BoTTube content discovery plugin."""

    def __init__(self, api_key: Optional[str] = None, timeout: int = 15):
        super().__init__()
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self._configure_session()

    def _configure_session(self) -> None:
        """Configure session with headers and retries."""
        headers = {
            "User-Agent": f"Grazer/{__version__}",
            "Accept": "application/json",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self.session.headers.update(headers)
        self.session.mount(
            "https://",
            HTTPAdapter(
                max_retries=Retry(
                    total=3,
                    backoff_factor=1,
                    status_forcelist=[429, 500, 502, 503, 504],
                )
            ),
        )

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make API request with error handling."""
        try:
            response = self.session.get(
                f"https://bottube.ai/api/{endpoint}",
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.warning(f"BoTTube API request failed: {e}")
            return {}

    def discover(self, limit: int = 10, category: Optional[str] = None, agent: Optional[str] = None) -> List[Dict]:
        """Discover videos with optional filters."""
        params = {"limit": limit}
        if category:
            params["category"] = category
        if agent:
            params["agent"] = agent

        data = self._make_request("videos", params)
        return data.get("videos", [])

    def trending(self, limit: int = 10) -> List[Dict]:
        """Get trending videos."""
        return self.discover(limit=limit, category="trending")

    def new_uploads(self, limit: int = 10) -> List[Dict]:
        """Get new uploads."""
        return self.discover(limit=limit, category="new")

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for videos."""
        return self.discover(limit=limit, category="search", agent=query)

    def agent_profile(self, agent_name: str) -> Dict:
        """Get agent profile."""
        data = self._make_request(f"agents/{agent_name}")
        return data.get("agent", {})

    def agent_videos(self, agent_name: str, limit: int = 10) -> List[Dict]:
        """Get videos by agent."""
        return self.discover(limit=limit, agent=agent_name)

    def stats(self) -> Dict:
        """Get platform statistics."""
        data = self._make_request("stats")
        return data.get("stats", {})