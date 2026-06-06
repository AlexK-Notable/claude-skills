# Recovery playbook

Per-failure-class playbook for `hypr-doctor audit` findings. Read the relevant
section when `audit` flags an issue and you're deciding what to do.

## Hyprland plugin ABI mismatch

### Symptom
- `hyprctl plugin load <so>` returns `Mismatched headers! Can't proceed.`
- Plugin missing from `hyprctl plugin list`.
- A plugin's keybind or feature silently does nothing (the `.so` failed to load).

### Root cause
The plugin `.so` was compiled against a different version of the Hyprland
headers than the running binary. Happens every Hyprland minor (0.55.x → 0.56.x)
and sometimes patch (0.55.1 → 0.55.2) bump.

### Fix
```bash
hypr-doctor rebuild              # rebuild all drifted plugins
hypr-doctor plugin-rebuild <name>   # just one (name from plugins.json)
```

The script does: `cd <repo> && eval <build_cmd>` then
`hyprctl plugin unload <so> && hyprctl plugin load <so>`.

### When the rebuild itself fails
Upstream API drifted in a way the local source code doesn't yet handle.
This requires a cherry-pick from upstream:

```bash
cd $repo_dir
git fetch origin
git log origin/main --oneline | head -10   # find the API-adaptation commits
git cherry-pick <commit>                    # NEVER rebase — see CLAUDE.md
```

If you maintain a local fork on a long-lived feature branch, cherry-pick the
upstream API-adaptation commits onto your branch rather than rebasing, so your
own patches don't get reordered or dropped.

If a plugin pins to a `hyprpm.toml` commit matrix, check
`git show origin/main:hyprpm.toml` for the correct pinned commit for the
current Hyprland version.

## Qt6 ↔ Python bindings skew

### Symptom
- `arch-update-tray` or other Python+Qt apps crash on launch with SIGABRT.
- Journal shows: `This application failed to start because no Qt platform
  plugin could be initialized.` (Misleading — wayland IS in the available
  list. The fatal is actually in `QApplicationPrivate::init`.)
- `coredumpctl list` shows recent `python3` cores.

### Root cause
`qt6-base` was upgraded in [extra], but `python-pyqt6` (and sometimes
`pyside6`) is still on the previous version. Their compiled bindings call
Qt6 APIs that no longer ABI-match. Pacman doesn't block this because the
packages have no strict version dependency.

### Fix
**Not locally fixable.** Wait for the Arch maintainer to bump
`python-pyqt6` (usually within hours-to-days). The mismatch resolves itself
on the next `pacman -Syu`.

### Mitigation while waiting
Mask any user-facing service that's looping on the broken binding to silence
boot coredumps:

```bash
systemctl --user mask arch-update-tray.service
# undo once python-pyqt6 catches up:
systemctl --user unmask arch-update-tray.service
```

Don't mask things you actually use — accept the noise if the app is needed.

## Failed systemd user units

### Symptom
- `hypr-doctor audit` reports N failed user units.
- `systemctl --user --failed` lists them.

### Root cause
Many. A common one is a launch race: an `exec-once` in Hyprland's autostart
races the D-Bus activation systemd unit (a notification daemon is a typical
culprit); the loser gets "already running" and exits 1; systemd's
`Restart=on-failure` retries until `StartLimitBurst` leaves the unit failed
even though the app itself works.

### Fix
**Do not just `reset-failed` blindly.** That clears the symptom but leaves
the bug. Triage first:

```bash
systemctl --user status <unit>        # current state + recent logs
journalctl --user -u <unit> -n 50     # full recent log
```

Common patterns:

| Log pattern | Likely cause | Fix |
|---|---|---|
| `An instance ... is already running` | Double-launch race (autostart + systemd unit + D-Bus) | Pick ONE startup path. Recommend keeping the systemd unit; remove the `exec-once` line from autostart.conf. Update via chezmoi. |
| `Permission denied` on a path | XDG / permission drift | Check `XDG_RUNTIME_DIR`, dir ownership, `groups` membership |
| Repeated `code=exited, status=1` with no other context | App-internal error | Run the binary in a foreground terminal to see real stderr |
| `start-limit-hit` reached | Cascade from any of the above | Fix the underlying issue, then `systemctl --user reset-failed <unit>` |

After fixing: `systemctl --user reset-failed <unit>`.

## xdg-desktop-portal regressions

### Symptom
- Screen capture broken in OBS, Vesktop, Weylus, browser screen-sharing.
- `hypr-doctor audit` shows a portal unit in `failed` state.

### Root cause
Either: (a) a portal backend package was upgraded and its socket activation
failed, (b) `xdg-desktop-portal-hyprland` lost the race with another backend
for an interface that the current `portals.conf` doesn't pin, or (c) the
backend itself crashed.

### Fix
First reload the portal stack:

```bash
systemctl --user restart xdg-desktop-portal \
                         xdg-desktop-portal-hyprland \
                         xdg-desktop-portal-kde \
                         xdg-desktop-portal-gtk
```

If the failure persists, check `~/.config/xdg-desktop-portal/portals.conf`
to confirm Hyprland owns the `ScreenCast` interface. The file is
chezmoi-managed; if it drifted, `chezmoi diff` will show it.

Reference: CLAUDE.md "xdg-desktop-portal Backend Selection" section.

## AUR rebuild hints

### Symptom
- `hypr-doctor audit` shows AUR packages flagged by rebuild-detector.
- An AUR app that uses dynamic linking starts misbehaving after a system
  library upgrade (cryptic shared-library errors, "symbol not found", etc.).

### Root cause
The AUR package was built against an older `.so` ABI that an upgraded
system library no longer provides. Common after major bumps to `boost`,
`icu`, `libsoup`, `webkit2gtk`, etc.

### Fix
Rebuild the listed AUR packages. Doesn't have to be all at once — start
with anything you actually use:

```bash
paru -S --rebuild <pkg>           # rebuild one
paru -Syua --rebuild              # rebuild all out-of-date AUR packages
```

Don't auto-rebuild from this skill without user consent — AUR builds can be
slow (e.g., webkit-gtk) and may require user attention for build prompts.

## When audit reports "everything healthy" but something is still broken

The script's checks are necessarily a subset of what *can* break. If the
user reports a symptom and `hypr-doctor audit` finds nothing:

1. Read `/var/log/pacman.log` for upgrades to packages outside
   `stack_packages.*`. Something obscure may have changed.
2. Check `journalctl -p err --boot=0` for kernel/driver errors not surfaced
   by the user-session checks.
3. Check `coredumpctl list --since "1 hour ago"` for crashes in any binary.
4. Consider extending the manifest's `stack_packages.*` arrays once you've
   found the culprit — that's how the skill stays useful over time.
