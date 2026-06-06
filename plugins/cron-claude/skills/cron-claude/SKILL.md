---
name: cron-claude
description: Use when the user wants to schedule, manage, inspect, or trigger recurring `claude -p` jobs on this Linux machine — creating systemd user timers that fire prompt scripts non-interactively, listing existing schedules, removing them, running them on-demand, or viewing their logs. Triggers on terms like "schedule", "cron job", "recurring task", "systemd timer", "scheduled prompt", "run claude on a schedule", "automate claude", "background claude job", "every Sunday at 3am", or any direct mention of the `cron-claude` CLI.
---

# cron-claude

A Python CLI installed at `cron-claude` (source: `~/repos/claude-skills/plugins/cron-claude/`) for scheduling local `claude -p` jobs as systemd user timers. Use this CLI instead of writing raw cron entries or invoking `systemctl --user` directly.

## When to use this skill

- User asks to schedule, automate, or run claude on a recurring basis
- User mentions cron, systemd timer, OnCalendar, or relative phrasing like "every Sunday morning"
- User wants to list, inspect, or delete scheduled claude jobs
- User wants to manually trigger a scheduled job out-of-band
- User wants to read logs from past scheduled runs

## CLI surface

```
cron-claude --help
cron-claude --version

cron-claude schedule add NAME --when 'OnCalendar spec' --prompt PATH [-d DESC]
cron-claude schedule list [--json]
cron-claude schedule rm NAME [--force]
cron-claude schedule show NAME

cron-claude run NAME            # trigger on-demand, ignoring schedule
cron-claude logs NAME [--tail N] [--follow]

cron-claude tui                 # interactive (needs `uv sync --extra tui`)
```

## Conventions

- **Schedule names** become systemd unit basenames and are validated to `[A-Za-z0-9_-]+` (letters, digits, hyphens, underscores — no spaces or slashes). Underlying units are written as `cron-claude-<name>.{service,timer}`.
- **`--when`** accepts any systemd `OnCalendar=` value: `weekly`, `Sun 03:07`, `*-*-* 09:00`, `Mon..Fri 17:00`. Resolve fuzzy phrasing ("every Sunday morning") to a concrete OnCalendar spec before passing it.
- **`--prompt`** accepts **any path**: an *executable* file (which owns its own `claude -p` invocation + allowlist, like those in `prompts/`) runs directly; a *non-executable text* file is wrapped by cron-claude in a `claude -p "$(cat …)"` call. Pass `--scaffold` to create an executable starter when the path doesn't exist yet.
- **Text-prompt flags** (ignored for executable prompts): `--allowed-tools` (repeatable), `--permission-mode`, `--dangerously-skip-permissions`, `--no-bare`, `--output-format`. Defaults: `--bare --output-format json` with no permission mode (relying on the allowlist). `--no-bare` keeps OAuth/keychain auth.
- **`--json`** is supported on listing/inspection commands when you'll parse the result.

## When *not* to use this skill

- One-off Claude invocations the user wants to run *right now* — call `claude -p` directly.
- Schedules belonging to other tools (anacron, fcron, plain crontab). This skill manages systemd user timers only.
- Non-Linux platforms — systemd-specific.

## Reference

- Repo: `~/repos/claude-skills/plugins/cron-claude/` (`your-username/claude-skills`)
- Prompts directory: `~/repos/claude-skills/plugins/cron-claude/prompts/`
- Underlying unit files: `~/.config/systemd/user/cron-claude-<name>.{service,timer}`
- Raw logs: `journalctl --user-unit cron-claude-<name>.service` (also via `cron-claude logs`)
