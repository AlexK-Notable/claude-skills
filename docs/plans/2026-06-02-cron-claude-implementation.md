# cron-claude Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish the `cron-claude` scaffold into a working, self-contained CLI that schedules/manages local `claude -p` jobs as systemd `--user` timers, installed on PATH by the monorepo `install.sh`.

**Architecture:** Fill in bodies against the scaffold's existing, stable interfaces. `systemd/` stays Claude-agnostic (writes/parses unit files, wraps `systemctl`/`journalctl`); `runners/` render the `ExecStart` (executable prompt → run directly; text prompt → `bash -c 'claude -p …'`); `cli.py` orchestrates; a Textual `tui` reuses the same modules. Deployed via a self-locating `bin/` shim + `uv sync`.

**Tech Stack:** Python 3.11+, Typer, Rich, Textual (extra), uv, systemd user timers, pytest.

**Spec:** `docs/specs/2026-06-02-cron-claude-implementation-design.md`

**Working directory for all commands:** `/home/komi/repos/claude-skills/plugins/cron-claude` (referred to below as `$CC`). Tests run with `uv run pytest`.

---

### Task 0: Environment setup

**Files:**
- Modify: `$CC/.gitignore` (ensure `.venv/` ignored)

- [ ] **Step 1: Sync the uv environment (dev + tui extras)**

Run: `cd /home/komi/repos/claude-skills/plugins/cron-claude && uv sync --extra tui`
Expected: creates `.venv/`, installs typer/rich/textual/pytest/ruff, and installs `cron-claude` editable. Ends with a summary listing installed packages.

- [ ] **Step 2: Confirm the existing smoke tests pass**

Run: `cd /home/komi/repos/claude-skills/plugins/cron-claude && uv run pytest -q`
Expected: `3 passed` (the existing `tests/test_smoke.py`).

- [ ] **Step 3: Ensure `.venv/` is gitignored**

Read `$CC/.gitignore`. If it does not already contain a line `.venv/`, append it. Confirm with:
Run: `grep -qxF '.venv/' /home/komi/repos/claude-skills/plugins/cron-claude/.gitignore && echo ok`
Expected: `ok`

- [ ] **Step 4: Commit**

```bash
cd /home/komi/repos/claude-skills
git add plugins/cron-claude/.gitignore plugins/cron-claude/uv.lock
git commit -m "chore(cron-claude): sync env, gitignore .venv"
```

---

### Task 1: Error hierarchy

**Files:**
- Create: `$CC/src/cron_claude/errors.py`
- Test: `$CC/tests/test_errors.py`

- [ ] **Step 1: Write the failing test**

Create `$CC/tests/test_errors.py`:
```python
"""Errors form a single catchable hierarchy; SystemdError carries argv+stderr."""
import pytest

from cron_claude.errors import (
    CronClaudeError,
    InvalidCalendar,
    ScheduleExists,
    ScheduleNotFound,
    SystemdError,
)


@pytest.mark.parametrize("exc", [ScheduleExists, ScheduleNotFound, InvalidCalendar, SystemdError])
def test_all_subclass_base(exc):
    assert issubclass(exc, CronClaudeError)


def test_systemd_error_carries_argv_and_stderr():
    err = SystemdError(["systemctl", "--user", "start", "x"], "  boom\n")
    assert err.argv == ["systemctl", "--user", "start", "x"]
    assert err.stderr == "boom"
    assert "boom" in str(err)
    assert "systemctl --user start x" in str(err)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd $CC && uv run pytest tests/test_errors.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'cron_claude.errors'`.

- [ ] **Step 3: Implement**

Create `$CC/src/cron_claude/errors.py`:
```python
"""cron-claude exception hierarchy. The CLI catches CronClaudeError → exit 1."""
from __future__ import annotations


class CronClaudeError(Exception):
    """Base for all cron-claude errors."""


class ScheduleExists(CronClaudeError):
    """A schedule with this name already exists."""


class ScheduleNotFound(CronClaudeError):
    """No schedule with this name exists."""


class InvalidCalendar(CronClaudeError):
    """An OnCalendar spec was rejected by systemd-analyze."""


class SystemdError(CronClaudeError):
    """A systemctl/journalctl invocation failed."""

    def __init__(self, argv: list[str], stderr: str) -> None:
        self.argv = list(argv)
        self.stderr = stderr.strip()
        super().__init__(f"command failed: {' '.join(self.argv)}\n{self.stderr}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd $CC && uv run pytest tests/test_errors.py -q`
Expected: `3 passed`.

- [ ] **Step 5: Commit**

```bash
cd /home/komi/repos/claude-skills
git add plugins/cron-claude/src/cron_claude/errors.py plugins/cron-claude/tests/test_errors.py
git commit -m "feat(cron-claude): error hierarchy"
```

---

### Task 2: Runners (ScriptRunner, ClaudeRunner, select_runner)

**Files:**
- Create: `$CC/src/cron_claude/runners/script.py`
- Modify: `$CC/src/cron_claude/runners/claude.py` (implement `to_exec_start`, drop `max_turns`, fix flags)
- Modify: `$CC/src/cron_claude/runners/__init__.py` (add `Runner` protocol + `select_runner`)
- Test: `$CC/tests/test_runners.py`

**Quoting strategy (critical):** the text runner renders `/bin/bash -c '<inner>'`. The inner uses **double quotes** for sub-parts (`"$(cat "/abs/prompt")"`, `--allowed-tools "Bash(git *) Edit"`) and the whole inner is wrapped in **single quotes** for systemd+bash. Reject any inner containing a `'` (rare: a prompt path or tool spec with a literal single quote) — fail loud rather than emit a broken `ExecStart`.

- [ ] **Step 1: Write the failing test**

