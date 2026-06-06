# Sanitization report — public-ready version of claude-skills

This branch (`claude/repo-sanitization-assessment-Jar7d`) holds a **sanitized,
generalized** version of the repo, produced so it can be made public without
exposing anything about your specific setup. **Your private `master` was never
touched** — all work happened on this branch only.

## What you're looking at

- **Commit 1 — "Sanitize repo into a generalized, public-ready version"**: the full
  sanitization diff vs `master`. Review this to see exactly what changed (55 files).
- **Commit 2 — this report + `dist/`**: delivery artifacts for you. These are **not**
  part of the public release (the bundle below was built from commit 1, before they existed).
- **`dist/claude-skills-public.bundle`**: the actual publishable artifact — a standalone
  git repo with **zero history** (a single "Initial public release" commit, neutral
  author `your-username <you@example.com>`). See `dist/README.md` to publish it.

## Placeholder conventions used (consistent across the tree)

| Personal value | Replaced with |
|---|---|
| `Alex Kechichian` | `Your Name` |
| `alexkechichian1@gmail.com` | `you@example.com` |
| `AlexK-Notable` (GitHub) | `your-username` |
| unix user `komi`, host `KOMI`/`komi-hypr` | `user`, `workstation` |
| `/home/komi/...` | `/home/user/...` (or `$HOME` / `~` in prose) |
| Real device IPs (`192.168.1.139/.229/.165/.188/.254`, …) | example scheme: router `.1`, sbc `.10`, printer `.20`, pi `.30`, laptop `.40`, workstation `.50` (all labeled "(example)") |
| Real MAC addresses | `aa:bb:cc:00:00:NN` / `AA:BB:CC:DD:EE:FF` placeholders |
| Owner devices (`indiedroid nova`, `zbred`/bredOS, `BIGTREETECH CB2`, Pi `komi-2`, AT&T gateway, Ring/Echo/LIFX/Govee, MacBook/iPad) | generic roles (an SBC, a 3D-printer controller, your router, a smart speaker/bulb/laptop) |
| Hardware serials / machine-ids (SONOFF dongle serial, `514f3e75…`) | removed; `/dev/ttyUSB0` etc. |
| Bitwarden project/secret UUIDs | `<your-project-id>` / `<your-secret-id>` (no real tokens were ever committed) |
| Repo / dotfiles URLs | `github.com/your-username/...` |

## The two "inventory" plugins (per your instruction: example + template)

- **home-network** — `DEVICES.md` and the device tables were rebuilt as a labeled
  **EXAMPLE DATA / template** with synthetic devices; the format/columns are intact so
  you (or the skill's `home-net-learn` agent) can refill them. A nice byproduct: the docs
  now suggest keeping your *real* entries in a git-ignored `DEVICES.local.md`.
- **home-assistant** — `INVENTORY.generated.md`, `TOPOLOGY.md`, and the `GOTCHAS` files
  were converted to example/template form; `config.sh` uses example HA host/path values;
  `GOTCHAS.journal.md` was reset to an empty header template. Genuinely-general HA lessons
  were kept; owner-specific entity/automation/device names were stripped.

## Verification performed

Full-tree sweeps (case-insensitive) for: `komi`, `kechichian`, `AlexK-Notable`,
`indiedroid`, `nova`, `zbred`, `bredos`, `BIGTREETECH`, `SONOFF`, the serial/machine-id
prefixes, `Alexs-MacBook`, real Bitwarden UUIDs, `AT&T`, the real IPv6 prefix, every
`192.168.x.x` literal, every MAC, and every `/home/<name>` path — **all clean** (only
example/placeholder values remain). The sweep was re-run against a **fresh clone of the
bundle** (the real artifact), which also confirmed exactly one commit with a neutral author.

## Judgment calls worth a glance before you publish

1. **Generic hardware/driver names kept as instructive examples**: `RK3588`,
   `rtw88_8821cs`/`RTL8821CS` (in `home-network/.../TROUBLESHOOTING.md` and `DISCOVERY.md`).
   These are common public part/driver names, not owner-identifying, and the surrounding
   text is framed as "for example, on an RK3588 SBC." If you'd rather they be fully generic,
   they're easy to soften further.
2. **Public software/integration names kept**: Home Assistant integration keywords
   (`govee`, `klipper`, `moonraker`, `spotify`, `sensevoice`, `piper`, …) remain as
   activation triggers/scope examples, and app names (`Sunshine`, `Plex`, `Weylus`) appear
   in example firewall rows. They name only public software, not your devices.
3. **cron-claude example prompts** `refresh-hyprtasking` / `refresh-dynamic-cursors` keep
   those public Hyprland plugin names as illustrative "keep a plugin fork updated" examples;
   the owner-specific fork *paths* were genericized.

None of these are identity or secret leaks; they're "how generic do you want it" choices.

## Recommended before going public

- Skim commit 1's diff once for tone/voice (the framing was rewritten from "mine" to
  "you can fork and adapt").
- Decide on items 1–3 above.
- Publish from the bundle per `dist/README.md`, then set placeholders (`your-username`,
  Bitwarden IDs, example IPs) to whatever you want the public default to be.
