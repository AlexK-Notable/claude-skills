"""Systemd .timer + .service unit pair writers."""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

UNITS_DIR: Path = Path.home() / ".config" / "systemd" / "user"
"""Where user-scoped systemd unit files live."""

CRON_CLAUDE_MARKER: str = "X-CronClaude-Managed=1"
"""Marker placed in [Unit] sections so we can identify our own units when listing."""

UNIT_PREFIX: str = "cron-claude-"
"""All units we manage are named cron-claude-<schedule>.{service,timer}."""


@dataclass(slots=True, frozen=True)
class TimerSpec:
    """Specification for a single scheduled job, expressed as a systemd timer pair.

    Backend-agnostic of what gets executed — `exec_start` is rendered upstream
    by a runner (see `cron_claude.runners`).
    """

    name: str
    on_calendar: str
    exec_start: str
    description: str | None = None
    persistent: bool = True
    randomized_delay_sec: int = 0


def write_units(spec: TimerSpec) -> tuple[Path, Path]:
    """Materialise the .service + .timer unit files. Returns (service_path, timer_path)."""
    raise NotImplementedError


def remove_units(name: str) -> None:
    """Delete both unit files for `name`. Caller is responsible for stop/disable first."""
    raise NotImplementedError


def list_units() -> Iterable[TimerSpec]:
    """Return all cron-claude-managed timer specs by parsing existing unit files."""
    raise NotImplementedError
