"""Systemd .timer + .service unit pair writers/parsers."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from cron_claude.errors import CronClaudeError

UNITS_DIR: Path = Path.home() / ".config" / "systemd" / "user"
CRON_CLAUDE_MARKER: str = "X-CronClaude-Managed=1"
UNIT_PREFIX: str = "cron-claude-"
NOTIFY_TEMPLATE_PREFIX: str = "cron-claude-notify-fail@"
NOTIFY_TEMPLATE_UNIT: str = f"{NOTIFY_TEMPLATE_PREFIX}.service"

_NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def validate_name(name: str) -> None:
    """Reject any name that isn't a safe unit basename / path component.

    Names become systemd unit basenames and path components — keep them strict
    to prevent unit-file path traversal (e.g. rm 'x/../../victim') and
    directive injection. Every entry point that touches unit files by name
    (add/rm/show/run/logs, TUI removal) must call this.
    """
    if not _NAME_RE.fullmatch(name):
        raise CronClaudeError(
            f"schedule name {name!r} must contain only letters, digits, "
            "hyphens, and underscores"
        )


@dataclass(slots=True, frozen=True)
class TimerSpec:
    name: str
    on_calendar: str
    exec_start: str
    prompt_path: str
    runner: str  # "script" | "claude"
    description: str | None = None
    persistent: bool = True
    randomized_delay_sec: int = 0
    timeout_sec: int | None = None


def service_unit(name: str) -> str:
    return f"{UNIT_PREFIX}{name}.service"


def timer_unit(name: str) -> str:
    return f"{UNIT_PREFIX}{name}.timer"


def unit_paths(name: str) -> tuple[Path, Path]:
    return UNITS_DIR / service_unit(name), UNITS_DIR / timer_unit(name)


def schedule_exists(name: str) -> bool:
    """True only when BOTH unit files are present (a fully-written schedule)."""
    return all(p.exists() for p in unit_paths(name))


def _sanitize_unit_value(label: str, value: str) -> str:
    """Reject newlines in any value written into a unit file (directive injection)."""
    if "\n" in value or "\r" in value:
        raise CronClaudeError(
            f"systemd unit field {label!r} must not contain newlines: {value!r}"
        )
    return value


def _escape_specifiers(value: str) -> str:
    """Escape % → %% so systemd specifier expansion can't corrupt the value."""
    return value.replace("%", "%%")


def _unescape_specifiers(value: str) -> str:
    """Inverse of _escape_specifiers for round-tripping parsed unit files."""
    return value.replace("%%", "%")


def _render_service(spec: TimerSpec) -> str:
    # Description/ExecStart undergo systemd specifier expansion → escape user %.
    # X-CronClaude-* are unknown-to-systemd bookkeeping keys (no expansion) and
    # are parsed back verbatim by _parse_spec, so they stay unescaped.
    desc = _escape_specifiers(
        _sanitize_unit_value("description", spec.description or f"cron-claude: {spec.name}")
    )
    name = _sanitize_unit_value("name", spec.name)
    prompt_path = _sanitize_unit_value("prompt_path", spec.prompt_path)
    exec_start = _escape_specifiers(_sanitize_unit_value("exec_start", spec.exec_start))
    lines = [
        "[Unit]",
        f"Description={desc}",
        CRON_CLAUDE_MARKER,
        f"X-CronClaude-Name={name}",
        f"X-CronClaude-Prompt={prompt_path}",
        f"X-CronClaude-Runner={spec.runner}",
        # Desktop notification on failure; %n = this unit's full name. The shared
        # template is installed by write_units() and intentionally never removed.
        f"OnFailure={NOTIFY_TEMPLATE_PREFIX}%n.service",
        "",
        "[Service]",
        "Type=oneshot",
        "Environment=PATH=%h/.local/bin:%h/bin:/usr/local/bin:/usr/bin:/bin",
        f"ExecStart={exec_start}",
    ]
    if spec.timeout_sec:
        lines.append(f"TimeoutStartSec={spec.timeout_sec}")
    return "\n".join(lines) + "\n"


