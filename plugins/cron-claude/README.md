# cron-claude

A Python CLI + Claude Code skill for scheduling local `claude -p` jobs as
**systemd user timers**. Headless Claude on a schedule, with full local
file access — what `/schedule` (remote) and `/loop` (in-REPL) both miss.

> **Status:** scaffold-only. CLI surface is wired, all commands raise
> `NotImplementedError`. The shell playground (`./run`, `prompts/`, `logs/`)
> still works as before — it's the substrate the CLI will eventually drive.

## Quickstart

```bash
# install (creates .venv, sets up entry point)
uv sync

# poke around — every command stubbed for now
uv run cron-claude --help
uv run cron-claude --version
uv run cron-claude schedule --help

# install the Claude skill (auto-activates on scheduling-related prompts)
ln -s "$(pwd)/skills/cron-claude" ~/.claude/skills/cron-claude

# run smoke tests
uv run pytest
```

## Layout

```
cron-claude/
├── README.md
├── pyproject.toml              # uv-managed
├── src/cron_claude/
│   ├── cli.py                  # Typer entry point (cron-claude ...)
│   ├── systemd/                # module: .timer/.service writers (backend)
│   ├── runners/                # module: ExecStart= renderers (claude -p, ...)
│   └── tui/                    # module: Textual TUI (optional, placeholder)
├── skills/cron-claude/SKILL.md              # Claude Code skill — symlink into ~/.claude/skills/
├── tests/                      # pytest smoke tests
├── prompts/                    # per-prompt executables (legacy playground; CLI consumes these)
│   └── hello                   # smoke test — proves claude -p works headless
├── run                         # legacy bash wrapper (still works)
└── logs/                       # gitignored except .gitkeep
```

The `systemd` and `runners` modules are intentionally separate — the systemd
side knows nothing about claude, and the claude runner knows nothing about
unit files. Adding a new runner type (plain shell, python script, pacman
hook trigger) means a new file in `runners/`, no changes elsewhere.

## Legacy playground (still valid)

## Conventions

Each prompt is its own executable script. It owns:
- The actual `claude -p '...'` invocation
- Its own `--allowed-tools` allowlist (narrow → safe)
- Any pre/post shell logic (env setup, exit-code handling, notifications)

The runner (`./run NAME`) is just a thin convenience that:
- Locates `prompts/NAME`, requires it executable
- Timestamps a log file under `logs/`
- Tees stdout+stderr there

## Running a prompt by hand

```bash
cd ~/repos/claude-skills/plugins/cron-claude
./run hello
```

You should see the prompt's output streamed to your terminal AND saved to
`logs/hello-<timestamp>.log`. Re-running creates a new log file each time.

## Wiring a prompt into cron

```cron
# weekly Sunday 03:00 — note: not 03:00 sharp; jitter via :07 to be polite
7 3 * * 0  /home/komi/repos/claude-skills/plugins/cron-claude/run hello
```

Things to know:
- Cron runs with a near-empty environment. The `run` script exports `PATH` so
  `claude` is reachable, but if your prompt itself depends on shell rc state
  (aliases, functions, custom `PATH` entries beyond the standard ones), you'll
  need to source what you need explicitly inside the prompt script.
- Auth: cron'd Claude reads `~/.claude/.credentials.json`. If that expires
  (token rotation, etc.), the cron runs will silently fail until you `claude`
  login interactively at least once to refresh.
- **No sudo.** Cron has no TTY → pam_unix conversation fails → pam_faillock
  ticks toward locking your account after 3 failures. Anything requiring root
  needs to live in a pacman hook or systemd unit, not in a `claude -p` prompt.
- Each cron run consumes Claude Code API quota. Be deliberate with frequency.

## Permissions model

Cron'd Claude can't pop a permission prompt. Two choices per prompt:

1. **Whitelist narrowly** with `--allowed-tools`:
   `claude -p '...' --allowed-tools 'Bash(git *) Edit Read'`

   Per `claude --help`: tools are comma- or space-separated; `Bash(cmd *)`
   matches all `cmd ...` invocations. Recommended.

2. **`--dangerously-skip-permissions`** — bypasses everything. Don't use this
   for cron unless you've thought hard about what the agent could do if it
   misinterprets the prompt.

## Other useful flags

- `--bare` — skips hooks, LSP, plugin sync, auto-memory, CLAUDE.md discovery,
  and keychain reads. Reduces overhead for simple cron jobs. Auth becomes
  strictly `ANTHROPIC_API_KEY` env var or `apiKeyHelper` (no OAuth/keychain),
  so requires explicit env wiring.
- `--add-dir <dir>` — grant tool access to a specific directory.
- `--effort low` — cheaper runs for simple jobs.
- `--fallback-model <name>` — graceful degradation if default is overloaded
  (only works with `--print`).

## Adding a new prompt

```bash
cp prompts/hello prompts/my-new-thing
chmod +x prompts/my-new-thing
$EDITOR prompts/my-new-thing
./run my-new-thing  # test it
```

Then add a cron line pointing at `./run my-new-thing`.
