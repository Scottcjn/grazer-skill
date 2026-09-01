import os
import unittest
from unittest.mock import Mock, patch

from grazer import GrazerClient


class RateLimitBackoffTests(unittest.TestCase):
    def _resp(self, status, retry_after=None):
        resp = Mock()
        resp.status_code = status
        resp.headers = {}
        if retry_after is not None:
            resp.headers["Retry-After"] = retry_after
        return resp

    def test_retries_429_then_succeeds(self):
        with patch.dict(os.environ, {"GRAZER_MAX_RETRIES": "2", "GRAZER_BACKOFF_BASE_MS": "100"}, clear=False):
            client = GrazerClient()
        client.session.get = Mock(side_effect=[self._resp(429), self._resp(200)])

        with patch("grazer._time.sleep") as sleep_mock, patch("grazer.random.uniform", return_value=0.0), patch("grazer.logger.warning") as log_mock:
            resp = client._rate_limited_get("https://example.com")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(client.session.get.call_count, 2)
        sleep_mock.assert_called_once_with(0.1)
        log_mock.assert_called_once()

    def test_retry_after_header_wins_over_exponential_backoff(self):
        with patch.dict(os.environ, {"GRAZER_MAX_RETRIES": "1", "GRAZER_BACKOFF_BASE_MS": "100"}, clear=False):
            client = GrazerClient()
        client.session.post = Mock(side_effect=[self._resp(429, retry_after="2.5"), self._resp(200)])

        with patch("grazer._time.sleep") as sleep_mock, patch("grazer.logger.warning"):
            resp = client._rate_limited_post("https://example.com")

        self.assertEqual(resp.status_code, 200)
        sleep_mock.assert_called_once_with(2.5)

    def test_returns_last_429_when_retry_budget_exhausted(self):
        with patch.dict(os.environ, {"GRAZER_MAX_RETRIES": "1", "GRAZER_BACKOFF_BASE_MS": "100"}, clear=False):
            client = GrazerClient()
        client.session.patch = Mock(side_effect=[self._resp(429), self._resp(429)])

        with patch("grazer._time.sleep") as sleep_mock, patch("grazer.random.uniform", return_value=0.0), patch("grazer.logger.warning") as log_mock:
            resp = client._rate_limited_patch("https://example.com")

        self.assertEqual(resp.status_code, 429)
        self.assertEqual(client.session.patch.call_count, 2)
        sleep_mock.assert_called_once_with(0.1)
        log_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
