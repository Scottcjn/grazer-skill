"""Guard the README's privacy promise: Grazer never phones home on its own.

The README states that installing, importing, or constructing GrazerClient makes
no network calls, and that there is no download-reporting code path. These tests
pin that down so a future "helpful" telemetry hook cannot land silently.
"""

import importlib
import json
import pathlib
import sys
from unittest.mock import patch

import pytest
import requests

import grazer.cli as _CLI_AT_COLLECTION

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


@pytest.fixture
def no_network():
    """Fail loudly if anything tries to open an HTTP connection."""

    def _boom(*args, **kwargs):  # pragma: no cover - only hit on regression
        raise AssertionError(f"unexpected network call: {args} {kwargs}")

    with patch.object(requests.Session, "request", side_effect=_boom), \
            patch.object(requests, "request", side_effect=_boom), \
            patch.object(requests, "get", side_effect=_boom), \
            patch.object(requests, "post", side_effect=_boom):
        yield


def test_import_makes_no_network_calls(no_network):
    # Re-import grazer from scratch, then put the original module objects back.
    # Leaving the fresh copies in sys.modules splits the package in two: other
    # test modules hold references to the *old* grazer.cli, while
    # patch("grazer.cli.X") resolves to the *new* one -- so their mocks silently
    # miss and the CLI under test makes real network calls.
    saved = {m: mod for m, mod in sys.modules.items() if m == "grazer" or m.startswith("grazer.")}
    for name in saved:
        del sys.modules[name]
    try:
        importlib.import_module("grazer")
    finally:
        for name in [m for m in list(sys.modules) if m == "grazer" or m.startswith("grazer.")]:
            del sys.modules[name]
        sys.modules.update(saved)

    # Regression (checked here, not in a separate test, so it does not depend
    # on test order): the reimport must not leave a second grazer.cli behind.
    # The module objects other tests imported at collection time must still be
    # the ones that patch("grazer.cli.X") resolves to.
    assert sys.modules["grazer.cli"] is _CLI_AT_COLLECTION
    assert sys.modules["grazer"].cli is _CLI_AT_COLLECTION
    for name, mod in saved.items():
        assert sys.modules[name] is mod, f"{name} was replaced by a fresh copy"


def test_constructing_client_makes_no_network_calls(no_network):
    from grazer import GrazerClient

    client = GrazerClient()
    assert client is not None


def test_no_download_reporting_code_path():
    """The tracking method was removed; make sure it does not come back."""
    from grazer import GrazerClient

    assert not hasattr(GrazerClient, "report_download")

    py_src = (REPO_ROOT / "grazer" / "__init__.py").read_text(encoding="utf-8")
    ts_src = (REPO_ROOT / "src" / "index.ts").read_text(encoding="utf-8")
    for src in (py_src, ts_src):
        assert "api/downloads" not in src
        assert "reportDownload" not in src and "report_download" not in src


def test_no_install_hooks_in_package_metadata():
    """Neither the Python nor the npm package registers an install-time script."""
    setup_py = (REPO_ROOT / "setup.py").read_text(encoding="utf-8")
    assert "cmdclass" not in setup_py
    assert "install_requires" in setup_py  # sanity: we read the right file

    package_json = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))
    scripts = package_json.get("scripts", {})
    for hook in ("preinstall", "install", "postinstall", "prepare"):
        assert hook not in scripts, f"package.json must not define an install hook: {hook}"
