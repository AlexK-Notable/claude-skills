# cron-claude — Implementation Design

**Date:** 2026-06-02
**Status:** Approved (design); ready for implementation plan
**Plugin:** `plugins/cron-claude/` in the `claude-skills` monorepo

## Goal

Turn the `cron-claude` scaffold (clean module boundaries, every body raising
`NotImplementedError`) into a working, self-contained, installable CLI that
schedules and manages local `claude -p` jobs as **systemd `--user` timers**.
All commands functional — `schedule add/list/rm/show`, `run`, `logs`, plus a
Textual `tui` — installed on PATH by the monorepo's `install.sh`.

No new runtime dependencies beyond those already declared: `typer`, `rich`,
and `textual` (the `tui` optional-extra). Toolchain is `uv` (a `uv.lock` already
exists).

## Approved decisions (the three forks)

1. **Scope:** Full build — all six commands *plus* a functional Textual TUI.
2. **Install model:** `uv` shim via `install.sh`. `install.sh` runs `uv sync`
   (isolated, locked `.venv`, project installed **editable**) and a tracked
   self-locating `bin/cron-claude` shim auto-deploys via the existing
   `plugins/*/bin/*` symlink loop. Live-editable, consistent with the monorepo's
   symlink doctrine. Requires `uv` present.
3. **Prompt model:** Support both. `select_runner(prompt_path)` dispatches at
   `schedule add` time: an **executable** prompt runs directly; a **non-executable
   text** prompt gets a rendered `claude -p` call.

## Architecture — module map

Boundaries are unchanged from the scaffold; only bodies are filled in (plus two
new small modules and the shim).

| Module | Responsibility | Change |
|---|---|---|
| `systemd/timers.py` | Write/parse/remove `.timer`+`.service` pairs; `TimerSpec` round-trip | implement `write_units` / `remove_units` / `list_units` |
| `systemd/control.py` *(new)* | Thin `systemctl --user` / `journalctl --user` subprocess wrapper | new |
| `runners/claude.py` | Render `ExecStart` for a **text** prompt | implement `to_exec_start` |
| `runners/script.py` *(new)* | Render `ExecStart` for an **executable** prompt | new |
| `runners/__init__.py` | `Runner` protocol + `select_runner(path)` factory | extend |
| `cli.py` | Orchestrate runner → systemd → control; Rich output | implement all 6 bodies |
| `tui/app.py` | Textual app over the same `systemd` module | implement |
| `bin/cron-claude` *(new)* | self-locating shim → sibling `.venv/bin/cron-claude` | new |

The `systemd` module stays agnostic of Claude; `runners` produce the `ExecStart`
string; `cli` orchestrates. This separation is preserved deliberately.

## Component specs

### Runner protocol (`runners/`)

```python
# runners/__init__.py
class Runner(Protocol):
    prompt_path: Path
    def to_exec_start(self) -> str: ...
    def validate(self) -> None: ...   # raises CronClaudeError on bad prompt

def select_runner(prompt_path: Path, **opts) -> Runner:
    # regular file + os.access(X_OK) -> ScriptRunner
    # regular readable file (not executable) -> ClaudeRunner
    # missing -> raise (caller may scaffold first)
```

- **`ScriptRunner(prompt_path)`** — `to_exec_start()` returns the absolute path
  to the executable (it has its own shebang and owns its `claude -p` call, like
  `prompts/hello`). Zero systemd-quoting risk.
- **`ClaudeRunner(prompt_path, allowed_tools, bare, permission_mode,
  output_format, max_turns, timeout_sec)`** — `to_exec_start()` renders:
  ```
  /bin/bash -c 'claude -p "$(cat <shlex-quoted abs prompt>)" \
    --bare --permission-mode <mode> --output-format <fmt> \
    --max-turns <n> [--allowed-tools "<tools>"]'
  ```
  Inner command assembled with `shlex.quote` on the prompt path; `allowed_tools`
  joined space-separated.

> **Implementation verification point:** the scaffold's `ClaudeRunner` field
> defaults (`permission_mode="dontAsk"`, etc.) are placeholders and may not match
> the real CLI. Verify every rendered flag against `claude --help` during
> implementation (likely `--permission-mode`, `--output-format`, `--max-turns`,
> `--allowed-tools`, `--bare`). A rendered job that uses a wrong flag fails
> silently in the timer — this is the highest-risk detail.

### systemd units (`systemd/timers.py`)

`write_units(spec) -> (service_path, timer_path)` writes:

**`cron-claude-<name>.service`**
```ini
[Unit]
Description=<spec.description or "cron-claude: <name>">
X-CronClaude-Managed=1
X-CronClaude-Name=<name>
X-CronClaude-Prompt=<abs prompt path>
X-CronClaude-Runner=<script|claude>

[Service]
Type=oneshot
Environment=PATH=%h/.local/bin:%h/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=<spec.exec_start>
# TimeoutStartSec=<n>   (only when a timeout is set; covers BOTH runner types —
#                        no `timeout` binary wrapping needed)
```

**`cron-claude-<name>.timer`**
```ini
[Unit]
Description=<… or "cron-claude timer: <name>">
X-CronClaude-Managed=1

[Timer]
OnCalendar=<spec.on_calendar>
Persistent=<spec.persistent>
RandomizedDelaySec=<n>   # only when > 0

[Install]
WantedBy=timers.target
```

- `%h` is the systemd home specifier (portable across users/machines).
- The `X-CronClaude-*` keys in `[Unit]` (systemd ignores unknown `X-` keys) let
  `list_units` / `show` reconstruct the `TimerSpec` by parsing — no re-derivation.