Create `$CC/tests/test_runners.py`:
```python
"""Runner selection + ExecStart rendering (flags verified vs `claude --help`)."""
import os
from pathlib import Path

import pytest

from cron_claude.errors import CronClaudeError
from cron_claude.runners import select_runner
from cron_claude.runners.claude import ClaudeRunner
from cron_claude.runners.script import ScriptRunner


def _exe(p: Path) -> Path:
    p.write_text("#!/usr/bin/env bash\nexec claude -p 'hi'\n")
    p.chmod(0o755)
    return p


def test_select_executable_prompt_is_scriptrunner(tmp_path):
    runner = select_runner(_exe(tmp_path / "job"))
    assert isinstance(runner, ScriptRunner)


def test_select_text_prompt_is_clauderunner(tmp_path):
    p = tmp_path / "job.txt"
    p.write_text("summarize my inbox")
    assert isinstance(select_runner(p), ClaudeRunner)


def test_select_missing_prompt_raises(tmp_path):
    with pytest.raises(CronClaudeError):
        select_runner(tmp_path / "nope")


def test_scriptrunner_execstart_is_abs_path(tmp_path):
    p = _exe(tmp_path / "job")
    assert ScriptRunner(prompt_path=p).to_exec_start() == str(p.resolve())


def test_scriptrunner_rejects_non_executable(tmp_path):
    p = tmp_path / "job.txt"
    p.write_text("text")
    with pytest.raises(CronClaudeError):
        ScriptRunner(prompt_path=p).validate()


def test_clauderunner_renders_expected_command(tmp_path):
    p = tmp_path / "job.txt"
    p.write_text("do the thing")
    runner = ClaudeRunner(prompt_path=p, allowed_tools=("Bash(git *)", "Edit"))
    out = runner.to_exec_start()
    abs_p = str(p.resolve())
    assert out == (
        "/bin/bash -c "
        f"'claude -p \"$(cat \"{abs_p}\")\" --bare --output-format json "
        "--allowed-tools \"Bash(git *) Edit\"'"
    )


def test_clauderunner_optional_flags(tmp_path):
    p = tmp_path / "job.txt"
    p.write_text("x")
    runner = ClaudeRunner(prompt_path=p, bare=False, permission_mode="bypassPermissions", dangerously_skip=True)
    out = runner.to_exec_start()
    assert "--bare" not in out
    assert "--permission-mode bypassPermissions" in out
    assert "--dangerously-skip-permissions" in out


def test_clauderunner_rejects_bad_permission_mode(tmp_path):
    p = tmp_path / "job.txt"
    p.write_text("x")
    with pytest.raises(CronClaudeError):
        ClaudeRunner(prompt_path=p, permission_mode="dontAsk").validate()


def test_clauderunner_rejects_bad_output_format(tmp_path):
    p = tmp_path / "job.txt"
    p.write_text("x")
    with pytest.raises(CronClaudeError):
        ClaudeRunner(prompt_path=p, output_format="yaml").validate()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd $CC && uv run pytest tests/test_runners.py -q`
Expected: FAIL — `ImportError: cannot import name 'select_runner'` / `ScriptRunner`.

- [ ] **Step 3a: Implement ScriptRunner**

Create `$CC/src/cron_claude/runners/script.py`:
```python
"""ScriptRunner — ExecStart for an executable prompt script.

The script owns its own `claude -p` invocation (allowed-tools, etc.), exactly
like the legacy prompts/ playground. ExecStart is simply the absolute path —
no systemd-quoting concerns.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from cron_claude.errors import CronClaudeError


@dataclass(slots=True, frozen=True)
class ScriptRunner:
    prompt_path: Path

    def validate(self) -> None:
        p = self.prompt_path
        if not p.is_file():
            raise CronClaudeError(f"prompt is not a file: {p}")
        if not os.access(p, os.X_OK):
            raise CronClaudeError(f"prompt is not executable: {p}")

    def to_exec_start(self) -> str:
        return str(self.prompt_path.resolve())
```

- [ ] **Step 3b: Reimplement ClaudeRunner**

Replace the body of `$CC/src/cron_claude/runners/claude.py` with:
```python
"""ClaudeRunner — ExecStart for a TEXT prompt wrapped in a `claude -p` call.

Flag spellings verified against `claude --help` (2026-06-02): there is no
--max-turns, and permission_mode defaults to None (rely on the --allowed-tools
allowlist, per the safe-cron model).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from cron_claude.errors import CronClaudeError

VALID_MODES = ("acceptEdits", "auto", "bypassPermissions", "default", "plan")
VALID_FORMATS = ("text", "json", "stream-json")


@dataclass(slots=True, frozen=True)
class ClaudeRunner:
    prompt_path: Path
    allowed_tools: tuple[str, ...] = field(default_factory=tuple)
    bare: bool = True
    output_format: str = "json"
    permission_mode: str | None = None
    dangerously_skip: bool = False
    timeout_sec: int | None = 120

    def validate(self) -> None:
        if not self.prompt_path.is_file():
            raise CronClaudeError(f"prompt is not a file: {self.prompt_path}")
        if self.output_format not in VALID_FORMATS:
            raise CronClaudeError(
                f"invalid output format {self.output_format!r}; "
                f"choose one of {', '.join(VALID_FORMATS)}"
            )
        if self.permission_mode is not None and self.permission_mode not in VALID_MODES:
            raise CronClaudeError(
                f"invalid permission mode {self.permission_mode!r}; "
                f"choose one of {', '.join(VALID_MODES)}"
            )

    def to_exec_start(self) -> str:
        self.validate()
        abs_prompt = str(self.prompt_path.resolve())
        parts = ["claude", "-p", f'"$(cat "{abs_prompt}")"']
        if self.bare:
            parts.append("--bare")
        parts += ["--output-format", self.output_format]
        if self.allowed_tools:
            parts += ["--allowed-tools", f'"{" ".join(self.allowed_tools)}"']
        if self.permission_mode:
            parts += ["--permission-mode", self.permission_mode]
        if self.dangerously_skip:
            parts.append("--dangerously-skip-permissions")
        inner = " ".join(parts)
        if "'" in inner:
            raise CronClaudeError(
                "rendered command contains a single quote (prompt path or tool "
                "spec); unsupported in the bash -c wrapper"
            )
        return f"/bin/bash -c '{inner}'"
```

