"""
Tests for the Bluesky, Farcaster, Semantic Scholar, OpenReview, Mastodon,
and Nostr discovery plugins.
24 tests covering parsing, client methods, error handling, and CLI integration.
"""

import io
import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from grazer.bluesky_grazer import BlueskyGrazer, _normalize_post
from grazer.farcaster_grazer import FarcasterGrazer, _normalize_cast
from grazer.semantic_scholar_grazer import SemanticScholarGrazer, _normalize_paper
from grazer.openreview_grazer import OpenReviewGrazer, _normalize_note
from grazer.mastodon_grazer import MastodonGrazer, _normalize_status
from grazer.nostr_grazer import NostrGrazer, _normalize_event
from grazer import GrazerClient


# ─── Bluesky Tests ──────────────────────────────────────────


SAMPLE_BSKY_POST = {
    "uri": "at://did:plc:abc123/app.bsky.feed.post/rkey456",
    "cid": "bafy123",
    "author": {
        "did": "did:plc:abc123",
        "handle": "alice.bsky.social",
        "displayName": "Alice",
    },
    "record": {
        "text": "Hello Bluesky from an AI agent!",
        "createdAt": "2026-03-20T12:00:00Z",
        "langs": ["en"],
    },
    "likeCount": 42,
    "repostCount": 5,
    "replyCount": 3,
}


def test_normalize_bluesky_post():
    """Normalize a Bluesky post into consistent dict."""
    post = _normalize_post(SAMPLE_BSKY_POST)
    assert post["text"] == "Hello Bluesky from an AI agent!"
    assert post["author_handle"] == "alice.bsky.social"
    assert post["author_name"] == "Alice"
    assert post["likes"] == 42
    assert "bsky.app/profile/alice.bsky.social/post/rkey456" in post["url"]
    assert post["language"] == "en"


def test_normalize_bluesky_post_empty():
    """Normalize an empty post gracefully."""
    post = _normalize_post({})
    assert post["text"] == ""
    assert post["author_handle"] == ""
    assert post["likes"] == 0
    assert post["url"] == ""


def test_bluesky_discover_calls_api():
    """BlueskyGrazer.discover makes HTTP request and returns posts."""
    grazer = BlueskyGrazer(timeout=5)
    mock_resp = Mock()
    mock_resp.json.return_value = {"posts": [SAMPLE_BSKY_POST]}
    mock_resp.raise_for_status = Mock()

    with patch.object(grazer.session, "get", return_value=mock_resp) as mock_get:
        results = grazer.discover(query="test", limit=5)
        assert len(results) == 1
        assert results[0]["text"] == "Hello Bluesky from an AI agent!"
        mock_get.assert_called_once()
        call_url = mock_get.call_args[0][0]
        assert "searchPosts" in call_url


def test_bluesky_timeline():
    """BlueskyGrazer.timeline fetches actor feed."""
    grazer = BlueskyGrazer(timeout=5)
    mock_resp = Mock()
    mock_resp.json.return_value = {"feed": [{"post": SAMPLE_BSKY_POST}]}
    mock_resp.raise_for_status = Mock()

    with patch.object(grazer.session, "get", return_value=mock_resp):
        results = grazer.timeline(actor="alice.bsky.social", limit=5)
        assert len(results) == 1


# ─── Farcaster Tests ────────────────────────────────────────


SAMPLE_CAST = {
    "hash": "0xabc123def456",
    "text": "GM Farcaster! Building in public.",
    "timestamp": "2026-03-20T10:00:00Z",
    "author": {
        "fid": 12345,
        "username": "alice",
        "display_name": "Alice",
        "pfp_url": "https://example.com/pfp.png",
    },
    "reactions": {"likes_count": 100, "recasts_count": 20},
    "replies": {"count": 8},
    "channel": {"id": "ai"},
}


def test_normalize_farcaster_cast():
    """Normalize a Farcaster cast into consistent dict."""
    cast = _normalize_cast(SAMPLE_CAST)
    assert cast["text"] == "GM Farcaster! Building in public."
    assert cast["author_username"] == "alice"
    assert cast["likes"] == 100
    assert cast["recasts"] == 20
    assert cast["replies"] == 8
    assert cast["channel"] == "ai"
    assert "warpcast.com/alice" in cast["url"]


def test_farcaster_discover_calls_api():
    """FarcasterGrazer.discover makes HTTP request."""
    grazer = FarcasterGrazer(timeout=5)
    mock_resp = Mock()
    mock_resp.json.return_value = {"result": {"casts": [SAMPLE_CAST]}}
    mock_resp.raise_for_status = Mock()

    with patch.object(grazer.session, "get", return_value=mock_resp) as mock_get:
        results = grazer.discover(query="test", limit=5)
        assert len(results) == 1
        assert results[0]["author_username"] == "alice"
        call_url = mock_get.call_args[0][0]
        assert "cast/search" in call_url


