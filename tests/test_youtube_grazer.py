"""Regression tests for YouTube RSS text decoding."""

from grazer.youtube_grazer import _parse_youtube_rss


def test_youtube_rss_decodes_xml_entities_in_text_fields():
    xml = """
    <feed xmlns:yt="http://www.youtube.com/xml/schemas/2015"
          xmlns:media="http://search.yahoo.com/mrss/">
      <entry>
        <yt:videoId>abc123def45</yt:videoId>
        <title>Tom &amp; Jerry &#39;Test&#39;</title>
        <author><name>Rock &amp; Roll</name></author>
        <published>2026-09-12T00:00:00+00:00</published>
        <media:description>A &lt;useful&gt; &amp; clear summary</media:description>
        <media:thumbnail url="https://example.com/thumb?a=1&amp;b=2"/>
        <media:statistics views="42"/>
      </entry>
    </feed>
    """

    [video] = _parse_youtube_rss(xml)

    assert video["title"] == "Tom & Jerry 'Test'"
    assert video["channel"] == "Rock & Roll"
    assert video["description"] == "A <useful> & clear summary"
    assert video["thumbnail"] == "https://example.com/thumb?a=1&amp;b=2"