- [ ] **Step 3c: Add the Runner protocol + select_runner**

Replace `$CC/src/cron_claude/runners/__init__.py` with:
```python
"""Job runners — produce ExecStart= for a scheduled job.

select_runner() dispatches on the prompt: an executable prompt runs directly
(ScriptRunner); a non-executable text prompt is wrapped in `claude -p`
(ClaudeRunner). The protocol is deliberately minimal so other runner types
(plain shell, python, pacman hooks) can be added without touching systemd/.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol, runtime_checkable

from cron_claude.errors import CronClaudeError
from cron_claude.runners.claude import ClaudeRunner
from cron_claude.runners.script import ScriptRunner


@runtime_checkable
class Runner(Protocol):
    prompt_path: Path

    def validate(self) -> None: ...
    def to_exec_start(self) -> str: ...


def select_runner(
    prompt_path: Path,
    *,
    allowed_tools: tuple[str, ...] = (),
    bare: bool = True,
    output_format: str = "json",
    permission_mode: str | None = None,
    dangerously_skip: bool = False,
    timeout_sec: int | None = None,
) -> Runner:
    if not prompt_path.exists():
        raise CronClaudeError(f"prompt not found: {prompt_path}")
    if prompt_path.is_file() and os.access(prompt_path, os.X_OK):
        return ScriptRunner(prompt_path=prompt_path)
    return ClaudeRunner(
        prompt_path=prompt_path,
        allowed_tools=tuple(allowed_tools),
        bare=bare,
        output_format=output_format,
        permission_mode=permission_mode,
        dangerously_skip=dangerously_skip,
        timeout_sec=timeout_sec,
    )


__all__ = ["Runner", "ClaudeRunner", "ScriptRunner", "select_runner"]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd $CC && uv run pytest tests/test_runners.py -q`
Expected: `9 passed`.

- [ ] **Step 5: Commit**

```bash
cd /home/komi/repos/claude-skills
git add plugins/cron-claude/src/cron_claude/runners/ plugins/cron-claude/tests/test_runners.py
git commit -m "feat(cron-claude): runners — script + claude ExecStart rendering"
```

---

### Task 3: systemd unit writing/parsing (timers.py)

**Files:**
- Modify: `$CC/src/cron_claude/systemd/timers.py` (add `TimerSpec` fields; implement write/remove/list + helpers)
- Modify: `$CC/src/cron_claude/systemd/__init__.py` (export new helpers)
- Test: `$CC/tests/test_timers.py`

- [ ] **Step 1: Write the failing test**

Create `$CC/tests/test_timers.py`:
```python
"""write_units → list_units round-trip + unit file content."""
import cron_claude.systemd.timers as t
from cron_claude.systemd.timers import TimerSpec


def _spec(name="demo"):
    return TimerSpec(
        name=name,
        on_calendar="Sun 03:07",
        exec_start="/abs/prompt",
        prompt_path="/abs/prompt",
        runner="script",
        description="weekly demo",
        randomized_delay_sec=300,
        timeout_sec=120,
    )


def test_write_units_creates_pair_with_marker(tmp_path, monkeypatch):
    monkeypatch.setattr(t, "UNITS_DIR", tmp_path)
    svc, tmr = t.write_units(_spec())
    assert svc.exists() and tmr.exists()
    assert svc.name == "cron-claude-demo.service"
    assert tmr.name == "cron-claude-demo.timer"
    svc_text = svc.read_text()
    assert "X-CronClaude-Managed=1" in svc_text
    assert "Type=oneshot" in svc_text
    assert "ExecStart=/abs/prompt" in svc_text
    assert "TimeoutStartSec=120" in svc_text
    tmr_text = tmr.read_text()
    assert "OnCalendar=Sun 03:07" in tmr_text
    assert "RandomizedDelaySec=300" in tmr_text
    assert "WantedBy=timers.target" in tmr_text


def test_list_units_roundtrips(tmp_path, monkeypatch):
    monkeypatch.setattr(t, "UNITS_DIR", tmp_path)
    t.write_units(_spec("alpha"))
    t.write_units(_spec("beta"))
    got = {s.name: s for s in t.list_units()}
    assert set(got) == {"alpha", "beta"}
    a = got["alpha"]
    assert a.on_calendar == "Sun 03:07"
    assert a.exec_start == "/abs/prompt"
    assert a.runner == "script"
    assert a.prompt_path == "/abs/prompt"
    assert a.randomized_delay_sec == 300
    assert a.timeout_sec == 120


def test_remove_units(tmp_path, monkeypatch):
    monkeypatch.setattr(t, "UNITS_DIR", tmp_path)
    svc, tmr = t.write_units(_spec("gone"))
    t.remove_units("gone")
    assert not svc.exists() and not tmr.exists()


def test_list_ignores_foreign_units(tmp_path, monkeypatch):
    monkeypatch.setattr(t, "UNITS_DIR", tmp_path)
    (tmp_path / "cron-claude-x.timer").write_text("[Timer]\nOnCalendar=daily\n")
    (tmp_path / "cron-claude-x.service").write_text("[Service]\nExecStart=/bin/true\n")  # no marker
    assert list(t.list_units()) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd $CC && uv run pytest tests/test_timers.py -q`
Expected: FAIL — `NotImplementedError` from `write_units`.

- [ ] **Step 3: Implement**

