import io
from argparse import Namespace
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

from grazer import GrazerClient
from grazer import cli


def test_deduplicate_discoveries_normalizes_tracking_urls():
    results = {
        "bottube": [
            {
                "title": "A shared item",
                "url": "https://www.example.com/watch/42/?utm_source=bottube",
            }
        ],
        "moltbook": [
            {
                "title": "A shared item",
                "url": "https://example.com/watch/42?fbclid=tracking",
            }
        ],
        "_errors": {},
    }

    groups = GrazerClient.deduplicate_discoveries(results)

    assert len(groups) == 1
    assert groups[0]["observed_platforms"] == ["bottube", "moltbook"]
    assert len(groups[0]["variants"]) == 2
    assert groups[0]["canonical"]["platform"] == "bottube"


def test_deduplicate_discoveries_matches_mirrors_by_content_identity():
    results = {
        "clawnews": [
            {
                "headline": "RustChain releases indexed UTXO pagination",
                "author": {"username": "alice"},
                "created_at": "2026-06-12T01:15:00Z",
                "url": "https://news.example/posts/100",
            }
        ],
        "moltbook": [
            {
                "title": "RustChain releases indexed UTXO pagination",
                "author_name": "Alice",
                "timestamp": "2026-06-12T09:45:00Z",
                "url": "https://social.example/thread/abc",
            }
        ],
    }

    groups = GrazerClient.deduplicate_discoveries(results)

    assert len(groups) == 1
    assert len(groups[0]["variants"]) == 2


def test_deduplicate_discoveries_keeps_ambiguous_titles_separate():
    results = {
        "bottube": [{"title": "Daily update"}],
        "moltbook": [{"title": "Daily update"}],
    }

    groups = GrazerClient.deduplicate_discoveries(results)

    assert len(groups) == 2


def test_deduplicate_discoveries_tolerates_invalid_url_ports():
    results = {
        "bottube": [
            {
                "title": "Port parsing should not abort discovery",
                "url": "https://example.com:not-a-port/watch",
            }
        ]
    }

    groups = GrazerClient.deduplicate_discoveries(results)

    assert len(groups) == 1


def test_discover_all_only_adds_canonical_output_when_requested():
    client = GrazerClient()
    methods = [
        "discover_bottube",
        "discover_moltbook",
        "discover_clawcities",
        "discover_clawsta",
        "discover_fourclaw",
        "discover_pinchedin",
        "discover_clawtasks",
        "discover_clawnews",
        "discover_directory",
        "discover_agentchan",
        "discover_colony",
        "discover_moltx",
        "discover_moltexchange",
        "discover_arxiv",
        "discover_youtube",
        "discover_podcasts",
        "discover_bluesky",
        "discover_farcaster",
        "discover_semantic_scholar",
        "discover_openreview",
        "discover_mastodon",
        "discover_nostr",
    ]
    for method in methods:
        setattr(client, method, Mock(return_value=[]))
    client.discover_bottube = Mock(
        return_value=[{"title": "Shared", "author": "alice"}]
    )
    client.discover_moltbook = Mock(
        return_value=[{"title": "Shared", "author": "alice"}]
    )

    regular = client.discover_all(limit=1)
    deduplicated = client.discover_all(limit=1, deduplicate=True)

    assert "_canonical" not in regular
    assert len(deduplicated["_canonical"]) == 1
    assert len(deduplicated["_canonical"][0]["variants"]) == 2


def test_cli_reports_collapsed_observations():
    mock_client = Mock()
    mock_client.discover_all.return_value = {
        "bottube": [{"title": "Shared"}],
        "moltbook": [{"title": "Shared"}],
        "_errors": {},
        "_canonical": [
            {
                "canonical_key": "content:key",
                "canonical": {"platform": "bottube", "item": {"title": "Shared"}},
                "observed_platforms": ["bottube", "moltbook"],
                "variants": [
                    {"platform": "bottube", "item": {"title": "Shared"}},
                    {"platform": "moltbook", "item": {"title": "Shared"}},
                ],
            }
        ],
    }
    args = Namespace(
        platform="all",
        category=None,
        submolt="tech",
        board=None,
        limit=5,
        include_health=False,
        deduplicate=True,
    )

    with patch("grazer.cli.load_config", return_value={}):
        with patch("grazer.cli._make_client", return_value=mock_client):
            output = io.StringIO()
            with redirect_stdout(output):
                cli.cmd_discover(args)

    mock_client.discover_all.assert_called_once_with(
        limit=5,
        include_health=False,
        deduplicate=True,
    )
    assert "Canonical items: 1 (1 duplicate observations collapsed)" in output.getvalue()
