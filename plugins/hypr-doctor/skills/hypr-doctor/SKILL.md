---
name: hypr-doctor
description: Use after `pacman -Syu` (or any system update on this Arch/CachyOS Hyprland desktop) to triage and repair recurring post-update breakage. Covers Hyprland plugin ABI mismatch (Hyprtasking, dynamic-cursors — both local-build, rebuilt manually), Qt6 ↔ python-pyqt6/pyside6 binding skew (PyQt6 lag breaks Variety, arch-update-tray, and other Python+Qt apps with "no Qt platform plugin can be initialized" SIGABRTs), failed systemd user units (today's swaync double-launch was an example; each is shown with an exit-code triage hint), broken `~/bin` shims / dangling symlinks and orphaned Python venvs (the "a repo moved and a wrapper or venv now points at a dead path" class), xdg-desktop-portal regressions, and rebuild-detector hints for AUR packages. Triggers on terms like "post-update", "what broke", "another update broke my config", "rebuild plugins", "Hyprland plugin failed to load", "hypr doctor", "plugin ABI", "Mismatched headers", "Qt platform plugin", "system update broke", "command not found after update", "broken venv", "dangling symlink", "service keeps failing", or any session-start drift warning from `~/bin/hypr-doctor abi-drift`. The skill has TWO MODES — audit (read-only, the safe default) and rebuild (applies fixes). Always run audit first and present findings to the user before invoking rebuild. The manifest at `plugins.json` is the source of truth for which plugins to manage; edit it when adding/retiring local-build plugins.
---

# hypr-doctor

Post-update health check + repair tool for this Arch/CachyOS Hyprland stack.

The skill teaches **strategy** — when to audit, when to rebuild, how to interpret
the report, what to do when the script can't fix something itself.

The actual diagnostic logic lives in [`~/bin/hypr-doctor`](../../bin/hypr-doctor)
and the plugin metadata in [plugins.json](plugins.json). Both are designed to
be edited as the stack evolves; this skill explains the *mental model*.

## The mental model

A rolling-release Wayland desktop has many independent ABI contracts: compiler
output ↔ runtime libraries, language bindings ↔ their native counterparts,
plugins ↔ host application, systemd units ↔ D-Bus names. Every `pacman -Syu`
ships a small set of upgrades that *individually* are routine, but
*collectively* can drift one or more of those contracts apart.

The user's complaint is almost always "another update broke my config" — but
the actual cause is rarely a config file. It's an ABI contract that one side
quietly violated. The pattern is identical across layers:

| Layer | Producer | Consumer | Failure signature |
|-------|----------|----------|-------------------|
| Hyprland plugins | local `.so` build | running `Hyprland` binary | `Mismatched headers! Can't proceed.` from `hyprctl plugin load` |
| Python ↔ Qt | `qt6-base` | `python-pyqt6` / `pyside6` | `no Qt platform plugin can be initialized` → SIGABRT |
| Drivers ↔ kernel | `linux` headers | `nvidia` / DKMS modules | Module fails to load; `lspci -k` shows no driver |
| Systemd ↔ D-Bus | exec-once in autostart | DBus-activated unit | `An instance is already running!` loop → `start-limit-hit` |
| xdg-desktop-portal | one backend | another backend | ScreenCast/Inhibit silently no-ops |

**The umbrella response is the same in every case:** detect the version skew,
identify which side is rebuilt-able locally (plugins, AUR packages) vs.
upstream-blocked (PyQt6 in the official repo), and either rebuild or wait.

## When to invoke this skill

- The user reports anything that started after the last update: "broken
  config," "X stopped working," "another update," "what broke?"
- A session-start drift warning came in from `hypr-doctor abi-drift` (you'll
  see "⚠ hypr-doctor: post-update drift detected" in your context).
- User asks to rebuild plugins, check for AUR rebuilds, or audit system
  health after `pacman -Syu`.
- User says any of the trigger keywords listed in the description.

## How to use it

**Step 1 — always start with audit:**

```bash
hypr-doctor          # or: hypr-doctor audit  (same thing)
```

This is read-only. It produces a structured report with sections for: recent
stack updates (filtered from `/var/log/pacman.log`, compared by absolute
epoch), plugin ABI drift (load verified against the live `hyprctl plugin
list`), Qt6/PyQt6/PySide6 skew, failed systemd user units (each with an
exit-code-specific triage hint), `~/bin` shim integrity, Python venv health,
portal health, and rebuild-detector hints. Exit code is non-zero if anything
is flagged. (`checkrebuild` rescans every installed ELF, so a full audit takes
~10s; the `abi-drift` hook skips it and is instant.)

**Step 2 — present findings to the user.** Map flagged items to action:

| Flagged item | Action |
|---|---|
| Plugin `.so` older than Hyprland binary | `hypr-doctor rebuild` (or `hypr-doctor plugin-rebuild <name>` for one) |
| `python-pyqt6` lags `qt6-base` | **Wait** for the Arch repo to catch up (hours-to-days). Not locally fixable. Once acknowledged, run `hypr-doctor ack-skew` so the session-start hook stops nagging until the versions change. |
| Failed user unit | The audit prints the exit code + a hint. Follow it: 127 → a command/shim path is missing (check the shim-integrity section), 126 → bad interpreter (recreate the venv), else → `journalctl --user -u <unit> -e`. Fix the cause, *then* `reset-failed`. Never `reset-failed` blindly. |
| Broken `~/bin` shim / dangling symlink | The repo it points at moved or was removed. Fix the shim's target path (or recreate the symlink). This is also how hypr-doctor's own hook would silently die. |
| Broken venv | Run the printed `rm -rf … && python -m venv … && pip install -e …` recipe. Usually caused by a python version bump or a moved repo. |
| AUR rebuild hint | The audit prints a ready `paru -S --rebuild <pkgs>` line. Suggest it; don't auto-run (AUR rebuilds are slow and need user attention). |

**Step 3 — rebuild only when the user agrees, and only what they agree to:**

```bash
hypr-doctor rebuild                       # all drifted plugins
hypr-doctor plugin-rebuild hyprtasking    # named plugin only
```

Rebuild does: read manifest, `cd $repo_dir && eval $build_cmd`, then
`hyprctl plugin unload && hyprctl plugin load` to swap the in-memory .so.

## What hypr-doctor will NOT do (and you shouldn't either)

- **Will not** restart Hyprland or log the user out. Plugin reload happens
  via `hyprctl plugin unload/load` which is non-disruptive.
- **Will not** modify hyprland.conf, autostart.conf, or any config file.
  Config drift fixes are out of scope (use chezmoi for that).
- **Will not** install or upgrade packages (`pacman`, `paru`, `gh`). Triage
  only, plus local-build rebuilds.
- **Will not** auto-rebuild if `audit` shows everything is healthy. It only
  acts on drift.
- **Will not** touch a plugin marked `enabled: false` in the manifest. To
  re-enable, edit the JSON.

## The manifest

[plugins.json](plugins.json) is the shared source of truth. The script reads
it via `jq`; you read it via the Read tool. Schema:

```jsonc
{
  "plugins": [
    {
      "name": "hyprtasking",                    // short id used in CLI
      "enabled": true,                          // false → skipped entirely
      "loaded_name": "Hyprtasking",             // name in `hyprctl plugin list`; verifies a load took
      "repo_dir": "/abs/path/to/clone",
      "branch": "komi/workspace-fixes-v55",     // informational
      "remote_push_to": "komi",                 // informational
      "build_system": "meson",                  // informational ("make"/"meson"/"cargo"/…)
      "build_cmd": "<full shell pipeline>",     // run with `cd $repo_dir && eval $build_cmd`
      "so_path": "/abs/path/to/built.so",       // used for mtime check & hyprctl load
      "loader_directive_file": "…",             // informational, where the load line lives
      "loader_directive_pattern": "…",          // informational regex
      "notes": "…"                              // free-form
    }
  ],
  "watched_venvs": ["/abs/project-dir"],        // venvs whose interpreter health is checked
  "suppressions": { "pyqt_skew_ack": "x vs y" },// acknowledged skew pair; hook silent while it matches (set via ack-skew)
  "qt_python_bindings": { "watch": ["…"] },     // packages whose version skew matters
  "stack_packages": { "compositor": [], … }     // upgrades that warrant a hypr-doctor run
}
```

**When you should edit this file:**
- New local-build plugin → add a `plugins[]` entry.
- Plugin retired or migrated to hyprpm → set `enabled: false` and document
  `disabled_reason`.
- New stack-relevant package (e.g., a new Wayland portal backend) → add to
  the appropriate `stack_packages.*` array.

## Reference docs

- [recovery-playbook.md](references/recovery-playbook.md) — per-category
  fix sequences when audit flags an issue. Read this when you're unsure how
  to act on a specific failure class.
- [plugin-manifest.md](references/plugin-manifest.md) — full schema and
  worked examples for adding/editing/retiring plugins.

## Integration with the rest of the setup

- **CLAUDE.md "Plugin Management" section** documents the manual rebuild
  recipe and is the authoritative narrative reference. When this skill's
  diagnostic and that section disagree, CLAUDE.md is the source of truth
  for *how* to build; this skill is the source of truth for *when*.
- **SessionStart hook** at `~/.claude/hooks/hypr-doctor-drift.sh` runs
  `hypr-doctor abi-drift` on every Claude Code session start. Output is
  silent if healthy; surfaces a "⚠ hypr-doctor: post-update drift detected"
  line as session context if not. When you see that line, run `audit`
  immediately and report.
- **chezmoi**: if a fix involves editing a `~/.config/...` file (e.g., the
  swaync double-launch repair), follow the chezmoi safety doctrine — edit
  source, diff, apply — rather than touching the destination directly.
  hypr-doctor itself never edits configs.

## Failure modes of the tool itself

- **`hyprctl` unresponsive** (Hyprland not running, recovery TTY) → live
  load checks skipped; report still useful. Rebuild still works; plugin
  loads on next session.
- **`pacman` log truncated** (after `pacman -Scc` or logrotate) → "recent
  updates" section may be sparse. Not a failure — the other checks still
  run.
- **`jq` missing** → fatal, but unlikely on this system (jq is in `base`).
- **Plugin build fails** → script reports `✗ <name>: build FAILED` with the
  last 15 log lines and a pointer to the full log under
  `~/.cache/hypr-doctor/`; continues to next plugin. User must investigate
  the build error (usually upstream API drift requiring a cherry-pick).
- **hypr-doctor's own shim breaks** → `~/bin/hypr-doctor` is a symlink into
  `~/repos/claude-skills/plugins/hypr-doctor`. If that repo moves, the symlink dangles,
  the SessionStart hook silently no-ops (it's `|| true; exit 0`), and drift
  stops being surfaced. The shim-integrity check flags this *while it can still
  run* — but if it's already dangling, re-point the symlink to the repo's new
  location. This is the one failure the detector cannot announce about itself.

## Knowledge capture (optional, future)

This skill follows the same pattern as `home-network` — knowledge about
*which combinations of updates tend to break together* could be captured
into [recovery-playbook.md](references/recovery-playbook.md) over time, via
a background `claude -p` agent invoked at the end of each meaningful repair
session. Not implemented today; the playbook is hand-curated for now.
Add this when the recurring patterns become tedious to re-recognize.

<!-- self-learn:begin (do not hand-edit inside; managed by self-learn) -->
- **When starting post-update triage, or reading a safe-update log (~/.config/update-log/) that ends with '!! paru exited 1 — a package may have failed to build; the rest still upgraded.':** step zero of any update triage: verify the update actually committed before diagnosing what it broke. Don't trust safe-update's exit-1 message — a conflicting-files abort means NOTHING upgraded, not 'the rest still upgraded' (the script's handler conflates AUR build failures with transaction aborts). Verify via 'Errors occurred, no packages were upgraded' in the same log, or a 'transaction started' line in /var/log/pacman.log after the upgrade began *(lrn-b85a9921)*
- **When hypr-doctor plugin-rebuild fails and the console output is inspected to diagnose the cause:** don't diagnose from the console tail alone — hypr-doctor's rebuild command only prints the last ~15 lines of ninja/compiler output on failure, which can cut off earlier errors. Read the full log at ~/.cache/hypr-doctor/rebuild-<plugin>.log directly, or a fix pass based on the truncated tail will miss real breakage and look complete when it isn't. *(lrn-4736c04a)*
<!-- self-learn:end -->
