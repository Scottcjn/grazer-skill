#!/usr/bin/env python3
"""
Grazer CLI Demo - Shows content discovery in action across multiple platforms.

Run:
    python demo.py              # Full demo (ArXiv + YouTube + Podcasts + BoTTube)
    python demo.py --offline    # Offline demo with sample data (no network)
    python demo.py --arxiv      # ArXiv only
    python demo.py --youtube    # YouTube only
    python demo.py --podcasts   # Podcasts only
"""

import argparse
import json
import sys
import time

# ── Sample data for offline demo ────────────────────────────

SAMPLE_ARXIV = [
    {
        "arxiv_id": "2401.12345v1",
        "title": "Constraint-Bound Selection in Non-Bijunctive Attention Mechanisms",
        "authors": ["A. Researcher", "B. Collaborator", "C. Advisor"],
        "summary": "We propose a novel approach to attention that uses hardware-native "
                   "selection operations to prune weak paths and amplify strong ones.",
        "published": "2024-01-15T00:00:00Z",
        "url": "https://arxiv.org/abs/2401.12345",
        "pdf_url": "https://arxiv.org/pdf/2401.12345v1",
        "categories": ["cs.AI", "cs.LG"],
    },
    {
        "arxiv_id": "2401.67890v2",
        "title": "Proof of Antiquity: Hardware Age as a Sybil Resistance Mechanism",
        "authors": ["S. Boudreaux"],
        "summary": "We introduce a blockchain consensus mechanism that rewards vintage "
                   "hardware, using silicon aging fingerprints as unforgeable identity.",
        "published": "2024-01-10T00:00:00Z",
        "url": "https://arxiv.org/abs/2401.67890",
        "pdf_url": "https://arxiv.org/pdf/2401.67890v2",
        "categories": ["cs.CR", "cs.DC"],
    },
]

SAMPLE_YOUTUBE = [
    {
        "id": "dQw4w9WgXcQ",
        "title": "Building AI Agents That Discover Content Autonomously",
        "channel": "Elyan Labs",
        "description": "A walkthrough of the Grazer skill for multi-platform discovery.",
        "published": "2024-03-01T12:00:00Z",
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "views": 4200,
    },
    {
        "id": "abc123XYZab",
        "title": "POWER8 LLM Inference at 147 tokens/sec",
        "channel": "Vintage Computing",
        "description": "Running language models on IBM POWER8 with vec_perm collapse.",
        "published": "2024-02-15T08:00:00Z",
        "url": "https://www.youtube.com/watch?v=abc123XYZab",
        "views": 8900,
    },
]

SAMPLE_PODCASTS = [
    {
        "id": 99999,
        "name": "The Agent Internet Podcast",
        "artist": "Elyan Labs",
        "genre": "Technology",
        "episode_count": 24,
        "url": "https://podcasts.apple.com/podcast/99999",
        "feed_url": "https://feeds.example.com/agent-internet",
        "artwork": "https://example.com/artwork.jpg",
    },
    {
        "id": 88888,
        "name": "Proof of Work: Crypto & Hardware",
        "artist": "BlockTalk Media",
        "genre": "Technology",
        "episode_count": 150,
        "url": "https://podcasts.apple.com/podcast/88888",
        "feed_url": "https://feeds.example.com/pow",
        "artwork": "https://example.com/pow-art.jpg",
    },
]


def print_header(text):
    """Print a styled section header."""
    width = 60
    print()
    print("=" * width)
    print(f"  {text}")
    print("=" * width)
    print()


def print_divider():
    print("-" * 60)


def demo_arxiv(offline=False):
    """Demonstrate ArXiv paper discovery."""
    print_header("ArXiv Paper Discovery")

    if offline:
        papers = SAMPLE_ARXIV
        print("  [offline mode - using sample data]\n")
    else:
        from grazer.arxiv_grazer import ArxivGrazer
        grazer = ArxivGrazer()
        print("  Searching arXiv for recent AI papers...\n")
        try:
            papers = grazer.discover(query="large language models", category="ai", limit=5)
        except Exception as e:
            print(f"  Error: {e}")
            print("  Falling back to sample data...\n")
            papers = SAMPLE_ARXIV

    for i, p in enumerate(papers, 1):
        title = p.get("title", "(untitled)")
        authors = p.get("authors", [])
        author_str = ", ".join(authors[:3])
        if len(authors) > 3:
            author_str += f" +{len(authors) - 3} more"
        url = p.get("url", "")
        published = p.get("published", "")[:10]
        cats = ", ".join(p.get("categories", [])[:3])
        summary = p.get("summary", "")
        if len(summary) > 120:
            summary = summary[:117] + "..."

        print(f"  [{i}] {title}")
        print(f"      Authors: {author_str}")
        print(f"      Date: {published}  |  Categories: {cats}")
        if summary:
            print(f"      {summary}")
        print(f"      {url}")
        print()

    print(f"  Found {len(papers)} papers.")
    print_divider()


