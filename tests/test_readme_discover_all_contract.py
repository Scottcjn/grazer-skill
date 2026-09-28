# SPDX-License-Identifier: MIT
"""The README's "What `all` covers" list must match discover_all()'s providers.

`grazer discover -p all` / `discover_all()` is a behavioural contract that
automation relies on. The README previously claimed 24 providers while
discover_all() traversed 22; this test keeps the documented set in lockstep
with the code.
"""

import re
from pathlib import Path
from unittest.mock import Mock

from grazer import GrazerClient

README = Path(__file__).resolve().parent.parent / "README.md"
META_KEYS = {"_errors", "_health", "_canonical"}


def _documented_providers():
    text = README.read_text(encoding="utf-8")
    match = re.search(r"^### What `all` covers\n(.*?)^### ", text, re.S | re.M)
    assert match, "README is missing the '### What `all` covers' section"
    section = match.group(1)
    # The provider list is the paragraph of back-ticked keys ending in `nostr`.
    listing = re.search(r"((?:`[a-z_]+`,\s*)+`[a-z_]+`)\s*\n\n", section)
    assert listing, "could not find the back-ticked provider list"
    return re.findall(r"`([a-z_]+)`", listing.group(1))


def _discover_all_providers():
    client = GrazerClient()
    for name in dir(client):
        if name.startswith("discover_") and name != "discover_all":
            setattr(client, name, Mock(return_value=[]))
    result = client.discover_all(limit=1)
    assert not result["_errors"], result["_errors"]
    return [key for key in result if key not in META_KEYS]


def test_readme_discover_all_list_matches_code():
    documented = _documented_providers()
    assert len(documented) == len(set(documented)), "duplicate provider in README list"
    assert set(documented) == set(_discover_all_providers())


def test_readme_discover_all_count_matches_code():
    text = README.read_text(encoding="utf-8")
    count = len(_discover_all_providers())
    match = re.search(r"^### What `all` covers\n(.*?)^### ", text, re.S | re.M)
    assert f"**{count}** of them" in match.group(1)
