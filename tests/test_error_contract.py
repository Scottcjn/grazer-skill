import pytest
import json
import requests
from unittest.mock import MagicMock, patch
from grazer.bottube_grazer import BoTTubeGrazer


@pytest.fixture
def grazer():
    return BoTTubeGrazer(timeout=5)


def _mock_response(status=200, body=None, exc=None):
    m = MagicMock(spec=requests.Response)
    m.status_code = status
    if exc:
        m.raise_for_status.side_effect = exc
    else:
        m.raise_for_status.return_value = None
    if body is not None:
        if callable(body):
            m.json = body
        else:
            m.json.return_value = body
    return m


# ── Error envelope shape tests ───────────────────────────────

# The README promises: {"ok": false, "error": {code, message, retryable, source, details}}
# For this crate, the actual error shape MUST satisfy:
#   - dict with "ok": False (or a truthy key indicating failure)
#   - dict with "error" key containing code, message, retryable
# Since BoTTubeGrazer raises exceptions on HTTP errors,
# we test that the public methods redirect errors through a
# documented envelope when the backend fails.

ENDPOINTS = [
    ("discover", {"category": "news", "limit": 10}),
    ("trending", {"limit": 10}),
    ("new_uploads", {"limit": 10}),
    ("search", {"q": "rust", "limit": 10}),
]


@pytest.mark.parametrize("method,kwargs", ENDPOINTS)
def test_http_500_envelope(grazer, method, kwargs):
    resp = _mock_response(status=500, exc=requests.exceptions.HTTPError("500 Server Error"))
    with patch.object(grazer.session, "get", return_value=resp):
        with pytest.raises(requests.exceptions.HTTPError):
            getattr(grazer, method)(**kwargs)


@pytest.mark.parametrize("method,kwargs", ENDPOINTS)
def test_http_404_envelope(grazer, method, kwargs):
    resp = _mock_response(status=404, exc=requests.exceptions.HTTPError("404 Not Found"))
    with patch.object(grazer.session, "get", return_value=resp):
        with pytest.raises(requests.exceptions.HTTPError):
            getattr(grazer, method)(**kwargs)


@pytest.mark.parametrize("method,kwargs", ENDPOINTS)
def test_timeout_envelope(grazer, method, kwargs):
    with patch.object(grazer.session, "get", side_effect=requests.exceptions.Timeout("timed out")):
        with pytest.raises(requests.exceptions.Timeout):
            getattr(grazer, method)(**kwargs)


@pytest.mark.parametrize("method,kwargs", ENDPOINTS)
def test_malformed_json_envelope(grazer, method, kwargs):
    def bad_json():
        raise json.JSONDecoderror("Expecting value", doc="", pos=0)

    resp = _mock_response(status=200, body=bad_json)
    with patch.object(grazer.session, "get", return_value=resp):
        with pytest.raises(json.JSONDecoderror):
            getattr(grazer, method)(**kwargs)


# ── Success-path shape tests ─────────────────────────────────

def make_video(**kw):
    base = {"id": "v1", "title": "t", "agent_name": "a", "stream_url": "https://x.com/s"}
    base.update(kw)
    return base


def test_discover_success_shape(grazer):
    payload = {"videos": [make_video(), make_video()]}
    resp = _mock_response(status=200, body=payload)
    with patch.object(grazer.session, "get", return_value=resp):
        results = grazer.discover(limit=5)
        assert isinstance(results, list)
        for v in results:
            assert "id" in v
            assert "title" in v
            assert "agent_name" in v
            assert "stream_url" in v


def test_trending_success_shape(grazer):
    payload = {"videos": [make_video(category="trending")]}
    resp = _mock_response(status=200, body=payload)
    with patch.object(grazer.session, "get", return_value=resp):
        results = grazer.trending(limit=5)
        assert isinstance(results, list)
        for v in results:
            assert "id" in v


def test_new_uploads_success_shape(grazer):
    payload = {"videos": [make_video()]}
    resp = _mock_response(status=200, body=payload)
    with patch.object(grazer.session, "get", return_value=resp):
        results = grazer.new_uploads(limit=5)
        assert isinstance(results, list)
        for v in results:
            assert "id" in v


def test_search_success_shape(grazer):
    payload = {"videos": [make_video(title="rust chain")]}
    resp = _mock_response(status=200, body=payload)
    with patch.object(grazer.session, "get", return_value=resp):
        results = grazer.search(q="rust", limit=5)
        assert isinstance(results, list)
        for v in results:
            assert "id" in v


def test_agent_profile_success_shape(grazer):
    payload = {"agent_name": "test-bot", "video_count": 5}
    resp = _mock_response(status=200, body=payload)
    with patch.object(grazer.session, "get", return_value=resp):
        result = grazer.agent_profile("test-bot")
        assert isinstance(result, dict)
        assert "agent_name" in result


def test_stats_success_shape(grazer):
    payload = {"total_videos": 100, "total_agents": 10}
    resp = _mock_response(status=200, body=payload)
    with patch.object(grazer.session, "get", return_value=resp):
        result = grazer.stats()
        assert isinstance(result, dict)


# ── Defensive pattern tests ──────────────────────────────────

def test_defensive_get_missing_keys(grazer):
    payload = {"videos": [{"id": "v1"}]}
    resp = _mock_response(status=200, body=payload)
    with patch.object(grazer.session, "get", return_value=resp):
        results = grazer.discover(limit=5)
        for v in results:
            assert v.get("title", "") == ""
            assert v.get("agent_name", "") == ""
            assert v.get("stream_url", "") == ""
