import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from grazer import imagegen


def test_sanitize_svg_text_strips_active_svg_vectors_and_escapes_xml():
    raw = '<script>alert(1)</script><text onload="steal()">A&B "quoted" javascript:alert(2)</text>'

    sanitized = imagegen.sanitize_svg_text(raw)

    assert "script" not in sanitized.lower()
    assert "onload" not in sanitized.lower()
    assert "javascript:" not in sanitized.lower()
    assert "&amp;" in sanitized
    assert "&quot;quoted&quot;" in sanitized
    assert "&lt;text" in sanitized


def test_truncate_sanitizes_before_applying_limit():
    truncated = imagegen._truncate("<b>abcdef</b>", 8)

    assert len(truncated) == 8
    assert truncated.endswith("~")
    assert "<" not in truncated


def test_validate_svg_adds_namespace_and_rejects_bad_payloads():
    svg = imagegen._validate_svg("<svg><text>ok</text></svg>")
    assert imagegen.SVG_NAMESPACE in svg

    with pytest.raises(ValueError, match="not valid SVG"):
        imagegen._validate_svg("<html></html>")

    oversized = f"<svg>{'x' * (imagegen.SVG_MAX_BYTES + 1)}</svg>"
    with pytest.raises(ValueError, match="4KB limit"):
        imagegen._validate_svg(oversized)


def test_generate_template_svg_uses_sanitized_prompt_text():
    svg = imagegen.generate_template_svg(
        'badge <script>alert(1)</script> & "launch"',
        template="badge",
        palette="tech",
    )

    assert svg.startswith("<svg")
    assert imagegen.SVG_NAMESPACE in svg
    assert "script" not in svg.lower()
    assert "javascript:" not in svg.lower()
    assert "&amp;" in svg
    assert "&quot;" in svg
    assert len(svg.encode("utf-8")) <= imagegen.SVG_MAX_BYTES
