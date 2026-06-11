"""control.py builds correct argv, raises SystemdError on failure, and the
calendar validator inspects OUTPUT TEXT (systemd-analyze exits 0 on bad input)."""
import subprocess
import types
from datetime import UTC, datetime

import pytest

import cron_claude.systemd.control as c
from cron_claude.errors import InvalidCalendar, SystemdError


def _fake_run(returncode=0, stdout="", stderr=""):
    def runner(argv, capture_output=False, text=False, **kwargs):
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


def test_last_result_success(monkeypatch):
    monkeypatch.setattr(subprocess, "run", _fake_run(stdout="Result=success\nExecMainStatus=0\n"))
    assert c.last_result("cron-claude-x.service") == ("success", 0)


def test_last_result_failed(monkeypatch):
    monkeypatch.setattr(subprocess, "run", _fake_run(stdout="Result=exit-code\nExecMainStatus=1\n"))
    assert c.last_result("cron-claude-x.service") == ("exit-code", 1)


def test_last_result_signal_keeps_negative_exit(monkeypatch):
    # Regression: a SIGKILL'd job reports ExecMainStatus=-9; must NOT collapse to -1.
    monkeypatch.setattr(subprocess, "run", _fake_run(stdout="Result=signal\nExecMainStatus=-9\n"))
    assert c.last_result("cron-claude-x.service") == ("signal", -9)


def test_last_result_empty_output(monkeypatch):
    monkeypatch.setattr(subprocess, "run", _fake_run(stdout=""))
    assert c.last_result("cron-claude-x.service") == ("unknown", -1)


def test_next_elapse_unix_form(monkeypatch):
    # Real output of `systemctl --user show -p NextElapseUSecRealtime --timestamp=unix`
    # on systemd 260: an @-prefixed unix-seconds timestamp.
    fake = _fake_run(stdout="NextElapseUSecRealtime=@1781146800\n")
    monkeypatch.setattr(subprocess, "run", fake)
    got = c.next_elapse("cron-claude-x.timer")
    assert isinstance(got, datetime)
    assert got == datetime.fromtimestamp(1781146800, tz=UTC).astimezone()
    assert "--timestamp=unix" in fake.argv


def test_next_elapse_formatted_date_is_none(monkeypatch):
    # Legacy/default format (no --timestamp=unix support): a formatted date.
    # Must degrade to None, never crash.
    fake = _fake_run(stdout="NextElapseUSecRealtime=Wed 2026-06-10 20:00:00 PDT\n")
    monkeypatch.setattr(subprocess, "run", fake)
    assert c.next_elapse("cron-claude-x.timer") is None


def test_next_elapse_zero_is_none(monkeypatch):
    monkeypatch.setattr(subprocess, "run", _fake_run(stdout="NextElapseUSecRealtime=@0\n"))
    assert c.next_elapse("cron-claude-x.timer") is None


def test_next_elapse_empty_is_none(monkeypatch):
    # No next elapse scheduled (or unknown unit): property prints empty.
    monkeypatch.setattr(subprocess, "run", _fake_run(stdout="NextElapseUSecRealtime=\n"))
    assert c.next_elapse("cron-claude-x.timer") is None
