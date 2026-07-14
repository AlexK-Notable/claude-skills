---
id: lrn-c8b8ba7e
type: knowledge
scope: skill:home-assistant
source: backlog
status: superseded
created_at: '2026-07-14T04:19:30Z'
sightings: 1
evidence:
  - origin: GOTCHAS.journal.md#sha256:267ae6520b8e
    note: journal entry dated 2026-06-03
routing: null
supersedes: null
superseded_by: canon
resolution_note: overnight batch per user authorization 2026-07-14 (safe subset)
---

## Fact
light.bedroom_lights group reports color_temp_kelvin=None → attribute-based 'active scene' detection on the dashboard doesn't work

## Context
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** HA light groups only expose an attribute when members agree; the Govee/bulb group reports color_temp_kelvin=None whenever any member is in RGB mode (or members disagree). brightness/state ARE reliable, color_temp is not. So Mushroom scene-button coloring keyed on color_temp_kelvin always evaluates false.
- **Fix:** Don't key dashboard scene-active state on the group's color_temp_kelvin. Either use fixed/always-on button colors, or drive active-state from an input_select.bedroom_scene helper set by per-scene scripts (robust source of truth). Verify any dashboard Jinja with POST /api/template before relying on it — check_config does NOT validate Lovelace templates.
- **Repro / verify:** `POST /api/template: {{ state_attr('light.bedroom_lights','color_temp_kelvin') }} -> None even with bulbs at a warm temp.`
- **Tags:** lovelace, lights
