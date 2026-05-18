import json
from unittest.mock import patch

from grazer import cli


def test_load_idempotency_cache_handles_missing_invalid_and_non_object_json(tmp_path):
    missing_path = tmp_path / "missing" / "idempotency_keys.json"
    assert cli._load_idempotency_cache(missing_path) == {}

    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text("{not-json")
    assert cli._load_idempotency_cache(invalid_path) == {}

    list_path = tmp_path / "list.json"
    list_path.write_text(json.dumps(["scope:key", 123]))
    assert cli._load_idempotency_cache(list_path) == {}


def test_save_idempotency_cache_creates_parent_directory_and_round_trips_json(tmp_path):
    cache_path = tmp_path / "nested" / "cache" / "idempotency_keys.json"
    cache = {"post:abc": 1000.0, "comment:def": 1001.5}

    cli._save_idempotency_cache(cache, cache_path)

    assert cache_path.exists()
    assert json.loads(cache_path.read_text()) == cache


def test_cleanup_idempotency_cache_keeps_only_numeric_unexpired_entries():
    cache = {
        "fresh": 990.0,
        "boundary": 900.0,
        "expired": 899.9,
        "string-ts": "995",
        "none-ts": None,
    }

    cleaned = cli._cleanup_idempotency_cache(cache, ttl_seconds=100, now_ts=1000.0)

    assert cleaned == {"fresh": 990.0, "boundary": 900.0}


def test_idempotency_duplicate_cleans_cache_before_lookup():
    cache = {
        "post:abc": 990.0,
        "post:old": 100.0,
        "post:bad": "not-a-number",
    }

    with patch("grazer.cli._load_idempotency_cache", return_value=cache):
        with patch("grazer.cli.time.time", return_value=1000.0):
            with patch("grazer.cli._save_idempotency_cache") as save_mock:
                assert cli._idempotency_is_duplicate("post", "abc", ttl_seconds=100) is True

    save_mock.assert_called_once_with({"post:abc": 990.0})


def test_idempotency_duplicate_short_circuits_empty_key():
    with patch("grazer.cli._load_idempotency_cache") as load_mock:
        assert cli._idempotency_is_duplicate("post", "", ttl_seconds=100) is False

    load_mock.assert_not_called()


def test_idempotency_mark_records_current_time_after_cleanup():
    cache = {
        "post:old": 100.0,
        "post:existing": 990.0,
    }

    with patch("grazer.cli._load_idempotency_cache", return_value=cache):
        with patch("grazer.cli.time.time", return_value=1000.0):
            with patch("grazer.cli._save_idempotency_cache") as save_mock:
                cli._idempotency_mark("post", "new", ttl_seconds=100)

    save_mock.assert_called_once_with({"post:existing": 990.0, "post:new": 1000.0})


def test_idempotency_mark_short_circuits_empty_key():
    with patch("grazer.cli._load_idempotency_cache") as load_mock:
        cli._idempotency_mark("post", None, ttl_seconds=100)

    load_mock.assert_not_called()
