"""Every place a version is declared must agree, and none may be hardcoded in the CLI.

Grazer publishes to PyPI and npm from the same tree, and the Homebrew formula
wraps the npm tarball. When the four version strings drift (it happened: the
npm CLI reported 1.9.1 while 2.0.1 shipped), users and the formula test cannot
trust `grazer --version`.
"""

import json
import pathlib
import re

import grazer

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _setup_py_version() -> str:
    src = (REPO_ROOT / "setup.py").read_text(encoding="utf-8")
    match = re.search(r'version\s*=\s*"([^"]+)"', src)
    assert match, "setup.py must declare version=\"...\""
    return match.group(1)


def _package_json():
    return json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))


def test_python_and_npm_versions_agree():
    pkg = _package_json()
    assert grazer.__version__ == _setup_py_version()
    assert grazer.__version__ == pkg["version"]
    assert grazer.__version__ == pkg["claudeSkill"]["version"]


def test_ts_cli_does_not_hardcode_version():
    cli_ts = (REPO_ROOT / "src" / "cli.ts").read_text(encoding="utf-8")
    hardcoded = re.search(r"\.version\(\s*['\"]\d+\.\d+\.\d+['\"]\s*\)", cli_ts)
    assert hardcoded is None, f"src/cli.ts hardcodes a version: {hardcoded.group(0)}"
    assert "package.json" in cli_ts, "src/cli.ts should read its version from package.json"


def test_python_cli_reports_package_version(capsys):
    import sys

    from grazer.cli import main

    argv = sys.argv
    sys.argv = ["grazer", "--version"]
    try:
        try:
            main()
        except SystemExit as exc:  # argparse's version action exits 0
            assert exc.code in (0, None)
    finally:
        sys.argv = argv
    assert grazer.__version__ in capsys.readouterr().out


def test_debian_packaging_tracks_package_version():
    pkg = _package_json()
    control = (REPO_ROOT / "debian" / "control").read_text(encoding="utf-8")
    match = re.search(r"^Version:\s*(\S+)\s*$", control, re.MULTILINE)
    assert match, "debian/control must declare Version"
    assert match.group(1) == pkg["version"]

    build_script = (REPO_ROOT / "debian" / "build-deb.sh").read_text(encoding="utf-8")
    assert "package.json" in build_script, "Debian build must source its version from package.json"
    assert not re.search(r"^VERSION=[\"\']\d+\.\d+\.\d+", build_script, re.MULTILINE), (
        "debian/build-deb.sh must not hardcode a release version"
    )