Replace `$CC/src/cron_claude/systemd/timers.py` with:
```python
"""Systemd .timer + .service unit pair writers/parsers."""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

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


def _render_service(spec: TimerSpec) -> str:
    desc = spec.description or f"cron-claude: {spec.name}"
    lines = [
        "[Unit]",
        f"Description={desc}",
        CRON_CLAUDE_MARKER,
        f"X-CronClaude-Name={spec.name}",
        f"X-CronClaude-Prompt={spec.prompt_path}",
        f"X-CronClaude-Runner={spec.runner}",
        "",
        "[Service]",
        "Type=oneshot",
        "Environment=PATH=%h/.local/bin:%h/bin:/usr/local/bin:/usr/bin:/bin",
        f"ExecStart={spec.exec_start}",
    ]
    if spec.timeout_sec:
        lines.append(f"TimeoutStartSec={spec.timeout_sec}")
    return "\n".join(lines) + "\n"


def _render_timer(spec: TimerSpec) -> str:
    desc = spec.description or f"cron-claude timer: {spec.name}"
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


def list_units() -> Iterable[TimerSpec]:
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
```

- [ ] **Step 4: Update the systemd package exports**

Replace `$CC/src/cron_claude/systemd/__init__.py` with:
```python
"""Systemd user timer/service writers and managers (Claude-agnostic)."""
from cron_claude.systemd.timers import (
    CRON_CLAUDE_MARKER,
    UNIT_PREFIX,
    UNITS_DIR,
    TimerSpec,
    list_units,
    remove_units,
    service_unit,
    timer_unit,
    unit_paths,
    write_units,
)

__all__ = [
    "CRON_CLAUDE_MARKER",
    "UNIT_PREFIX",
    "UNITS_DIR",
    "TimerSpec",
    "list_units",
    "remove_units",
    "service_unit",
    "timer_unit",
    "unit_paths",
    "write_units",
]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd $CC && uv run pytest tests/test_timers.py -q`
Expected: `4 passed`.

- [ ] **Step 6: Commit**

```bash
cd /home/komi/repos/claude-skills
git add plugins/cron-claude/src/cron_claude/systemd/ plugins/cron-claude/tests/test_timers.py
git commit -m "feat(cron-claude): systemd unit write/parse/list + TimerSpec round-trip"
```

---

### Task 4: systemctl/journalctl wrapper + calendar validation (control.py)

**Files:**
- Create: `$CC/src/cron_claude/systemd/control.py`
- Test: `$CC/tests/test_control.py`

- [ ] **Step 1: Write the failing test**

Create `$CC/tests/test_control.py`:
```python
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
    monkeypatch.setattr(
        subprocess, "run",
        _fake_run(returncode=0, stdout="Failed to parse calendar specification 'x': Invalid argument\n"),
    )
    with pytest.raises(InvalidCalendar):
        c.validate_calendar("x")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd $CC && uv run pytest tests/test_control.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'cron_claude.systemd.control'`.

- [ ] **Step 3: Implement**

Create `$CC/src/cron_claude/systemd/control.py`:
```python
"""Thin systemctl --user / journalctl --user wrapper + calendar validation.

Every helper builds an argv and runs it; non-zero exit raises SystemdError
(carrying argv + stderr). journal() streams to the terminal (no capture).
"""
from __future__ import annotations

import subprocess
from datetime import datetime, timezone

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
    status = kv.get("ExecMainStatus", "")
    return kv.get("Result", "unknown"), int(status) if status.isdigit() else -1


def next_elapse(timer: str) -> datetime | None:
    proc = _run(
        ["systemctl", "--user", "show", timer, "-p", "NextElapseUSecRealtime"],
        check=False,
    )
    raw = proc.stdout.strip().partition("=")[2]
    if not raw.isdigit() or raw == "0":
        return None
    return datetime.fromtimestamp(int(raw) / 1_000_000, tz=timezone.utc).astimezone()


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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd $CC && uv run pytest tests/test_control.py -q`
Expected: `5 passed`.

- [ ] **Step 5: Commit**

```bash
cd /home/komi/repos/claude-skills
git add plugins/cron-claude/src/cron_claude/systemd/control.py plugins/cron-claude/tests/test_control.py
git commit -m "feat(cron-claude): systemctl/journalctl wrapper + calendar validation"
```

---

### Task 5: CLI command bodies (cli.py)

**Files:**
- Modify: `$CC/src/cron_claude/cli.py` (implement all six command bodies; add `schedule add` options)
- Test: `$CC/tests/test_cli.py`

- [ ] **Step 1: Write the failing test**

Create `$CC/tests/test_cli.py`:
```python
"""CLI orchestration: UNITS_DIR → tmp, control.* monkeypatched (no real systemd)."""
from pathlib import Path

from typer.testing import CliRunner

import cron_claude.systemd.timers as timers
from cron_claude.cli import app

runner = CliRunner()


def _patch(monkeypatch, tmp_path):
    monkeypatch.setattr(timers, "UNITS_DIR", tmp_path)
    import cron_claude.cli as cli
    monkeypatch.setattr(cli.control, "validate_calendar", lambda spec: None)
    monkeypatch.setattr(cli.control, "daemon_reload", lambda: None)
    monkeypatch.setattr(cli.control, "enable_now", lambda t: None)
    monkeypatch.setattr(cli.control, "disable_now", lambda t: None)
    monkeypatch.setattr(cli.control, "stop", lambda s: None)
    monkeypatch.setattr(cli.control, "next_elapse", lambda t: None)
    monkeypatch.setattr(cli.control, "last_result", lambda s: ("success", 0))


def test_add_then_list(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    prompt = tmp_path / "job.txt"
    prompt.write_text("summarize")
    r = runner.invoke(app, ["schedule", "add", "demo", "--when", "Sun 03:07", "--prompt", str(prompt)])
    assert r.exit_code == 0, r.output
    assert (tmp_path / "cron-claude-demo.timer").exists()
    r2 = runner.invoke(app, ["schedule", "list"])
    assert r2.exit_code == 0
    assert "demo" in r2.output


def test_add_duplicate_fails(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    prompt = tmp_path / "job.txt"
    prompt.write_text("x")
    args = ["schedule", "add", "dup", "--when", "daily", "--prompt", str(prompt)]
    assert runner.invoke(app, args).exit_code == 0
    r = runner.invoke(app, args)
    assert r.exit_code == 1
    assert "already exists" in r.output


def test_rm(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    prompt = tmp_path / "job.txt"
    prompt.write_text("x")
    runner.invoke(app, ["schedule", "add", "bye", "--when", "daily", "--prompt", str(prompt)])
    r = runner.invoke(app, ["schedule", "rm", "bye", "--force"])
    assert r.exit_code == 0
    assert not (tmp_path / "cron-claude-bye.timer").exists()


def test_rm_missing_fails(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    r = runner.invoke(app, ["schedule", "rm", "ghost", "--force"])
    assert r.exit_code == 1
    assert "not found" in r.output


def test_list_json(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    prompt = tmp_path / "job.txt"
    prompt.write_text("x")
    runner.invoke(app, ["schedule", "add", "j", "--when", "daily", "--prompt", str(prompt)])
    r = runner.invoke(app, ["schedule", "list", "--json"])
    assert r.exit_code == 0
    assert '"name": "j"' in r.output


def test_add_scaffold_creates_executable(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    prompt = tmp_path / "prompts" / "newjob"
    r = runner.invoke(app, ["schedule", "add", "nj", "--when", "daily", "--prompt", str(prompt), "--scaffold"])
    assert r.exit_code == 0, r.output
    assert prompt.exists() and (prompt.stat().st_mode & 0o111)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd $CC && uv run pytest tests/test_cli.py -q`
