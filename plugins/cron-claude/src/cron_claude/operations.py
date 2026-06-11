"""Cross-module operations orchestrating the systemd timers + control wrappers.

These live outside the thin systemd/ wrappers (which stay single-purpose:
timers = unit files, control = systemctl) and outside the UI layers (cli, tui),
so both UIs share one implementation.
"""
from __future__ import annotations

from cron_claude.systemd import control, timers


def remove_schedule(name: str) -> None:
    """Disable + stop + delete a schedule's unit pair, then reload systemd."""
    timers.validate_name(name)  # both UIs route removal here — block path traversal
    control.disable_now(timers.timer_unit(name))
    control.stop(timers.service_unit(name))
    timers.remove_units(name)
    control.daemon_reload()
