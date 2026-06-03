"""Systemd .timer + .service unit pair writers/parsers."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cron_claude.errors import CronClaudeError

UNITS_DIR: Path = Path.home() / ".config" / "systemd" / "user"
CRON_CLAUDE_MARKER: str = "X-CronClaude-Managed=1"
UNIT_PREFIX: str = "cron-claude-"


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


def _render_service(spec: TimerSpec) -> str:
    desc = _sanitize_unit_value("description", spec.description or f"cron-claude: {spec.name}")
    name = _sanitize_unit_value("name", spec.name)
    prompt_path = _sanitize_unit_value("prompt_path", spec.prompt_path)
    exec_start = _sanitize_unit_value("exec_start", spec.exec_start)
    lines = [
        "[Unit]",
        f"Description={desc}",
        CRON_CLAUDE_MARKER,
        f"X-CronClaude-Name={name}",
        f"X-CronClaude-Prompt={prompt_path}",
        f"X-CronClaude-Runner={spec.runner}",
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
    desc = _sanitize_unit_value(
        "description", spec.description or f"cron-claude timer: {spec.name}"
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


def write_units(spec: TimerSpec) -> tuple[Path, Path]:
    UNITS_DIR.mkdir(parents=True, exist_ok=True)
    svc, tmr = unit_paths(spec.name)
    svc.write_text(_render_service(spec))
    tmr.write_text(_render_timer(spec))
    return svc, tmr


def remove_units(name: str) -> None:
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
    return TimerSpec(
        name=name,
        on_calendar=t.get("OnCalendar", ""),
        exec_start=s.get("ExecStart", ""),
        prompt_path=s.get("X-CronClaude-Prompt", ""),
        runner=s.get("X-CronClaude-Runner", ""),
        description=s.get("Description"),
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
