"""control.py builds correct argv, raises SystemdError on failure, and the
calendar validator inspects OUTPUT TEXT (systemd-analyze exits 0 on bad input)."""
import subprocess
import types

import pytest

import cron_claude.systemd.control as c
from cron_claude.errors import InvalidCalendar, SystemdError


def _fake_run(returncode=0, stdout="", stderr=""):
    def runner(argv, capture_output=False, text=False):
        runner.argv = argv
        return types.SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)
    return runner


def test_daemon_reload_argv(monkeypatch):
    fake = _fake_run()
    monkeypatch.setattr(subprocess, "run", fake)
    c.daemon_reload()
    assert fake.argv == ["systemctl", "--user", "daemon-reload"]


def test_failure_raises_systemderror(monkeypatch):
    monkeypatch.setattr(subprocess, "run", _fake_run(returncode=1, stderr="nope"))
    with pytest.raises(SystemdError):
        c.start("cron-claude-x.service")


def test_is_active_true(monkeypatch):
    monkeypatch.setattr(subprocess, "run", _fake_run(stdout="active\n"))
    assert c.is_active("cron-claude-x.timer") is True


def test_validate_calendar_accepts_valid(monkeypatch):
    monkeypatch.setattr(subprocess, "run", _fake_run(stdout="  Next elapse: Sun 2026-06-07\n"))
    c.validate_calendar("Sun 03:07")  # no raise


def test_validate_calendar_rejects_invalid(monkeypatch):
    # systemd-analyze exits 0 even here — must detect from stdout text.
    bad_out = "Failed to parse calendar specification 'x': Invalid argument\n"
    monkeypatch.setattr(subprocess, "run", _fake_run(returncode=0, stdout=bad_out))
    with pytest.raises(InvalidCalendar):
        c.validate_calendar("x")


def test_journal_text_returns_stdout(monkeypatch):
    monkeypatch.setattr(subprocess, "run", _fake_run(stdout="line1\nline2\n"))
    assert c.journal_text("cron-claude-x.service", tail=5) == "line1\nline2\n"
