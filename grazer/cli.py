#!/usr/bin/env python3
"""
Grazer CLI for Python
"""

import argparse
import json
import os
import sys
import time
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
        thecolony_key=config.get("thecolony", {}).get("api_key"),
        moltx_key=config.get("moltx", {}).get("api_key"),
        moltexchange_key=config.get("moltexchange", {}).get("api_key"),
        clawhub_token=config.get("clawhub", {}).get("token"),
        llm_url=llm.get("llm_url"),
        llm_model=llm.get("llm_model", "gpt-oss-120b"),
        llm_api_key=llm.get("llm_api_key"),
        **extra,
    )


def _to_text(value, default="") -> str:
    """Normalize mixed API values to printable text."""
    if value is None:
        return default
    if isinstance(value, str):
        return value
    return str(value)


def _truncate(value, max_len: int, default="") -> str:
    text = _to_text(value, default=default)
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text


def _redact_payload(value):
    """Recursively redact token/secret-looking keys in payload previews."""
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            key_lower = str(k).lower()
            if any(marker in key_lower for marker in ("token", "secret", "password", "authorization", "api_key")):
                out[k] = "***REDACTED***"
            else:
                out[k] = _redact_payload(v)
        return out
    if isinstance(value, list):
        return [_redact_payload(v) for v in value]
    return value


def _print_dry_run_preview(provider: str, payload: dict, text_value: Optional[str] = None, media_meta: Optional[dict] = None):
    """Print provider-normalized payload preview for dry-run mode."""
    text_len = len(_to_text(text_value, default="")) if text_value is not None else 0
    safe_payload = _redact_payload(payload)

    print("\n🔍 Dry-run preview (no publish):")
    print(f"  provider: {provider}")
    print(f"  text_length: {text_len}")
    if media_meta:
        print(f"  media: {json.dumps(media_meta, ensure_ascii=False)}")
    print("  payload:")
    print(json.dumps(safe_payload, indent=2, ensure_ascii=False))


DEFAULT_IDEMPOTENCY_TTL = 24 * 60 * 60


def _idempotency_cache_path() -> Path:
    return Path.home() / ".grazer" / "idempotency_keys.json"


def _load_idempotency_cache(path: Optional[Path] = None) -> dict:
    cache_path = path or _idempotency_cache_path()
    if not cache_path.exists():
        return {}
    try:
        data = json.loads(cache_path.read_text())
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_idempotency_cache(cache: dict, path: Optional[Path] = None) -> None:
    cache_path = path or _idempotency_cache_path()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache, indent=2, sort_keys=True))


def _cleanup_idempotency_cache(cache: dict, ttl_seconds: int, now_ts: Optional[float] = None) -> dict:
    now = time.time() if now_ts is None else now_ts
    cleaned = {}
    for key, ts in cache.items():
        if isinstance(ts, (int, float)) and (now - ts) <= ttl_seconds:
            cleaned[key] = ts
    return cleaned


def _idempotency_is_duplicate(scope: str, key: Optional[str], ttl_seconds: int) -> bool:
    if not key:
        return False
    cache = _load_idempotency_cache()
    cache = _cleanup_idempotency_cache(cache, ttl_seconds)
    _save_idempotency_cache(cache)
    return f"{scope}:{key}" in cache


def _idempotency_mark(scope: str, key: Optional[str], ttl_seconds: int) -> None:
    if not key:
        return
    cache = _load_idempotency_cache()
    cache = _cleanup_idempotency_cache(cache, ttl_seconds)
    cache[f"{scope}:{key}"] = time.time()
    _save_idempotency_cache(cache)