Expected: FAIL — `schedule_add` raises `NotImplementedError` (exit code 1 with traceback, assertions fail).

- [ ] **Step 3: Implement**

Replace `$CC/src/cron_claude/cli.py` with:
```python
"""cron-claude CLI — entry point."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

from cron_claude import __version__
from cron_claude.errors import CronClaudeError, ScheduleExists, ScheduleNotFound
from cron_claude.runners import ScriptRunner, select_runner
from cron_claude.systemd import control, timers

app = typer.Typer(
    name="cron-claude",
    help="Schedule and manage local claude -p invocations via systemd user timers.",
    no_args_is_help=True,
    add_completion=False,
)
schedule_app = typer.Typer(
    help="Manage scheduled claude -p jobs (systemd .timer/.service unit pairs).",
    no_args_is_help=True,
)
app.add_typer(schedule_app, name="schedule")

console = Console()
err_console = Console(stderr=True)

_STARTER_TEMPLATE = """\
#!/usr/bin/env bash
# cron-claude prompt: {name}. Owns its own `claude -p` invocation + allowlist.
exec claude -p 'REPLACE ME: describe this scheduled job' --allowed-tools 'Bash(echo *)'
"""


def _fail(exc: CronClaudeError) -> "typer.Exit":
    err_console.print(f"[red]error:[/red] {exc}")
    return typer.Exit(code=1)


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"cron-claude {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option("--version", "-V", callback=_version_callback, is_eager=True,
                     help="Show version and exit."),
    ] = None,
) -> None:
    """cron-claude — schedule local claude -p jobs via systemd user timers."""


# ---------- schedule subcommands ----------


@schedule_app.command("add")
def schedule_add(
    name: Annotated[str, typer.Argument(help="Schedule name (systemd unit basename).")],
    when: Annotated[str, typer.Option("--when", "-w", help="OnCalendar spec, e.g. 'Sun 03:07'.")],
    prompt: Annotated[Path, typer.Option("--prompt", "-p", help="Prompt: an executable script, or a text file.")],
    description: Annotated[Optional[str], typer.Option("--description", "-d")] = None,
    timeout: Annotated[Optional[int], typer.Option("--timeout", help="TimeoutStartSec (seconds).")] = None,
    allowed_tools: Annotated[Optional[list[str]], typer.Option("--allowed-tools", help="Text prompts only; repeatable.")] = None,
    permission_mode: Annotated[Optional[str], typer.Option("--permission-mode", help="Text prompts only.")] = None,
    dangerously_skip: Annotated[bool, typer.Option("--dangerously-skip-permissions", help="Text prompts only.")] = False,
    randomized_delay: Annotated[int, typer.Option("--randomized-delay", help="RandomizedDelaySec.")] = 0,
    scaffold: Annotated[bool, typer.Option("--scaffold", "-s", help="If --prompt is missing, create an executable starter there.")] = False,
) -> None:
    """Create a new scheduled job (writes a .service + .timer unit pair)."""
    try:
        if timers.unit_paths(name)[0].exists():
            raise ScheduleExists(
                f"schedule {name!r} already exists; remove it first: cron-claude schedule rm {name}"
            )
        control.validate_calendar(when)
        prompt_path = prompt.expanduser()
        if not prompt_path.exists() and scaffold:
            prompt_path.parent.mkdir(parents=True, exist_ok=True)
            prompt_path.write_text(_STARTER_TEMPLATE.format(name=name))
            prompt_path.chmod(0o755)
            console.print(f"[yellow]scaffolded[/yellow] {prompt_path} — edit it before the first run")
        runner = select_runner(
            prompt_path,
            allowed_tools=tuple(allowed_tools or ()),
            permission_mode=permission_mode,
            dangerously_skip=dangerously_skip,
            timeout_sec=timeout,
        )
        runner.validate()
        is_script = isinstance(runner, ScriptRunner)
        if is_script and (allowed_tools or permission_mode or dangerously_skip):
            console.print("[yellow]note:[/yellow] claude flags are ignored for an executable prompt (the script owns them).")
        spec = timers.TimerSpec(
            name=name,
            on_calendar=when,
            exec_start=runner.to_exec_start(),
            prompt_path=str(prompt_path.resolve()),
            runner="script" if is_script else "claude",
            description=description,
            randomized_delay_sec=randomized_delay,
            timeout_sec=timeout,
        )
        timers.write_units(spec)
        control.daemon_reload()
        control.enable_now(timers.timer_unit(name))
    except CronClaudeError as exc:
        raise _fail(exc) from exc
    console.print(f"[green]✓[/green] scheduled [bold]{name}[/bold] → {timers.timer_unit(name)}")
    nxt = control.next_elapse(timers.timer_unit(name))
    if nxt is not None:
        console.print(f"  next run: {nxt:%Y-%m-%d %H:%M:%S %Z}")


@schedule_app.command("list")
def schedule_list(
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON instead of a table.")] = False,
) -> None:
    """List all cron-claude-managed schedules."""
    specs = list(timers.list_units())
    if json_output:
        payload = [
            {"name": s.name, "on_calendar": s.on_calendar, "runner": s.runner,
             "prompt": s.prompt_path, "description": s.description}
            for s in specs
        ]
        console.print_json(json.dumps(payload))
        return
    if not specs:
        console.print("[dim]no schedules[/dim]")
        return
    table = Table("Name", "Schedule", "Next run", "Last result", "Description")
    for s in specs:
        nxt = control.next_elapse(timers.timer_unit(s.name))
        result, _ = control.last_result(timers.service_unit(s.name))
        table.add_row(
            s.name, s.on_calendar,
            f"{nxt:%Y-%m-%d %H:%M}" if nxt else "—",
            result, s.description or "",
        )
    console.print(table)


@schedule_app.command("rm")
def schedule_rm(
    name: Annotated[str, typer.Argument(help="Schedule name.")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation.")] = False,
) -> None:
    """Remove a scheduled job (disables, stops, and deletes both unit files)."""
    try:
        if not timers.unit_paths(name)[0].exists():
            raise ScheduleNotFound(f"schedule {name!r} not found")
        if not force and not typer.confirm(f"Remove schedule {name!r}?"):
            raise typer.Abort()
        control.disable_now(timers.timer_unit(name))
        control.stop(timers.service_unit(name))
        timers.remove_units(name)
        control.daemon_reload()
    except CronClaudeError as exc:
        raise _fail(exc) from exc
    console.print(f"[green]✓[/green] removed [bold]{name}[/bold]")


@schedule_app.command("show")
def schedule_show(
    name: Annotated[str, typer.Argument(help="Schedule name.")],
) -> None:
    """Show details for a single scheduled job."""
    try:
        svc, tmr = timers.unit_paths(name)
        if not tmr.exists():
            raise ScheduleNotFound(f"schedule {name!r} not found")
    except CronClaudeError as exc:
        raise _fail(exc) from exc
    console.rule(f"{name}")
    console.print(tmr.read_text())
    console.print(svc.read_text())
    nxt = control.next_elapse(timers.timer_unit(name))
    result, status = control.last_result(timers.service_unit(name))
    console.print(f"next run: {nxt:%Y-%m-%d %H:%M:%S %Z}" if nxt else "next run: —")
    console.print(f"last result: {result} (exit {status})")
    console.rule("recent log")
    control.journal(timers.service_unit(name), tail=20)


@app.command("run")
def run_now(
    name: Annotated[str, typer.Argument(help="Schedule name.")],
) -> None:
    """Trigger a scheduled job to run immediately (blocks until it finishes)."""
    try:
        if not timers.unit_paths(name)[0].exists():
            raise ScheduleNotFound(f"schedule {name!r} not found")
        console.print(f"running [bold]{name}[/bold] …")
        control.start(timers.service_unit(name))  # oneshot: blocks until done
    except CronClaudeError as exc:
        raise _fail(exc) from exc
    result, status = control.last_result(timers.service_unit(name))
    console.print(f"[green]done[/green] — result: {result} (exit {status})")
    control.journal(timers.service_unit(name), tail=20)


@app.command("logs")
def logs(
    name: Annotated[str, typer.Argument(help="Schedule name.")],
    tail: Annotated[int, typer.Option("--tail", "-n", help="Show last N entries.")] = 50,
    follow: Annotated[bool, typer.Option("--follow", "-f", help="Tail-follow.")] = False,
) -> None:
    """View logs for a scheduled job's recent runs."""
    try:
        if not timers.unit_paths(name)[0].exists():
            raise ScheduleNotFound(f"schedule {name!r} not found")
    except CronClaudeError as exc:
        raise _fail(exc) from exc
    raise typer.Exit(control.journal(timers.service_unit(name), tail=tail, follow=follow))


@app.command("tui")
def tui() -> None:
    """Launch the interactive TUI (requires `uv sync --extra tui`)."""
    try:
        from cron_claude.tui.app import CronClaudeApp
    except ImportError as exc:
        err_console.print(
            "[red]TUI dependencies not installed.[/red] Install with: "
            "[bold]uv sync --extra tui[/bold]\n"
            f"  details: {exc}"
        )
        raise typer.Exit(code=1) from exc
    CronClaudeApp().run()


if __name__ == "__main__":
    app()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd $CC && uv run pytest tests/test_cli.py tests/test_smoke.py -q`
