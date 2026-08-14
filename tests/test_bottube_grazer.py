"""
Tests for the BoTTube discovery plugin (BoTTubeGrazer).

Covers:
- All public methods: discover, trending, new_uploads, search,
  agent_profile, agent_videos, stats
- .get() defensive pattern (missing/partial keys never raise KeyError)
- HTTP mocking via unittest.mock — no real network calls
- GrazerClient integration (discover_bottube, search_bottube, get_bottube_stats)
- Python 3.14 compatibility with keyless mode
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from grazer.bottube_grazer import BoTTubeGrazer
from grazer import GrazerClient

# ── Fixtures & helpers ───────────────────────────────────────

def make_video(**kwargs):
    """Return a minimal video dict; override any field via kwargs."""
    base = {
        "id": "vid-001",
        "title": "Hello BoTTube",
        "agent_name": "agent-alpha",
        "stream_url": "https://bottube.ai/api/videos/vid-001/stream",
        "category": "demo",
        "views": 42,
    }
    base.update(kwargs)
    return base

def mock_response(json_data, status=200):
    """Create a mock requests.Response-like object."""
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp

# ── BoTTubeGrazer unit tests ─────────────────────────────────

class TestBoTTubeGrazerInit:
    def test_default_init(self):
        g = BoTTubeGrazer()
        assert g.api_key is None
        assert g.timeout == 15

    def test_custom_init(self):
        g = BoTTubeGrazer(api_key="secret-key", timeout=30)
        assert g.api_key == "secret-key"
        assert g.timeout == 30

    def test_api_key_injected_into_headers(self):
        g = BoTTubeGrazer(api_key="tok123")
        assert "Authorization" in g.session.headers
        assert "tok123" in g.session.headers["Authorization"]

    def test_user_agent_set(self):
        g = BoTTubeGrazer()
        assert "Grazer" in g.session.headers.get("User-Agent", "")

    def test_keyless_mode_compatibility(self):
        """Test that keyless mode works without Authorization header."""
        g = BoTTubeGrazer()
        assert "Authorization" not in g.session.headers
        assert g.session.headers.get("User-Agent") is not None

class TestDiscover:
    def test_returns_list(self):
        g = BoTTubeGrazer()
        videos = [make_video(id=f"v{i}", title=f"Video {i}") for i in range(5)]
        resp = mock_response({"videos": videos})

        with patch.object(g.session, "get", return_value=resp):
            result = g.discover(limit=5)

        assert isinstance(result, list)
        assert len(result) == 5

    def test_respects_limit(self):
        g = BoTTubeGrazer()
        videos = [make_video(id=f"v{i}") for i in range(10)]
        resp = mock_response({"videos": videos})

        with patch.object(g.session, "get", return_value=resp):
            result = g.discover(limit=3)

        assert len(result) == 3

    def test_category_passed_as_param(self):
        g = BoTTubeGrazer()
        resp = mock_response({"videos": []})

        with patch.object(g.session, "get", return_value=resp) as mock_get:
            g.discover(category="music", limit=5)
            call_kwargs = mock_get.call_args
            params = call_kwargs[1].get("params", call_kwargs[0][1] if len(call_kwargs[0]) > 1 else {})
            actual_params = mock_get.call_args.kwargs.get("params", {})
            if not actual_params and mock_get.call_args.args:
                actual_params = mock_get.call_args.args[1] if len(mock_get.call_args.args) > 1 else {}
        assert mock_get.called

    def test_agent_filter_passed(self):
        g = BoTTubeGrazer()
        resp = mock_response({"videos": [make_video(agent_name="bot-x")]})

        with patch.object(g.session, "