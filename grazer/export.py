"""Structured export helpers for Grazer discovery results."""

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


def _timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _platform_items(platform: str, data: Any) -> Iterable[Tuple[str, Dict[str, Any]]]:
    if platform == "all" and isinstance(data, dict):
        for name, items in data.items():
            if name.startswith("_") or not isinstance(items, list):
                continue
            for item in items:
                if isinstance(item, dict):
                    yield name, item
        return

    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                yield platform, item


def _serialize_cell(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if value is None:
        return ""
    return value


def _export_payload(platform: str, data: Any) -> Dict[str, Any]:
    discovered_at = _timestamp()
    if platform == "all" and isinstance(data, dict):
        platforms = {
            name: items
            for name, items in data.items()
            if not name.startswith("_") and isinstance(items, list)
        }
        payload = {
            "platform": platform,
            "discovered_at": discovered_at,
            "count": sum(len(items) for items in platforms.values()),
            "platforms": platforms,
        }
        metadata = {
            name.lstrip("_"): value
            for name, value in data.items()
            if name.startswith("_")
        }
        if metadata:
            payload["metadata"] = metadata
        return payload

    items = data if isinstance(data, list) else []
    return {
        "platform": platform,
        "discovered_at": discovered_at,
        "count": len(items),
        "items": items,
    }


def _write_json(path: Path, platform: str, data: Any) -> None:
    path.write_text(
        json.dumps(_export_payload(platform, data), indent=2, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )


def _write_csv(path: Path, platform: str, data: Any) -> None:
    rows: List[Dict[str, Any]] = []
    fields = {"platform"}
    for item_platform, item in _platform_items(platform, data):
        row = {"platform": item_platform}
        row.update({key: _serialize_cell(value) for key, value in item.items()})
        rows.append(row)
        fields.update(row)

    fieldnames = ["platform"] + sorted(fields - {"platform"})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_markdown(path: Path, platform: str, data: Any) -> None:
    payload = _export_payload(platform, data)
    lines = [
        "# Grazer Discovery Export",
        "",
        f"- Platform: `{platform}`",
        f"- Discovered at: `{payload['discovered_at']}`",
        f"- Items: {payload['count']}",
        "",
    ]

    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for item_platform, item in _platform_items(platform, data):
        grouped.setdefault(item_platform, []).append(item)

    for name, items in grouped.items():
        lines.extend([f"## {name}", ""])
        for index, item in enumerate(items, start=1):
            title = next(
                (
                    str(item[key]).strip()
                    for key in ("title", "headline", "name", "subject", "text", "content")
                    if item.get(key)
                ),
                f"Item {index}",
            )
            lines.extend(
                [
                    f"### {index}. {title}",
                    "",
                    "```json",
                    json.dumps(item, indent=2, ensure_ascii=False, sort_keys=True),
                    "```",
                    "",
                ]
            )

    path.write_text("\n".join(lines), encoding="utf-8")


def export_discovery(platform: str, data: Any, export_format: str, output: str) -> int:
    """Write discovery data and return the exported item count."""
    path = Path(output).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)

    if export_format == "json":
        _write_json(path, platform, data)
    elif export_format == "csv":
        _write_csv(path, platform, data)
    elif export_format == "md":
        _write_markdown(path, platform, data)
    else:
        raise ValueError(f"Unsupported export format: {export_format}")

    return sum(1 for _ in _platform_items(platform, data))
