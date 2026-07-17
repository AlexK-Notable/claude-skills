# CLAUDE.md — claude-skills

Personal Claude Code skills monorepo for **komi** (github.com/AlexK-Notable). One private repo holding every skill written for the user's own daily use, deployed **live** into the runtime via symlinks. This file explains the architecture and *why* the non-obvious choices were made — read the Deployment section before changing how skills load.

## What this repo is

A Claude Code **plugin marketplace** by structure (`.claude-plugin/marketplace.json` + `plugins/<name>/`). But on the user's own machine it deploys via **live symlinks into `~/.claude/skills/`**, *not* via `claude plugin install`. That distinction is deliberate and load-bearing — see "Deployment model" below.

## Layout

```
.claude-plugin/marketplace.json     catalog listing every plugin (keeps it a real, shareable marketplace)
plugins/<name>/
  .claude-plugin/plugin.json         per-plugin manifest
  skills/<name>/SKILL.md             the skill (+ references/, agents/, domains/ as needed)
  skill-rules.fragment.json          OPTIONAL custom activation-hook triggers (only skills that want proactive suggestion)
  scripts/ | bin/ | src/             CLIs/tools the skill uses (symlinked to ~/bin)
install.sh                           idempotent deploy: symlinks + rules merge + hook + autosync
bin/claude-skills-sync               autosync action (commit+push when the repo changes)
bin/claude-skills-watch              inotify watcher that debounces and calls the sync
systemd/                             user unit that runs the watcher
hooks/skill-activation-prompt.*      the activation-suggestion hook, bundled for portability
docs/specs|plans/                    design history (how this repo came to be)
```

## Deployment model — READ THIS (the non-obvious part)

**Skills deploy as LIVE SYMLINKS into `~/.claude/skills/`, NOT via `claude plugin install`.** The reasoning, because it's easy to get wrong:

- This repo *is* a directory-source marketplace, so `claude plugin install <name>@claude-skills` works. **But that command copies the plugin into a versioned `~/.claude/plugins/cache/` snapshot** — verified on this machine (an installed directory-source plugin is a real-dir *copy* in `cache/`, not a symlink to its source). An installed plugin is therefore a **frozen copy**: editing this repo does *not* change the loaded skill until you `claude plugin update`/reinstall.
- The user **actively edits these skills** — they're daily tools, improved constantly. A frozen-snapshot install is the wrong mechanism for that workflow.
- **Symlinking `~/.claude/skills/<name>` → `plugins/<name>/skills/<name>`** makes Claude load each skill *directly from this repo*, so every edit is live in the next session. This is the ordinary way any personal skill in `~/.claude/skills/` loads.
- `marketplace.json` is kept anyway so the repo remains a **proper, shareable marketplace** — a *different* machine (or another person), where live editing isn't needed, can `claude plugin install` from it. Live-symlink (here) and marketplace-install (elsewhere) are two valid deploy paths for one repo; we never do **both on the same machine** (that double-loads the skill).

**Corollary for agents:** to make a skill change take effect, just edit the file under `plugins/<name>/skills/<name>/` and start a new session (or `/reload-plugins`). **Do NOT `claude plugin install` these on this machine** — it would freeze a cache copy and your future edits would silently stop applying.

## Why one repo (the "hub" model)

The user's personal skills used to be scattered across separate GitHub repos plus loose dirs in `~/.claude/skills`. Consolidating into ONE repo means: `git clone … && ./install.sh` reconstitutes the whole skill set on a new machine; one place to version everything; one autosync keeps the remote current. **Third-party skills the user did not write are deliberately excluded** — this repo is unambiguously "mine," so cloning it carries no foreign baggage. Skills with their own prior repos (home-network, cron-claude, hypr-doctor) were merged in with `git subtree`, so `git log --follow` on any merged file still shows its full provenance.

## Skills

| Plugin | Purpose | CLIs (→ ~/bin) |
|---|---|---|
| `bitwarden-cli` | `bw` vault + `bws` Secrets Manager workflows (secure notes, SSH keys, machine-secret injection) | `bws-secret-add` |
| `home-network` | LAN discovery/troubleshooting + self-healing device inventory (background `claude -p` agents) | `scan-lan`, `wol`, `port-check`, `find-host`, `home-net-*` |
| `home-assistant` | operate the self-hosted HA instance safely (safe-mutation discipline, secret-safe inventory snapshot, gotcha journal) | `ha-inventory`, `ha-note` |
| `cron-claude` | schedule recurring `claude -p` jobs as systemd user timers | `cron-claude` (Python/uv) |
| `hypr-doctor` | post-`pacman -Syu` triage/repair for Arch/CachyOS Hyprland | `hypr-doctor` |
| `chezmoi` | dotfiles management (apply/diff, templating, age encryption) | — |
| `universal-directory-organizer` | interactive directory cleanup with safety hooks | — |
| `agentic-engineering` | evidence-based reference for prompt/context/agent/loop engineering (theory + orchestrator-worker, tool-design, caching practice) | — |

## Activation

Two independent layers:
1. **Native** — Claude reads each `SKILL.md`'s `description` frontmatter to decide relevance. Every skill gets this for free.
2. **Custom suggestion hook** — `hooks/skill-activation-prompt.*` (a UserPromptSubmit hook) reads `~/.claude/skills/skill-rules.json` and proactively prints "🎯 SKILL ACTIVATION CHECK → recommends X" on keyword/intent match. Only skills that want proactive suggestion ship a `skill-rules.fragment.json`; `install.sh` merges all fragments into the runtime `skill-rules.json` **without disturbing entries it doesn't own**. Skills without a fragment (home-network, cron-claude, hypr-doctor) rely on layer 1.