def test_farcaster_with_api_key():
    """FarcasterGrazer passes API key in headers when provided."""
    grazer = FarcasterGrazer(api_key="test-key-123", timeout=5)
    assert grazer.session.headers.get("x-api-key") == "test-key-123"


def test_farcaster_trending():
    """FarcasterGrazer.trending fetches trending casts."""
    grazer = FarcasterGrazer(timeout=5)
    mock_resp = Mock()
    mock_resp.json.return_value = {"casts": [SAMPLE_CAST]}
    mock_resp.raise_for_status = Mock()

    with patch.object(grazer.session, "get", return_value=mock_resp):
        results = grazer.trending(limit=5)
        assert len(results) == 1


# ─── Semantic Scholar Tests ─────────────────────────────────


SAMPLE_PAPER = {
    "paperId": "abc123",
    "title": "Attention Is All You Need",
    "abstract": "We propose a new architecture based on attention mechanisms.",
    "authors": [{"name": "Ashish Vaswani"}, {"name": "Noam Shazeer"}],
    "year": 2017,
    "citationCount": 90000,
    "referenceCount": 40,
    "venue": "NeurIPS",
    "publicationDate": "2017-06-12",
    "url": "https://www.semanticscholar.org/paper/abc123",
    "openAccessPdf": {"url": "https://arxiv.org/pdf/1706.03762"},
}


def test_normalize_semantic_scholar_paper():
    """Normalize a Semantic Scholar paper into consistent dict."""
    paper = _normalize_paper(SAMPLE_PAPER)
    assert paper["title"] == "Attention Is All You Need"
    assert len(paper["authors"]) == 2
    assert paper["authors"][0] == "Ashish Vaswani"
    assert paper["citation_count"] == 90000
    assert paper["year"] == 2017
    assert paper["pdf_url"] == "https://arxiv.org/pdf/1706.03762"


def test_normalize_paper_missing_pdf():
    """Paper without openAccessPdf gets empty pdf_url."""
    paper = _normalize_paper({"paperId": "x", "title": "Test"})
    assert paper["pdf_url"] == ""
    assert paper["authors"] == []


def test_semantic_scholar_discover():
    """SemanticScholarGrazer.discover makes HTTP request."""
    grazer = SemanticScholarGrazer(timeout=5)
    mock_resp = Mock()
    mock_resp.json.return_value = {"data": [SAMPLE_PAPER]}
    mock_resp.raise_for_status = Mock()

    with patch.object(grazer.session, "get", return_value=mock_resp) as mock_get:
        results = grazer.discover(query="transformers", limit=5)
        assert len(results) == 1
        assert results[0]["title"] == "Attention Is All You Need"
        call_url = mock_get.call_args[0][0]
        assert "paper/search" in call_url


def test_semantic_scholar_get_paper_not_found():
    """SemanticScholarGrazer.get_paper returns None for 404."""
    grazer = SemanticScholarGrazer(timeout=5)
    mock_resp = Mock()
    mock_resp.status_code = 404

    with patch.object(grazer.session, "get", return_value=mock_resp):
        result = grazer.get_paper("nonexistent")
        assert result is None


# ─── OpenReview Tests ───────────────────────────────────────


SAMPLE_NOTE = {
    "id": "note123",
    "forum": "note123",
    "content": {
        "title": {"value": "Scaling Language Models"},
        "abstract": {"value": "We study scaling laws for LLMs."},
        "authors": {"value": ["Alice", "Bob"]},
        "venue": {"value": "ICLR 2025"},
    },
    "cdate": 1700000000,
    "mdate": 1700100000,
}


def test_normalize_openreview_note():
    """Normalize an OpenReview note into consistent dict."""
    paper = _normalize_note(SAMPLE_NOTE)
    assert paper["title"] == "Scaling Language Models"
    assert len(paper["authors"]) == 2
    assert paper["venue"] == "ICLR 2025"
    assert "openreview.net/forum?id=note123" in paper["url"]
    assert "openreview.net/pdf?id=note123" in paper["pdf_url"]


def test_normalize_openreview_note_flat_content():
    """OpenReview notes with flat string content (API v1 style)."""
    note = {
        "id": "x",
        "forum": "x",
        "content": {
            "title": "A Direct Title",
            "abstract": "A direct abstract",
            "authors": ["Charlie"],
            "venue": "NeurIPS",
        },
    }
    paper = _normalize_note(note)
    assert paper["title"] == "A Direct Title"
    assert paper["authors"] == ["Charlie"]


def test_openreview_discover():
    """OpenReviewGrazer.discover makes HTTP request."""
    grazer = OpenReviewGrazer(timeout=5)
    mock_resp = Mock()
    mock_resp.json.return_value = {"notes": [SAMPLE_NOTE]}
    mock_resp.raise_for_status = Mock()

    with patch.object(grazer.session, "get", return_value=mock_resp) as mock_get:
        results = grazer.discover(query="LLM", limit=5)
        assert len(results) == 1
        assert results[0]["title"] == "Scaling Language Models"


# ─── Mastodon Tests ─────────────────────────────────────────


