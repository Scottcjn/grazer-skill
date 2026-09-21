"""Compatibility entry point for opportunity-focused Moltbook discovery."""

import sys

from grazer import GrazerClient
from grazer import cli as legacy_cli
from grazer.opportunities import rank_moltbook_opportunities


def _is_opportunity_mode(argv):
    return "--bounties-only" in argv or "--intent=opportunities" in argv or any(
        value == "--intent" and index + 1 < len(argv) and argv[index + 1] == "opportunities"
        for index, value in enumerate(argv)
    )


def _strip_opportunity_flags(argv):
    clean = []
    index = 0
    while index < len(argv):
        value = argv[index]
        if value in ("--bounties-only", "--intent=opportunities"):
            index += 1
            continue
        if value == "--intent" and index + 1 < len(argv) and argv[index + 1] == "opportunities":
            index += 2
            continue
        clean.append(value)
        index += 1
    return clean


def main():
    argv = sys.argv[1:]
    if not _is_opportunity_mode(argv):
        return legacy_cli.main()

    if not argv or argv[0] != "discover":
        raise SystemExit("opportunity mode is only valid with grazer discover")
    if not any(value in ("moltbook", "--platform=moltbook", "-p=moltbook") for value in argv):
        raise SystemExit("opportunity mode currently requires --platform moltbook")

    original = GrazerClient.discover_moltbook

    def discover_opportunities(self, submolt="tech", limit=20):
        fetch_limit = min(max(int(limit) * 5, 50), 100)
        posts = original(self, submolt=submolt, limit=fetch_limit)
        return rank_moltbook_opportunities(posts, limit=limit)

    GrazerClient.discover_moltbook = discover_opportunities
    sys.argv = [sys.argv[0]] + _strip_opportunity_flags(argv)
    return legacy_cli.main()


if __name__ == "__main__":
    main()
