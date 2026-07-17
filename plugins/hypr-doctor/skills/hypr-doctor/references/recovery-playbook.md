# Recovery playbook

Per-failure-class playbook for `hypr-doctor audit` findings. Read the relevant
section when `audit` flags an issue and you're deciding what to do.

## Hyprland plugin ABI mismatch

### Symptom
- `hyprctl plugin load <so>` returns `Mismatched headers! Can't proceed.`
- Plugin missing from `hyprctl plugin list`.
- For Hyprtasking specifically: `$mainMod + G` does nothing.

### Root cause
The plugin `.so` was compiled against a different version of the Hyprland
headers than the running binary. Happens every Hyprland minor (0.55.x → 0.56.x)
and sometimes patch (0.55.1 → 0.55.2) bump.

### Fix
```bash
hypr-doctor rebuild              # rebuild all drifted plugins
hypr-doctor plugin-rebuild hyprtasking   # just one
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

For hyprtasking specifically, the active branch is `komi/workspace-fixes-v55`
and the upstream divergence concern is the LAYERS feature (see CLAUDE.md
"Plugin Management" section).

For dynamic-cursors, check `git show origin/main:hyprpm.toml` for the
correct pinned commit for the current Hyprland version.

## Qt6 ↔ Python bindings skew

### Symptom
- A Python+Qt app crashes on launch with SIGABRT. (⚠ Don't assume this for `arch-update-tray` — its *usual* failure is the env-import race under "Failed systemd user units"; the error text is identical. Verify before blaming the skew.)
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
systemctl --user mask <looping-unit>.service
# undo once python-pyqt6 catches up:
systemctl --user unmask <looping-unit>.service
```

Don't mask things you actually use — accept the noise if the app is needed.
(For `arch-update-tray` specifically, masking is the *wrong* fix — its failure is
the env-import race, solved by the drop-in. See "Failed systemd user units".)

## Failed systemd user units

### Symptom
- `hypr-doctor audit` reports N failed user units.
- `systemctl --user --failed` lists them.

### Root cause
Many. Today's swaync case was a launch race: an `exec-once` in Hyprland's
autostart raced the D-Bus activation systemd unit; the loser got "already
running" and exited 1; systemd's `Restart=on-failure` retried until
`StartLimitBurst` left the unit failed even though notifications themselves
worked.

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
| `Could not load the Qt platform plugin` / empty platform string at login | **Env-import race** — unit reached `graphical-session.target` before Hyprland imported `WAYLAND_DISPLAY`/`DISPLAY`, burning its start limit in the env-less window | Drop-in: raise `StartLimitBurst`/`RestartSec` to outlast the import + pin `Environment="QT_QPA_PLATFORM=wayland;xcb"`. Worked example below. |
| `start-limit-hit` reached | Cascade from any of the above | Fix the underlying issue, then `systemctl --user reset-failed <unit>` |

After fixing: `systemctl --user reset-failed <unit>`.

### Worked example: arch-update-tray (env-import race)

`arch-update-tray.service` (package unit, `After=/WantedBy=graphical-session.target`, runs `arch-update --tray`) fails at login with `Could not load the Qt platform plugin "xcb"` → `start-limit-hit`. **It looks identical to the Qt6↔Python skew above but is NOT it** — the tells are an *empty* platform string + "could not connect to display" in the journal, and the binary launches fine once the display env is present (`QT_QPA_PLATFORM=wayland timeout 3 arch-update --tray` survives → exit 124). Cause is the env-import race, not an ABI mismatch.

Durable fix — chezmoi-managed drop-in at `~/.config/systemd/user/arch-update-tray.service.d/override.conf`:

```ini
[Unit]
StartLimitIntervalSec=120
StartLimitBurst=20

[Service]
RestartSec=2
Environment="QT_QPA_PLATFORM=wayland;xcb"
```

**Distinguishing test** for any "no Qt platform plugin" failure: a *display/platform* error in `journalctl --user -u <unit>` = this race; a *symbol/version* error = a real ABI break (→ Qt6↔Python skew).

## Empty system tray (StatusNotifierWatcher / kded6)

### Symptom
- Waybar tray module is empty; tray apps (Blueman, Steam, Variety, Vesktop) never appear.
- Apps log `No such object path '/StatusNotifierWatcher'`.

### Root cause
On Hyprland with KDE components installed, `kded6` claims the `org.kde.StatusNotifierWatcher` D-Bus name but doesn't load the actual module — so nothing services tray registrations.

### Fix
Force the module to autoload via `~/.config/kded6rc` (chezmoi-managed):

```ini
[Module-statusnotifierwatcher]
autoload=true
```

Verify, or load it without a restart:

```bash
# List registered tray items (empty / "No such object path" = watcher not working)
dbus-send --session --dest=org.kde.StatusNotifierWatcher --type=method_call \
  --print-reply /StatusNotifierWatcher org.freedesktop.DBus.Properties.Get \
  string:org.kde.StatusNotifierWatcher string:RegisteredStatusNotifierItems
# Manually load the module (temporary)
qdbus6 org.kde.kded6 /kded org.kde.kded6.loadModule statusnotifierwatcher
```

After the fix, restart tray apps that started before the watcher worked — they must re-register.

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

## npm ↔ pacman split-brain (root `npm install -g` wrote into pacman territory)

### Symptom
- `safe-update`/`paru`/`pacman -Syu` fails with `error: failed to commit
  transaction (conflicting files)` naming files under `/usr/lib/node_modules/`.
- `/var/log/pacman.log` shows repeated `starting full system upgrade` lines
  with no `transaction started` after them — updates have been silently
  aborting, possibly for weeks.

### Root cause
A root `npm install -g` wrote into pacman-owned territory. npm self-updates
in place, and files new to that npm version are unowned by any package —
they collide when the repo's `npm` package catches up.

### Confirm
Compare the two version claims — a mismatch is the split-brain:
```bash
pacman -Q npm
grep '"version"' /usr/lib/node_modules/npm/package.json
```

### Fix (user runs — needs root)
```bash
sudo rm -rf /usr/lib/node_modules/npm && sudo pacman -Syu
```
Overwriting only the *listed* conflicts (`--overwrite`) is the wrong move —
it leaves hundreds of unowned strays behind (283 in the 2026-07 incident).

### Prevent
Never `sudo npm install -g` on this machine — use pacman/paru or a user
prefix. (Enforced by the self-learn PreToolUse guard from lrn-dd9489b2.)

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
