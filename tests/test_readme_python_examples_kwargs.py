# SPDX-License-Identifier: MIT
"""Python examples in the docs must only pass kwargs GrazerClient accepts.

GrazerClient.__init__ has no **kwargs, so a mis-cased keyword in a copied
example (e.g. ``ClawCities_key=`` instead of ``clawcities_key=``) raises
TypeError at construction time.
"""

import ast
import inspect
import re
from pathlib import Path

import pytest

from grazer import GrazerClient

ROOT = Path(__file__).resolve().parent.parent
DOCS = ["README.md", "SKILL.md", "INTEGRATION.md"]
PY_BLOCK = re.compile(r"^```python\n(.*?)^```", re.S | re.M)


def _grazer_client_calls(doc):
    """Yield (block_index, [kwarg names]) for each GrazerClient(...) call."""
    text = (ROOT / doc).read_text(encoding="utf-8")
    for index, block in enumerate(PY_BLOCK.findall(text)):
        try:
            tree = ast.parse(block)
        except SyntaxError:
            # Illustrative fragments that are not valid Python on their own.
            continue
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "GrazerClient"
            ):
                yield index, [kw.arg for kw in node.keywords if kw.arg is not None]


def _accepted_kwargs():
    params = inspect.signature(GrazerClient.__init__).parameters
    assert not any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values())
    return {name for name in params if name != "self"}


@pytest.mark.parametrize("doc", DOCS)
def test_doc_grazer_client_examples_use_valid_kwargs(doc):
    accepted = _accepted_kwargs()
    bad = [
        (index, kwarg)
        for index, kwargs in _grazer_client_calls(doc)
        for kwarg in kwargs
        if kwarg not in accepted
    ]
    assert not bad, f"{doc}: GrazerClient() examples use unknown kwargs {bad}"


def test_readme_constructor_example_is_checked():
    # Guard against the parser silently skipping the main README example.
    calls = list(_grazer_client_calls("README.md"))
    assert any("clawcities_key" in kwargs for _, kwargs in calls)
