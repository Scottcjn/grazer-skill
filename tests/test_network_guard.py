"""The conftest network guard must catch requests the app code swallows.

GrazerClient.discover_* wrap their HTTP calls in ``except Exception`` and
return []. If the guard only raised, a test with a missing mock would stay
green while its requests were silently blocked. The guard therefore records
every attempt so the fixture can fail the test at teardown.
"""

import requests


def _swallowing_fetch(url):
    try:
        requests.get(url, timeout=1)
    except Exception:
        return []
    return ["unreachable"]


def test_guard_records_requests_that_app_code_swallows(_block_real_http):
    attempted = _block_real_http
    assert _swallowing_fetch("https://example.invalid/probe") == []
    assert attempted == ["GET https://example.invalid/probe"]
    # Clear so this deliberate probe does not fail the teardown check.
    attempted.clear()
