# SPDX-License-Identifier: MIT
"""Regression tests for Farcaster & Semantic Scholar null guards and URL-safe IDs."""

from unittest.mock import Mock, patch

import pytest

from grazer.farcaster_grazer import FarcasterGrazer, _normalize_cast
from grazer.semantic_scholar_grazer import SemanticScholarGrazer, _normalize_paper


def test_farcaster_handles_null_subobjects_and_null_lists():
    cast = _normalize_cast(
        {
            "hash": None,
            "text": None,
            "author": None,
            "reactions": None,
            "replies": None,
            "channel": None,
        }
    )
    assert cast["hash"] == ""
    assert cast["author_username"] == ""
    assert cast["likes"] == 0
    assert cast["replies"] == 0
    assert cast["channel"] == ""

    grazer = FarcasterGrazer(timeout=5)
    mock_resp = Mock()
    mock_resp.raise_for_status = Mock()
    mock_resp.json.side_effect = [
        {"result": None, "casts": None},
        {"casts": None},
        {"casts": [None, {"author": None, "replies": None}]},
    ]
    with patch.object(grazer.session, "get", return_value=mock_resp):
        assert grazer.discover(query="ai") == []
        assert grazer.trending() == []
        ch = grazer.channel("ai")
        assert len(ch) == 1
        assert ch[0]["replies"] == 0


def test_semantic_scholar_handles_null_fields_and_encodes_ids():
    paper = _normalize_paper(
        {
            "paperId": None,
            "title": None,
            "abstract": None,
            "authors": [None, {"name": "Ada"}],
            "openAccessPdf": None,
        }
    )
    assert paper["authors"] == ["Ada"]
    assert paper["pdf_url"] == ""
    assert paper["abstract"] == ""

    grazer = SemanticScholarGrazer(timeout=5)
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = Mock()
    mock_resp.json.side_effect = [
        {"data": None},
        {
            "paperId": "p1",
            "title": "Test",
            "citations": [{"citingPaper": None}],
            "references": None,
        },
        {"authorId": "a b", "name": "Researcher"},
        {"data": None},
    ]

    with patch.object(grazer.session, "get", return_value=mock_resp) as mock_get:
        assert grazer.discover(query="x") == []
        one = grazer.get_paper("arXiv:2401.12345")
        assert one["title"] == "Test"
        assert len(one["citations"]) == 1
        assert one["references"] == []

        author = grazer.get_author("123?admin=1")
        assert author is not None
        author_url = mock_get.call_args_list[-2][0][0]
        assert author_url.endswith("/author/123%3Fadmin%3D1")


@pytest.mark.parametrize("bad_id", ["", "   ", ".", "..", "10.1234/../../etc/passwd"])
def test_semantic_scholar_rejects_traversal_and_blank_ids(bad_id):
    grazer = SemanticScholarGrazer(timeout=5)
    with patch.object(grazer.session, "get", side_effect=AssertionError("must not call HTTP")):
        with pytest.raises(ValueError):
            grazer.get_paper(bad_id)


def test_semantic_scholar_allows_doi_with_slash():
    grazer = SemanticScholarGrazer(timeout=5)
    mock_resp = Mock()
    mock_resp.status_code = 404
    with patch.object(grazer.session, "get", return_value=mock_resp) as mock_get:
        assert grazer.get_paper("10.1038/nature12373") is None
    assert mock_get.call_args[0][0].endswith("/paper/10.1038/nature12373")
