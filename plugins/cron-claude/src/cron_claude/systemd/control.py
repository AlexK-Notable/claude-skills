"""Thin systemctl --user / journalctl --user wrapper + calendar validation.

Every helper builds an argv and runs it; non-zero exit raises SystemdError
(carrying argv + stderr). journal() streams to the terminal (no capture).
"""
from __future__ import annotations

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
    proc = _run(
        ["systemctl", "--user", "show", timer, "-p", "NextElapseUSecRealtime"],
        check=False,
    )
    raw = proc.stdout.strip().partition("=")[2]
    if not raw.isdigit() or raw == "0":
        return None
    return datetime.fromtimestamp(int(raw) / 1_000_000, tz=UTC).astimezone()


def validate_calendar(spec: str) -> None:
    # NB: systemd-analyze exits 0 even on invalid input — inspect stdout.
    proc = subprocess.run(["systemd-analyze", "calendar", spec], capture_output=True, text=True)
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
