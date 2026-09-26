"""Shared pytest fixtures for the Grazer test suite.

Unit tests must never reach the real internet. A test that silently falls
through to a live endpoint passes or fails depending on what that platform
happens to return today (and how fast), which is how the CLI discover tests
ended up asserting against live ArXiv/YouTube/iTunes data on main.

The guard sits on ``HTTPAdapter.send`` -- the lowest layer requests uses -- so
any test that mocks a client method, ``requests.get``, or a session still
works; only an *unmocked* request reaches the guard.

Raising alone is not enough: GrazerClient's discover_* methods wrap their
requests in ``except Exception`` and return ``[]``, so the guard's exception
would be swallowed and the test would stay green. The fixture therefore also
*records* every guarded request and fails the test at teardown if any were
attempted, regardless of whether the application code caught the exception.
"""

import pytest
import requests.adapters


class UnexpectedNetworkCall(AssertionError):
    """Raised when a unit test attempts a real HTTP request."""


@pytest.fixture(autouse=True)
def _block_real_http(monkeypatch):
    attempted = []

    def _refuse(self, request, *args, **kwargs):
        attempted.append(f"{request.method} {request.url}")
        raise UnexpectedNetworkCall(
            f"unit test attempted a real HTTP request: {request.method} {request.url}"
        )

    monkeypatch.setattr(requests.adapters.HTTPAdapter, "send", _refuse)
    yield attempted
    if attempted:
        pytest.fail(
            "unit test attempted real HTTP request(s) (blocked, but the mock is "
            "missing):\n  " + "\n  ".join(attempted),
            pytrace=False,
        )