def demo_youtube(offline=False):
    """Demonstrate YouTube video discovery."""
    print_header("YouTube Video Discovery")

    if offline:
        videos = SAMPLE_YOUTUBE
        print("  [offline mode - using sample data]\n")
    else:
        from grazer.youtube_grazer import YouTubeGrazer
        grazer = YouTubeGrazer()
        print("  Searching YouTube for AI agent videos...\n")
        try:
            videos = grazer.discover(query="AI agents tutorial", limit=5)
        except Exception as e:
            print(f"  Error: {e}")
            print("  Falling back to sample data...\n")
            videos = SAMPLE_YOUTUBE

    for i, v in enumerate(videos, 1):
        title = v.get("title", "(untitled)")
        channel = v.get("channel", "unknown")
        url = v.get("url", "")
        views = v.get("views", "")
        views_str = f"  |  {views:,} views" if views else ""

        print(f"  [{i}] {title}")
        print(f"      Channel: {channel}{views_str}")
        print(f"      {url}")
        print()

    print(f"  Found {len(videos)} videos.")
    print_divider()


def demo_podcasts(offline=False):
    """Demonstrate podcast discovery."""
    print_header("Podcast Discovery (iTunes)")

    if offline:
        shows = SAMPLE_PODCASTS
        print("  [offline mode - using sample data]\n")
    else:
        from grazer.podcast_grazer import PodcastGrazer
        grazer = PodcastGrazer()
        print("  Searching iTunes for AI/technology podcasts...\n")
        try:
            shows = grazer.search(query="artificial intelligence technology", limit=5)
        except Exception as e:
            print(f"  Error: {e}")
            print("  Falling back to sample data...\n")
            shows = SAMPLE_PODCASTS

    for i, s in enumerate(shows, 1):
        name = s.get("name", "(unnamed)")
        artist = s.get("artist", "unknown")
        genre = s.get("genre", "")
        ep_count = s.get("episode_count", 0)
        url = s.get("url", "")

        print(f"  [{i}] {name}")
        print(f"      By: {artist}  |  Genre: {genre}  |  {ep_count} episodes")
        print(f"      {url}")
        print()

    print(f"  Found {len(shows)} podcasts.")
    print_divider()


def demo_integration(offline=False):
    """Show GrazerClient unified discovery across all platforms."""
    print_header("Unified Discovery (GrazerClient)")

    if offline:
        print("  [offline mode - showing what discover_all() returns]\n")
        result = {
            "arxiv": SAMPLE_ARXIV,
            "youtube": SAMPLE_YOUTUBE,
            "podcasts": SAMPLE_PODCASTS,
            "bottube": [{"title": "Sample BoTTube video", "agent": "sophia-elya"}],
            "moltbook": [{"title": "Sample Moltbook post", "submolt": "ai"}],
        }
        for platform, items in result.items():
            print(f"  {platform}: {len(items)} items")
            if items:
                first = items[0]
                label = first.get("title") or first.get("name") or "(item)"
                print(f"    First: {label}")
        print()
    else:
        from grazer import GrazerClient
        client = GrazerClient()
        print("  Calling client.discover_all(limit=3)...\n")
        try:
            result = client.discover_all(limit=3)
            errors = result.pop("_errors", {})
            for platform, items in sorted(result.items()):
                err = errors.get(platform)
                if err:
                    print(f"  {platform}: OFFLINE ({err[:50]})")
                else:
                    print(f"  {platform}: {len(items)} items")
            print()
            if errors:
                print(f"  ({len(errors)} platform(s) offline -- this is normal without API keys)")
        except Exception as e:
            print(f"  Error: {e}")

    print_divider()


def main():
    parser = argparse.ArgumentParser(
        description="Grazer Demo - Content discovery in action"
    )
    parser.add_argument("--offline", action="store_true", help="Use sample data (no network calls)")
    parser.add_argument("--arxiv", action="store_true", help="ArXiv demo only")
    parser.add_argument("--youtube", action="store_true", help="YouTube demo only")
    parser.add_argument("--podcasts", action="store_true", help="Podcasts demo only")
    args = parser.parse_args()

    specific = args.arxiv or args.youtube or args.podcasts

    print()
    print("  Grazer - Multi-Platform Content Discovery for AI Agents")
    print("  https://github.com/Scottcjn/grazer-skill")
    print()

    if not specific or args.arxiv:
        demo_arxiv(offline=args.offline)

    if not specific or args.youtube:
        demo_youtube(offline=args.offline)

    if not specific or args.podcasts:
        demo_podcasts(offline=args.offline)

    if not specific:
        demo_integration(offline=args.offline)

    print()
    print("  Demo complete. Install: pip install grazer-skill")
    print("  CLI usage:  grazer discover -p arxiv -l 5")
    print("              grazer discover -p youtube -l 5")
    print("              grazer discover -p podcasts -l 5")
    print()


if __name__ == "__main__":
    main()
