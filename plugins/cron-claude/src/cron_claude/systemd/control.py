"""Thin systemctl --user / journalctl --user wrapper + calendar validation.

Every helper builds an argv and runs it; non-zero exit raises SystemdError
(carrying argv + stderr). journal() streams to the terminal (no capture).
"""
from __future__ import annotations

import os
import subprocess
from datetime import UTC, datetime

from cron_claude.errors import InvalidCalendar, SystemdError


def _run(argv: list[str], check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(argv, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise SystemdError(argv, proc.stderr or proc.stdout)
    return proc


def daemon_reload() -> None:
    _run(["systemctl", "--user", "daemon-reload"])


def enable_now(timer: str) -> None:
    _run(["systemctl", "--user", "enable", "--now", timer])


def disable_now(timer: str) -> None:
    _run(["systemctl", "--user", "disable", "--now", timer], check=False)


def start(service: str) -> None:
    _run(["systemctl", "--user", "start", service])


def stop(service: str) -> None:
    _run(["systemctl", "--user", "stop", service], check=False)


def is_active(unit: str) -> bool:
    return _run(["systemctl", "--user", "is-active", unit], check=False).stdout.strip() == "active"


def last_result(service: str) -> tuple[str, int]:
    proc = _run(
        ["systemctl", "--user", "show", service, "-p", "Result", "-p", "ExecMainStatus"],
        check=False,
    )
    kv = dict(line.split("=", 1) for line in proc.stdout.splitlines() if "=" in line)
    try:
        code = int(kv.get("ExecMainStatus", ""))
    except ValueError:
        code = -1
    return kv.get("Result", "unknown"), code


def next_elapse(timer: str) -> datetime | None:
    # --timestamp=unix makes systemctl print `@<seconds>` (verified on systemd 260;
    # the default is a formatted date like `Wed 2026-06-10 20:00:00 PDT`).
    proc = _run(
        ["systemctl", "--user", "show", timer, "-p", "NextElapseUSecRealtime", "--timestamp=unix"],
        check=False,
    )
    raw = proc.stdout.strip().partition("=")[2]
    secs = raw.removeprefix("@")
    # Empty (no next elapse), "0", or any non-@-unix form (e.g. a formatted date
    # from an older systemd that lacks --timestamp=unix) → None, never a crash.
    if not raw.startswith("@") or not secs.isdigit() or secs == "0":
        return None
    return datetime.fromtimestamp(int(secs), tz=UTC).astimezone()


def validate_calendar(spec: str) -> None:
    # NB: systemd-analyze exits 0 even on invalid input — inspect stdout.
    # Force the C locale so the "Next elapse:" marker is stable regardless of LC_ALL.
    proc = subprocess.run(
        ["systemd-analyze", "calendar", spec],
        capture_output=True,
        text=True,
        env={**os.environ, "LC_ALL": "C"},
    )
    if "Next elapse:" not in proc.stdout:
        detail = (proc.stdout + proc.stderr).strip() or "unrecognized calendar spec"
        raise InvalidCalendar(f"invalid OnCalendar {spec!r}: {detail}")


def journal(unit: str, tail: int = 50, follow: bool = False) -> int:
    argv = ["journalctl", "--user-unit", unit, "-n", str(tail)]
    if follow:
        argv.append("-f")
    return subprocess.run(argv).returncode


def journal_text(unit: str, tail: int = 50) -> str:
    """Return journal output as a string (for embedding in a TUI / string context)."""
    proc = subprocess.run(
        ["journalctl", "--user-unit", unit, "-n", str(tail), "--no-pager"],
        capture_output=True,
        text=True,
    )
    return proc.stdout or proc.stderr