def _render_timer(spec: TimerSpec) -> str:
    desc = _escape_specifiers(
        _sanitize_unit_value(
            "description", spec.description or f"cron-claude timer: {spec.name}"
        )
    )
    lines = [
        "[Unit]",
        f"Description={desc}",
        CRON_CLAUDE_MARKER,
        "",
        "[Timer]",
        f"OnCalendar={spec.on_calendar}",
        f"Persistent={'true' if spec.persistent else 'false'}",
    ]
    if spec.randomized_delay_sec:
        lines.append(f"RandomizedDelaySec={spec.randomized_delay_sec}")
    lines += ["", "[Install]", "WantedBy=timers.target"]
    return "\n".join(lines) + "\n"


def _render_notify_template() -> str:
    # %i = instance = full name of the failed unit (OnFailure=...@%n.service).
    lines = [
        "[Unit]",
        "Description=cron-claude failure notifier for %i",
        CRON_CLAUDE_MARKER,
        "",
        "[Service]",
        "Type=oneshot",
        "ExecStart=/usr/bin/notify-send --urgency=critical "
        '"cron-claude: %i failed" '
        '"Check: journalctl --user-unit %i -e (or: cron-claude logs <name>)"',
    ]
    return "\n".join(lines) + "\n"


def write_notify_template() -> Path:
    """Idempotently install the shared OnFailure notifier template unit.

    Installed whenever any schedule is added. NEVER auto-removed on schedule
    removal: it is shared by every cron-claude service, and a dangling
    OnFailure= on the survivors would silently kill their failure alerts.
    """
    UNITS_DIR.mkdir(parents=True, exist_ok=True)
    path = UNITS_DIR / NOTIFY_TEMPLATE_UNIT
    content = _render_notify_template()
    if not path.exists() or path.read_text() != content:
        path.write_text(content)
    return path


def write_units(spec: TimerSpec) -> tuple[Path, Path]:
    UNITS_DIR.mkdir(parents=True, exist_ok=True)
    svc, tmr = unit_paths(spec.name)
    svc.write_text(_render_service(spec))
    tmr.write_text(_render_timer(spec))
    write_notify_template()  # shared OnFailure handler, idempotent
    return svc, tmr


def remove_units(name: str) -> None:
    # Deliberately leaves NOTIFY_TEMPLATE_UNIT in place — see write_notify_template.
    svc, tmr = unit_paths(name)
    svc.unlink(missing_ok=True)
    tmr.unlink(missing_ok=True)


def _scan(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(("[", "#", ";")) or "=" not in line:
            continue
        key, _, value = line.partition("=")
        out.setdefault(key.strip(), value.strip())
    return out


def _parse_spec(name: str, svc_text: str, tmr_text: str) -> TimerSpec:
    s = _scan(svc_text)
    t = _scan(tmr_text)
    delay = t.get("RandomizedDelaySec", "")
    timeout = s.get("TimeoutStartSec", "")
    desc = s.get("Description")
    return TimerSpec(
        name=name,
        on_calendar=t.get("OnCalendar", ""),
        exec_start=_unescape_specifiers(s.get("ExecStart", "")),
        prompt_path=s.get("X-CronClaude-Prompt", ""),
        runner=s.get("X-CronClaude-Runner", ""),
        description=_unescape_specifiers(desc) if desc is not None else None,
        persistent=t.get("Persistent", "true") == "true",
        randomized_delay_sec=int(delay) if delay.isdigit() else 0,
        timeout_sec=int(timeout) if timeout.isdigit() else None,
    )


def list_units() -> list[TimerSpec]:
    if not UNITS_DIR.is_dir():
        return []
    specs: list[TimerSpec] = []
    for tmr in sorted(UNITS_DIR.glob(f"{UNIT_PREFIX}*.timer")):
        name = tmr.name[len(UNIT_PREFIX):-len(".timer")]
        svc = UNITS_DIR / service_unit(name)
        if not svc.is_file():
            continue
        svc_text = svc.read_text()
        if CRON_CLAUDE_MARKER not in svc_text:
            continue
        specs.append(_parse_spec(name, svc_text, tmr.read_text()))
    return specs
