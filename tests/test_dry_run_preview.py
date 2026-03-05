import io
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

from grazer import cli


class DryRunPreviewTests(unittest.TestCase):
    def test_comment_dry_run_pinchedin_does_not_publish(self):
        args = Namespace(
            platform="pinchedin",
            target="post-123",
            message="hello dry run",
            dry_run=True,
        )
        fake_client = Mock()

        with patch("grazer.cli.load_config", return_value={}):
            with patch("grazer.cli.GrazerClient", return_value=fake_client):
                out = io.StringIO()
                with redirect_stdout(out):
                    cli.cmd_comment(args)

        output = out.getvalue()
        self.assertIn("Dry-run preview", output)
        self.assertIn('"post_id": "post-123"', output)
        fake_client.comment_pinchedin.assert_not_called()

    def test_post_dry_run_clawtasks_does_not_publish(self):
        args = Namespace(
            platform="clawtasks",
            board="security,python",
            title="Task title",
            message="Task description",
            image=None,
            template=None,
            palette=None,
            dry_run=True,
        )
        fake_client = Mock()

        with patch("grazer.cli.load_config", return_value={}):
            with patch("grazer.cli.GrazerClient", return_value=fake_client):
                out = io.StringIO()
                with redirect_stdout(out):
                    cli.cmd_post(args)

        output = out.getvalue()
        self.assertIn("provider: clawtasks", output)
        self.assertIn('"tags": [', output)
        self.assertIn('"security"', output)
        fake_client.post_clawtask.assert_not_called()

    def test_redact_payload_hides_sensitive_keys(self):
        payload = {
            "token": "abc",
            "nested": {"api_key": "secret", "ok": 1},
            "normal": "value",
        }
        redacted = cli._redact_payload(payload)
        self.assertEqual(redacted["token"], "***REDACTED***")
        self.assertEqual(redacted["nested"]["api_key"], "***REDACTED***")
        self.assertEqual(redacted["normal"], "value")


if __name__ == "__main__":
    unittest.main()
