#!/usr/bin/env python3
"""
Grazer CLI for Python
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

from grazer import GrazerClient


def load_config() -> dict:
    """Load config from ~/.grazer/config.json."""
    config_path = Path.home() / ".grazer" / "config.json"
    if not config_path.exists():
        print("⚠️  No config found at ~/.grazer/config.json")
        print("Using limited features (public APIs only)")
        return {}
    return json.loads(config_path.read_text())


def cmd_discover(args):
    """Discover trending content."""
    config = load_config()
    client = GrazerClient(
        bottube_key=config.get("bottube", {}).get("api_key"),
        moltbook_key=config.get("moltbook", {}).get("api_key"),
        clawcities_key=config.get("clawcities", {}).get("api_key"),
        clawsta_key=config.get("clawsta", {}).get("api_key"),
        fourclaw_key=config.get("fourclaw", {}).get("api_key"),
    )

    if args.platform == "bottube":
        videos = client.discover_bottube(category=args.category, limit=args.limit)
        print("\n🎬 BoTTube Videos:\n")
        for v in videos:
            print(f"  {v['title']}")
            print(f"    by {v['agent']} | {v['views']} views | {v['category']}")
            print(f"    {v['stream_url']}\n")

    elif args.platform == "moltbook":
        posts = client.discover_moltbook(submolt=args.submolt, limit=args.limit)
        print("\n📚 Moltbook Posts:\n")
        for p in posts:
            print(f"  {p['title']}")
            print(f"    m/{p['submolt']} | {p.get('upvotes', 0)} upvotes")
            print(f"    https://moltbook.com{p['url']}\n")

    elif args.platform == "clawcities":
        sites = client.discover_clawcities(limit=args.limit)
        print("\n🏙️ ClawCities Sites:\n")
        for s in sites:
            print(f"  {s['display_name']}")
            print(f"    {s['url']}\n")

    elif args.platform == "clawsta":
        posts = client.discover_clawsta(limit=args.limit)
        print("\n🦞 Clawsta Posts:\n")
        for p in posts:
            content = p["content"][:60] + "..." if len(p["content"]) > 60 else p["content"]
            print(f"  {content}")
            print(f"    by {p['author']} | {p.get('likes', 0)} likes\n")

    elif args.platform == "fourclaw":
        board = args.board or "b"
        threads = client.discover_fourclaw(board=board, limit=args.limit, include_content=True)
        print(f"\n🦞 4claw /{board}/:\n")
        for t in threads:
            title = t.get("title", "(untitled)")
            replies = t.get("replyCount", 0)
            agent = t.get("agentName", "anon")
            print(f"  {title}")
            print(f"    by {agent} | {replies} replies | id:{t['id'][:8]}\n")

    elif args.platform == "all":
        all_content = client.discover_all()
        print("\n🌐 All Platforms:\n")
        print(f"  BoTTube: {len(all_content['bottube'])} videos")
        print(f"  Moltbook: {len(all_content['moltbook'])} posts")
        print(f"  ClawCities: {len(all_content['clawcities'])} sites")
        print(f"  Clawsta: {len(all_content['clawsta'])} posts")
        print(f"  4claw: {len(all_content['fourclaw'])} threads\n")


def cmd_stats(args):
    """Get platform statistics."""
    config = load_config()
    client = GrazerClient()

    if args.platform == "bottube":
        stats = client.get_bottube_stats()
        print("\n🎬 BoTTube Stats:\n")
        print(f"  Total Videos: {stats.get('total_videos', 0)}")
        print(f"  Total Views: {stats.get('total_views', 0)}")
        print(f"  Total Agents: {stats.get('total_agents', 0)}")
        print(f"  Categories: {', '.join(stats.get('categories', []))}\n")


def cmd_comment(args):
    """Leave a comment."""
    config = load_config()
    client = GrazerClient(
        moltbook_key=config.get("moltbook", {}).get("api_key"),
        clawcities_key=config.get("clawcities", {}).get("api_key"),
        clawsta_key=config.get("clawsta", {}).get("api_key"),
        fourclaw_key=config.get("fourclaw", {}).get("api_key"),
    )

    if args.platform == "clawcities":
        result = client.comment_clawcities(args.target, args.message)
        print(f"\n✓ Comment posted to {args.target}")
        print(f"  ID: {result.get('comment', {}).get('id')}")

    elif args.platform == "clawsta":
        result = client.post_clawsta(args.message)
        print(f"\n✓ Posted to Clawsta")
        print(f"  ID: {result.get('id')}")

    elif args.platform == "fourclaw":
        if args.target:
            result = client.reply_fourclaw(args.target, args.message)
            print(f"\n✓ Reply posted to thread {args.target[:8]}...")
            print(f"  ID: {result.get('reply', {}).get('id', 'ok')}")
        else:
            print("Error: --target thread_id required for 4claw replies")
            sys.exit(1)


def _get_llm_config(config: dict) -> dict:
    """Extract LLM config for image generation."""
    llm = config.get("imagegen", {})
    return {
        "llm_url": llm.get("llm_url"),
        "llm_model": llm.get("llm_model", "gpt-oss-120b"),
        "llm_api_key": llm.get("llm_api_key"),
    }


def cmd_post(args):
    """Create a new post/thread."""
    config = load_config()
    llm_cfg = _get_llm_config(config)
    client = GrazerClient(
        moltbook_key=config.get("moltbook", {}).get("api_key"),
        fourclaw_key=config.get("fourclaw", {}).get("api_key"),
        **llm_cfg,
    )

    if args.platform == "fourclaw":
        if not args.board:
            print("Error: --board required for 4claw (e.g. b, singularity, crypto)")
            sys.exit(1)
        image_prompt = getattr(args, "image", None)
        template = getattr(args, "template", None)
        palette = getattr(args, "palette", None)
        result = client.post_fourclaw(
            args.board, args.title, args.message,
            image_prompt=image_prompt, template=template, palette=palette,
        )
        thread = result.get("thread", {})
        print(f"\n✓ Thread created on /{args.board}/")
        print(f"  Title: {thread.get('title')}")
        print(f"  ID: {thread.get('id')}")
        if image_prompt:
            print(f"  Image: generated from '{image_prompt}'")

    elif args.platform == "moltbook":
        result = client.post_moltbook(args.message, args.title, submolt=args.board or "tech")
        print(f"\n✓ Posted to m/{args.board or 'tech'}")
        print(f"  ID: {result.get('id', 'ok')}")


def cmd_clawhub(args):
    """ClawHub skill registry commands."""
    config = load_config()
    from grazer import GrazerClient

    client = GrazerClient(clawhub_token=config.get("clawhub", {}).get("token"))

    if args.action == "search":
        query = " ".join(args.query)
        skills = client.search_clawhub(query, limit=args.limit)
        print(f"\n🐙 ClawHub Search: \"{query}\"\n")
        if not skills:
            print("  No skills found.")
            return
        for s in skills:
            name = s.get("displayName", s.get("slug", "?"))
            slug = s.get("slug", "?")
            summary = s.get("summary", "")
            if summary and len(summary) > 80:
                summary = summary[:77] + "..."
            downloads = s.get("stats", {}).get("downloads", 0)
            versions = s.get("stats", {}).get("versions", 0)
            print(f"  {name} ({slug})")
            if summary:
                print(f"    {summary}")
            print(f"    {downloads} downloads | {versions} versions | https://clawhub.ai/{slug}\n")

    elif args.action == "trending":
        skills = client.trending_clawhub(limit=args.limit)
        print("\n🐙 ClawHub Trending Skills:\n")
        for i, s in enumerate(skills, 1):
            name = s.get("displayName", s.get("slug", "?"))
            downloads = s.get("stats", {}).get("downloads", 0)
            print(f"  {i}. {name} ({downloads} downloads)")

    elif args.action == "info":
        if not args.query:
            print("Error: skill slug required (e.g. grazer clawhub info grazer)")
            sys.exit(1)
        slug = args.query[0]
        skill = client.get_clawhub_skill(slug)
        info = skill.get("skill", skill)
        owner = skill.get("owner", {})
        latest = skill.get("latestVersion", {})
        print(f"\n🐙 {info.get('displayName', slug)}")
        print(f"  Slug: {info.get('slug')}")
        if info.get("summary"):
            print(f"  Summary: {info['summary']}")
        print(f"  Owner: @{owner.get('handle', '?')}")
        print(f"  Version: {latest.get('version', '?')}")
        print(f"  Downloads: {info.get('stats', {}).get('downloads', 0)}")
        print(f"  Stars: {info.get('stats', {}).get('stars', 0)}")
        if latest.get("changelog"):
            print(f"  Changelog: {latest['changelog']}")
        print(f"  URL: https://clawhub.ai/{info.get('slug')}\n")


def cmd_imagegen(args):
    """Generate an SVG image (preview without posting)."""
    config = load_config()
    llm_cfg = _get_llm_config(config)
    client = GrazerClient(**llm_cfg)

    result = client.generate_image(
        args.prompt,
        template=getattr(args, "template", None),
        palette=getattr(args, "palette", None),
    )
    print(f"\n🎨 SVG Generated ({result['method']}, {result['bytes']} bytes):\n")
    if args.output:
        with open(args.output, "w") as f:
            f.write(result["svg"])
        print(f"  Saved to: {args.output}")
    else:
        print(result["svg"])


def main():
    parser = argparse.ArgumentParser(
        description="🐄 Grazer - Content discovery for AI agents"
    )
    parser.add_argument("--version", action="version", version="grazer 1.3.0")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # discover command
    discover_parser = subparsers.add_parser("discover", help="Discover trending content")
    discover_parser.add_argument(
        "-p", "--platform",
        choices=["bottube", "moltbook", "clawcities", "clawsta", "fourclaw", "all"],
        default="all",
        help="Platform to search"
    )
    discover_parser.add_argument("-c", "--category", help="BoTTube category")
    discover_parser.add_argument("-s", "--submolt", help="Moltbook submolt", default="tech")
    discover_parser.add_argument("-b", "--board", help="4claw board (e.g. b, singularity, crypto)")
    discover_parser.add_argument("-l", "--limit", type=int, default=20, help="Result limit")

    # stats command
    stats_parser = subparsers.add_parser("stats", help="Get platform statistics")
    stats_parser.add_argument(
        "-p", "--platform",
        choices=["bottube"],
        required=True,
        help="Platform"
    )

    # comment command
    comment_parser = subparsers.add_parser("comment", help="Reply to a thread or comment")
    comment_parser.add_argument(
        "-p", "--platform",
        choices=["clawcities", "clawsta", "fourclaw"],
        required=True,
        help="Platform"
    )
    comment_parser.add_argument("-t", "--target", help="Target (site name, post/thread ID)")
    comment_parser.add_argument("-m", "--message", required=True, help="Comment message")

    # post command
    post_parser = subparsers.add_parser("post", help="Create a new post or thread")
    post_parser.add_argument(
        "-p", "--platform",
        choices=["fourclaw", "moltbook"],
        required=True,
        help="Platform"
    )
    post_parser.add_argument("-b", "--board", help="Board/submolt name")
    post_parser.add_argument("-t", "--title", required=True, help="Post/thread title")
    post_parser.add_argument("-m", "--message", required=True, help="Post content")
    post_parser.add_argument("-i", "--image", help="Generate SVG image from this prompt")
    post_parser.add_argument("--template", help="SVG template: circuit, wave, grid, badge, terminal")
    post_parser.add_argument("--palette", help="Color palette: tech, crypto, retro, nature, dark, fire, ocean")

    # clawhub command
    clawhub_parser = subparsers.add_parser("clawhub", help="ClawHub skill registry")
    clawhub_parser.add_argument(
        "action",
        choices=["search", "trending", "info"],
        help="Action: search, trending, or info"
    )
    clawhub_parser.add_argument("query", nargs="*", help="Search query or skill slug")
    clawhub_parser.add_argument("-l", "--limit", type=int, default=20, help="Result limit")

    # imagegen command
    imagegen_parser = subparsers.add_parser("imagegen", help="Generate SVG image (preview)")
    imagegen_parser.add_argument("prompt", help="Image description prompt")
    imagegen_parser.add_argument("-o", "--output", help="Save SVG to file")
    imagegen_parser.add_argument("--template", help="SVG template: circuit, wave, grid, badge, terminal")
    imagegen_parser.add_argument("--palette", help="Color palette: tech, crypto, retro, nature, dark, fire, ocean")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "discover":
            cmd_discover(args)
        elif args.command == "stats":
            cmd_stats(args)
        elif args.command == "comment":
            cmd_comment(args)
        elif args.command == "post":
            cmd_post(args)
        elif args.command == "clawhub":
            cmd_clawhub(args)
        elif args.command == "imagegen":
            cmd_imagegen(args)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
