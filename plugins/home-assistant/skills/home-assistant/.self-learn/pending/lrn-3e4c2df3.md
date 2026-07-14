---
id: lrn-3e4c2df3
type: knowledge
scope: skill:home-assistant
source: backlog
status: pending
created_at: '2026-07-14T04:19:30Z'
sightings: 1
evidence:
  - origin: GOTCHAS.journal.md#2026-07-08
routing: null
supersedes: null
superseded_by: null
resolution_note: null
---

## Fact
Govee 'Tree Floor Lamp' (member of light.bedroom_lights) flares bright then settles on each night-downramp step; exposes stale phantom segment sub-entities

## Context
- **Status:** unverified  ⚠ re-check before acting
- **HA version:** 2026.5.4
- **Cause:** LEADING HYPOTHESIS (unconfirmed): the ramp sends one light.turn_on with rgb_color+brightness_pct+transition:2 every 60s; the Govee applies the color at its prior brightness first, then drops brightness, so each step briefly brightens before dimming. Only surfaced 2026-07-07 — first night the downramp reached the group (prior 4 nights it crashed at step 1). Separately, light.tree_floor_lamp_segment_001/002/003 report 255/white but last_changed 2026-07-03 — stale phantom entities the integration no longer syncs; NOT the live driver (parent + physical LEDs correctly followed the ramp to red@1%).
- **Fix:** TODO tomorrow, test off-hours: try brightness-before-color as two ordered calls, or drop transition for Govee members, or split the tree lamp out of the group ramp. Night hold sends no commands so it stays put after 22:00 — flares are winddown-window only.
- **Repro / verify:** `watch light.tree_floor_lamp physically during a 20:30-22:00 downramp; compare parent last_updated (tracks ramp) vs segment_00x last_changed (frozen 2026-07-03)`
- **Tags:** govee, lighting
