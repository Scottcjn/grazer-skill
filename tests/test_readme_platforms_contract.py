# SPDX-License-Identifier: MIT
"""Unit test validating that README.md reflects the 22-platform discover_all contract."""

import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from grazer import GrazerClient


class TestReadmePlatformsContract(unittest.TestCase):
    def setUp(self):
        self.readme_path = Path(__file__).resolve().parent.parent / "README.md"
        self.assertTrue(self.readme_path.exists(), "README.md must exist")
        self.readme_text = self.readme_path.read_text(encoding="utf-8")

    def test_no_stale_all_5_platforms(self):
        """README must not contain stale 'all 5 platforms' references."""
        self.assertNotIn(
            "all 5 platforms",
            self.readme_text.lower(),
            "Found stale 'all 5 platforms' contract in README.md",
        )

    def test_contract_specifies_22_platforms(self):
        """README specifies 22 platforms for discover_all / -p all."""
        self.assertIn(
            "# Discover across all 22 platforms",
            self.readme_text,
            "CLI or Python SDK examples must specify '# Discover across all 22 platforms'",
        )

    def test_discover_all_platform_count_matches(self):
        """client.discover_all keys must match the 22 documented discovery platforms."""
        client = GrazerClient()
        mock_resp = Mock()
        mock_resp.json.return_value = {}
        mock_resp.raise_for_status = Mock()
        mock_resp.status_code = 200

        with patch("requests.Session.get", return_value=mock_resp), patch("requests.Session.post", return_value=mock_resp):
            results = client.discover_all(limit=1)

        platform_keys = [k for k in results.keys() if not k.startswith("_")]
        self.assertEqual(
            len(platform_keys),
            22,
            f"Expected exactly 22 platforms in discover_all, found {len(platform_keys)}: {platform_keys}",
        )

    def test_all_22_platforms_in_readme_table(self):
        """Every platform in discover_all must be listed in the README Supported Platforms table."""
        expected_platforms = [
            "BoTTube", "Moltbook", "ClawCities", "Clawsta", "4claw",
            "PinchedIn", "ClawTasks", "ClawNews", "AgentChan", "The Colony",
            "MoltX", "MoltExchange", "Directory", "ArXiv", "YouTube",
            "Podcasts", "Bluesky", "Farcaster", "Semantic Scholar", "OpenReview",
            "Mastodon", "Nostr",
        ]
        for name in expected_platforms:
            self.assertIn(
                name,
                self.readme_text,
                f"Platform '{name}' is in discover_all contract but missing from README.md",
            )


if __name__ == "__main__":
    unittest.main()
