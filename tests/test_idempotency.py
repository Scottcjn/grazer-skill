import io
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

from grazer import cli


class IdempotencyTests(unittest.TestCase):
    def test_comment_duplicate_key_skips_publish(self):
        args = Namespace(
            platform="pinchedin",
            target="post-abc",
            message="hello",
            idempotency_key="k1",
            idempotency_ttl=86400,
        )
        fake_client = Mock()

        with patch("grazer.cli.load_config", return_value={}):
            with patch("grazer.cli.GrazerClient", return_value=fake_client):
                with patch("grazer.cli._idempotency_is_duplicate", return_value=True):
                    out = io.StringIO()
                    with redirect_stdout(out):
                        cli.cmd_comment(args)

        output = out.getvalue()
        self.assertIn("Idempotency hit", output)
        fake_client.comment_pinchedin.assert_not_called()

    def test_post_new_key_marks_after_publish(self):
        args = Namespace(
            platform="pinchedin",
            board=None,
            title="Title",
            message="Message",
            image=None,
            template=None,
            palette=None,
            idempotency_key="k2",
            idempotency_ttl=86400,
        )
        fake_client = Mock()
        fake_client.post_pinchedin.return_value = {"id": "123"}

        with patch("grazer.cli.load_config", return_value={}):
            with patch("grazer.cli.GrazerClient", return_value=fake_client):
                with patch("grazer.cli._idempotency_is_duplicate", return_value=False):
                    with patch("grazer.cli._idempotency_mark") as mark_mock:
                        out = io.StringIO()
                        with redirect_stdout(out):
                            cli.cmd_post(args)

        fake_client.post_pinchedin.assert_called_once_with("Message")
        mark_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
