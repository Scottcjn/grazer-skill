"""
Tests for the ArXiv, YouTube, and Podcast discovery plugins.
15 tests covering parsing, client methods, error handling, and CLI integration.
"""

import io
import pytest
from argparse import Namespace
from contextlib import redirect_stdout
from unittest.mock import Mock, patch, MagicMock

from grazer.arxiv_grazer import ArxivGrazer, _parse_atom_entries, CATEGORIES
from grazer.youtube_grazer import YouTubeGrazer, _parse_youtube_rss
from grazer.podcast_grazer import PodcastGrazer, _parse_podcast_rss
from grazer import GrazerClient
from grazer import cli


# ─── ArXiv Tests ────────────────────────────────────────────


SAMPLE_ARXIV_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<entry>
  <id>http://arxiv.org/abs/2401.99999v1</id>
  <title>Attention Is All You Need (Again)</title>
  <summary>We revisit transformer architectures and propose improvements.</summary>
  <published>2024-01-15T00:00:00Z</published>
  <updated>2024-01-16T00:00:00Z</updated>
  <author><name>Alice Smith</name></author>
  <author><name>Bob Jones</name></author>
  <link title="pdf" href="https://arxiv.org/pdf/2401.99999v1" rel="related" type="application/pdf"/>
  <category term="cs.AI" scheme="http://arxiv.org/schemas/atom"/>
  <category term="cs.CL" scheme="http://arxiv.org/schemas/atom"/>
</entry>
<entry>
  <id>http://arxiv.org/abs/2401.88888v1</id>
  <title>Scaling Laws for Neural Language Models</title>
  <summary>We study how performance scales with model size.</summary>
  <published>2024-01-10T00:00:00Z</published>
  <updated>2024-01-10T00:00:00Z</updated>
  <author><name>Carol Lee</name></author>
  <category term="cs.LG" scheme="http://arxiv.org/schemas/atom"/>
</entry>
</feed>
"""


def test_parse_arxiv_entries():
    """Test that arXiv Atom XML is parsed into structured paper dicts."""
    papers = _parse_atom_entries(SAMPLE_ARXIV_XML)
    assert len(papers) == 2

    p0 = papers[0]
    assert p0["arxiv_id"] == "2401.99999v1"
    assert "Attention" in p0["title"]
    assert len(p0["authors"]) == 2
    assert p0["authors"][0] == "Alice Smith"
    assert "cs.AI" in p0["categories"]
    assert p0["pdf_url"] == "https://arxiv.org/pdf/2401.99999v1"
    assert p0["url"] == "https://arxiv.org/abs/2401.99999v1"


def test_parse_arxiv_entries_empty():
    """Parse empty feed returns empty list."""
    papers = _parse_atom_entries("<feed></feed>")
    assert papers == []


def test_arxiv_available_categories():
    """ArxivGrazer exposes known categories."""
    cats = ArxivGrazer.available_categories()
    assert "ai" in cats
    assert cats["ai"] == "cs.AI"
    assert "ml" in cats


def test_arxiv_discover_calls_api():
    """ArxivGrazer.discover makes HTTP request and parses response."""
    grazer = ArxivGrazer(timeout=5)
    mock_resp = Mock()
    mock_resp.text = SAMPLE_ARXIV_XML
    mock_resp.raise_for_status = Mock()

    with patch.object(grazer.session, "get", return_value=mock_resp) as mock_get:
        results = grazer.discover(query="transformers", category="ai", limit=5)

    assert len(results) == 2
    mock_get.assert_called_once()
    call_kwargs = mock_get.call_args
    assert "cs.AI" in str(call_kwargs)


def test_arxiv_get_paper():
    """ArxivGrazer.get_paper fetches single paper by ID."""
    grazer = ArxivGrazer(timeout=5)
    mock_resp = Mock()
    mock_resp.text = SAMPLE_ARXIV_XML
    mock_resp.raise_for_status = Mock()

    with patch.object(grazer.session, "get", return_value=mock_resp):
        paper = grazer.get_paper("2401.99999")

    assert paper is not None
    assert "Attention" in paper["title"]


# ─── YouTube Tests ──────────────────────────────────────────


SAMPLE_YOUTUBE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015"
      xmlns:media="http://search.yahoo.com/mrss/">
<entry>
  <yt:videoId>dQw4w9WgXcQ</yt:videoId>
  <title>Never Gonna Give You Up</title>
  <author><name>Rick Astley</name></author>
  <published>2009-10-25T06:57:33+00:00</published>
  <media:description>The classic.</media:description>
  <media:thumbnail url="https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg" width="480" height="360"/>
  <media:statistics views="1500000000"/>
</entry>
<entry>
  <yt:videoId>abc123XYZab</yt:videoId>
  <title>AI Agent Tutorial</title>
  <author><name>Tech Channel</name></author>
  <published>2024-03-01T12:00:00+00:00</published>
  <media:description>How to build agents.</media:description>
  <media:statistics views="42000"/>
</entry>
</feed>
"""


