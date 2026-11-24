# SPDX-License-Identifier: MIT
from unittest.mock import Mock

from grazer import GrazerClient
from grazer.imagegen import generate_svg, generate_template_svg


LLM_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect width="10" height="10"/></svg>'


def test_forced_template_skips_llm(monkeypatch):
    llm_mock = Mock(return_value=LLM_SVG)
    monkeypatch.setattr("grazer.imagegen.generate_llm_svg", llm_mock)

    result = generate_svg(
        "a red fox",
        llm_url="https://llm.invalid/v1",
        template="circuit",
    )

    assert result["method"] == "template"
    assert result["svg"] == generate_template_svg("a red fox", template="circuit")
    llm_mock.assert_not_called()


def test_forced_palette_skips_llm(monkeypatch):
    llm_mock = Mock(return_value=LLM_SVG)
    monkeypatch.setattr("grazer.imagegen.generate_llm_svg", llm_mock)

    result = generate_svg(
        "a red fox",
        llm_url="https://llm.invalid/v1",
        palette="crypto",
    )

    assert result["method"] == "template"
    assert result["svg"] == generate_template_svg("a red fox", palette="crypto")
    llm_mock.assert_not_called()


def test_forced_template_and_palette_via_client(monkeypatch):
    llm_mock = Mock(return_value=LLM_SVG)
    monkeypatch.setattr("grazer.imagegen.generate_llm_svg", llm_mock)

    client = GrazerClient(llm_url="https://llm.invalid/v1")
    result = client.generate_image("a red fox", template="circuit", palette="crypto")

    assert result["method"] == "template"
    assert result["svg"] == generate_template_svg(
        "a red fox", template="circuit", palette="crypto"
    )
    llm_mock.assert_not_called()


def test_unforced_svg_still_prefers_llm(monkeypatch):
    llm_mock = Mock(return_value=LLM_SVG)
    monkeypatch.setattr("grazer.imagegen.generate_llm_svg", llm_mock)

    result = generate_svg("a red fox", llm_url="https://llm.invalid/v1")

    assert result["method"] == "llm"
    assert result["svg"] == LLM_SVG
    llm_mock.assert_called_once()
