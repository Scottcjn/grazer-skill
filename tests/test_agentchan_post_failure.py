"""A failed AgentChan post must not look like success.

Regression: post_agentchan() returns None on any failure, but cmd_post
recorded the idempotency key *before* checking the result and then returned
normally. A failed send therefore (1) exited 0, so cron/agent callers saw
success, and (2) burned the idempotency key, so the retry with the same key
was skipped as a "duplicate" for the whole TTL -- the post never went out.
"""

import io
from argparse import Namespace
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import Mock, patch

import pytest

from grazer import cli


def _args():
    return Namespace(
        platform="agentchan",
        board="ai",
        title="Title",
        message="hello",
        image=None,
        template=None,
        palette=None,
        dry_run=False,
        idempotency_key="retry-me",
        idempotency_ttl=86400,
    )


def _run(result, cache_path):
    client = Mock()
    client.post_agentchan.return_value = result
    out, err = io.StringIO(), io.StringIO()
    with patch("grazer.cli.load_config", return_value={}), \
            patch("grazer.cli._make_client", return_value=client), \
            patch("grazer.cli._idempotency_cache_path", return_value=cache_path), \
            redirect_stdout(out), redirect_stderr(err):
        try:
            cli.cmd_post(_args())
            code = 0
        except SystemExit as exc:
            code = exc.code
    return client, code, out.getvalue() + err.getvalue()


def test_failed_agentchan_post_exits_nonzero(tmp_path):
    _, code, output = _run(None, tmp_path / "keys.json")
    assert code not in (0, None)
    assert "Failed to post on AgentChan" in output


def test_failed_agentchan_post_does_not_burn_idempotency_key(tmp_path):
    cache = tmp_path / "keys.json"
    _run(None, cache)

    # The retry with the same key must actually attempt the send again.
    client, code, output = _run({"data": {"id": 42}}, cache)
    client.post_agentchan.assert_called_once()
    assert "Idempotency hit" not in output
    assert code in (0, None)


def test_successful_agentchan_post_marks_key(tmp_path):
    cache = tmp_path / "keys.json"
    _, code, _ = _run({"data": {"id": 42}}, cache)
    assert code in (0, None)

    client, _, output = _run({"data": {"id": 43}}, cache)
    client.post_agentchan.assert_not_called()
    assert "Idempotency hit" in output


@pytest.mark.parametrize("empty_body", [{}, []])
def test_empty_2xx_body_counts_as_sent_and_marks_key(tmp_path, empty_body):
    """post_agentchan returns resp.json() on any 2xx, so a falsy body is a
    delivered post. It must exit 0 and record the key, otherwise an automated
    retry with the same key would create a duplicate thread."""
    cache = tmp_path / "keys.json"
    _, code, output = _run(empty_body, cache)
    assert code in (0, None)
    assert "Failed to post on AgentChan" not in output

    client, _, output = _run({"data": {"id": 43}}, cache)
    client.post_agentchan.assert_not_called()
    assert "Idempotency hit" in output
