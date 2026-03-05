import io
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

from grazer import cli


class DiscoverDefensiveOutputTests(unittest.TestCase):
    def _run_discover(self, platform: str, client: Mock) -> str:
        args = Namespace(
            platform=platform,
            category=None,
            submolt="tech",
            board=None,
            limit=5,
        )
        with patch("grazer.cli.load_config", return_value={}):
            with patch("grazer.cli._make_client", return_value=client):
                output = io.StringIO()
                with redirect_stdout(output):
                    cli.cmd_discover(args)
        return output.getvalue()

    def test_moltbook_handles_missing_fields(self):
        client = Mock()
        client.discover_moltbook.return_value = [{"upvotes": 7}]
        output = self._run_discover("moltbook", client)
        self.assertIn("(untitled)", output)
        self.assertIn("m/unknown", output)
        self.assertIn("(no url)", output)

    def test_clawsta_handles_non_string_and_missing_author(self):
        client = Mock()
        client.discover_clawsta.return_value = [{"content": None, "likes": 3}]
        output = self._run_discover("clawsta", client)
        self.assertIn("(no content)", output)
        self.assertIn("by unknown", output)

    def test_agentchan_handles_missing_subject_and_author(self):
        client = Mock()
        client.discover_agentchan.return_value = [{"reply_count": 2}]
        output = self._run_discover("agentchan", client)
        self.assertIn("(untitled)", output)
        self.assertIn("by anon", output)

    def test_colony_handles_non_string_ids(self):
        client = Mock()
        client.discover_colony.return_value = [
            {"id": 123456789, "author": None, "body": None, "comment_count": 1}
        ]
        output = self._run_discover("thecolony", client)
        self.assertIn("(untitled)", output)
        self.assertIn("id:12345678", output)

    def test_moltx_handles_missing_content_and_author(self):
        client = Mock()
        client.discover_moltx.return_value = [{"like_count": 1, "reply_count": 0}]
        output = self._run_discover("moltx", client)
        self.assertIn("(no content)", output)
        self.assertIn("by ?", output)

    def test_moltexchange_handles_dict_author_and_non_string_content(self):
        client = Mock()
        client.discover_moltexchange.return_value = [
            {"content": {"unexpected": True}, "author": {"username": "bot-1"}}
        ]
        output = self._run_discover("moltexchange", client)
        self.assertIn("by bot-1", output)

    def test_pinchedin_handles_non_dict_author(self):
        client = Mock()
        client.discover_pinchedin.return_value = [
            {"content": "test post", "author": "agent-42", "likesCount": 2, "commentsCount": 1}
        ]
        output = self._run_discover("pinchedin", client)
        self.assertIn("by agent-42", output)
        self.assertIn("2 likes", output)

    def test_pinchedin_jobs_handles_non_dict_poster(self):
        client = Mock()
        client.discover_pinchedin_jobs.return_value = [
            {"title": "Backend role", "poster": "team-alpha", "status": None}
        ]
        output = self._run_discover("pinchedin-jobs", client)
        self.assertIn("by team-alpha", output)
        self.assertIn("status: ?", output)

    def test_clawtasks_handles_non_list_tags(self):
        client = Mock()
        client.discover_clawtasks.return_value = [
            {"title": "Bounty A", "tags": "security", "status": "open", "deadline_hours": None}
        ]
        output = self._run_discover("clawtasks", client)
        self.assertIn("tags: security", output)
        self.assertIn("deadline: ?h", output)


if __name__ == "__main__":
    unittest.main()
