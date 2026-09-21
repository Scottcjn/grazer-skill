"""Opportunity ranking helpers for Moltbook discovery.

The scorer intentionally requires a concrete compensation/hiring signal instead of
treating generic uses of "job" or "task" as paid work. That keeps scheduler,
worker-queue, and orchestration chatter out of opportunity-focused discovery.
"""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Sequence, Tuple


_SIGNAL_PATTERNS: Sequence[Tuple[str, int, re.Pattern[str]]] = (
    ("bounty", 8, re.compile(r"\bbount(?:y|ies)\b", re.IGNORECASE)),
    ("reward", 6, re.compile(r"\brewards?\b", re.IGNORECASE)),
    ("paid", 6, re.compile(r"\bpaid\b|\bpaying\b", re.IGNORECASE)),
    ("payout", 5, re.compile(r"\bpayouts?\b", re.IGNORECASE)),
    ("hiring", 5, re.compile(r"\bhiring\b|\bwe(?:'re| are) hiring\b", re.IGNORECASE)),
    ("commission", 5, re.compile(r"\bcommissions?\b", re.IGNORECASE)),
    ("grant", 4, re.compile(r"\bgrants?\b", re.IGNORECASE)),
    ("prize", 4, re.compile(r"\bprizes?\b", re.IGNORECASE)),
    ("compensation", 4, re.compile(r"\bcompensat(?:e|ed|ion)\b|\bstipends?\b", re.IGNORECASE)),
    ("freelance", 4, re.compile(r"\bfreelance\b|\bcontract work\b", re.IGNORECASE)),
)

_AMOUNT_RE = re.compile(
    r"(?:\$\s*\d+(?:[.,]\d+)?|\b\d+(?:[.,]\d+)?\s*(?:USD|USDC|RTC|XLM|EUR|GBP)\b)",
    re.IGNORECASE,
)

_NOISE_PATTERNS: Sequence[Tuple[str, re.Pattern[str]]] = (
    ("scheduler noise", re.compile(r"\b(?:cron|scheduled|background) (?:job|task)s?\b", re.IGNORECASE)),
    ("queue noise", re.compile(r"\b(?:job|task|worker) queues?\b|\bqueue(?:d|ing)? (?:job|task)s?\b", re.IGNORECASE)),
    ("runner noise", re.compile(r"\b(?:job|task) runners?\b", re.IGNORECASE)),
    ("orchestration noise", re.compile(r"\b(?:job|task) orchestration\b|\borchestrat(?:e|ing) (?:jobs|tasks)\b", re.IGNORECASE)),
    ("async noise", re.compile(r"\b(?:async|celery) tasks?\b", re.IGNORECASE)),
)


def _post_text(post: Dict) -> str:
    parts: List[str] = []
    for key in ("title", "content", "body", "description", "text"):
        value = post.get(key)
        if value is not None:
            parts.append(str(value))

    tags = post.get("tags")
    if isinstance(tags, (list, tuple, set)):
        parts.extend(str(tag) for tag in tags)
    elif tags:
        parts.append(str(tags))

    return "\n".join(parts)


def score_moltbook_opportunity(post: Dict) -> Tuple[int, List[str]]:
    """Return an opportunity score plus the concrete signals that produced it."""

    text = _post_text(post)
    score = 0
    signals: List[str] = []

    for label, weight, pattern in _SIGNAL_PATTERNS:
        if pattern.search(text):
            score += weight
            signals.append(label)

    if _AMOUNT_RE.search(text):
        score += 5
        signals.append("amount")

    # "job" and "task" by themselves are weak evidence. They can break ties when
    # paired with real pay/hiring language but can never clear the default gate.
    if re.search(r"\bjobs?\b", text, re.IGNORECASE):
        score += 1
    if re.search(r"\btasks?\b", text, re.IGNORECASE):
        score += 1

    for _label, pattern in _NOISE_PATTERNS:
        if pattern.search(text):
            score -= 4

    return score, signals


def rank_moltbook_opportunities(
    posts: Iterable[Dict],
    limit: int = 20,
    min_score: int = 3,
) -> List[Dict]:
    """Filter and rank Moltbook posts by paid-opportunity likelihood.

    Returned records are copies with machine-readable _opportunity_score and
    _opportunity_signals annotations.
    """

    ranked = []
    for index, post in enumerate(posts):
        if not isinstance(post, dict):
            continue
        score, signals = score_moltbook_opportunity(post)
        if score < min_score:
            continue
        enriched = dict(post)
        enriched["_opportunity_score"] = score
        enriched["_opportunity_signals"] = signals
        upvotes = post.get("upvotes", 0)
        try:
            upvotes = int(upvotes)
        except (TypeError, ValueError):
            upvotes = 0
        ranked.append((score, upvotes, -index, enriched))

    ranked.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
    return [item[3] for item in ranked[: max(0, int(limit))]]
