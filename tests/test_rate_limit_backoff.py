"""
Unit tests for Grazer HTTP rate-limiting 429 exponential backoff strategy.
"""

import os
import time
import unittest
from unittest.mock import MagicMock, patch
import requests

from grazer import GrazerClient, _compute_backoff_delay


class TestRateLimitBackoff(unittest.TestCase):
    def setUp(self):
        self.client = GrazerClient(max_retries=3, backoff_base_ms=100)

    def test_compute_backoff_delay_exponential(self):
        """Test exponential growth of backoff delay with base_ms."""
        d0 = _compute_backoff_delay(None, attempt=0, base_ms=1000)
        d1 = _compute_backoff_delay(None, attempt=1, base_ms=1000)
        d2 = _compute_backoff_delay(None, attempt=2, base_ms=1000)

        # Base values should be ~1.0, ~2.0, ~4.0 (+ jitter up to 10%)
        self.assertGreaterEqual(d0, 1.0)
        self.assertLess(d0, 1.2)

        self.assertGreaterEqual(d1, 2.0)
        self.assertLess(d1, 2.3)

        self.assertGreaterEqual(d2, 4.0)
        self.assertLess(d2, 4.5)

    def test_compute_backoff_delay_retry_after_integer(self):
        """Test parsing integer seconds from Retry-After header."""
        resp = MagicMock(spec=requests.Response)
        resp.headers = {"Retry-After": "5"}

        delay = _compute_backoff_delay(resp, attempt=0, base_ms=1000)
        self.assertEqual(delay, 5.0)

    @patch("time.sleep")
    def test_retry_success_after_429(self, mock_sleep):
        """Test that a 429 response triggers backoff and retries successfully."""
        resp_429 = MagicMock(spec=requests.Response)
        resp_429.status_code = 429
        resp_429.headers = {"Retry-After": "1"}

        resp_200 = MagicMock(spec=requests.Response)
        resp_200.status_code = 200

        with patch.object(self.client.session, "request", side_effect=[resp_429, resp_200]) as mock_req:
            res = self.client._rate_limited_get("https://api.test.com/endpoint")
            self.assertEqual(res.status_code, 200)
            self.assertEqual(mock_req.call_count, 2)
            mock_sleep.assert_called_once_with(1.0)

    @patch("time.sleep")
    def test_retry_budget_exhaustion(self, mock_sleep):
        """Test that 429 stops after max_retries attempts."""
        resp_429 = MagicMock(spec=requests.Response)
        resp_429.status_code = 429
        resp_429.headers = {}

        client = GrazerClient(max_retries=2, backoff_base_ms=10)

        with patch.object(client.session, "request", return_value=resp_429) as mock_req:
            res = client._rate_limited_get("https://api.test.com/endpoint")
            self.assertEqual(res.status_code, 429)
            # Initial attempt + 2 retries = 3 total calls
            self.assertEqual(mock_req.call_count, 3)
            self.assertEqual(mock_sleep.call_count, 2)

    @patch.dict(os.environ, {"GRAZER_MAX_RETRIES": "1", "GRAZER_BACKOFF_BASE_MS": "50"})
    @patch("time.sleep")
    def test_env_var_configuration(self, mock_sleep):
        """Test that GRAZER_MAX_RETRIES and GRAZER_BACKOFF_BASE_MS env vars take effect."""
        client = GrazerClient()
        self.assertEqual(client.max_retries, 1)
        self.assertEqual(client.backoff_base_ms, 50)

        resp_429 = MagicMock(spec=requests.Response)
        resp_429.status_code = 429
        resp_429.headers = {}

        with patch.object(client.session, "request", return_value=resp_429) as mock_req:
            res = client._rate_limited_post("https://api.test.com/post", json={"msg": "hello"})
            self.assertEqual(res.status_code, 429)
            # Initial + 1 retry = 2 calls
            self.assertEqual(mock_req.call_count, 2)
            self.assertEqual(mock_sleep.call_count, 1)


if __name__ == "__main__":
    unittest.main()