def test_parse_youtube_rss():
    """YouTube RSS feed is parsed into video dicts."""
    videos = _parse_youtube_rss(SAMPLE_YOUTUBE_RSS)
    assert len(videos) == 2

    v0 = videos[0]
    assert v0["id"] == "dQw4w9WgXcQ"
    assert "Never Gonna" in v0["title"]
    assert v0["channel"] == "Rick Astley"
    assert v0["views"] == 1500000000
    assert v0["url"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert "hqdefault" in v0["thumbnail"]


def test_youtube_channel_videos():
    """YouTubeGrazer.channel_videos fetches from RSS feed."""
    grazer = YouTubeGrazer(timeout=5)
    mock_resp = Mock()
    mock_resp.text = SAMPLE_YOUTUBE_RSS
    mock_resp.raise_for_status = Mock()

    with patch.object(grazer.session, "get", return_value=mock_resp):
        videos = grazer.channel_videos("UC_test", limit=1)

    assert len(videos) == 1
    assert videos[0]["id"] == "dQw4w9WgXcQ"


def test_youtube_discover_with_api_key():
    """YouTubeGrazer uses Data API when key is provided."""
    grazer = YouTubeGrazer(api_key="test_key_123", timeout=5)
    mock_resp = Mock()
    mock_resp.json.return_value = {
        "items": [
            {
                "id": {"videoId": "xyz789"},
                "snippet": {
                    "title": "Test Video",
                    "channelTitle": "Test Channel",
                    "description": "desc",
                    "publishedAt": "2024-01-01T00:00:00Z",
                    "thumbnails": {"high": {"url": "https://thumb.jpg"}},
                },
            }
        ]
    }
    mock_resp.raise_for_status = Mock()

    with patch.object(grazer.session, "get", return_value=mock_resp) as mock_get:
        videos = grazer.discover(query="test", limit=5)

    assert len(videos) == 1
    assert videos[0]["id"] == "xyz789"
    assert videos[0]["channel"] == "Test Channel"
    # Should have called the API endpoint, not scraping
    call_url = mock_get.call_args[0][0]
    assert "googleapis.com" in call_url


# ─── Podcast Tests ──────────────────────────────────────────


SAMPLE_PODCAST_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
<channel>
  <title>AI Talk Show</title>
  <item>
    <title><![CDATA[Episode 42: The Future of Agents]]></title>
    <description><![CDATA[We discuss what comes next for AI agents.]]></description>
    <pubDate>Mon, 15 Jan 2024 08:00:00 GMT</pubDate>
    <enclosure url="https://podcast.example.com/ep42.mp3" type="audio/mpeg" length="48000000"/>
    <itunes:duration>01:15:30</itunes:duration>
    <itunes:episode>42</itunes:episode>
    <link>https://podcast.example.com/episodes/42</link>
  </item>
  <item>
    <title>Episode 41: LLMs in Production</title>
    <description>Running language models at scale.</description>
    <pubDate>Mon, 08 Jan 2024 08:00:00 GMT</pubDate>
    <enclosure url="https://podcast.example.com/ep41.mp3" type="audio/mpeg" length="35000000"/>
    <itunes:duration>55:20</itunes:duration>
    <itunes:episode>41</itunes:episode>
  </item>
</channel>
</rss>
"""


def test_parse_podcast_rss():
    """Podcast RSS feed is parsed into episode dicts."""
    episodes = _parse_podcast_rss(SAMPLE_PODCAST_RSS)
    assert len(episodes) == 2

    ep0 = episodes[0]
    assert "Episode 42" in ep0["title"]
    assert ep0["audio_url"] == "https://podcast.example.com/ep42.mp3"
    assert ep0["duration"] == "01:15:30"
    assert ep0["episode_number"] == "42"
    assert "agents" in ep0["description"].lower()


def test_parse_podcast_rss_empty():
    """Empty podcast RSS returns empty list."""
    episodes = _parse_podcast_rss("<rss><channel></channel></rss>")
    assert episodes == []


def test_podcast_search():
    """PodcastGrazer.search calls iTunes Search API."""
    grazer = PodcastGrazer(timeout=5)
    mock_resp = Mock()
    mock_resp.json.return_value = {
        "results": [
            {
                "collectionId": 12345,
                "collectionName": "AI Podcast",
                "artistName": "Tech Host",
                "feedUrl": "https://feed.example.com/rss",
                "artworkUrl600": "https://art.example.com/600.jpg",
                "primaryGenreName": "Technology",
                "trackCount": 100,
                "collectionViewUrl": "https://podcasts.apple.com/podcast/12345",
            }
        ]
    }
    mock_resp.raise_for_status = Mock()

    with patch.object(grazer.session, "get", return_value=mock_resp) as mock_get:
        results = grazer.search("AI", limit=5)

    assert len(results) == 1
    assert results[0]["name"] == "AI Podcast"
    assert results[0]["feed_url"] == "https://feed.example.com/rss"
    call_url = mock_get.call_args[0][0]
    assert "itunes.apple.com" in call_url


def test_podcast_episodes():
    """PodcastGrazer.episodes fetches and parses RSS feed."""
    grazer = PodcastGrazer(timeout=5)
    mock_resp = Mock()
    mock_resp.text = SAMPLE_PODCAST_RSS
    mock_resp.raise_for_status = Mock()

    with patch.object(grazer.session, "get", return_value=mock_resp):
        eps = grazer.episodes("https://feed.example.com/rss", limit=1)

    assert len(eps) == 1
    assert "Episode 42" in eps[0]["title"]


# ─── GrazerClient Integration ──────────────────────────────


def test_grazer_client_has_new_methods():
    """GrazerClient exposes arxiv, youtube, and podcast methods."""
    client = GrazerClient()
    assert hasattr(client, "discover_arxiv")
    assert hasattr(client, "get_arxiv_paper")
    assert hasattr(client, "discover_youtube")
    assert hasattr(client, "youtube_channel")
    assert hasattr(client, "discover_podcasts")
    assert hasattr(client, "podcast_episodes")


def test_discover_all_includes_new_platforms():
    """discover_all result dict includes arxiv, youtube, and podcasts keys."""
    client = GrazerClient()
    # Mock all the network calls to avoid real HTTP
    with patch.object(client, "discover_bottube", return_value=[]):
        with patch.object(client, "discover_moltbook", return_value=[]):
            with patch.object(client, "discover_clawcities", return_value=[]):
                with patch.object(client, "discover_clawsta", return_value=[]):
                    with patch.object(client, "discover_arxiv", return_value=[{"title": "paper"}]):
                        with patch.object(client, "discover_youtube", return_value=[{"title": "vid"}]):
                            with patch.object(client, "discover_podcasts", return_value=[{"name": "show"}]):
                                # Patch remaining platforms to avoid network
                                for m in ["discover_fourclaw", "discover_pinchedin", "discover_clawtasks",
                                           "discover_clawnews", "discover_directory", "discover_agentchan",
                                           "discover_colony", "discover_moltx", "discover_moltexchange"]:
                                    setattr(client, m, Mock(return_value=[]))
                                result = client.discover_all(limit=5)

    assert "arxiv" in result
    assert "youtube" in result
    assert "podcasts" in result
    assert len(result["arxiv"]) == 1
    assert len(result["youtube"]) == 1
    assert len(result["podcasts"]) == 1


# ─── CLI Integration ───────────────────────────────────────


def test_cli_discover_arxiv():
    """CLI discover --platform arxiv renders paper output."""
    mock_client = Mock()
    mock_client.discover_arxiv.return_value = [
        {
            "title": "Test Paper on AI",
            "authors": ["Author One", "Author Two"],
            "url": "https://arxiv.org/abs/2401.00001",
            "published": "2024-01-15T00:00:00Z",
            "categories": ["cs.AI"],
        }
    ]

    args = Namespace(
        platform="arxiv",
        category=None,
        submolt="tech",
        board=None,
        limit=5,
    )
    with patch("grazer.cli.load_config", return_value={}):
        with patch("grazer.cli._make_client", return_value=mock_client):
            output = io.StringIO()
            with redirect_stdout(output):
                cli.cmd_discover(args)

    text = output.getvalue()
    assert "ArXiv Papers" in text
    assert "Test Paper on AI" in text
    assert "Author One" in text


def test_cli_discover_youtube():
    """CLI discover --platform youtube renders video output."""
    mock_client = Mock()
    mock_client.discover_youtube.return_value = [
        {
            "title": "AI Tutorial",
            "channel": "TechChan",
            "url": "https://www.youtube.com/watch?v=abc123",
            "views": 5000,
        }
    ]

    args = Namespace(
        platform="youtube",
        category=None,
        submolt="tech",
        board=None,
        limit=5,
    )
    with patch("grazer.cli.load_config", return_value={}):
        with patch("grazer.cli._make_client", return_value=mock_client):
            output = io.StringIO()
            with redirect_stdout(output):
                cli.cmd_discover(args)

    text = output.getvalue()
    assert "YouTube Videos" in text
    assert "AI Tutorial" in text
    assert "TechChan" in text


def test_cli_discover_podcasts():
    """CLI discover --platform podcasts renders podcast output."""
    mock_client = Mock()
    mock_client.discover_podcasts.return_value = [
        {
            "name": "Future AI Show",
            "artist": "Host Name",
            "genre": "Technology",
            "episode_count": 50,
            "url": "https://podcasts.apple.com/podcast/99999",
        }
    ]

    args = Namespace(
        platform="podcasts",
        category=None,
        submolt="tech",
        board=None,
        limit=5,
    )
    with patch("grazer.cli.load_config", return_value={}):
        with patch("grazer.cli._make_client", return_value=mock_client):
            output = io.StringIO()
            with redirect_stdout(output):
                cli.cmd_discover(args)

    text = output.getvalue()
    assert "Podcasts" in text
    assert "Future AI Show" in text
    assert "Host Name" in text
    assert "50 episodes" in text
