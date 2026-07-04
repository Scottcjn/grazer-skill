import csv
import io
import json
from argparse import Namespace
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

from grazer import cli
from grazer.export import export_discovery


def test_json_export_includes_metadata_and_items(tmp_path):
    output = tmp_path / "results.json"
    count = export_discovery(
        "moltbook",
        [{"title": "Post", "author": {"name": "Alice"}}],
        "json",
        str(output),
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert count == 1
    assert payload["platform"] == "moltbook"
    assert payload["count"] == 1
    assert payload["discovered_at"].endswith("Z")
    assert payload["items"][0]["author"]["name"] == "Alice"


def test_csv_export_flattens_platforms_and_serializes_nested_values(tmp_path):
    output = tmp_path / "results.csv"
    data = {
        "bottube": [{"title": "Video", "tags": ["ai", "bitcoin"]}],
        "moltbook": [{"title": "Post", "author": {"name": "Alice"}}],
        "_errors": {},
    }

    count = export_discovery("all", data, "csv", str(output))

    with output.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert count == 2
    assert [row["platform"] for row in rows] == ["bottube", "moltbook"]
    assert json.loads(rows[0]["tags"]) == ["ai", "bitcoin"]
    assert json.loads(rows[1]["author"]) == {"name": "Alice"}


def test_markdown_export_groups_all_platform_results(tmp_path):
    output = tmp_path / "report.md"
    export_discovery(
        "all",
        {
            "bottube": [{"title": "Video"}],
            "moltbook": [{"title": "Post"}],
            "_errors": {},
        },
        "md",
        str(output),
    )

    text = output.read_text(encoding="utf-8")
    assert "# Grazer Discovery Export" in text
    assert "## bottube" in text
    assert "### 1. Video" in text
    assert "## moltbook" in text


def test_cli_bottube_export_keeps_normal_output(tmp_path):
    output = tmp_path / "videos.json"
    client = Mock()
    client.discover_bottube.return_value = [
        {"title": "Video", "agent_name": "Alice", "views": 3}
    ]
    args = Namespace(
        platform="bottube",
        category=None,
        submolt="tech",
        board=None,
        limit=5,
        include_health=False,
        export_json=str(output),
        export_csv=None,
        export_md=None,
    )

    with patch("grazer.cli.load_config", return_value={}):
        with patch("grazer.cli._make_client", return_value=client):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                cli.cmd_discover(args)

    assert "Exported 1 items" in stdout.getvalue()
    assert "BoTTube Videos" in stdout.getvalue()
    assert json.loads(output.read_text(encoding="utf-8"))["count"] == 1


def test_cli_export_flags_are_mutually_exclusive():
    source = Path(cli.__file__).read_text(encoding="utf-8")
    assert "add_mutually_exclusive_group()" in source
    assert "--export-json" in source
    assert "--export-csv" in source
    assert "--export-md" in source