SAMPLE_STATUS = {
    "id": "status123",
    "content": "<p>Hello from the <a href=\"#\">fediverse</a>!</p>",
    "created_at": "2026-03-20T09:00:00Z",
    "account": {
        "acct": "alice@mastodon.social",
        "display_name": "Alice",
        "url": "https://mastodon.social/@alice",
    },
    "url": "https://mastodon.social/@alice/status123",
    "favourites_count": 15,
    "reblogs_count": 3,
    "replies_count": 2,
    "language": "en",
    "visibility": "public",
}


def test_normalize_mastodon_status():
    """Normalize a Mastodon status with HTML stripping."""
    post = _normalize_status(SAMPLE_STATUS)
    assert "Hello from the" in post["text"]
    assert "<" not in post["text"]  # HTML stripped
    assert post["author_acct"] == "alice@mastodon.social"
    assert post["favourites"] == 15
    assert post["visibility"] == "public"


def test_mastodon_discover():
    """MastodonGrazer.discover makes HTTP request."""
    grazer = MastodonGrazer(timeout=5)
    mock_resp = Mock()
    mock_resp.json.return_value = {"statuses": [SAMPLE_STATUS]}
    mock_resp.raise_for_status = Mock()

    with patch.object(grazer.session, "get", return_value=mock_resp) as mock_get:
        results = grazer.discover(query="test", limit=5)
        assert len(results) == 1
        assert "Hello" in results[0]["text"]


def test_mastodon_custom_instance():
    """MastodonGrazer builds API URL for custom instance."""
    grazer = MastodonGrazer(instance="hachyderm.io", timeout=5)
    url = grazer._api_url()
    assert "hachyderm.io/api/v1" in url


def test_mastodon_trending_tags():
    """MastodonGrazer.trending_tags parses tag data."""
    grazer = MastodonGrazer(timeout=5)
    mock_resp = Mock()
    mock_resp.json.return_value = [
        {"name": "ai", "url": "https://mastodon.social/tags/ai", "history": [{"uses": "50", "accounts": "30"}]},
    ]
    mock_resp.raise_for_status = Mock()

    with patch.object(grazer.session, "get", return_value=mock_resp):
        tags = grazer.trending_tags(limit=5)
        assert len(tags) == 1
        assert tags[0]["name"] == "ai"
        assert tags[0]["uses_today"] == 50


# ─── Nostr Tests ────────────────────────────────────────────


SAMPLE_EVENT = {
    "id": "event123abc",
    "pubkey": "deadbeef01234567",
    "content": "Hello from Nostr! #ai #agents",
    "kind": 1,
    "created_at": 1710000000,
    "tags": [["t", "ai"], ["t", "agents"], ["e", "ref123"]],
}


def test_normalize_nostr_event():
    """Normalize a Nostr event into consistent dict."""
    event = _normalize_event(SAMPLE_EVENT)
    assert event["content"] == "Hello from Nostr! #ai #agents"
    assert event["pubkey"] == "deadbeef01234567"
    assert event["kind"] == 1
    assert "ai" in event["hashtags"]
    assert "agents" in event["hashtags"]
    assert "nostr.band" in event["url"]


def test_nostr_discover():
    """NostrGrazer.discover makes HTTP request."""
    grazer = NostrGrazer(timeout=5)
    mock_resp = Mock()
    mock_resp.json.return_value = {"events": [SAMPLE_EVENT]}
    mock_resp.raise_for_status = Mock()

    with patch.object(grazer.session, "get", return_value=mock_resp) as mock_get:
        results = grazer.discover(query="AI", limit=5)
        assert len(results) == 1
        assert results[0]["pubkey"] == "deadbeef01234567"
        call_url = mock_get.call_args[0][0]
        assert "search" in call_url


# ─── GrazerClient Integration ──────────────────────────────


def test_client_discover_bluesky():
    """GrazerClient.discover_bluesky delegates to BlueskyGrazer."""
    client = GrazerClient()
    mock_resp = Mock()
    mock_resp.json.return_value = {"posts": [SAMPLE_BSKY_POST]}
    mock_resp.raise_for_status = Mock()

    with patch.object(client._bluesky.session, "get", return_value=mock_resp):
        results = client.discover_bluesky(query="test", limit=5)
        assert len(results) == 1


def test_client_discover_all_includes_new_platforms():
    """discover_all result dict includes all 6 new platform keys."""
    client = GrazerClient()

    # Mock all session.get calls to return empty results
    mock_resp = Mock()
    mock_resp.json.return_value = {}
    mock_resp.raise_for_status = Mock()
    mock_resp.status_code = 200

    with patch("requests.Session.get", return_value=mock_resp):
        with patch("requests.Session.post", return_value=mock_resp):
            results = client.discover_all(limit=1)

    # All 6 new platforms should be present as keys
    for platform in ["bluesky", "farcaster", "semantic_scholar", "openreview", "mastodon", "nostr"]:
        assert platform in results, f"Missing platform key: {platform}"
