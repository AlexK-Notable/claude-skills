# claude-skills

Personal Claude Code skills monorepo — every skill written for my own daily use, in one private repo, deployed **live** into `~/.claude/skills` via symlinks.

## Setup (any machine)

```bash
git clone git@github.com:AlexK-Notable/claude-skills.git ~/repos/claude-skills
cd ~/repos/claude-skills
./install.sh            # idempotent; --dry-run to preview
```

This symlinks each skill into `~/.claude/skills`, links CLIs into `~/bin`, merges activation rules, and enables a systemd autosync watcher.

## Plugins

`bitwarden-cli` · `home-network` · `cron-claude` · `hypr-doctor` · `chezmoi` · `universal-directory-organizer`

## Architecture & rationale

See **[CLAUDE.md](CLAUDE.md)** — especially *Deployment model*, which explains why skills deploy via live symlinks rather than `claude plugin install` (the latter caches a frozen snapshot, breaking live editing). Don't "fix" the symlinks into a marketplace-install on this machine.

Design history: [`docs/specs/`](docs/specs) and [`docs/plans/`](docs/plans).
