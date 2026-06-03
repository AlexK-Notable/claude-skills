# cron-claude

A Python CLI + Claude Code skill for scheduling local `claude -p` jobs as
**systemd user timers**. Headless Claude on a schedule, with full local
file access — what `/schedule` (remote) and `/loop` (in-REPL) both miss.

> **Status:** working. All commands implemented; installed on PATH via the
> monorepo `install.sh` (`uv sync` + a self-locating `bin/cron-claude` shim).
> The legacy `./run` + `prompts/` playground still works for ad-hoc runs.

## Quickstart

```bash
# install (creates .venv, sets up entry point)
uv sync

# every command works now
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
│   └── tui/                    # module: Textual TUI (optional dep)
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

## Scheduling a prompt

Use the CLI — it writes a systemd `.timer`+`.service` pair (no crontab):

```bash
# weekly, Sunday 03:07 — an executable prompt runs directly
cron-claude schedule add weekly-hello --when 'Sun 03:07' --prompt prompts/hello

# a non-executable text file is wrapped in `claude -p "$(cat …)"`; narrow the tools
cron-claude schedule add inbox --when daily --prompt ./inbox.txt \
  --allowed-tools 'Bash(ls *)' --timeout 300
```

Things to know (apply to any scheduled run):
- The generated `.service` sets `Environment=PATH=…` so `claude` resolves under
  the timer's clean environment. If a prompt depends on extra shell rc state
  (aliases, functions, custom `PATH`), source what you need inside the prompt.
- Auth: scheduled Claude reads `~/.claude/.credentials.json`. If that expires
  (token rotation, etc.), runs silently fail until you `claude` login once to
  refresh. For text prompts, the default `--bare` switches auth to
  `ANTHROPIC_API_KEY`/`apiKeyHelper` only — pass `--no-bare` to keep the keychain.
- **No sudo.** A scheduled run has no TTY → pam_unix fails → pam_faillock ticks
  toward locking your account. Anything needing root belongs in a pacman hook or
  a separate systemd unit, not a `claude -p` prompt.
- Each run consumes Claude Code API quota. Be deliberate with frequency.

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
./run my-new-thing                     # smoke-test ad-hoc (legacy playground)
```

Then schedule it:

```bash
cron-claude schedule add my-job --when 'Sun 03:07' --prompt prompts/my-new-thing
```

(Or let the CLI scaffold an executable starter for you with
`--prompt prompts/my-new-thing --scaffold`.)
