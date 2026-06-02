"""Smoke tests — confirm the package imports cleanly and CLI is wired."""
from typer.testing import CliRunner

from cron_claude import __version__
from cron_claude.cli import app

runner = CliRunner()


def test_version_string_shape():
    parts = __version__.split(".")
    assert len(parts) == 3
    assert all(p.isdigit() for p in parts)


def test_cli_version_flag():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_cli_help_shows_subcommands():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for cmd in ("schedule", "run", "logs", "tui"):
        assert cmd in result.stdout
