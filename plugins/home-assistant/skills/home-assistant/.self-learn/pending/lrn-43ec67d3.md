---
id: lrn-43ec67d3
type: knowledge
scope: skill:home-assistant
source: backlog
status: pending
created_at: '2026-07-14T04:19:30Z'
sightings: 1
evidence:
  - origin: GOTCHAS.journal.md#sha256:a10a08644adb
    note: journal entry dated 2026-06-02
routing: null
supersedes: null
superseded_by: null
resolution_note: null
---

## Fact
govee2mqtt (MQTT) light entities read 'unavailable' for a few seconds after an HA restart until state repopulates from the broker — not a fault

## Context
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** MQTT entities have no state until govee2mqtt reconnects and (re)publishes after HA boots
- **Fix:** wait ~10-20s and re-query before concluding a light broke post-restart
- **Repro / verify:** `restart HA, immediately GET /api/states/light.smart_led_bulb -> unavailable, then on`
- **Tags:** govee2mqtt, mqtt