def cmd_discover(args):
    """Discover trending content."""
    config = load_config()
    client = _make_client(config)

    if args.platform == "bottube":
        videos = client.discover_bottube(category=args.category, limit=args.limit)
        videos = videos[:args.limit]
        print("\n🎬 BoTTube Videos:\n")
        for v in videos:
            title = v.get("title", "(untitled)")
            agent = v.get("agent_name") or v.get("agent") or v.get("display_name") or "unknown"
            views = v.get("views", 0)
            category = v.get("category", "n/a")
            stream_url = v.get("stream_url") or v.get("url") or "(no url)"
            print(f"  {title}")
            print(f"    by {agent} | {views} views | {category}")
            print(f"    {stream_url}\n")

    elif args.platform == "moltbook":
        posts = client.discover_moltbook(submolt=args.submolt, limit=args.limit)
        posts = posts[:args.limit]
        print("\n📚 Moltbook Posts:\n")
        for p in posts:
            title = _to_text(p.get("title"), default="(untitled)")
            submolt = _to_text(p.get("submolt"), default="unknown")
            upvotes = p.get("upvotes", 0)
            raw_url = _to_text(p.get("url"), default="")
            if raw_url.startswith("http://") or raw_url.startswith("https://"):
                post_url = raw_url
            elif raw_url:
                post_url = f"https://moltbook.com{raw_url}"
            else:
                post_url = "(no url)"
            print(f"  {title}")
            print(f"    m/{submolt} | {upvotes} upvotes")
            print(f"    {post_url}\n")

    elif args.platform == "clawcities":
        sites = client.discover_clawcities(limit=args.limit)
        sites = sites[:args.limit]
        print("\n🏙️ ClawCities Sites:\n")
        for s in sites:
            display_name = _to_text(s.get("display_name"), default=_to_text(s.get("name"), default="(unnamed site)"))
            site_url = _to_text(s.get("url"), default="(no url)")
            print(f"  {display_name}")
            print(f"    {site_url}\n")

    elif args.platform == "clawsta":
        posts = client.discover_clawsta(limit=args.limit)
        posts = posts[:args.limit]
        print("\n🦞 Clawsta Posts:\n")
        for p in posts:
            content = _truncate(p.get("content"), 60, default="(no content)")
            author_data = p.get("author")
            if isinstance(author_data, dict):
                author = _to_text(author_data.get("display_name"), default=_to_text(author_data.get("username"), default="unknown"))
            else:
                author = _to_text(author_data, default="unknown")
            likes = p.get("likes", p.get("like_count", 0))
            print(f"  {content}")
            print(f"    by {author} | {likes} likes\n")

    elif args.platform == "fourclaw":
        board = args.board or "b"
        threads = client.discover_fourclaw(board=board, limit=args.limit, include_content=True)
        threads = threads[:args.limit]
        print(f"\n🦞 4claw /{board}/:\n")
        for t in threads:
            title = t.get("title", "(untitled)")
            replies = t.get("replyCount", 0)
            agent = t.get("agentName", "anon")
            thread_id = _to_text(t.get("id"), default="?")
            print(f"  {title}")
            print(f"    by {agent} | {replies} replies | id:{thread_id[:8]}\n")

    elif args.platform == "pinchedin":
        posts = client.discover_pinchedin(limit=args.limit)
        posts = posts[:args.limit]
        print("\n💼 PinchedIn Feed:\n")
        for p in posts:
            content = _truncate(p.get("content"), 80, default="(no content)")
            author_data = p.get("author")
            if isinstance(author_data, dict):
                author = _to_text(author_data.get("name"), default="?")
            else:
                author = _to_text(author_data, default="?")
            likes = p.get("likesCount", 0)
            comments = p.get("commentsCount", 0)
            print(f"  {content}")
            print(f"    by {author} | {likes} likes | {comments} comments\n")

    elif args.platform == "pinchedin-jobs":
        jobs = client.discover_pinchedin_jobs(limit=args.limit)
        jobs = jobs[:args.limit]
        print("\n💼 PinchedIn Jobs:\n")
        for j in jobs:
            title = _to_text(j.get("title"), default="?")
            poster_data = j.get("poster")
            if isinstance(poster_data, dict):
                poster = _to_text(poster_data.get("name"), default="?")
            else:
                poster = _to_text(poster_data, default="?")
            status = _to_text(j.get("status"), default="?")
            print(f"  {title}")
            print(f"    by {poster} | status: {status}\n")

    elif args.platform == "clawtasks":
        bounties = client.discover_clawtasks(limit=args.limit)
        bounties = bounties[:args.limit]
        print("\n🎯 ClawTasks Bounties:\n")
        for b in bounties:
            title = _to_text(b.get("title"), default="(untitled bounty)")
            tags_data = b.get("tags")
            if isinstance(tags_data, list):
                tags = ", ".join(_to_text(tag) for tag in tags_data)
            elif tags_data is None:
                tags = ""
            else:
                tags = _to_text(tags_data)
            status = _to_text(b.get("status"), default="unknown")
            deadline_hours = _to_text(b.get("deadline_hours"), default="?")
            print(f"  {title}")
            print(f"    status: {status} | tags: {tags} | deadline: {deadline_hours}h\n")

    elif args.platform == "clawnews":
        stories = client.discover_clawnews(limit=args.limit)
        stories = stories[:args.limit]
        print("\n📰 ClawNews Stories:\n")
        for s in stories:
            title = s.get("headline", s.get("title", "?"))
            print(f"  {title}")
            print(f"    {s.get('url', '')}\n")

    elif args.platform == "agentchan":
        board = args.board or "ai"
        threads = client.discover_agentchan(board=board, limit=args.limit)
        threads = threads[:args.limit]
        print(f"\n🤖 AgentChan /{board}/:\n")
        for t in threads:
            subject = t.get("subject", t.get("title", "(untitled)"))
            replies = t.get("reply_count", t.get("replyCount", 0))
            author = t.get("author_name", t.get("author", "anon"))
            print(f"  {subject}")
            print(f"    by {author} | {replies} replies\n")

    elif args.platform == "thecolony":
        colony = args.board or None
        posts = client.discover_colony(colony=colony, limit=args.limit)
        posts = posts[:args.limit]
        label = f"c/{colony}" if colony else "all"
        print(f"\n🏰 The Colony {label}:\n")
        for p in posts:
            title = _to_text(p.get("title"), default="(untitled)")
            body = _truncate(p.get("body", p.get("safe_text", "")), 60, default="")
            author_data = p.get("author", {})
            author = author_data.get("display_name", author_data.get("username", "?")) if isinstance(author_data, dict) else str(author_data)
            ptype = p.get("post_type", p.get("type", "discussion"))
            comments = p.get("comment_count", 0)
            post_id = _to_text(p.get("id"), default="?")
            print(f"  {title}")
            print(f"    [{ptype}] by {author} | {comments} comments | id:{post_id[:8]}\n")

    elif args.platform == "moltx":
        posts = client.discover_moltx(limit=args.limit)
        posts = posts[:args.limit]
        print("\n📱 MoltX Feed:\n")
        for p in posts:
            content = _truncate(p.get("content"), 80, default="(no content)")
            author = _to_text(p.get("author_display_name"), default=_to_text(p.get("author_name"), default="?"))
            likes = p.get("like_count", 0)
            replies = p.get("reply_count", 0)
            print(f"  {content}")
            print(f"    by {author} | {likes} likes | {replies} replies\n")

    elif args.platform == "moltexchange":
        questions = client.discover_moltexchange(limit=args.limit)
        questions = questions[:args.limit]
        print("\n🔄 MoltExchange Questions:\n")
        for q in questions:
            title = _to_text(q.get("title"), default=_truncate(q.get("content"), 60, default="?"))
            answers = q.get("answer_count", q.get("answers", 0))
            author_data = q.get("author", q.get("agent_name", "?"))
            if isinstance(author_data, dict):
                author = _to_text(author_data.get("display_name"), default=_to_text(author_data.get("username"), default="?"))
            else:
                author = _to_text(author_data, default="?")
            print(f"  {title}")
            print(f"    by {author} | {answers} answers\n")

    elif args.platform == "arxiv":
        query = getattr(args, "category", None) or "AI"
        papers = client.discover_arxiv(query=query, limit=args.limit)
        papers = papers[:args.limit]
        print("\n📄 ArXiv Papers:\n")
        for p in papers:
            title = _to_text(p.get("title"), default="(untitled)")
            authors = p.get("authors", [])
            author_str = ", ".join(authors[:3])
            if len(authors) > 3:
                author_str += f" +{len(authors) - 3} more"
            url = _to_text(p.get("url"), default="(no url)")
            published = _to_text(p.get("published", ""), default="")[:10]
            cats = ", ".join(p.get("categories", [])[:3])
            print(f"  {title}")
            print(f"    by {author_str} | {published} | {cats}")
            print(f"    {url}\n")

    elif args.platform == "youtube":
        query = getattr(args, "category", None) or "AI agents"
        videos = client.discover_youtube(query=query, limit=args.limit)
        videos = videos[:args.limit]
        print("\n▶ YouTube Videos:\n")
        for v in videos:
            title = _to_text(v.get("title"), default="(untitled)")
            channel = _to_text(v.get("channel"), default="unknown")
            url = _to_text(v.get("url"), default="(no url)")
            views = v.get("views", "")
            views_str = f" | {views} views" if views else ""
            print(f"  {title}")
            print(f"    by {channel}{views_str}")
            print(f"    {url}\n")

    elif args.platform == "podcasts":
        query = getattr(args, "category", None) or "artificial intelligence"
        shows = client.discover_podcasts(query=query, limit=args.limit)
        shows = shows[:args.limit]
        print("\n🎙 Podcasts:\n")
        for s in shows:
            name = _to_text(s.get("name"), default="(unnamed)")
            artist = _to_text(s.get("artist"), default="unknown")
            genre = _to_text(s.get("genre"), default="")
            ep_count = s.get("episode_count", 0)
            url = _to_text(s.get("url"), default="(no url)")
            print(f"  {name}")
            print(f"    by {artist} | {genre} | {ep_count} episodes")
            print(f"    {url}\n")

    elif args.platform == "bluesky":
        query = getattr(args, "category", None) or "AI agents"
        posts = client.discover_bluesky(query=query, limit=args.limit)
        posts = posts[:args.limit]
        print("\n🦋 Bluesky Posts:\n")
        for p in posts:
            text = _truncate(p.get("text"), 80, default="(no content)")
            author = _to_text(p.get("author_name"), default=_to_text(p.get("author_handle"), default="unknown"))
            likes = p.get("likes", 0)
            url = _to_text(p.get("url"), default="(no url)")
            print(f"  {text}")
            print(f"    by {author} | {likes} likes")
            print(f"    {url}\n")

    elif args.platform == "farcaster":
        query = getattr(args, "category", None) or "AI agents"
        casts = client.discover_farcaster(query=query, limit=args.limit)
        casts = casts[:args.limit]
        print("\n🟪 Farcaster Casts:\n")
        for c in casts:
            text = _truncate(c.get("text"), 80, default="(no content)")
            author = _to_text(c.get("author_name"), default=_to_text(c.get("author_username"), default="unknown"))
            likes = c.get("likes", 0)
            url = _to_text(c.get("url"), default="(no url)")
            print(f"  {text}")
            print(f"    by {author} | {likes} likes")
            print(f"    {url}\n")

    elif args.platform == "semantic-scholar":
        query = getattr(args, "category", None) or "large language models"
        papers = client.discover_semantic_scholar(query=query, limit=args.limit)
        papers = papers[:args.limit]
        print("\n🎓 Semantic Scholar Papers:\n")
        for p in papers:
            title = _to_text(p.get("title"), default="(untitled)")
            authors = p.get("authors", [])
            author_str = ", ".join(authors[:3]) + ("..." if len(authors) > 3 else "")
            year = p.get("year", "")
            citations = p.get("citation_count", 0)
            url = _to_text(p.get("url"), default="(no url)")
            print(f"  {title}")
            print(f"    by {author_str} | {year} | {citations} citations")
            print(f"    {url}\n")

    elif args.platform == "openreview":
        query = getattr(args, "category", None) or "large language models"
        papers = client.discover_openreview(query=query, limit=args.limit)
        papers = papers[:args.limit]
        print("\n📋 OpenReview Papers:\n")
        for p in papers:
            title = _to_text(p.get("title"), default="(untitled)")
            authors = p.get("authors", [])
            author_str = ", ".join(authors[:3]) + ("..." if len(authors) > 3 else "")
            venue = _to_text(p.get("venue"), default="")
            url = _to_text(p.get("url"), default="(no url)")
            print(f"  {title}")
            print(f"    by {author_str} | {venue}")
            print(f"    {url}\n")

    elif args.platform == "mastodon":
        query = getattr(args, "category", None) or "AI"
        posts = client.discover_mastodon(query=query, limit=args.limit)
        posts = posts[:args.limit]
        print("\n🐘 Mastodon Posts:\n")
        for p in posts:
            text = _truncate(p.get("text"), 80, default="(no content)")
            author = _to_text(p.get("author_name"), default=_to_text(p.get("author_acct"), default="unknown"))
            favs = p.get("favourites", 0)
            url = _to_text(p.get("url"), default="(no url)")
            print(f"  {text}")
            print(f"    by {author} | {favs} favourites")
            print(f"    {url}\n")

    elif args.platform == "nostr":
        query = getattr(args, "category", None) or "AI"
        events = client.discover_nostr(query=query, limit=args.limit)
        events = events[:args.limit]
        print("\n🔮 Nostr Events:\n")
        for e in events:
            content = _truncate(e.get("content"), 80, default="(no content)")
            pubkey = _to_text(e.get("pubkey"), default="unknown")[:16]
            url = _to_text(e.get("url"), default="(no url)")
            print(f"  {content}")
            print(f"    by {pubkey}...")
            print(f"    {url}\n")

    elif args.platform == "all":
        all_content = client.discover_all(limit=args.limit)
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
            "thecolony": "Colony posts",
            "moltx": "MoltX posts",
            "moltexchange": "MoltExchange questions",
            "arxiv": "ArXiv papers",
            "youtube": "YouTube videos",
            "podcasts": "Podcasts",
            "bluesky": "Bluesky posts",
            "farcaster": "Farcaster casts",
            "semantic_scholar": "Semantic Scholar papers",
            "openreview": "OpenReview papers",
            "mastodon": "Mastodon posts",
            "nostr": "Nostr events",
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

    key = getattr(args, "idempotency_key", None)
    ttl_seconds = int(getattr(args, "idempotency_ttl", DEFAULT_IDEMPOTENCY_TTL))

    if args.platform == "clawcities":
        scope = f"comment:clawcities:{args.target or ''}"
        payload = {"site_name": args.target, "body": args.message}
        if getattr(args, "dry_run", False):
            _print_dry_run_preview("clawcities", payload, text_value=args.message)
            return
        if _idempotency_is_duplicate(scope, key, ttl_seconds):
            print(f"\n⚠️  Idempotency hit: skipped duplicate send (key={key})")
            return
        result = client.comment_clawcities(args.target, args.message)
        _idempotency_mark(scope, key, ttl_seconds)
        print(f"\n✓ Comment posted to {args.target}")
        print(f"  ID: {result.get('comment', {}).get('id')}")

    elif args.platform == "clawsta":
        scope = "comment:clawsta"
        payload = {"content": args.message, "imageUrl": "https://bottube.ai/static/og-banner.png"}
        if getattr(args, "dry_run", False):
            _print_dry_run_preview("clawsta", payload, text_value=args.message, media_meta={"kind": "image", "source": "default_og_banner"})
            return
        if _idempotency_is_duplicate(scope, key, ttl_seconds):
            print(f"\n⚠️  Idempotency hit: skipped duplicate send (key={key})")
            return
        result = client.post_clawsta(args.message)
        _idempotency_mark(scope, key, ttl_seconds)
        print(f"\n✓ Posted to Clawsta")
        print(f"  ID: {result.get('id')}")

    elif args.platform == "pinchedin":
        if args.target:
            scope = f"comment:pinchedin:{args.target}"
            payload = {"post_id": args.target, "content": args.message}
            if getattr(args, "dry_run", False):
                _print_dry_run_preview("pinchedin", payload, text_value=args.message)
                return
            if _idempotency_is_duplicate(scope, key, ttl_seconds):
                print(f"\n⚠️  Idempotency hit: skipped duplicate send (key={key})")
                return
            result = client.comment_pinchedin(args.target, args.message)
            _idempotency_mark(scope, key, ttl_seconds)
            print(f"\n✓ Comment posted on PinchedIn post {args.target[:8]}...")
            print(f"  ID: {result.get('id', 'ok')}")
        else:
            print("Error: --target post_id required for PinchedIn comments")
            sys.exit(1)

    elif args.platform == "fourclaw":
        if args.target:
            scope = f"comment:fourclaw:{args.target}"
            payload = {"thread_id": args.target, "content": args.message}
            if getattr(args, "dry_run", False):
                _print_dry_run_preview("fourclaw", payload, text_value=args.message)
                return
            if _idempotency_is_duplicate(scope, key, ttl_seconds):
                print(f"\n⚠️  Idempotency hit: skipped duplicate send (key={key})")
                return
            result = client.reply_fourclaw(args.target, args.message)
            _idempotency_mark(scope, key, ttl_seconds)
            print(f"\n✓ Reply posted to thread {args.target[:8]}...")
            print(f"  ID: {result.get('reply', {}).get('id', 'ok')}")
        else:
            print("Error: --target thread_id required for 4claw replies")
            sys.exit(1)

    elif args.platform == "thecolony":
        if args.target:
            scope = f"comment:thecolony:{args.target}"
            payload = {"post_id": args.target, "content": args.message}
            if getattr(args, "dry_run", False):
                _print_dry_run_preview("thecolony", payload, text_value=args.message)
                return
            if _idempotency_is_duplicate(scope, key, ttl_seconds):
                print(f"\n⚠️  Idempotency hit: skipped duplicate send (key={key})")
                return
            result = client.reply_colony(args.target, args.message)
            _idempotency_mark(scope, key, ttl_seconds)
            print(f"\n✓ Reply posted to Colony post {args.target[:8]}...")
            print(f"  ID: {result.get('id', 'ok')}")
        else:
            print("Error: --target post_id required for Colony replies")
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

    key = getattr(args, "idempotency_key", None)
    ttl_seconds = int(getattr(args, "idempotency_ttl", DEFAULT_IDEMPOTENCY_TTL))

    if args.platform == "fourclaw":
        if not args.board:
            print("Error: --board required for 4claw (e.g. b, singularity, crypto)")
            sys.exit(1)
        scope = f"post:fourclaw:{args.board}:{args.title}"
        image_prompt = getattr(args, "image", None)
        template = getattr(args, "template", None)
        palette = getattr(args, "palette", None)
        payload = {
            "board": args.board,
            "title": args.title,
            "content": args.message,
            "image_prompt": image_prompt,
            "template": template,
            "palette": palette,
        }
        media_meta = {"kind": "image", "generated_from_prompt": bool(image_prompt)} if image_prompt else None
        if getattr(args, "dry_run", False):
            _print_dry_run_preview("fourclaw", payload, text_value=args.message, media_meta=media_meta)
            return
        if _idempotency_is_duplicate(scope, key, ttl_seconds):
            print(f"\n⚠️  Idempotency hit: skipped duplicate send (key={key})")
            return
        result = client.post_fourclaw(
            args.board, args.title, args.message,
            image_prompt=image_prompt, template=template, palette=palette,
        )
        _idempotency_mark(scope, key, ttl_seconds)
        thread = result.get("thread", {})
        print(f"\n✓ Thread created on /{args.board}/")
        print(f"  Title: {thread.get('title')}")
        print(f"  ID: {thread.get('id')}")
        if image_prompt:
            print(f"  Image: generated from '{image_prompt}'")

    elif args.platform == "moltbook":
        scope = f"post:moltbook:{args.board or 'tech'}:{args.title}"
        payload = {"title": args.title, "content": args.message, "submolt_name": args.board or "tech"}
        if getattr(args, "dry_run", False):
            _print_dry_run_preview("moltbook", payload, text_value=args.message)
            return
        if _idempotency_is_duplicate(scope, key, ttl_seconds):
            print(f"\n⚠️  Idempotency hit: skipped duplicate send (key={key})")
            return
        result = client.post_moltbook(args.message, args.title, submolt=args.board or "tech")
        _idempotency_mark(scope, key, ttl_seconds)
        print(f"\n✓ Posted to m/{args.board or 'tech'}")
        print(f"  ID: {result.get('id', 'ok')}")

    elif args.platform == "pinchedin":
        scope = f"post:pinchedin:{args.title}"
        payload = {"content": args.message}
        if getattr(args, "dry_run", False):
            _print_dry_run_preview("pinchedin", payload, text_value=args.message)
            return
        if _idempotency_is_duplicate(scope, key, ttl_seconds):
            print(f"\n⚠️  Idempotency hit: skipped duplicate send (key={key})")
            return
        result = client.post_pinchedin(args.message)
        _idempotency_mark(scope, key, ttl_seconds)
        print(f"\n✓ Posted to PinchedIn")
        print(f"  ID: {result.get('id', 'ok')}")

    elif args.platform == "clawtasks":
        scope = f"post:clawtasks:{args.title}"
        tags = args.board.split(",") if args.board else None
        payload = {"title": args.title, "description": args.message, "tags": tags}
        if getattr(args, "dry_run", False):
            _print_dry_run_preview("clawtasks", payload, text_value=args.message)
            return
        if _idempotency_is_duplicate(scope, key, ttl_seconds):
            print(f"\n⚠️  Idempotency hit: skipped duplicate send (key={key})")
            return
        result = client.post_clawtask(args.title, args.message, tags=tags)
        _idempotency_mark(scope, key, ttl_seconds)
        print(f"\n✓ Bounty posted on ClawTasks")
        print(f"  ID: {result.get('id', 'ok')}")

    elif args.platform == "agentchan":
        board = args.board or "ai"
        scope = f"post:agentchan:{board}:{args.title}"
        payload = {"board": board, "content": args.message}
        if getattr(args, "dry_run", False):
            _print_dry_run_preview("agentchan", payload, text_value=args.message)
            return
        if _idempotency_is_duplicate(scope, key, ttl_seconds):
            print(f"\n⚠️  Idempotency hit: skipped duplicate send (key={key})")
            return
        result = client.post_agentchan(board=board, content=args.message)
        _idempotency_mark(scope, key, ttl_seconds)
        if result:
            print(f"\n✓ Thread posted on AgentChan /{board}/")
            print(f"  ID: {result.get('data', {}).get('id', result.get('id', 'ok'))}")
        else:
            print("\n✗ Failed to post on AgentChan")

    elif args.platform == "thecolony":
        colony = args.board or "general"
        scope = f"post:thecolony:{colony}:{args.title}"
        payload = {"colony": colony, "body": args.message}
        if getattr(args, "dry_run", False):
            _print_dry_run_preview("thecolony", payload, text_value=args.message)
            return
        if _idempotency_is_duplicate(scope, key, ttl_seconds):
            print(f"\n⚠️  Idempotency hit: skipped duplicate send (key={key})")
            return
        result = client.post_colony(colony, args.message)
        _idempotency_mark(scope, key, ttl_seconds)
        print(f"\n✓ Posted to c/{colony} on The Colony")
        print(f"  ID: {result.get('id', 'ok')}")

    elif args.platform == "moltx":
        scope = f"post:moltx:{args.title}"
        payload = {"content": args.message}
        if getattr(args, "dry_run", False):
            _print_dry_run_preview("moltx", payload, text_value=args.message)
            return
        if _idempotency_is_duplicate(scope, key, ttl_seconds):
            print(f"\n⚠️  Idempotency hit: skipped duplicate send (key={key})")
            return
        result = client.post_moltx(args.message)
        _idempotency_mark(scope, key, ttl_seconds)
        print(f"\n✓ Posted to MoltX")
        print(f"  ID: {result.get('id', 'ok')}")

    elif args.platform == "moltexchange":
        scope = f"post:moltexchange:{args.title}"
        tags = args.board.split(",") if args.board else None
        payload = {"title": args.title, "content": args.message, "tags": tags}
        if getattr(args, "dry_run", False):
            _print_dry_run_preview("moltexchange", payload, text_value=args.message)
            return
        if _idempotency_is_duplicate(scope, key, ttl_seconds):
            print(f"\n⚠️  Idempotency hit: skipped duplicate send (key={key})")
            return
        result = client.post_moltexchange(args.title, args.message, tags=tags)
        _idempotency_mark(scope, key, ttl_seconds)
        print(f"\n✓ Question posted on MoltExchange")
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
    parser.add_argument("--version", action="version", version="grazer 1.9.1")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # discover command
    discover_parser = subparsers.add_parser("discover", help="Discover trending content")
    discover_parser.add_argument(
        "-p", "--platform",
        choices=["bottube", "moltbook", "clawcities", "clawsta", "fourclaw", "pinchedin", "pinchedin-jobs", "clawtasks", "clawnews", "agentchan", "thecolony", "moltx", "moltexchange", "arxiv", "youtube", "podcasts", "bluesky", "farcaster", "semantic-scholar", "openreview", "mastodon", "nostr", "all"],
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
        choices=["clawcities", "clawsta", "fourclaw", "pinchedin", "thecolony"],
        required=True,
        help="Platform"
    )
    comment_parser.add_argument("-t", "--target", help="Target (site name, post/thread ID)")
    comment_parser.add_argument("-m", "--message", required=True, help="Comment message")
    comment_parser.add_argument("--dry-run", action="store_true", help="Preview normalized payload without publishing")
    comment_parser.add_argument("--idempotency-key", help="Skip duplicate sends for same key within TTL window")
    comment_parser.add_argument("--idempotency-ttl", type=int, default=DEFAULT_IDEMPOTENCY_TTL, help="Idempotency key TTL in seconds (default: 86400)")

    # post command
    post_parser = subparsers.add_parser("post", help="Create a new post or thread")
    post_parser.add_argument(
        "-p", "--platform",
        choices=["fourclaw", "moltbook", "pinchedin", "clawtasks", "agentchan", "thecolony", "moltx", "moltexchange"],
        required=True,
        help="Platform"
    )
    post_parser.add_argument("-b", "--board", help="Board/submolt name")
    post_parser.add_argument("-t", "--title", required=True, help="Post/thread title")
    post_parser.add_argument("-m", "--message", required=True, help="Post content")
    post_parser.add_argument("-i", "--image", help="Generate SVG image from this prompt")
    post_parser.add_argument("--template", help="SVG template: circuit, wave, grid, badge, terminal")
    post_parser.add_argument("--palette", help="Color palette: tech, crypto, retro, nature, dark, fire, ocean")
    post_parser.add_argument("--dry-run", action="store_true", help="Preview normalized payload without publishing")
    post_parser.add_argument("--idempotency-key", help="Skip duplicate sends for same key within TTL window")
    post_parser.add_argument("--idempotency-ttl", type=int, default=DEFAULT_IDEMPOTENCY_TTL, help="Idempotency key TTL in seconds (default: 86400)")

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
