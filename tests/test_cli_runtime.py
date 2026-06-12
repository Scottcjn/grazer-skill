import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from grazer import __version__, cli


class ReconfigurableStream:
    def __init__(self):
        self.calls = []

    def reconfigure(self, **kwargs):
        self.calls.append(kwargs)


class CLIRuntimeTests(unittest.TestCase):
    def test_version_matches_package_version(self):
        output = io.StringIO()

        with patch.object(cli.sys, "argv", ["grazer", "--version"]):
            with redirect_stdout(output):
                with self.assertRaises(SystemExit) as exit_context:
                    cli.main()

        self.assertEqual(exit_context.exception.code, 0)
        self.assertEqual(output.getvalue().strip(), f"grazer {__version__}")

    def test_windows_console_streams_are_configured_for_utf8(self):
        stdout = ReconfigurableStream()
        stderr = ReconfigurableStream()

        with patch.object(cli.os, "name", "nt"):
            with patch.object(cli.sys, "stdout", stdout):
                with patch.object(cli.sys, "stderr", stderr):
                    cli._configure_console_encoding()

        expected = [{"encoding": "utf-8", "errors": "replace"}]
        self.assertEqual(stdout.calls, expected)
        self.assertEqual(stderr.calls, expected)

    def test_console_configuration_allows_non_reconfigurable_streams(self):
        with patch.object(cli.os, "name", "nt"):
            with patch.object(cli.sys, "stdout", io.StringIO()):
                with patch.object(cli.sys, "stderr", io.StringIO()):
                    cli._configure_console_encoding()


if __name__ == "__main__":
    unittest.main()
