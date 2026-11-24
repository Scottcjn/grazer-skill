# SPDX-License-Identifier: MIT
"""Regression tests for ArxivGrazer query encoding, HTTPS endpoint, and XML entity parsing."""

from unittest.mock import Mock, patch

from grazer.arxiv_grazer import ARXIV_API_BASE, ArxivGrazer, _parse_atom_entries


SAMPLE_ATOM_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry xml:base="https://arxiv.org/">
    <id>http://arxiv.org/abs/2501.01234v1</id>
    <published>2025-01-03T12:00:00Z</published>
    <updated>2025-01-04T08:00:00Z</updated>
    <title type="html">Agents &amp; Benchmarks: Rock &amp; Roll &lt;v2&gt;</title>
    <summary>Compares A &amp; B with &quot;quotes&quot; &amp;#39;safe&amp;#39;.</summary>
    <author><name>Alice &amp; Bob</name></author>
    <link href="https://arxiv.org/pdf/2501.01234v1?download=1&amp;fmt=pdf" title="pdf" rel="related"/>
    <category term="cs.AI"/>
  </entry>
</feed>
"""


def test_arxiv_base_uses_https():
    assert ARXIV_API_BASE.startswith("https://")


def test_discover_joins_query_and_category_with_spaces_not_plus():
    grazer = ArxivGrazer(timeout=5)
    mock_resp = Mock()
    mock_resp.text = SAMPLE_ATOM_XML
    mock_resp.raise_for_status = Mock()

    with patch.object(grazer.session, "get", return_value=mock_resp) as mock_get:
        papers = grazer.discover(query="transformer", category="ai", limit=5)

    assert len(papers) == 1
    params = mock_get.call_args[1]["params"]
    assert params["search_query"] == "all:transformer AND cat:cs.AI"
    assert "+AND+" not in params["search_query"]


def test_parse_atom_entries_unescapes_entities_and_handles_attribute_order():
    papers = _parse_atom_entries(SAMPLE_ATOM_XML)
    assert len(papers) == 1
    paper = papers[0]
    assert paper["title"] == "Agents & Benchmarks: Rock & Roll <v2>"
    assert "&quot;" not in paper["summary"]
    assert '"quotes"' in paper["summary"]
    assert paper["authors"] == ["Alice & Bob"]
    assert paper["pdf_url"] == "https://arxiv.org/pdf/2501.01234v1?download=1&fmt=pdf"
    assert paper["categories"] == ["cs.AI"]