Expected: `6 passed` (cli) + `3 passed` (smoke).

- [ ] **Step 5: Commit**

```bash
cd /home/komi/repos/claude-skills
git add plugins/cron-claude/src/cron_claude/cli.py plugins/cron-claude/tests/test_cli.py
git commit -m "feat(cron-claude): implement all CLI command bodies"
```

---

### Task 6: Textual TUI (tui/app.py)

**Files:**
- Modify: `$CC/src/cron_claude/tui/app.py`
- Test: `$CC/tests/test_tui.py`

- [ ] **Step 1: Write the failing test**

Create `$CC/tests/test_tui.py` (Textual ships an async test pilot; this asserts the app mounts and lists schedules without a real terminal):
```python
"""TUI smoke: app mounts, populates the schedule table from list_units()."""
import pytest

import cron_claude.systemd.timers as timers
from cron_claude.systemd.timers import TimerSpec


@pytest.mark.asyncio
async def test_tui_lists_schedules(monkeypatch, tmp_path):
    monkeypatch.setattr(timers, "UNITS_DIR", tmp_path)
    timers.write_units(TimerSpec(
        name="demo", on_calendar="daily", exec_start="/bin/true",
        prompt_path="/bin/true", runner="script",
    ))
    from cron_claude.tui.app import CronClaudeApp
    app = CronClaudeApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        table = app.query_one("#schedules")
        assert table.row_count == 1
```

