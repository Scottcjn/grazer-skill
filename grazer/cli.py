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

from grazer import GrazerClient, PLATFORMS


def load_config() -> dict:
    """Load config from ~/.grazer/config.json."""
    config_path = Path.home() / ".grazer" / "config.json"
    if not config_path.exists():
        print("⚠️  No config found at ~/.grazer/config.json")
        print("Using limited features (public APIs only)")
        return {}
    return json.loads(config_path.read_text())


def _make_client(config: dict, **extra) -> GrazerClient:
    """Build a GrazerClient from config with all keys populated."""
    llm = config.get("imagegen", {})
    return GrazerClient(
        bottube_key=config.get("bottube", {}).get("api_key"),
        moltbook_key=config.get("moltbook", {}).get("api_key"),
        clawcities_key=config.get("clawcities", {}).get("api_key"),
        clawsta_key=config.get("clawsta", {}).get("api_key"),
        fourclaw_key=config.get("fourclaw", {}).get("api_key"),
        pinchedin_key=config.get("pinchedin", {}).get("api_key"),
        clawtasks_key=config.get("clawtasks", {}).get("api_key"),
        clawnews_key=config.get("clawnews", {}).get("api_key"),
        agentchan_key=config.get("agentchan", {}).get("api_key"),
        clawhub_token=config.get("clawhub", {}).get("token"),
        llm_url=llm.get("llm_url"),
        llm_model=llm.get("llm_model", "gpt-oss-120b"),
        llm_api_key=llm.get("llm_api_key"),
        **extra,
    )


def cmd_discover(args):
    """Discover trending content."""
    config = load_config()
    client = _make_client(config)

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

    elif args.platform == "pinchedin":
        posts = client.discover_pinchedin(limit=args.limit)
        print("\n💼 PinchedIn Feed:\n")
        for p in posts:
            content = p["content"][:80] + "..." if len(p["content"]) > 80 else p["content"]
            author = p.get("author", {}).get("name", "?")
            print(f"  {content}")
            print(f"    by {author} | {p.get('likesCount', 0)} likes | {p.get('commentsCount', 0)} comments\n")

    elif args.platform == "pinchedin-jobs":
        jobs = client.discover_pinchedin_jobs(limit=args.limit)
        print("\n💼 PinchedIn Jobs:\n")
        for j in jobs:
            print(f"  {j.get('title', '?')}")
            poster = j.get("poster", {}).get("name", "?")
            print(f"    by {poster} | status: {j.get('status', '?')}\n")

    elif args.platform == "clawtasks":
        bounties = client.discover_clawtasks(limit=args.limit)
        print("\n🎯 ClawTasks Bounties:\n")
        for b in bounties:
            print(f"  {b['title']}")
            tags = ", ".join(b.get("tags") or [])
            print(f"    status: {b['status']} | tags: {tags} | deadline: {b.get('deadline_hours', '?')}h\n")

    elif args.platform == "clawnews":
        stories = client.discover_clawnews(limit=args.limit)
        print("\n📰 ClawNews Stories:\n")
        for s in stories:
            title = s.get("headline", s.get("title", "?"))
            print(f"  {title}")
            print(f"    {s.get('url', '')}\n")

    elif args.platform == "agentchan":
        board = args.board or "ai"
        threads = client.discover_agentchan(board=board, limit=args.limit)
        print(f"\n🤖 AgentChan /{board}/:\n")
        for t in threads:
            subject = t.get("subject", t.get("title", "(untitled)"))
            replies = t.get("reply_count", t.get("replyCount", 0))
            author = t.get("author_name", t.get("author", "anon"))
            print(f"  {subject}")
            print(f"    by {author} | {replies} replies\n")

    elif args.platform == "all":
        all_content = client.discover_all()
        errors = all_content.pop("_errors", {})
        print("\n🌐 All Platforms:\n")
        labels = {
            "bottube": "BoTTube videos",
            "moltbook": "Moltbook posts",
            "clawcities": "ClawCities sites",
            "clawsta": "Clawsta posts",
            "fourclaw": "4claw threads",
            "pinchedin": "PinchedIn posts",
            "clawtasks": "ClawTasks bounties",
            "clawnews": "ClawNews stories",
            "directory": "Directory services",
            "agentchan": "AgentChan threads",
        }
        for key, label in labels.items():
            count = len(all_content.get(key, []))
            err = errors.get(key)
            if err:
                print(f"  {label}: OFFLINE ({err[:60]})")
            else:
                print(f"  {label}: {count}")
        print()


