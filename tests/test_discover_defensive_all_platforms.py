# SPDX-License-Identifier: MIT
"""Additional defensive output tests for ALL remaining discover platforms.

Covers: bottube, fourclaw, pinchedin, pinchedin-jobs, clawtasks, clawnews,
and the status command — all with missing/None fields.
"""
import io
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

from grazer import cli


class DiscoverDefensiveAllPlatformsTests(unittest.TestCase):
    def _run_discover(self, platform: str, client: Mock, board=None) -> str:
        args = Namespace(
            platform=platform,
            category=None,
            submolt="tech",
            board=board,
            limit=5,
        )
        with patch("grazer.cli.load_config", return_value={}):
            with patch("grazer.cli._make_client", return_value=client):
                output = io.StringIO()
                with redirect_stdout(output):
                    cli.cmd_discover(args)
        return output.getvalue()

    # --- BoTTube ---
    def test_bottube_handles_missing_fields(self):
        client = Mock()
        client.discover_bottube.return_value = [{"views": 5}]
        output = self._run_discover("bottube", client)
        self.assertIn("(untitled)", output)
        self.assertIn("unknown", output)  # agent default

    def test_bottube_handles_none_values(self):
        client = Mock()
        client.discover_bottube.return_value = [
            {"title": None, "agent": None, "views": None, "category": None, "stream_url": None, "url": None}
        ]
        output = self._run_discover("bottube", client)
        self.assertIn("BoTTube", output)

    # --- FourClaw ---
    def test_fourclaw_handles_missing_fields(self):
        client = Mock()
        client.discover_fourclaw.return_value = [{"replyCount": 3}]
        output = self._run_discover("fourclaw", client, board="b")
        self.assertIn("(untitled)", output)
        self.assertIn("anon", output)

    def test_fourclaw_handles_none_id(self):
        client = Mock()
        client.discover_fourclaw.return_value = [{"title": "test", "id": None}]
        output = self._run_discover("fourclaw", client, board="b")
        self.assertIn("test", output)

    # --- PinchedIn ---
    def test_pinchedin_handles_missing_author(self):
        client = Mock()
        client.discover_pinchedin.return_value = [{"likesCount": 1, "commentsCount": 0}]
        output = self._run_discover("pinchedin", client)
        self.assertIn("(no content)", output)
        self.assertIn("?", output)

    def test_pinchedin_handles_empty_author_dict(self):
        client = Mock()
        client.discover_pinchedin.return_value = [{"content": "hello", "author": {}}]
        output = self._run_discover("pinchedin", client)
        self.assertIn("hello", output)

    # --- PinchedIn Jobs ---
    def test_pinchedin_jobs_handles_missing_fields(self):
        client = Mock()
        client.discover_pinchedin_jobs.return_value = [{"status": "open"}]
        output = self._run_discover("pinchedin-jobs", client)
        self.assertIn("?", output)
        self.assertIn("open", output)

    def test_pinchedin_jobs_handles_missing_poster(self):
        client = Mock()
        client.discover_pinchedin_jobs.return_value = [{"title": "Dev role", "poster": {}}]
        output = self._run_discover("pinchedin-jobs", client)
        self.assertIn("Dev role", output)

    # --- ClawTasks ---
    def test_clawtasks_handles_missing_fields(self):
        client = Mock()
        client.discover_clawtasks.return_value = [{"tags": None}]
        output = self._run_discover("clawtasks", client)
        self.assertIn("(untitled bounty)", output)

    def test_clawtasks_handles_empty_tags(self):
        client = Mock()
        client.discover_clawtasks.return_value = [
            {"title": "Fix bug", "tags": [], "status": None, "deadline_hours": None}
        ]
        output = self._run_discover("clawtasks", client)
        self.assertIn("Fix bug", output)

    # --- ClawNews ---
    def test_clawnews_handles_missing_fields(self):
        client = Mock()
        client.discover_clawnews.return_value = [{}]
        output = self._run_discover("clawnews", client)
        self.assertIn("ClawNews", output)

    def test_clawnews_handles_headline_fallback(self):
        client = Mock()
        client.discover_clawnews.return_value = [{"title": "Breaking news"}]
        output = self._run_discover("clawnews", client)
        self.assertIn("Breaking news", output)


class StatusDefensiveTests(unittest.TestCase):
    def test_status_handles_missing_fields(self):
        client = Mock()
        client.platform_status.return_value = {
            "bottube": {"ok": True, "latency_ms": 50, "auth_configured": False},
            "broken": {},  # Missing all fields
        }
        args = Namespace(platform="all")
        with patch("grazer.cli.load_config", return_value={}):
            with patch("grazer.cli._make_client", return_value=client):
                output = io.StringIO()
                with redirect_stdout(output):
                    cli.cmd_status(args)
        self.assertIn("bottube", output.getvalue())
        self.assertIn("broken", output.getvalue())


if __name__ == "__main__":
    unittest.main()
