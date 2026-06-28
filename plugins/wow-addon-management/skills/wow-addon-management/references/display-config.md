# WoW Display & Window Configuration

## Table of Contents
- [System Overview](#system-overview)
- [The Problem](#the-problem)
- [Gamescope Setup](#gamescope-setup)
- [Hyprland Window Rules](#hyprland-window-rules)
- [Config.wtf Display Settings](#configwtf-display-settings)
- [Lutris Configuration](#lutris-configuration)
- [NVIDIA / CachyOS Kernel Notes](#nvidia--cachyos-kernel-notes)
- [Known Gamescope Issues](#known-gamescope-issues)
- [Troubleshooting](#troubleshooting)

## System Overview

| Component | Details |
|-----------|---------|
| GPU | NVIDIA RTX 4070 Ti SUPER, driver 590.48.01 |
| Compositor | Hyprland on Wayland |
| Kernel | linux-cachyos with nvidia-open modules |
| Game launcher | Lutris (game ID 659) via GE-Proton |
| Graphics API | D3D12 via VKD3D-Proton |
| Monitor (gaming) | AOC Q27G3XMN — DP-1, 2560x1440@180Hz, HDR |
| Monitor (secondary) | LG 27GL850 — DP-2, 2560x1440@144Hz |
| Monitor (tertiary) | ViewSonic VX2703 — HDMI-A-2, 1920x1080@60Hz |

Monitor layout is non-rectangular: DP-2 sits above, DP-1 bottom-right, HDMI-A-2 bottom-left.

## The Problem

Two issues with WoW on multi-monitor Hyprland:

1. **Wrong monitor**: Wine's virtual desktop spanning all 3 monitors doesn't map cleanly to Hyprland's monitor IDs. WoW's `GxMonitor` setting picks the wrong display.
2. **Window float/drift**: In windowed (non-maximized) mode, Wine tries to position the window at coordinates that made sense on its virtual desktop but map off-screen on the actual layout. Hyprland's tiling fights with Wine's positioning, causing the window to float/hover partially off-screen with no way to recover focus.

## Gamescope Setup

Gamescope creates a nested Wayland compositor presenting a **single virtual display** to Wine. This eliminates both problems — Wine sees exactly one monitor, and Hyprland sees gamescope as one well-behaved window.

### Launch flags (via Lutris command_prefix)

```
gamescope -W 2560 -H 1440 -w 2560 -h 1440 -r 180 -f --
```

| Flag | Purpose |
|------|---------|
| `-W 2560 -H 1440` | Gamescope output resolution (matches AOC native) |
| `-w 2560 -h 1440` | Game internal resolution (native, no upscaling) |
| `-r 180` | Framerate cap matching AOC's max refresh |
| `-f` | Fullscreen gamescope window |
| No `--force-grab-cursor` | Cursor naturally escapes on NVIDIA/Wayland — allows mouse to move to other monitors |

### Why no --force-grab-cursor

The user plays WoW with cursor freedom across monitors. On NVIDIA Wayland, cursor escape from gamescope happens naturally due to a known bug (gamescope #1711). This is actually desirable here — no flag needed.

## Hyprland Window Rules

In `~/.config/hypr/config/windowrules.conf`:

```ini
# Battle.net / WoW — force to gaming monitor (DP-1)
windowrule = monitor DP-1, match:class ^(steam_app_default)$
windowrule = monitor DP-1, match:class ^(battle.net.exe)$
windowrule = monitor DP-1, match:class ^(battlenet.exe)$
windowrule = monitor DP-1, match:class ^(wow.exe)$
windowrule = monitor DP-1, match:class ^(Wow-64.exe)$

# Gamescope — fullscreen on gaming monitor, no tiling interference
windowrule = monitor DP-1, fullscreen on, match:class ^(gamescope)$
windowrule = immediate on, match:class ^(gamescope)$
```

### Key rule explanations

- `monitor DP-1`: pins window to the AOC gaming display
- `fullscreen on`: prevents Hyprland from tiling or floating the gamescope window
- `immediate on`: disables VSync at the compositor level for gamescope (reduces latency)
- Both `wow.exe` and `Wow-64.exe` are matched as fallback if gamescope is not used

### Finding WoW's window class

WoW's Wine window class varies. To check at runtime:
```bash
hyprctl clients | grep -A 15 -i "wow\|warcraft"
```

## Config.wtf Display Settings

File: `.../World of Warcraft/_retail_/WTF/Config.wtf`

Key settings:

| CVar | Value | Notes |
|------|-------|-------|
| `GxMonitor` | `"0"` | Monitor index from Wine's perspective. With gamescope, always 0 (single virtual display). Without gamescope, may need trial-and-error (try 0, 1, 2) |
| `GxMaximize` | `"1"` | Maximized/borderless windowed mode. Prevents the window from floating at arbitrary positions. Set to 0 was the root cause of float/drift |
| `GxFullscreenResolution` | `"2560x1440"` | Must match gamescope's -W/-H |
| `GxWindowedResolution` | `"2546x1418"` | Windowed size (slightly smaller for title bar) |
| `GxApi` | `"D3D12"` | Uses VKD3D-Proton for D3D12->Vulkan translation. D3D11 (DXVK) is an alternative if issues arise |
| `vsync` | `"0"` | Disabled in-game; compositor handles sync |

## Lutris Configuration

File: `~/.local/share/lutris/games/world-of-warcraft-battlenet-1769929222.yml`

The gamescope command prefix is set in the top-level `system:` block:

```yaml
system:
  command_prefix: gamescope -W 2560 -H 1440 -w 2560 -h 1440 -r 180 -f --
  env:
    DXVK_HUD: compiler
    DXVK_STATE_CACHE_PATH: /data/battlenet
    ...
```

To disable gamescope, remove or comment out the `command_prefix` line. The Config.wtf + Hyprland rules still work as a standalone fallback.

## NVIDIA / CachyOS Kernel Notes

### Do NOT add kernel cmdline flags

CachyOS with nvidia-open 590+ already handles everything:

- **`nvidia_drm.modeset=1`**: Enabled by default since driver 545+. Verify: `/proc/fb` shows `nvidia-drmdrmfb`.
- **`nvidia_drm.fbdev=1`**: Also active by default. The fb entry in `/proc/fb` confirms it.
- **Early KMS (mkinitcpio MODULES)**: CachyOS's `linux-cachyos-nvidia-open` package handles module loading internally. Do NOT add nvidia modules to `MODULES=()` in mkinitcpio.conf — that's Arch wiki advice for `nvidia-dkms`, not CachyOS's integrated build.

### Potential problems from unnecessary kernel flags

- `nvidia_drm.modeset=1` explicit + driver default-on: usually harmless but has caused conflicts on some driver versions
- `nvidia_drm.fbdev=1` explicit: can cause black screen on boot with custom EDID (DP-1 uses `drm.edid_firmware=DP-1:edid/aoc-q27g3xmn.bin`)
- Adding nvidia to mkinitcpio MODULES: double-loading conflicts, initramfs size bloat

### Environment variables (already set in Hyprland config)

```ini
# ~/.config/hypr/config/environment.conf
envd = LIBVA_DRIVER_NAME,nvidia
envd = GBM_BACKEND,nvidia-drm
envd = __GLX_VENDOR_LIBRARY_NAME,nvidia
envd = WLR_NO_HARDWARE_CURSORS,1

# ~/.config/hypr/config/monitor.conf
env = NVIDIA_FORCE_EXPLICIT_SYNC,1
```

## Known Gamescope Issues

| Issue | Details | Impact |
|-------|---------|--------|
| Cursor visible during camera rotation | gamescope #1776 — cursor stays visible when hold-right-click dragging to rotate camera | Cosmetic only |
| `--force-grab-cursor` broken on NVIDIA | gamescope #1711 — cursor escapes even with the flag | Actually desirable for this setup |
| Lingering processes | gamescope #6250 — `gamescope-wl` and `gamescopereaper` may not exit after closing WoW | Kill manually: `pkill gamescopereaper` |
| WoW freezes | Reported on Lutris forums — game freezes inside gamescope | If encountered, remove `command_prefix` and rely on Config.wtf + Hyprland rules only |
| VK_KHR_present_wait stuck frames | NVIDIA developer forums — frame pacing issues in Wine Wayland + gamescope | Typically minor; driver updates improve this |

## Troubleshooting

### WoW still opens on wrong monitor (without gamescope)
1. Launch WoW, then run `hyprctl clients | grep -A 15 -i wow` to find the actual window class
2. Add a matching `windowrule = monitor DP-1, match:class ^(actual_class)$`
3. Try different `GxMonitor` values (0, 1, 2) in Config.wtf

### WoW floats off-screen
1. Ensure `GxMaximize "1"` in Config.wtf
2. Use gamescope — it eliminates the problem entirely
3. Emergency recovery: `hyprctl dispatch fullscreen 1` while WoW is focused

### Gamescope won't start
1. Check `gamescope --version` — need 3.14+
2. Ensure NVIDIA driver 515.43.04+ (you have 590)
3. Try without `-f` flag first to test in windowed mode

### D3D12 crashes on launch
1. Check for WoW's bundled `d3d12.dll` in game directory conflicting with VKD3D-Proton
2. Try switching to D3D11: set `GxApi "D3D11"` in Config.wtf (uses DXVK instead of VKD3D-Proton)
3. Ensure Wine version is set to Windows 10 in winecfg (WoW uses broken "12on7" codepath if it thinks it's Windows 7)