- `remove_units(name)` unlinks both files (caller stops/disables first).
- `list_units()` scans `UNITS_DIR` for `cron-claude-*.timer`, reads the marker +
  metadata from the paired `.service`, yields reconstructed `TimerSpec`s.
- Helpers: `unit_paths(name)`, `service_unit(name)`, `timer_unit(name)`.

### systemctl/journalctl wrapper (`systemd/control.py`)

Thin subprocess layer, all `--user` scoped. Each helper builds an argv and runs
it; non-zero exit raises `SystemdError(argv, stderr)`.

- `daemon_reload()`, `enable_now(timer)`, `disable_now(timer)`,
  `start(service)`, `stop(service)`, `is_active(unit) -> bool`
- `next_elapse(timer) -> datetime | None` (via `systemctl --user show -p
  NextElapseUSecRealtime` or `list-timers`)
- `last_result(service) -> tuple[str, int]` (via `show -p Result,ExecMainStatus`)
- `journal(unit, tail, follow)` — execs `journalctl --user-unit <unit> -n <tail>
  [-f]`; for `run`/`logs --follow` this replaces the current process / streams.

### CLI command bodies (`cli.py`)

| Command | Flow |
|---|---|
| `schedule add` | validate `OnCalendar` via `systemd-analyze calendar` → refuse if schedule exists → `select_runner` → `to_exec_start()` → `TimerSpec` → `write_units` → `daemon_reload` → `enable_now` → print unit names + next firing. If `--prompt` missing: offer to scaffold an executable starter under `prompts/`. |
| `schedule list [--json]` | `list_units()` → Rich table (name · schedule · next run · last result · description) or JSON. |
| `schedule rm [--force]` | confirm unless `--force` → `stop` + `disable_now` + `remove_units` + `daemon_reload`. |
| `schedule show` | unit file contents + next elapse + last `Result`/`ExecMainStatus` + recent journal lines. |
| `run` | `start(service)` → stream journal until the oneshot exits → print exit status. |
| `logs [--tail N] [--follow]` | proxy to `control.journal`. |
| `tui` | launch `CronClaudeApp` (existing ImportError guard for the `textual` extra stays). |

### TUI (`tui/app.py`)

A functional Textual app (not a dashboard): a `DataTable` of schedules from
`list_units()`, a log pane that tails the selected unit's journal, and keybinds
to **run** / **remove** / **show**. Reuses `list_units` + `control.py` — no logic
duplication. Gated behind the `textual` extra (already wired).

## Error handling

`CronClaudeError` base → `ScheduleExists`, `ScheduleNotFound`, `InvalidCalendar`,
`SystemdError`. The CLI wraps command bodies, catches `CronClaudeError`, prints
red to stderr, and `raise typer.Exit(code=1)`. `control.py` raises `SystemdError`
carrying the failed argv + captured stderr so messages are actionable.

## Packaging / install

- **`plugins/cron-claude/bin/cron-claude`** (tracked, executable): a shim that
  `readlink -f`-resolves its own path, derives the plugin dir, and
  `exec`s `…/cron-claude/.venv/bin/cron-claude "$@"`. Auto-deploys because
  `install.sh` already symlinks `plugins/*/bin/*` into `~/bin`.
- **`install.sh`**: add one step — for every `plugins/*/pyproject.toml`, run
  `uv sync` (guarded on `command -v uv`; warn + skip if absent). `uv sync`
  installs the project **editable** into `.venv`, so `src/` edits stay live.
- **`plugins/cron-claude/.gitignore`**: ensure `.venv/` is ignored so autosync
  never commits it.
- The `[project.scripts] cron-claude = "cron_claude.cli:app"` entry point
  (already declared) produces `.venv/bin/cron-claude` after `uv sync`.

## Testing strategy (ground-truth biased)

- **Pure logic, fast, no systemd:** runner rendering (script vs text, `shlex`
  quoting), `select_runner` dispatch, `write_units` content + `list_units`
  round-trip (monkeypatch `UNITS_DIR` → `tmp_path`), `remove_units`.
- **One real integration test (ground truth):** create a real
  `cron-claude-pytest-smoke` timer, assert it appears in `systemctl --user
  list-timers`, then remove it. Skip-guarded where `systemd --user` is
  unavailable (CI) via a `pytest.mark.skipif` checking `systemctl --user`
  reachability.
- **CLI:** Typer `CliRunner` with `UNITS_DIR` → tmp and `control.py`
  monkeypatched (records argv, does not execute). Keep the existing 3 smoke
  tests (version, help, subcommands) — already green.

## Files changed / added

```
plugins/cron-claude/
  bin/cron-claude                        NEW  self-locating shim
  src/cron_claude/cli.py                 implement 6 command bodies
  src/cron_claude/systemd/timers.py      implement write/remove/list
  src/cron_claude/systemd/control.py     NEW  systemctl/journalctl wrapper
  src/cron_claude/runners/__init__.py    Runner protocol + select_runner
  src/cron_claude/runners/claude.py      implement to_exec_start (text)
  src/cron_claude/runners/script.py      NEW  ScriptRunner (executable)
  src/cron_claude/errors.py              NEW  CronClaudeError hierarchy
  src/cron_claude/tui/app.py             implement Textual app
  tests/test_runners.py                  NEW
  tests/test_timers.py                   NEW
  tests/test_cli.py                      NEW
  tests/test_integration_systemd.py      NEW  (skip-guarded)
  .gitignore                             ignore .venv/
  README.md                              drop "scaffold-only" status
install.sh                               add uv sync step for Python plugins
```

## YAGNI boundaries

- Only `claude -p` runners (script + text). No pacman-hook/python runner types
  (the `Runner` protocol leaves that open for later).
- No remote / multi-machine timer sync.
- TUI is functional, not a full dashboard.
