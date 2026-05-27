# hypr-doctor

Post-`pacman -Syu` health check + repair toolkit for an Arch/CachyOS Hyprland
desktop. Triages the recurring drift that ships with rolling-release updates:
Hyprland plugin ABI mismatch, Qt6 ↔ python-pyqt6/pyside6 binding skew, failed
systemd user units, xdg-desktop-portal regressions, AUR rebuild hints.

This repo holds the source files. They live symlinked into their canonical
locations under `~/.claude/` and `~/bin/` so the tools just work; the repo
provides versioning, portability across machines, and a place to track
changes.

## Layout

| Repo path | Symlinked to | Purpose |
|-----------|--------------|---------|
| `skills/hypr-doctor/SKILL.md` | `~/.claude/skills/hypr-doctor/SKILL.md` | Claude Code skill — auto-discovered |
| `skills/hypr-doctor/plugins.json` | (under skills/) | Source-of-truth manifest of local-build plugins |
| `skills/hypr-doctor/references/` | (under skills/) | Progressive-disclosure reference docs |
| `hooks/hypr-doctor-drift.sh` | `~/.claude/hooks/hypr-doctor-drift.sh` | SessionStart hook — surfaces drift warnings |
| `bin/hypr-doctor` | `~/bin/hypr-doctor` | CLI: `audit` / `rebuild` / `abi-drift` / `plugin-rebuild NAME` |

The symlink target is the whole `skills/hypr-doctor/` directory (not each file
individually), so adding new reference files in the repo automatically shows
up under `~/.claude/skills/hypr-doctor/`.

## Daily use

```bash
hypr-doctor                              # audit, read-only (default)
hypr-doctor rebuild                      # apply fixes: rebuild drifted plugins + reload
hypr-doctor plugin-rebuild hyprtasking   # rebuild one plugin
hypr-doctor abi-drift                    # terse output for the SessionStart hook
```

The SessionStart hook fires on every Claude Code session start. If any drift is
detected (plugin .so older than Hyprland binary, or PyQt6 lagging qt6-base) it
prints a one-line warning that Claude sees as session context. Silent when
healthy.

## Bootstrap on a fresh machine

Clone the repo, then symlink:

```bash
git clone git@github.com:AlexK-Notable/hypr-doctor.git ~/repos/claude-dirs/hypr-doctor
cd ~/repos/claude-dirs/hypr-doctor

mkdir -p ~/.claude/skills ~/.claude/hooks ~/bin
ln -s "$PWD/skills/hypr-doctor"       ~/.claude/skills/hypr-doctor
ln -s "$PWD/hooks/hypr-doctor-drift.sh" ~/.claude/hooks/hypr-doctor-drift.sh
ln -s "$PWD/bin/hypr-doctor"           ~/bin/hypr-doctor
```

Then register the SessionStart hook in `~/.claude/settings.json`:

```json
"SessionStart": [
  /* ... existing entries ... */
  {
    "hooks": [
      { "type": "command", "command": "$HOME/.claude/hooks/hypr-doctor-drift.sh" }
    ]
  }
]
```

Edit `skills/hypr-doctor/plugins.json` to match this machine's local-build
plugins (the manifest is machine-specific by design — paths, branches,
build commands).

## What's covered

- **Hyprland plugin ABI**: detects `.so` mtime older than `/usr/bin/Hyprland`
  mtime → triggers rebuild via the per-plugin `build_cmd` from `plugins.json`.
- **Qt6 binding skew**: compares `qt6-base` repo version vs `python-pyqt6`
  and `pyside6`. PyQt6 lag is the historical culprit and not locally fixable
  — the skill flags it and waits for Arch to catch up.
- **Failed systemd user units**: surfaces anything in `systemctl --user
  --failed`. Triage hints, not blind `reset-failed`.
- **xdg-desktop-portal**: detects failed portal units. `inactive` is healthy
  (D-Bus activated); `failed` is not.
- **AUR rebuild hints**: surfaces output of `rebuild-detector`'s
  `checkrebuild` if installed.

## What's NOT covered (yet)

- Mesa / nvidia driver / kernel module match — extend `stack_packages.graphics`
  in `plugins.json` and add a check function in `bin/hypr-doctor` when this
  becomes a recurring problem.
- Wallust output freshness — different domain.
- Plugin manifest sync with CLAUDE.md — doc concern, separate from runtime.

## License

Private repo. No license — internal/personal use.
