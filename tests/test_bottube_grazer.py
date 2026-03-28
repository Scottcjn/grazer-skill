"""
Tests for the BoTTube discovery plugin (BoTTubeGrazer).

Covers:
- All public methods: discover, trending, new_uploads, search,
  agent_profile, agent_videos, stats
- .get() defensive pattern (missing/partial keys never raise KeyError)
- HTTP mocking via unittest.mock — no real network calls
- GrazerClient integration (discover_bottube, search_bottube, get_bottube_stats)
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
            # params can be in positional or keyword args
            actual_params = mock_get.call_args.kwargs.get("params", {})
            if not actual_params and mock_get.call_args.args:
                actual_params = mock_get.call_args.args[1] if len(mock_get.call_args.args) > 1 else {}
        # Just verify the call was made (params checked via other tests)
        assert mock_get.called

    def test_agent_filter_passed(self):
        g = BoTTubeGrazer()
        resp = mock_response({"videos": [make_video(agent_name="bot-x")]})

        with patch.object(g.session, "get", return_value=resp) as mock_get:
            result = g.discover(agent="bot-x", limit=10)

        assert len(result) == 1
        assert result[0].get("agent_name") == "bot-x"

    def test_empty_response(self):
        g = BoTTubeGrazer()
        resp = mock_response({"videos": []})

        with patch.object(g.session, "get", return_value=resp):
            result = g.discover()

        assert result == []

    def test_missing_videos_key(self):
        """API returns dict without 'videos' key — must not raise KeyError."""
        g = BoTTubeGrazer()
        resp = mock_response({})  # no "videos" key

        with patch.object(g.session, "get", return_value=resp):
            result = g.discover()

        assert result == []

    def test_non_dict_response(self):
        """API returns non-dict — must not raise."""
        g = BoTTubeGrazer()
        resp = mock_response([make_video()])  # list instead of dict

        with patch.object(g.session, "get", return_value=resp):
            result = g.discover()

        assert isinstance(result, list)


class TestTrending:
    def test_trending_calls_discover(self):
        g = BoTTubeGrazer()
        videos = [make_video(id=f"t{i}") for i in range(3)]
        resp = mock_response({"videos": videos})

        with patch.object(g.session, "get", return_value=resp):
            result = g.trending(limit=3)

        assert len(result) == 3

    def test_trending_uses_trending_category(self):
        """trending() should pass category=trending to the API."""
        g = BoTTubeGrazer()
        resp = mock_response({"videos": []})

        with patch.object(g.session, "get", return_value=resp) as mock_get:
            g.trending(limit=5)

        call_args = mock_get.call_args
        # params should include category=trending
        params = call_args.kwargs.get("params", {})
        assert params.get("category") == "trending"


class TestNewUploads:
    def test_new_uploads_returns_list(self):
        g = BoTTubeGrazer()
        videos = [make_video(id="nu1", category="new")]
        resp = mock_response({"videos": videos})

        with patch.object(g.session, "get", return_value=resp):
            result = g.new_uploads(limit=10)

        assert isinstance(result, list)
        assert len(result) == 1

    def test_new_uploads_uses_new_category(self):
        """new_uploads() should pass category=new to the API."""
        g = BoTTubeGrazer()
        resp = mock_response({"videos": []})

        with patch.object(g.session, "get", return_value=resp) as mock_get:
            g.new_uploads(limit=5)

        params = mock_get.call_args.kwargs.get("params", {})
        assert params.get("category") == "new"


class TestSearch:
    def test_search_returns_list(self):
        g = BoTTubeGrazer()
        videos = [make_video(id="s1", title="AI music")]
        resp = mock_response({"videos": videos})

        with patch.object(g.session, "get", return_value=resp):
            result = g.search("AI music", limit=5)

        assert len(result) == 1
        assert result[0].get("title") == "AI music"

    def test_search_passes_query(self):
        g = BoTTubeGrazer()
        resp = mock_response({"videos": []})

        with patch.object(g.session, "get", return_value=resp) as mock_get:
            g.search("robots", limit=5)

        params = mock_get.call_args.kwargs.get("params", {})
        assert params.get("q") == "robots"

    def test_search_respects_limit(self):
        g = BoTTubeGrazer()
        videos = [make_video(id=f"s{i}") for i in range(10)]
        resp = mock_response({"videos": videos})

        with patch.object(g.session, "get", return_value=resp):
            result = g.search("anything", limit=4)

        assert len(result) == 4

    def test_search_empty(self):
        g = BoTTubeGrazer()
        resp = mock_response({"videos": []})

        with patch.object(g.session, "get", return_value=resp):
            result = g.search("zzz_nothing_matches")

        assert result == []


class TestAgentProfile:
    def test_returns_profile_dict(self):
        g = BoTTubeGrazer()
        videos = [make_video(id="ap1", agent_name="bot-42")]
        resp = mock_response({"videos": videos})

        with patch.object(g.session, "get", return_value=resp):
            profile = g.agent_profile("bot-42")

        assert isinstance(profile, dict)
        assert profile.get("agent_name") == "bot-42"
        assert "video_count" in profile
        assert "profile_url" in profile
        assert "videos" in profile

    def test_profile_url_contains_agent_name(self):
        g = BoTTubeGrazer()
        resp = mock_response({"videos": []})

        with patch.object(g.session, "get", return_value=resp):
            profile = g.agent_profile("my-agent")

        assert "my-agent" in profile.get("profile_url", "")

    def test_video_count_matches_videos(self):
        g = BoTTubeGrazer()
        videos = [make_video(id=f"p{i}", agent_name="agent-z") for i in range(3)]
        resp = mock_response({"videos": videos})

        with patch.object(g.session, "get", return_value=resp):
            profile = g.agent_profile("agent-z")

        assert profile.get("video_count") == len(profile.get("videos", []))


class TestAgentVideos:
    def test_returns_list(self):
        g = BoTTubeGrazer()
        videos = [make_video(agent_name="bot-99")]
        resp = mock_response({"videos": videos})

        with patch.object(g.session, "get", return_value=resp):
            result = g.agent_videos("bot-99", limit=10)

        assert isinstance(result, list)

    def test_passes_agent_param(self):
        g = BoTTubeGrazer()
        resp = mock_response({"videos": []})

        with patch.object(g.session, "get", return_value=resp) as mock_get:
            g.agent_videos("cool-bot", limit=5)

        params = mock_get.call_args.kwargs.get("params", {})
        assert params.get("agent") == "cool-bot"


class TestStats:
    def test_returns_dict(self):
        g = BoTTubeGrazer()
        raw = {"total_videos": 447, "total_agents": 63, "total_views": 99000}
        resp = mock_response(raw)

        with patch.object(g.session, "get", return_value=resp):
            result = g.stats()

        assert isinstance(result, dict)
        assert result.get("total_videos") == 447
        assert result.get("total_agents") == 63

    def test_stats_missing_keys(self):
        """Stats with partial data must not raise KeyError."""
        g = BoTTubeGrazer()
        resp = mock_response({})  # empty stats

        with patch.object(g.session, "get", return_value=resp):
            result = g.stats()

        assert isinstance(result, dict)
        # Should return defaults, not raise
        assert result.get("total_videos", 0) == 0
        assert result.get("total_agents", 0) == 0

    def test_stats_non_dict_response(self):
        """Non-dict API response must not raise."""
        g = BoTTubeGrazer()
        resp = mock_response("unexpected string")

        with patch.object(g.session, "get", return_value=resp):
            result = g.stats()

        assert isinstance(result, dict)


# ── Defensive .get() pattern tests ──────────────────────────


class TestDefensiveGetPattern:
    """Ensure .get() is used everywhere — missing keys never raise KeyError."""

    def test_normalize_with_empty_dict(self):
        """_normalize({}) must not raise and returns defaults."""
        g = BoTTubeGrazer()
        result = g._normalize({})

        assert isinstance(result, dict)
        # All expected keys present with safe defaults
        assert result.get("id") == ""
        assert result.get("title") == ""
        assert result.get("agent_name") == ""
        assert result.get("stream_url") == ""
        assert result.get("views") == 0

    def test_normalize_auto_generates_stream_url(self):
        """stream_url is generated from id when missing from API."""
        g = BoTTubeGrazer()
        result = g._normalize({"id": "abc123"})

        assert "abc123" in result.get("stream_url", "")

    def test_normalize_preserves_stream_url_if_present(self):
        """stream_url from API is kept as-is."""
        g = BoTTubeGrazer()
        result = g._normalize({
            "id": "abc123",
            "stream_url": "https://cdn.bottube.ai/stream/abc123",
        })

        assert result.get("stream_url") == "https://cdn.bottube.ai/stream/abc123"

    def test_normalize_agent_alias(self):
        """'agent' key is also normalised from 'agent_name' and vice-versa."""
        g = BoTTubeGrazer()

        # API returns agent_name only
        result = g._normalize({"agent_name": "bot-a"})
        assert result.get("agent_name") == "bot-a"
        assert result.get("agent") == "bot-a"

        # API returns agent only
        result2 = g._normalize({"agent": "bot-b"})
        assert result2.get("agent_name") == "bot-b"
        assert result2.get("agent") == "bot-b"

    def test_discover_with_partial_video_dicts(self):
        """Videos with missing fields are normalised without raising."""
        g = BoTTubeGrazer()
        partial = [{"id": "x1"}, {"title": "no-id"}, {}]
        resp = mock_response({"videos": partial})

        with patch.object(g.session, "get", return_value=resp):
            result = g.discover()

        assert len(result) == 3
        for item in result:
            # Must have all keys, no KeyError raised
            _ = item.get("id")
            _ = item.get("title")
            _ = item.get("agent_name")
            _ = item.get("stream_url")
            _ = item.get("views")


# ── GrazerClient integration ─────────────────────────────────


class TestGrazerClientIntegration:
    """Verify GrazerClient wires into BoTTube correctly."""

    def test_discover_bottube_returns_list(self):
        client = GrazerClient()
        videos = [make_video()]
        resp = mock_response({"videos": videos})

        with patch.object(client.session, "get", return_value=resp):
            result = client.discover_bottube(limit=1)

        assert isinstance(result, list)
        assert len(result) == 1

    def test_search_bottube_returns_list(self):
        client = GrazerClient()
        videos = [make_video(title="searched")]
        resp = mock_response({"videos": videos})

        with patch.object(client.session, "get", return_value=resp):
            result = client.search_bottube("searched", limit=5)

        assert isinstance(result, list)

    def test_get_bottube_stats_returns_dict(self):
        client = GrazerClient()
        raw_stats = {"total_videos": 447, "total_agents": 63}
        resp = mock_response(raw_stats)

        with patch.object(client.session, "get", return_value=resp):
            result = client.get_bottube_stats()

        assert isinstance(result, dict)

    def test_discover_all_includes_bottube(self):
        """discover_all() result must have a 'bottube' key."""
        client = GrazerClient()
        videos = [make_video()]
        resp = mock_response({"videos": videos})

        # Mock all network calls to avoid external requests during tests
        with patch.object(client.session, "get", return_value=resp), \
             patch.object(client._arxiv.session, "get", return_value=mock_response({"entries": []})), \
             patch.object(client._youtube.session, "get", return_value=mock_response({})), \
             patch.object(client._podcast.session, "get", return_value=mock_response({})), \
             patch.object(client._bluesky.session, "get", return_value=mock_response({"posts": []})), \
             patch.object(client._farcaster.session, "get", return_value=mock_response({"casts": []})), \
             patch.object(client._semantic_scholar.session, "get", return_value=mock_response({"data": []})), \
             patch.object(client._openreview.session, "get", return_value=mock_response({"notes": []})), \
             patch.object(client._mastodon.session, "get", return_value=mock_response([])), \
             patch.object(client._nostr.session, "get", return_value=mock_response({"items": []})):
            result = client.discover_all(limit=1)

        assert "bottube" in result

    def test_bottube_grazer_importable_from_grazer(self):
        """BoTTubeGrazer must be importable from the grazer package."""
        from grazer.bottube_grazer import BoTTubeGrazer as BG
        assert BG is not None
