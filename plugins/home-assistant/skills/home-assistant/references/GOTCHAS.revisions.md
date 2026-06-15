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
