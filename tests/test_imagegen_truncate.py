"""Regression test for #386: template SVG truncation must not split XML entities.

`sanitize_svg_text` XML-escapes text, and `_truncate` used to slice the *escaped*
string, so a title whose escaped form had an entity straddling the cutoff (e.g.
``'x'*18 + '&y'`` -> ``...x&amp;y`` cut to ``...x&~``) produced a document that
ElementTree rejects as not well-formed. Truncate the plain text first, then
escape, so every emitted entity stays complete.
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from grazer.imagegen import generate_template_svg  # noqa: E402

TEMPLATES = ["circuit", "wave", "grid", "badge", "terminal"]


def test_entity_straddling_cutoff_is_well_formed():
    """The reported failure: escaped '&' at the truncation boundary."""
    svg = generate_template_svg("x" * 18 + "&y", template="circuit")
    ET.fromstring(svg)  # raises ParseError before the fix


def test_plain_and_short_controls_still_parse():
    for prompt in ["x" * 20, "A & B", "short title"]:
        svg = generate_template_svg(prompt, template="circuit")
        ET.fromstring(svg)


def test_all_templates_well_formed_with_entity_boundary_text():
    for template in TEMPLATES:
        svg = generate_template_svg("x" * 18 + "&y", template=template)
        ET.fromstring(svg)


def test_no_dangling_ampersand_in_output():
    svg = generate_template_svg("x" * 18 + "&y", template="circuit")
    # every '&' must begin a complete entity
    import re

    assert all(re.match(r"&(amp|lt|gt|quot|#39);", svg[i:]) for i in (m.start() for m in re.finditer("&", svg)))