`skill-rules.json` lives at `~/.claude/skills/skill-rules.json` (runtime config, not a skill), so it keeps working regardless of where the skills themselves load from.

## Per-plugin hooks

Beyond the marketplace-wide activation hook, individual plugins ship their own runtime hooks in `plugins/<name>/hooks/*.sh`. `install.sh` symlinks **every** `plugins/*/hooks/*.sh` into `~/.claude/hooks/` — a *third* deploy surface alongside `~/.claude/skills/` and `~/bin/`. Current per-plugin hooks:

- `hypr-doctor/hooks/hypr-doctor-drift.sh` — SessionStart drift warning.
- `universal-directory-organizer/hooks/{organizer-guard,organizer-logger,session-complete}.sh` — fail-closed PreToolUse guard + PostToolUse logger + Stop archiver (dormant unless an organize session manifest exists).

They must be **registered in `~/.claude/settings.json`** with their event — `install.sh` symlinks the scripts but never edits `settings.json` (it's load-bearing, left manual; each plugin's README/SKILL documents the event + matcher). Because they're symlinked from tracked files, a fresh `git clone … && ./install.sh` reconstitutes them — closing the gap that previously left these scripts living only in untracked `~/.claude/`. **`~/.claude/hooks/` is a deploy surface: when verifying a deploy, sweep it for dangling symlinks too** — a hook symlink pointing at an old repo path silently no-ops (exactly how `hypr-doctor-drift.sh` was dead after the migration until re-pointed).

## Autosync ("remote always current")

`install.sh` installs a `systemd --user` service running `bin/claude-skills-watch` — an `inotifywait -r` watcher (excluding `.git`) that debounces bursts and calls `bin/claude-skills-sync`. The sync does `git pull --rebase --autostash` → `add -A` → `commit` → `push`; on a rebase conflict it **stops and `notify-send`s** rather than auto-resolving (multi-machine safe). It's loop-safe: it only commits when there are non-`.git` changes, so its own commit doesn't re-trigger it. (home-network's capture loop also commits/pushes this repo — same remote.)

## Development workflow — worktree vs. autosync

Autosync (above) is a feature for *small* changes and a hazard for *large* ones. Pick by the size of the change:

- **Small edits / fixes / touch-ups** (a doc tweak, a one-file bug fix, a path correction): just edit on `master`. Autosync commits + pushes immediately. This is the default and the whole point of the watcher.
- **Larger multi-step work** (a new plugin, a feature spanning several files, anything built test-first across a sequence of commits): do it in an **isolated git worktree on a feature branch**, test there, then merge to `master`. Autosync does **not** watch other worktrees, so in-progress commits stay off `master` until the work is reviewed and green.

**Why not just build big features on `master`?** Autosync would race a multi-commit TDD loop — it fires on every file write, so it would commit half-written, test-failing intermediate states and overwrite the clean per-task commit messages. Worktree isolation avoids both.

```bash
# big project: isolate → test → merge
git worktree add ../claude-skills-<feature> -b <feature>
cd ../claude-skills-<feature>
# … implement + test (autosync ignores this worktree) …
cd ~/repos/claude-skills && git merge <feature> && git push
git worktree remove ../claude-skills-<feature> && git branch -d <feature>
```

Rule of thumb: **worktree → test → merge for projects; autosync for touch-ups.**

## Adding / editing a skill

1. Create `plugins/<name>/skills/<name>/SKILL.md` (+ `.claude-plugin/plugin.json`; optional `skill-rules.fragment.json` if you want proactive suggestion).
2. Add the plugin to `.claude-plugin/marketplace.json`.
3. Re-run `./install.sh` (idempotent) to symlink it in and merge its rules.
4. Edit freely — changes are live next session. No reinstall.

## Conventions

- **Scripts:** no file extension, shebang'd; `install.sh` symlinks them to `~/bin` (the user's `~/bin` scripts policy).
- **No secrets in any tracked file** — the repo is private but cloned across machines, so a committed secret is a permanent leak. Route credentials through the `bitwarden-cli` skill.
- **Don't `claude plugin install` on this machine** (see Deployment model).

<!-- self-learn:begin (do not hand-edit inside; managed by self-learn) -->
- **When about to sandbox-copy a uv Python project (cp -r, rsync) to run mutation tests, kill checks, or any experiment against the copy:** delete the copied venv first (rm -rf <copy>/.venv) and re-sync in the copy — the copied venv's editable install still points at the ORIGINAL source tree, so anything run inside the copy silently executes the original's code and every mutation appears to change nothing *(lrn-25968266)*
- **When about to run ./install.sh in claude-skills (or anything that calls it) during a maintenance window that requires the repo's daemons to stay stopped — e.g. a migration runbook with a stop-daemons-first step:** install.sh silently re-installs AND restarts the claude-skills-autosync service as part of its idempotent deploy — a prior 'systemctl --user stop' does not survive it. After any install.sh call inside a daemons-down window, re-check with 'systemctl --user is-active claude-skills-autosync.service' and re-stop if the window must stay open; sequence install.sh after the point where daemon liveness is safe again *(lrn-316a5411)*
<!-- self-learn:end -->
