# Learnings

Reference-routed lessons, appended by self-learn (newest last). Each
entry carries its record id for provenance; regenerate nothing here —
this file is append-only.

## 2026-08-10 — lrn-c826137f

**Fact:** cron-claude's `--prompt` argument auto-detects executability: an executable file is run directly as the systemd unit's ExecStart (a 'ScriptRunner' — the script itself decides whether/when to invoke `claude -p`, and any claude flags passed to `cron-claude schedule add` are ignored in this mode); a non-executable text file is instead wrapped so the job invokes `claude -p <file>` directly. This lets a cheap shell predicate gate an expensive `claude -p` call without a separate wrapper timer.

**Context:** Confirmed by reading cron-claude's own source (select_runner() docstring, cli.py) rather than trusting --help's ambiguous wording ('an executable script, or a text file'), then verifying the generated systemd unit's ExecStart pointed at the script itself.
