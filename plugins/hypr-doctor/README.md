# hypr-doctor

Post-`pacman -Syu` health check + repair toolkit for an Arch/CachyOS Hyprland
desktop. Triages the recurring drift that ships with rolling-release updates:
Hyprland plugin ABI mismatch, Qt6 ↔ python-pyqt6/pyside6 binding skew, failed
systemd user units, xdg-desktop-portal regressions, AUR rebuild hints.

This repo holds the source files. They live symlinked into their canonical
locations under `~/.claude/` and `~/bin/` so the tools just work; the repo
provides versioning, portability across machines, and a place to track
changes. Fork it and point the manifest, clone URL, and paths at your own
setup — see the bootstrap section below.

## Layout

| Repo path | Symlinked to | Purpose |
|-----------|--------------|---------|
| `skills/hypr-doctor/SKILL.md` | `~/.claude/skills/hypr-doctor/SKILL.md` | Claude Code skill — auto-discovered |
| `skills/hypr-doctor/plugins.json` | (under skills/) | Source-of-truth manifest of local-build plugins |
| `skills/hypr-doctor/references/` | (under skills/) | Progressive-disclosure reference docs |
| `hooks/hypr-doctor-drift.sh` | `~/.claude/hooks/hypr-doctor-drift.sh` | SessionStart hook — surfaces drift warnings |
| `bin/hypr-doctor` | `~/bin/hypr-doctor` | CLI: `audit` / `rebuild` / `abi-drift` / `ack-skew` / `plugin-rebuild NAME` |

The symlink target is the whole `skills/hypr-doctor/` directory (not each file
individually), so adding new reference files in the repo automatically shows
up under `~/.claude/skills/hypr-doctor/`.

## Daily use

```bash
hypr-doctor                              # audit, read-only (default)
hypr-doctor rebuild                      # apply fixes: rebuild drifted plugins + reload
hypr-doctor plugin-rebuild <plugin>      # rebuild one plugin (name from plugins.json)
hypr-doctor abi-drift                    # terse output for the SessionStart hook
hypr-doctor ack-skew                     # silence the hook about the current PyQt6↔Qt6 skew
```

The SessionStart hook fires on every Claude Code session start. If any drift is
detected (plugin .so older than Hyprland binary, or PyQt6 lagging qt6-base) it
prints a one-line warning that Claude sees as session context. Silent when
healthy — and stays silent about an acknowledged skew (see `ack-skew`) so a
known-unfixable lag doesn't erode the signal. Rebuild output is captured to
`~/.cache/hypr-doctor/rebuild-<plugin>.log` rather than flooding the terminal.

## Bootstrap on a fresh machine

hypr-doctor ships as a plugin inside the **claude-skills** monorepo — bootstrap
the whole repo rather than this plugin alone:

```bash
git clone git@github.com:your-username/claude-skills.git ~/repos/claude-skills
cd ~/repos/claude-skills
./install.sh   # symlinks the skill dir, ~/bin/hypr-doctor, and the drift hook
```

`install.sh` creates all three hypr-doctor symlinks (the skill dir, the
`~/bin/hypr-doctor` CLI, and the `~/.claude/hooks/hypr-doctor-drift.sh`
SessionStart hook). It does **not** edit `~/.claude/settings.json` (that file is
load-bearing and left manual) — register the SessionStart hook there yourself:

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

Then edit `skills/hypr-doctor/plugins.json` to match this machine's local-build
plugins (the manifest is machine-specific by design — paths, branches,
build commands).

## What's covered

- **Hyprland plugin ABI**: detects `.so` mtime older than `/usr/bin/Hyprland`
  mtime → triggers rebuild via the per-plugin `build_cmd` from `plugins.json`.
  Load success is verified against the live `hyprctl plugin list` (ground
  truth), keyed on each plugin's `loaded_name` — never against `plugin load`'s
  own output, which exits 0 and prints "loaded" on both success and failure.
- **Qt6 binding skew**: compares `qt6-base` version vs `python-pyqt6` and
  `pyside6`. PyQt6 lag is the historical culprit and not locally fixable — the
  skill flags it and waits for Arch to catch up. Acknowledge it with `ack-skew`
  to silence the hook; the ack self-expires when either version changes.
- **Failed systemd user units**: surfaces anything in `systemctl --user
  --failed`, each with its exit code and a code-specific hint (127 → missing
  command/shim, 126 → bad interpreter/venv, 203 → bad ExecStart, …). Targeted
  triage, never a blind `reset-failed`.
- **`~/bin` shim integrity**: flags dangling symlinks and thin `exec`-wrappers
  whose target path no longer exists — the "repo moved, shim still points at
  the old path" class (and the layout hypr-doctor itself depends on).
- **Python venv health**: runs each `watched_venvs` interpreter and prints the
  recreate recipe on failure — catches venvs orphaned by a python bump or a
  moved repo.
- **xdg-desktop-portal**: detects failed portal units. `inactive` is healthy
  (D-Bus activated); `failed` is not.
- **AUR rebuild hints**: surfaces `rebuild-detector`'s `checkrebuild` output
  if installed, plus a ready-to-paste `paru -S --rebuild <pkgs>` command.

## What's NOT covered (yet)

- Mesa / nvidia driver / kernel module match — extend `stack_packages.graphics`
  in `plugins.json` and add a check function in `bin/hypr-doctor` when this
  becomes a recurring problem.
- Wallust output freshness — different domain.
- Plugin manifest sync with CLAUDE.md — doc concern, separate from runtime.

## License

MIT — see the repository root.