Add the async test dependency: in `$CC/pyproject.toml`, under `[dependency-groups] dev`, ensure `pytest-asyncio>=0.23` is present, and add under `[tool.pytest.ini_options]` the line `asyncio_mode = "auto"`. (See Step 3a.)

- [ ] **Step 2: Run test to verify it fails**

Run: `cd $CC && uv sync --extra tui && uv run pytest tests/test_tui.py -q`
Expected: FAIL — `NotImplementedError("TUI not yet implemented.")` is gone but `CronClaudeApp` has no `#schedules` table → query error.

- [ ] **Step 3a: Add the test dep**

Edit `$CC/pyproject.toml`:
- In `[dependency-groups]` `dev = [...]`, add `"pytest-asyncio>=0.23"`.
- In `[tool.pytest.ini_options]`, add a line: `asyncio_mode = "auto"`.

Run: `cd $CC && uv sync --extra tui`
Expected: resolves and installs `pytest-asyncio`.

- [ ] **Step 3b: Implement the TUI**

Replace `$CC/src/cron_claude/tui/app.py` with:
```python
"""Textual app: browse schedules, view logs, run/remove — over the systemd module."""
from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import DataTable, Footer, Header, RichLog

from cron_claude.systemd import control, timers


class CronClaudeApp(App):
    """List cron-claude schedules; r=run, x=remove, l=logs, q=quit."""

    BINDINGS = [
        Binding("r", "run", "Run"),
        Binding("x", "remove", "Remove"),
        Binding("l", "logs", "Logs"),
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        table = DataTable(id="schedules", cursor_type="row")
        table.add_columns("Name", "Schedule", "Runner", "Description")
        yield table
        yield RichLog(id="log", markup=True, highlight=True)
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_table()

    def refresh_table(self) -> None:
        table = self.query_one("#schedules", DataTable)
        table.clear()
        for s in timers.list_units():
            table.add_row(s.name, s.on_calendar, s.runner, s.description or "", key=s.name)

    def _selected(self) -> str | None:
        table = self.query_one("#schedules", DataTable)
        if table.row_count == 0:
            return None
        return table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value

    def _log(self, msg: str) -> None:
        self.query_one("#log", RichLog).write(msg)

    def action_run(self) -> None:
        name = self._selected()
        if not name:
            return
        try:
            control.start(timers.service_unit(name))
            result, status = control.last_result(timers.service_unit(name))
            self._log(f"[green]ran {name}[/green] — {result} (exit {status})")
        except Exception as exc:  # surface, don't crash the TUI
            self._log(f"[red]run failed:[/red] {exc}")

    def action_remove(self) -> None:
        name = self._selected()
        if not name:
            return
        try:
            control.disable_now(timers.timer_unit(name))
            control.stop(timers.service_unit(name))
            timers.remove_units(name)
            control.daemon_reload()
            self._log(f"[yellow]removed {name}[/yellow]")
            self.refresh_table()
        except Exception as exc:
            self._log(f"[red]remove failed:[/red] {exc}")

    def action_logs(self) -> None:
        name = self._selected()
        if not name:
            return
        self._log(f"[dim]$ journalctl --user-unit {timers.service_unit(name)} -n 20[/dim]")
        control.journal(timers.service_unit(name), tail=20)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd $CC && uv run pytest tests/test_tui.py -q`
Expected: `1 passed`.

- [ ] **Step 5: Commit**

```bash
cd /home/komi/repos/claude-skills
git add plugins/cron-claude/src/cron_claude/tui/app.py plugins/cron-claude/tests/test_tui.py plugins/cron-claude/pyproject.toml plugins/cron-claude/uv.lock
git commit -m "feat(cron-claude): functional Textual TUI"
```

---

### Task 7: Packaging — self-locating shim + install.sh uv-sync step

**Files:**
- Create: `$CC/bin/cron-claude` (executable shim)
- Modify: `/home/komi/repos/claude-skills/install.sh` (add uv-sync step for Python plugins)

- [ ] **Step 1: Create the shim**

