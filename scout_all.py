#!/usr/bin/env python3
"""Scout all Grazer platforms for recent posts worth replying to."""
import requests
import json
import os


def bearer(env_name):
    """Authorization header from env var; empty dict if unset (fail-soft)."""
    tok = os.environ.get(env_name, "")
    return {"Authorization": f"Bearer {tok}"} if tok else {}

def scout(name, url, params=None, headers=None):
    print(f"\n{'='*60}")
    print(f"=== {name} ===")
    print(f"{'='*60}")
    try:
        resp = requests.get(url, params=params or {}, headers=headers or {}, timeout=15)
        print(f"  Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict):
                print(f"  Keys: {list(data.keys())[:10]}")
            elif isinstance(data, list):
                print(f"  List of {len(data)} items")
            return data
        else:
            print(f"  Body: {resp.text[:300]}")
    except Exception as e:
        print(f"  Error: {e}")
    return None

def get_author(p):
    author = p.get('author', p.get('username', p.get('user', '?')))
    if isinstance(author, dict):
        return author.get('display_name', author.get('username', author.get('name', '?')))
    return author

# ============================================================
# 1. BOTTUBE
# ============================================================
data = scout("BOTTUBE", "https://bottube.ai/api/videos", {"limit": 10})
if data:
    vids = data.get('videos', []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    for v in vids[:10]:
        cat = v.get('category', '')
        title = (v.get('title', '') or '?')[:70]
        creator = v.get('agent', v.get('creator', v.get('agent_name', '?')))
        if isinstance(creator, dict):
            creator = creator.get('name', creator.get('username', '?'))
        views = v.get('views', v.get('view_count', 0))
        vid = v.get('id', '?')
        comments = v.get('comment_count', v.get('comments', '?'))
        print(f"  [{cat}] {title}")
        print(f"    by {creator} | {views} views, {comments} comments | id={vid}")

# ============================================================
# 2. MOLTBOOK
# ============================================================
data = scout("MOLTBOOK", "https://www.moltbook.com/api/v1/posts",
    {"limit": 10},
    bearer("MOLTBOOK_TOKEN"))
if data:
    posts = data.get('posts', data.get('results', [])) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    for p in posts[:10]:
        author = get_author(p)
        submolt = p.get('submolt_name', p.get('submolt', ''))
        title = (p.get('title', '') or p.get('content', '') or '')[:80]
        upvotes = p.get('upvotes', p.get('score', 0))
        comments = p.get('comment_count', p.get('comments', 0))
        pid = p.get('id', '?')
        print(f"  [{submolt}] {title}")
        print(f"    by {author} | {upvotes} upvotes, {comments} comments | id={pid}")

# ============================================================
# 3. CLAWCITIES
# ============================================================
data = scout("CLAWCITIES", "https://clawcities.com/api/v1/sites",
    {"limit": 8},
    bearer("CLAWCITIES_TOKEN"))
if data:
    items = data.get('sites', data) if isinstance(data, dict) else data
    if isinstance(items, list):
        for s in items[:8]:
            name = s.get('display_name', s.get('name', '?'))
            url = s.get('url', s.get('site_url', '?'))
            desc = (s.get('description', '') or '')[:60]
            print(f"  {name} - {url}")
            if desc:
                print(f"    {desc}")

# ============================================================
# 4. CLAWSTA
# ============================================================
for prefix in ['', '/api']:
    data = scout(f"CLAWSTA ({prefix or 'v1'})", f"https://clawsta.io{prefix}/v1/posts",
        {"limit": 8},
        bearer("CLAWSTA_TOKEN"))
    if data:
        posts = data.get('posts', data) if isinstance(data, dict) else data
        if isinstance(posts, list):
            for p in posts[:8]:
                author = get_author(p)
                content = (p.get('content', '') or '')[:80]
                likes = p.get('likes', p.get('like_count', 0))
                pid = p.get('id', '?')
                print(f"  {content}")
                print(f"    by {author} | {likes} likes | id={pid}")
            break  # Found working endpoint

# ============================================================
# 5. 4CLAW (multiple boards)
# ============================================================
for board in ['b', 'singularity', 'crypto', 'tech', 'random']:
    data = scout(f"4CLAW /{board}/", f"https://www.4claw.org/api/v1/boards/{board}/threads",
        {"limit": 5, "includeContent": 1},
        bearer("CLAWCHAN_TOKEN"))
    if data:
        threads = data.get('threads', data) if isinstance(data, dict) else data
        if isinstance(threads, list):
            for t in threads[:5]:
                title = (t.get('title', '') or t.get('content', '') or '(untitled)')[:70]
                author = t.get('agentName', t.get('author', t.get('agent_name', 'anon')))
                replies = t.get('replyCount', t.get('reply_count', 0))
                tid = t.get('id', '?')
                print(f"  {title}")
                print(f"    by {author} | {replies} replies | id={tid}")

# ============================================================
# 6. PINCHEDIN
# ============================================================
data = scout("PINCHEDIN", "https://pinchedin.com/api/v1/feed",
    {"limit": 8},
    bearer("PINCHEDIN_TOKEN"))
if data:
    items = data.get('posts', data.get('feed', data)) if isinstance(data, dict) else data
    if isinstance(items, list):
        for p in items[:8]:
            author = get_author(p)
            title = (p.get('title', '') or p.get('content', '') or '')[:80]
            likes = p.get('likes', p.get('like_count', 0))
            pid = p.get('id', '?')
            print(f"  {title}")
            print(f"    by {author} | {likes} likes | id={pid}")

# ============================================================
# 7. CLAWTASKS
# ============================================================
data = scout("CLAWTASKS", "https://clawtasks.ai/api/v1/tasks",
    {"limit": 8},
    bearer("CLAWTASKS_TOKEN"))
if data:
    items = data.get('tasks', data) if isinstance(data, dict) else data
    if isinstance(items, list):
        for t in items[:8]:
            title = (t.get('title', '') or '?')[:70]
            status = t.get('status', '?')
            reward = t.get('reward', t.get('bounty', '?'))
            tid = t.get('id', '?')
            print(f"  {title}")
            print(f"    status={status} | reward={reward} | id={tid}")

# ============================================================
# 8. CLAWNEWS
# ============================================================
data = scout("CLAWNEWS", "https://clawnews.ai/api/v1/articles",
    {"limit": 8},
    bearer("CLAWNEWS_TOKEN"))
if data:
    items = data.get('articles', data) if isinstance(data, dict) else data
    if isinstance(items, list):
        for a in items[:8]:
            title = (a.get('title', '') or '?')[:70]
            author = get_author(a)
            aid = a.get('id', '?')
            print(f"  {title}")
            print(f"    by {author} | id={aid}")

# ============================================================
# 9. AGENTCHAN (no key, try public)
# ============================================================
data = scout("AGENTCHAN", "https://agentchan.ai/api/v1/threads",
    {"limit": 8, "board": "general"})
if data:
    threads = data.get('threads', data) if isinstance(data, dict) else data
    if isinstance(threads, list):
        for t in threads[:8]:
            title = (t.get('title', '') or t.get('content', '') or '?')[:70]
            author = get_author(t)
            tid = t.get('id', '?')
            replies = t.get('replyCount', t.get('reply_count', 0))
            print(f"  {title}")
            print(f"    by {author} | {replies} replies | id={tid}")

# ============================================================
# 10. THECOLONY (from config)
# ============================================================
for endpoint in ['feed', 'posts']:
    data = scout(f"THECOLONY (/{endpoint})", f"https://thecolony.ai/api/v1/{endpoint}",
        {"limit": 8},
        bearer("THECOLONY_TOKEN"))
    if data:
        items = data.get('posts', data.get('feed', data)) if isinstance(data, dict) else data
        if isinstance(items, list):
            for p in items[:8]:
                author = get_author(p)
                title = (p.get('title', '') or p.get('content', '') or '')[:80]
                pid = p.get('id', '?')
                print(f"  {title}")
                print(f"    by {author} | id={pid}")
            break

# ============================================================
# 11. MOLTX (from config)
# ============================================================
for prefix in ['/api/v1', '/v1']:
    data = scout(f"MOLTX ({prefix})", f"https://moltx.io{prefix}/posts",
        {"limit": 8},
        bearer("MOLTX_TOKEN"))
    if data:
        items = data.get('posts', data) if isinstance(data, dict) else data
        if isinstance(items, list):
            for p in items[:8]:
                author = get_author(p)
                title = (p.get('title', '') or p.get('content', '') or '')[:80]
                likes = p.get('likes', 0)
                pid = p.get('id', '?')
                print(f"  {title}")
                print(f"    by {author} | {likes} likes | id={pid}")
            break

# ============================================================
# 12. MOLTEXCHANGE (from config)
# ============================================================
for endpoint in ['feed', 'posts', 'listings']:
    data = scout(f"MOLTEXCHANGE (/{endpoint})", f"https://moltexchange.com/api/v1/{endpoint}",
        {"limit": 8},
        bearer("MOLTEXCHANGE_TOKEN"))
    if data:
        items = data.get('posts', data.get('listings', data.get('feed', data))) if isinstance(data, dict) else data
        if isinstance(items, list) and items:
            for p in items[:8]:
                author = get_author(p)
                title = (p.get('title', '') or p.get('content', '') or '')[:80]
                pid = p.get('id', '?')
                print(f"  {title}")
                print(f"    by {author} | id={pid}")
            break
