---
name: solakaka-sm809pro
description: Use when working with the user's Solakaka SM809Pro gaming mouse (Yuandaxin/Elan, USB 04f3:026e wired / 04f3:026f 2.4G) on Linux — granting HID/udev permissions so the browser or a script can reach it, decoding or editing the web-configurator's Onboard_Config.json (button remaps, DPI, lighting, sensor settings), understanding the 3-byte action-code convention, or talking to the mouse's onboard memory directly over hidraw feature reports.
---

# Solakaka SM809Pro mouse

A budget MMO-style gaming mouse (16 assignable button slots, per-stage DPI, RGB) sold as
"Solakaka SM809Pro"; internally a **Yuandaxin (远大芯)** design on an **Elan** controller.
Configured through a **WebHID** browser app, not a native driver. There are also two
Windows-only `.exe` firmware flashers (`*_USB_IAP_*.exe`) — those are for firmware only and
should be run on real Windows (flashing over Wine risks bricking).

**Device:** VID `0x04F3` · wired PID `0x026E` · 2.4G-dongle PID `0x026F` · else Bluetooth.
**Web configurator:** `https://driver.yuandaxin-tech.com/HYX/V1000_SM809_3311/#/device`
(needs a **Chromium-based** browser — WebHID is not in Firefox).

Full byte tables, the DPI/lighting/performance field meanings, and the raw HID protocol
live in **`reference.md`** (read it when editing codes or doing direct access).
A helper CLI lives at **`~/bin/sm809-codec`** (decode a config, or encode a keybind).

## 1. HID permission setup (do this first — gates everything)

The mouse's `/dev/hidraw*` nodes are root-only by default, so neither the browser (WebHID)
nor a script can open the device until the user is granted access via a `uaccess` udev rule.

Create **`/etc/udev/rules.d/60-solakaka-sm809.rules`** (filename number **must sort below 73** — see gotcha):
```
KERNEL=="hidraw*", ATTRS{idVendor}=="04f3", ATTRS{idProduct}=="026f", TAG+="uaccess"
KERNEL=="hidraw*", ATTRS{idVendor}=="04f3", ATTRS{idProduct}=="026e", TAG+="uaccess"
```
Then (user runs, needs sudo — never run sudo from the agent per user's policy):
```
sudo udevadm control --reload-rules && sudo udevadm trigger
```
…and **physically replug** the mouse/receiver (the `uaccess` ACL is applied on a device *add* event).

**Verify (agent can do this, no sudo):**
```
getfacl /dev/hidrawN        # success = a "user:<name>:rw-" line, and a trailing + on ls -l
```
Find the mouse's nodes: iterate `/sys/class/hidraw/*/device/uevent`, match `04F3` / "Yuan Da Xin".

## 2. Reading / editing button bindings (Onboard_Config.json)

The web app imports/exports a JSON profile. To change bindings, edit that JSON and re-import,
or (advanced) write to the mouse directly (§4).

- **Decode a config:** `sm809-codec decode ~/Downloads/Onboard_Config.json`
- **Get bytes for a key:** `sm809-codec key "Ctrl+C"` → `0x70 0x01 0x06` · `sm809-codec key 7` → `0x70 0x00 0x24`
- **Explain a triplet:** `sm809-codec explain 0x40 0x01 0x00` → `DPI Cycle`

Each button's real action is `currentKey.code = [TYPE, P1, P2]`. Also set `currentKey.id`
(preset), `name` (literal, for custom keys) or `nameKey` (`mouse.labels.*`, for built-ins),
and keep `enabled` consistent. TYPE/P1/P2 and the keyboard usage table are in `reference.md`.
DPI-Cycle specifically is `id:"m6"`, `nameKey:"mouse.labels.dpiCycle"`, `code:["0x40","0x01","0x00"]`.

### Editing workflow that avoids clobbering other settings
1. Work from the user's **latest** export — they may have changed sensor/DPI/lighting since you last read it.
2. Write a **new** file (e.g. `Onboard_Config_WoW.json`), never overwrite their export.
3. After editing, **diff old vs new** and confirm *only the intended buttons* changed — the
   `dpi`/`performance`/`other`/`sensorType` blocks must stay byte-identical unless intentionally edited.
   (This exact check caught a stale-`performance` regression once.)
4. Re-decode the new file with `sm809-codec decode` to confirm every code maps to the intended key.

## 3. Sensor / performance guidance (for aim-focused / FPS use)
- **angleSnap → 0** (edits raw input; universally off for aiming)
- **rippleControl → 0** (smoothing latency; only useful at ultra-high DPI)
- **motionSync** → preference (~1 ms latency vs steadier report timing; try both)
- **liftOffDistance** → 1–2 mm (lower = cleaner swipe resets)
- `pollingRate` is an enum index, not Hz (`1` = 1000 Hz here).

## 4. Direct onboard access (no browser)

Yes — the mouse can be driven directly. The configurator only uses **HID feature reports**,
reachable from Linux hidraw once §1 is done. Report id `5` = status (read), report id `6` =
command (write + ACK). Command packet = `[opcode, seq, subcmd, checksum, …]` with
`checksum = (6 + sum of other bytes) & 0xFF` at byte 3; ACK = `receiveFeatureReport(6)` byte1==1.
Known opcodes: `0x0F` reset, `0x11` macro. **Caveat:** the per-field *write* opcodes
(buttons/DPI/lighting) are not fully reverse-engineered yet — to finish, either keep analyzing
the app's apply-functions or capture the feature reports with `usbmon`/Wireshark while clicking
"Apply", then replay. Reading state and importing JSON via the web app both work today.
See `reference.md` for the packet layout and a hidapi read example. (No `libratbag`/Piper
support exists for this mouse.)

## Gotchas
- **udev filename < 73**: `uaccess` is applied by `/usr/lib/udev/rules.d/73-seat-late.rules`, which
  reads the tag *at file 73*. A `99-*.rules` sets the tag too late — it shows in `CURRENT_TAGS`
  but no ACL is ever applied. Name the file `60-*` (or anything <73).
- **`button12` (left click) `enabled:false`** appears in exports — likely a benign UI artifact
  (you can't disable the primary click), but verify left-click still fires after applying.
- **WoW keybinds**: extended F-keys aren't supported by WoW. Good non-conflicting keys are the far
  action bar `7 8 9 0 - =` (slots 7–12, hard to reach on keyboard) plus default-unbound `[ ] \ ;`.
- **DPI cycle quirk**: uses preset `m6` while DPI+/− use `m19`. Label key is `dpiCycle`, not `dpiLoop`.
- Firmware `.exe` flashers: Windows-only; flash on real Windows, not Wine (brick risk).
