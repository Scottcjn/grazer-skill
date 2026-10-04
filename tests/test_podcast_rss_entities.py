"""Regression test for #384: podcast RSS fields must be XML-decoded.

`_parse_podcast_rss` extracted regex capture text verbatim, so XML entities
leaked into consumer fields: an enclosure URL spelled
``...episode=1&amp;sig=abc`` kept the literal ``&amp;`` (changing query-parameter
identity) and a title ``A &amp; B`` stayed escaped. `youtube_grazer.py` already
uses `html.unescape`; the podcast parser now matches it.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from grazer.podcast_grazer import _parse_podcast_rss  # noqa: E402

RSS = """<?xml version="1.0"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>Feed</title>
    <item>
      <title>A &amp; B &lt;live&gt;</title>
      <description>Tom &amp; Jerry</description>
      <pubDate>Mon, 01 Jan 2026 00:00:00 GMT</pubDate>
      <enclosure url="https://example.invalid/audio.mp3?episode=1&amp;sig=abc" type="audio/mpeg" length="1"/>
      <itunes:duration>42:00</itunes:duration>
      <link>https://example.invalid/ep1?x=1&amp;y=2</link>
      <itunes:episode>7</itunes:episode>
    </item>
  </channel>
</rss>
"""


def test_entities_are_decoded():
    episodes = _parse_podcast_rss(RSS)
    assert len(episodes) == 1
    ep = episodes[0]
    assert ep["title"] == "A & B <live>"
    assert ep["description"] == "Tom & Jerry"
    assert ep["audio_url"] == "https://example.invalid/audio.mp3?episode=1&sig=abc"
    assert ep["url"] == "https://example.invalid/ep1?x=1&y=2"


def test_plain_feed_unchanged():
    plain = """<rss><channel><item><title>Hello World</title>
    <enclosure url="https://example.invalid/a.mp3" type="audio/mpeg"/></item></channel></rss>"""
    ep = _parse_podcast_rss(plain)[0]
    assert ep["title"] == "Hello World"
    assert ep["audio_url"] == "https://example.invalid/a.mp3"
