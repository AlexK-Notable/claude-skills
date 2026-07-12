# solakaka-sm809pro

Configure the **Solakaka SM809Pro** gaming mouse (a Yuandaxin/远大芯 design on an Elan
controller — USB `04f3:026e` wired, `04f3:026f` 2.4G) on Linux. The mouse has no native
driver; it's configured through a **WebHID** browser app that reads/writes an
`Onboard_Config.json` profile. This skill captures everything needed to work with it.

## What it covers

- **HID permissions** — the `uaccess` udev rule that lets the browser/scripts reach the
  mouse's `/dev/hidraw*`, incl. the non-obvious "filename must sort below 73" rule.
- **Button remaps** — the full 3-byte action-code convention (`[TYPE, P1, P2]`), HID usage
  tables, DPI/fire/media/combo encodings, decoded from the configurator's own JS bundle.
- **Sensor/DPI/lighting** — what `angleSnap` / `motionSync` / `rippleControl` / LOD / polling
  actually do and recommended values for aim-focused use.
- **Direct onboard access** — the HID feature-report protocol (report IDs, packet layout,
  checksum, ACK) for talking to the mouse without the browser.

See `skills/solakaka-sm809pro/SKILL.md` (workflows) and `reference.md` (full tables + protocol).

## CLI: `sm809-codec`

Symlinked into `~/bin` by the repo's `install.sh`.

```bash
sm809-codec decode ~/Downloads/Onboard_Config.json   # pretty-print every button
sm809-codec key "Ctrl+C"                             # -> 0x70 0x01 0x06
sm809-codec explain 0x40 0x01 0x00                   # -> DPI Cycle
```

## Notes

- The two `*_USB_IAP_*.exe` files that ship with the mouse are **firmware flashers** —
  Windows-only; flash on real Windows, not Wine (brick risk).
- No `libratbag`/Piper support exists for this mouse.
