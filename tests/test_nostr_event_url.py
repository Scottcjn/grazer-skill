"""Regression test for #385: normalized Nostr event URLs must keep full identity.

`_normalize_event` built ``https://nostr.band/note{event_id[:8]}`` — only the
first 8 hex chars of a 32-byte (64-hex) event id — so two distinct events that
share an 8-char prefix collapsed to the same navigation URL, discarding 224
bits of identity. The normalized ``id`` field already preserved the full id;
the URL must too.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from grazer.nostr_grazer import _normalize_event  # noqa: E402

PREFIX = "deadbeef"
ID_A = PREFIX + "1" * 56
ID_B = PREFIX + "2" * 56


def _event(event_id):
    return _normalize_event(
        {"id": event_id, "kind": 1, "pubkey": "0" * 64, "content": "fixture", "created_at": 1, "tags": []}
    )


def test_full_event_id_is_preserved_in_url():
    assert _event(ID_A)["url"] == f"https://nostr.band/note{ID_A}"


def test_distinct_events_sharing_prefix_do_not_collide():
    url_a = _event(ID_A)["url"]
    url_b = _event(ID_B)["url"]
    assert url_a != url_b
    assert ID_A in url_a and ID_B in url_b


def test_missing_id_yields_empty_url():
    assert _normalize_event({"kind": 1, "tags": []})["url"] == ""