Create `$CC/bin/cron-claude`:
```bash
#!/usr/bin/env bash
# Self-locating shim → the plugin's uv-managed venv entry point.
# Auto-deployed into ~/bin by the monorepo install.sh `plugins/*/bin/*` loop.
set -euo pipefail
here="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"   # -> plugins/cron-claude
venv_bin="$here/.venv/bin/cron-claude"
if [ ! -x "$venv_bin" ]; then
  echo "cron-claude: venv missing — run: (cd '$here' && uv sync)" >&2
  exit 127
fi
exec "$venv_bin" "$@"
```

- [ ] **Step 2: Make it executable + smoke-test it**

```bash
chmod +x /home/komi/repos/claude-skills/plugins/cron-claude/bin/cron-claude
/home/komi/repos/claude-skills/plugins/cron-claude/bin/cron-claude --version
```
Expected: prints `cron-claude 0.0.1` (resolves through the shim to the venv entry point).

- [ ] **Step 3: Add the uv-sync step to install.sh**

In `/home/komi/repos/claude-skills/install.sh`, immediately **before** the `== per-plugin hooks` section, insert:
```bash
say "== python plugins (uv sync) =="
if command -v uv >/dev/null; then
  while IFS= read -r pyproj; do
    pdir="$(dirname "$pyproj")"
    say "  uv sync  ${pdir/#$HOME/\~}"
    run "uv sync --project '$pdir'"
  done < <(find "$REPO"/plugins -maxdepth 2 -name pyproject.toml 2>/dev/null || true)
else
  say "  NOTE: 'uv' not found — skipping; install uv to build Python plugins (cron-claude)"
fi
```

- [ ] **Step 4: Verify install.sh dry-run discovers the plugin + the shim deploys**

```bash
cd /home/komi/repos/claude-skills && bash -n install.sh && ./install.sh --dry-run 2>&1 | grep -A2 'python plugins'
```
Expected: shows `uv sync  ~/repos/claude-skills/plugins/cron-claude` under the new section.

```bash
cd /home/komi/repos/claude-skills && ./install.sh 2>&1 | grep -E 'cron-claude'
ls -l ~/bin/cron-claude && ~/bin/cron-claude --version
```
Expected: `~/bin/cron-claude` is a symlink into the plugin's `bin/`, and `--version` prints `cron-claude 0.0.1`.

- [ ] **Step 5: Commit**

```bash
cd /home/komi/repos/claude-skills
git add plugins/cron-claude/bin/cron-claude install.sh
git commit -m "feat(cron-claude): self-locating bin shim + install.sh uv-sync step"
```

---

### Task 8: Real-systemd integration test + docs

**Files:**
- Create: `$CC/tests/test_integration_systemd.py`
- Modify: `$CC/README.md` (drop "scaffold-only" status), `$CC/skills/cron-claude/SKILL.md` (note CLI is live)

- [ ] **Step 1: Write the integration test (skip-guarded)**

Create `$CC/tests/test_integration_systemd.py`:
```python
"""Ground-truth: create a REAL user timer, see it in list-timers, remove it.
Skipped where systemd --user is unavailable (e.g. CI)."""
import shutil
import subprocess

import pytest

from cron_claude.systemd import control, timers
from cron_claude.systemd.timers import TimerSpec

pytestmark = pytest.mark.integration


def _systemd_user_available() -> bool:
    if not shutil.which("systemctl"):
        return False
    return subprocess.run(
        ["systemctl", "--user", "is-system-running"], capture_output=True, text=True
    ).returncode in (0, 1)  # 1 = degraded but usable


@pytest.mark.skipif(not _systemd_user_available(), reason="no systemd --user")
def test_real_timer_lifecycle(tmp_path):
    name = "pytest-smoke"
    spec = TimerSpec(
        name=name, on_calendar="*-*-* 04:00:00", exec_start="/bin/true",
        prompt_path="/bin/true", runner="script", description="cron-claude integration smoke",
    )
    try:
        timers.write_units(spec)
        control.daemon_reload()
        control.enable_now(timers.timer_unit(name))
        listed = subprocess.run(
            ["systemctl", "--user", "list-timers", "--all", timers.timer_unit(name)],
            capture_output=True, text=True,
        )
        assert timers.timer_unit(name) in listed.stdout
    finally:
        control.disable_now(timers.timer_unit(name))
        control.stop(timers.service_unit(name))
        timers.remove_units(name)
        control.daemon_reload()
    assert not timers.unit_paths(name)[0].exists()
```

Register the `integration` marker: in `$CC/pyproject.toml` under `[tool.pytest.ini_options]`, add `markers = ["integration: touches real systemd --user"]`.

- [ ] **Step 2: Run the full suite (integration included locally)**

Run: `cd $CC && uv run pytest -q`
Expected: all tests pass — unit tests + the integration test (this dev box has systemd --user). Confirm the timer is gone afterward:
Run: `systemctl --user list-unit-files 'cron-claude-pytest-smoke*'`
Expected: `0 unit files` (cleaned up by the test's `finally`).

- [ ] **Step 3: Confirm CI-style skip works**

Run: `cd $CC && uv run pytest -q -m 'not integration'`
Expected: all non-integration tests pass; integration test deselected.

- [ ] **Step 4: Update docs status**

In `$CC/README.md`, replace the status blockquote:
```
> **Status:** scaffold-only. CLI surface is wired, all commands raise
> `NotImplementedError`. The shell playground (`./run`, `prompts/`, `logs/`)
> still works as before — it's the substrate the CLI will eventually drive.
```
with:
```
> **Status:** working. All commands implemented; installed on PATH via the
> monorepo `install.sh` (`uv sync` + a self-locating `bin/cron-claude` shim).
> The legacy `./run` + `prompts/` playground still works for ad-hoc runs.
```

In `$CC/skills/cron-claude/SKILL.md`, line 8, change `A Python CLI installed at \`cron-claude\`` if it implies scaffolding — confirm it reads as a working CLI (it already documents the live command surface; no functional change needed beyond the README).

- [ ] **Step 5: Final full-suite + lint + commit**

```bash
cd /home/komi/repos/claude-skills/plugins/cron-claude
uv run pytest -q
uv run ruff check src tests
```
Expected: all tests pass; ruff reports no errors (fix any it flags).

```bash
cd /home/komi/repos/claude-skills
git add plugins/cron-claude/tests/test_integration_systemd.py plugins/cron-claude/pyproject.toml plugins/cron-claude/README.md plugins/cron-claude/skills/cron-claude/SKILL.md plugins/cron-claude/uv.lock
git commit -m "test(cron-claude): real-systemd integration test + docs: mark working"
```

---

## Final verification (whole feature)

- [ ] `cd $CC && uv run pytest -q` → all green.
- [ ] `~/bin/cron-claude --version` → `cron-claude 0.0.1`.
- [ ] End-to-end manual: `~/bin/cron-claude schedule add smoke -w '*-*-* 04:00:00' -p plugins/cron-claude/prompts/hello` → `schedule list` shows it → `schedule show smoke` → `schedule run smoke` (runs the hello prompt; check output) → `schedule rm smoke -f`. Confirm `systemctl --user list-timers` no longer lists it.
- [ ] `cron-claude tui` launches, lists `smoke` (if present), `q` quits.
```
```
