"""Shared pytest fixtures for the Grazer test suite.

Unit tests must never reach the real internet. A test that silently falls
through to a live endpoint passes or fails depending on what that platform
happens to return today (and how fast), which is how the CLI discover tests
ended up asserting against live ArXiv/YouTube/iTunes data on main.

The guard sits on ``HTTPAdapter.send`` -- the lowest layer requests uses -- so
any test that mocks a client method, ``requests.get``, or a session still
works; only an *unmocked* request reaches the guard and fails loudly.
"""

import pytest
import requests.adapters


class UnexpectedNetworkCall(AssertionError):
    """Raised when a unit test attempts a real HTTP request."""


@pytest.fixture(autouse=True)
def _block_real_http(monkeypatch):
    def _refuse(self, request, *args, **kwargs):
        raise UnexpectedNetworkCall(
            f"unit test attempted a real HTTP request: {request.method} {request.url}"
        )

    monkeypatch.setattr(requests.adapters.HTTPAdapter, "send", _refuse)
    yield
