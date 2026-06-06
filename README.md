# claude-skills

A personal Claude Code skills monorepo you can fork and adapt — a set of skills kept in one repo and deployed **live** into `~/.claude/skills` via symlinks.

## Setup (any machine)

```bash
# fork this repo first, then clone YOUR fork:
git clone git@github.com:your-username/claude-skills.git ~/repos/claude-skills
cd ~/repos/claude-skills
./install.sh            # idempotent; --dry-run to preview
```

The repo location is assumed to be `~/repos/claude-skills` throughout, but that path is yours to customize (adjust the systemd unit and any references if you move it).

This symlinks each skill into `~/.claude/skills`, links CLIs into `~/bin`, merges activation rules, and (optionally) enables a systemd autosync watcher.

## Plugins

`bitwarden-cli` · `home-network` · `cron-claude` · `hypr-doctor` · `chezmoi` · `universal-directory-organizer`

## Working in this repo

- **Small edits / fixes** → edit on `master`; the optional autosync watcher commits + pushes automatically (to your own fork's remote).
- **Bigger work** (new plugin, multi-file feature) → isolate in a git worktree, test, then merge to `master`. Autosync would otherwise race a multi-commit build and push broken intermediate states. See **[CLAUDE.md](CLAUDE.md)** → *Development workflow*.

Autosync is **optional** — see the *Autosync* section in CLAUDE.md. It pushes to your own fork's remote, and you choose whether to run it at all.

## Architecture & rationale

See **[CLAUDE.md](CLAUDE.md)** — especially *Deployment model*, which explains why skills deploy via live symlinks rather than `claude plugin install` (the latter caches a frozen snapshot, breaking live editing). Don't "fix" the symlinks into a marketplace-install on the same machine where you edit the skills live.

Design history: [`docs/specs/`](docs/specs) and [`docs/plans/`](docs/plans).
