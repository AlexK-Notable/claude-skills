---
id: lrn-f1e8e8f9
type: knowledge
scope: skill:home-assistant
source: backlog
status: pending
created_at: '2026-07-14T04:19:30Z'
sightings: 1
evidence:
  - origin: GOTCHAS.journal.md#2026-06-02
routing: null
supersedes: null
superseded_by: null
resolution_note: null
---

## Fact
govee2mqtt group devices (model BaseGroup/SameModeGroup) mirror Govee-app groups and DO have ~3 entities each — they are functional, not empty cruft

## Context
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** govee2mqtt republishes the Govee account's groups/scenes as MQTT devices
- **Fix:** do not delete/disable assuming 0 entities; to remove for real, delete the group in the Govee app so gv2mqtt stops publishing it
- **Repro / verify:** `count entities per device via core.entity_registry keyed on the FULL device_id (a truncated-prefix == match silently yields 0)`
- **Tags:** govee, govee2mqtt