def cmd_status(args):
    """Check platform health and reachability."""
    config = load_config()
    client = _make_client(config)

    platforms = [args.platform] if args.platform and args.platform != "all" else None
    results = client.platform_status(platforms)

    print("\n📡 Platform Status:\n")
    up_count = 0
    for name, info in sorted(results.items()):
        ok = info["ok"]
        latency = info["latency_ms"]
        err = info.get("error")
        auth = info["auth_configured"]
        status_icon = "UP" if ok else "DOWN"
        auth_icon = "key" if auth else "---"
        if ok:
            up_count += 1
            print(f"  [{status_icon}] {name:14s}  {latency:6.0f}ms  [{auth_icon}]")
        else:
            print(f"  [{status_icon}] {name:14s}  {latency:6.0f}ms  [{auth_icon}]  {err}")

    total = len(results)
    print(f"\n  {up_count}/{total} platforms reachable\n")


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
        pinchedin_key=config.get("pinchedin", {}).get("api_key"),
    )

    if args.platform == "clawcities":
        result = client.comment_clawcities(args.target, args.message)
        print(f"\n✓ Comment posted to {args.target}")
        print(f"  ID: {result.get('comment', {}).get('id')}")

    elif args.platform == "clawsta":
        result = client.post_clawsta(args.message)
        print(f"\n✓ Posted to Clawsta")
        print(f"  ID: {result.get('id')}")

    elif args.platform == "pinchedin":
        if args.target:
            result = client.comment_pinchedin(args.target, args.message)
            print(f"\n✓ Comment posted on PinchedIn post {args.target[:8]}...")
            print(f"  ID: {result.get('id', 'ok')}")
        else:
            print("Error: --target post_id required for PinchedIn comments")
            sys.exit(1)

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
        pinchedin_key=config.get("pinchedin", {}).get("api_key"),
        clawtasks_key=config.get("clawtasks", {}).get("api_key"),
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

    elif args.platform == "pinchedin":
        result = client.post_pinchedin(args.message)
        print(f"\n✓ Posted to PinchedIn")
        print(f"  ID: {result.get('id', 'ok')}")

    elif args.platform == "clawtasks":
        tags = args.board.split(",") if args.board else None
        result = client.post_clawtask(args.title, args.message, tags=tags)
        print(f"\n✓ Bounty posted on ClawTasks")
        print(f"  ID: {result.get('id', 'ok')}")

    elif args.platform == "agentchan":
        board = args.board or "ai"
        result = client.post_agentchan(board=board, content=args.message)
        if result:
            print(f"\n✓ Thread posted on AgentChan /{board}/")
            print(f"  ID: {result.get('data', {}).get('id', result.get('id', 'ok'))}")
        else:
            print("\n✗ Failed to post on AgentChan")


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
    parser.add_argument("--version", action="version", version="grazer 1.7.0")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # discover command
    discover_parser = subparsers.add_parser("discover", help="Discover trending content")
    discover_parser.add_argument(
        "-p", "--platform",
        choices=["bottube", "moltbook", "clawcities", "clawsta", "fourclaw", "pinchedin", "pinchedin-jobs", "clawtasks", "clawnews", "agentchan", "all"],
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

    # status command
    status_parser = subparsers.add_parser("status", help="Check platform health and reachability")
    status_parser.add_argument(
        "-p", "--platform",
        choices=list(PLATFORMS.keys()) + ["all"],
        default="all",
        help="Platform to check (default: all)"
    )

    # comment command
    comment_parser = subparsers.add_parser("comment", help="Reply to a thread or comment")
    comment_parser.add_argument(
        "-p", "--platform",
        choices=["clawcities", "clawsta", "fourclaw", "pinchedin"],
        required=True,
        help="Platform"
    )
    comment_parser.add_argument("-t", "--target", help="Target (site name, post/thread ID)")
    comment_parser.add_argument("-m", "--message", required=True, help="Comment message")

    # post command
    post_parser = subparsers.add_parser("post", help="Create a new post or thread")
    post_parser.add_argument(
        "-p", "--platform",
        choices=["fourclaw", "moltbook", "pinchedin", "clawtasks", "agentchan"],
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
        elif args.command == "status":
            cmd_status(args)
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
