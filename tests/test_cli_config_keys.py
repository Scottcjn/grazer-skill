"""`grazer post` / `grazer comment` must use every API key in ~/.grazer/config.json.

Regression: cmd_post and cmd_comment built their own GrazerClient with a
hand-picked subset of keys, so a configured thecolony / moltx / moltexchange /
agentchan key was silently dropped. Posting to those platforms then failed
with "... API key required" (or, for AgentChan, went out unauthenticated)
even though the user had configured the key.
"""

import io
from argparse import Namespace
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

import pytest

from grazer import GrazerClient, cli

CONFIG = {
    "thecolony": {"api_key": "colony-test-key"},
    "moltx": {"api_key": "moltx-test-key"},
    "moltexchange": {"api_key": "mx-test-key"},
    "agentchan": {"api_key": "agentchan-test-key"},
}


def _ok_response(payload):
    resp = Mock()
    resp.ok = True
    resp.status_code = 200
    resp.json.return_value = payload
    resp.raise_for_status.return_value = None
    return resp


def _post_args(platform, board=None):
    return Namespace(
        platform=platform,
        board=board,
        title="Title",
        message="hello",
        image=None,
        template=None,
        palette=None,
        dry_run=False,
        idempotency_key=None,
        idempotency_ttl=86400,
    )


def _run(fn, args, sent):
    def fake_request(self, method, url, **kwargs):
        sent.append((method, url, kwargs.get("headers") or {}))
        if url.endswith("/auth/token"):
            return _ok_response({"access_token": "jwt-from-colony"})
        return _ok_response({"id": "new-id"})

    with patch("grazer.cli.load_config", return_value=CONFIG), \
            patch.object(GrazerClient, "_request_with_backoff", fake_request):
        out = io.StringIO()
        with redirect_stdout(out):
            fn(args)
    return out.getvalue()


@pytest.mark.parametrize(
    "platform,expected_token",
    [
        ("moltx", "moltx-test-key"),
        ("moltexchange", "mx-test-key"),
        ("agentchan", "agentchan-test-key"),
        ("thecolony", "jwt-from-colony"),
    ],
)
def test_post_uses_configured_key(platform, expected_token):
    sent = []
    output = _run(cli.cmd_post, _post_args(platform), sent)

    assert sent, "post was never sent"
    method, url, headers = sent[-1]
    assert method == "POST"
    assert headers.get("Authorization") == f"Bearer {expected_token}"
    assert "✓" in output


def test_colony_reply_uses_configured_key():
    sent = []
    args = Namespace(
        platform="thecolony",
        target="post-123",
        message="hello",
        dry_run=False,
        idempotency_key=None,
        idempotency_ttl=86400,
    )
    output = _run(cli.cmd_comment, args, sent)

    method, url, headers = sent[-1]
    assert url.endswith("/posts/post-123/replies")
    assert headers.get("Authorization") == "Bearer jwt-from-colony"
    assert "✓ Reply posted" in output
