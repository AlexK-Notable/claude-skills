# GOTCHAS — revisions (append-only companion to the journal)

The journal is a META-RECORD of paths taken and what was believed AT THE TIME —
provenance, not a live mirror of HA. Journal entries are never rewritten or
deleted. When one later proves wrong, stale, or partial, file a revision here
(`ha-note --supersede <ref> --why …`) that points at the journal entry by its
ref. `ha-note --list` then flags that entry; `--pending` drops superseded /
retracted ones from promotion candidates.

Status vocabulary: superseded (no longer true) · corrected (true with a fix) ·
retracted (was never right) · confirmed (re-verified still true).

---

### 2026-06-15 — superseded f0d948
- **Target:** `f0d948` — 2026-06-03 — 'Did HA go down?' is usually the Nova's Wi-Fi blipping, not HA crashing
- **Status:** superseded
- **Why:** Nova moved to wired enP4p65s0 (DHCP-reserved .232) and wlan0 is DOWN — the premise (HA host on Wi-Fi) is inverted, so 'HA seems down = Wi-Fi blip' no longer applies.
- **See instead:** config.sh (Nova on wired). The generic diagnostic (docker ps/API up = not a crash; Klipper print independent of HA) still holds.

### 2026-06-15 — promoted 7867b8
- **Target:** `7867b8` — 2026-06-03 — lovelace.dashboards is indented 2 spaces under 'lovelace:'; a string-replace 
- **Status:** promoted
- **Why:** promoted into the curated GOTCHAS.md
- **See instead:** Anchored config edits can silently no-op — verify the change landed

### 2026-06-15 — promoted 0a86a8
- **Target:** `0a86a8` — 2026-06-03 — Config-flow integrations can be provisioned headlessly by hand-writing .stora
- **Status:** promoted
- **Why:** promoted into the curated GOTCHAS.md
- **See instead:** Config-flow integrations can be provisioned headlessly via core.config_entries

### 2026-06-15 — promoted b1fd94
- **Target:** `b1fd94` — 2026-06-03 — HA 'sections' dashboards use a 12-col grid; Mushroom cards default to half-wi
- **Status:** promoted
- **Why:** promoted into the curated GOTCHAS.md
- **See instead:** "Sections" dashboards use a 12-col grid — Mushroom cards default to half-width

### 2026-06-15 — promoted 5680ad
- **Target:** `5680ad` — 2026-06-03 — light.bedroom_lights group reports color_temp_kelvin=None → attribute-based '
- **Status:** promoted
- **Why:** promoted into the curated GOTCHAS.md
- **See instead:** Don't key dashboard logic on a light *group's* color_temp_kelvin

### 2026-06-15 — promoted e3804a
- **Target:** `e3804a` — 2026-06-03 — pyscript loads top-level .py from config/pyscript/; verify load via a log.inf
- **Status:** promoted
- **Why:** promoted into the curated GOTCHAS.md
- **See instead:** pyscript reloads look silent — confirm a load via DEBUG, not INFO

### 2026-06-15 — promoted f038f2
- **Target:** `f038f2` — 2026-06-03 — Bare relative light commands (dim / dimmer / brighter / 'lights down') have N
- **Status:** promoted
- **Why:** promoted into the curated GOTCHAS.md
- **See instead:** Bare relative light commands ("dim", "brighter") have no built-in intent — they fall to the LLM

### 2026-06-15 — promoted 55baf6
- **Target:** `55baf6` — 2026-06-03 — An unclean host reboot can ZERO-FILL HA .storage files (seen: core.restore_st
- **Status:** promoted
- **Why:** promoted into the curated GOTCHAS.md
- **See instead:** An unclean reboot can zero-fill a `.storage` file (microSD ext4) — HA self-recovers

### 2026-06-15 — promoted 2daf28
- **Target:** `2daf28` — 2026-06-08 — Adaptive Lighting reverting a light on a ~interval timer to ~1% = its sleep_m
- **Status:** promoted
- **Why:** promoted into the curated GOTCHAS.md
- **See instead:** AL snapping a light to ~1% on an interval = sleep_mode is ON

### 2026-06-15 — promoted 860983
- **Target:** `860983` — 2026-06-08 — Re-enabling a disabled integration (pyscript here) needs core.config_entries 
- **Status:** promoted
- **Why:** promoted into the curated GOTCHAS.md
- **See instead:** Re-enabling a disabled integration needs a .storage edit with HA stopped

### 2026-06-15 — promoted 6706c0
- **Target:** `6706c0` — 2026-06-14 — Nova DHCP IP change (192.168.1.229 -> .232) silently broke zeroconf-pinned Wy
- **Status:** promoted
- **Why:** promoted into the curated GOTCHAS.md
- **See instead:** A host's DHCP IP change silently breaks integrations pinned to the old IP

### 2026-06-15 — promoted 743f45
- **Target:** `743f45` — 2026-06-14 — Voice PE status LED ring is a controllable rgb light (light.<device>_led_ring
- **Status:** promoted
- **Why:** promoted into the curated GOTCHAS.md
- **See instead:** The Voice PE status LED ring is a controllable light — keep it UNEXPOSED to Assist
