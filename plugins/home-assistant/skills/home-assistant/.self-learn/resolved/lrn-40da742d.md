---
id: lrn-40da742d
type: knowledge
scope: skill:home-assistant
source: backlog
status: routed
created_at: '2026-07-14T04:19:30Z'
sightings: 1
evidence:
  - origin: GOTCHAS.journal.md#sha256:ebbfc07d7142
    note: journal entry dated 2026-06-23
routing:
  routed_at: '2026-07-14T07:23:08Z'
  destination: reference
  by: human
supersedes: null
superseded_by: null
resolution_note: overnight batch per user authorization 2026-07-14 (safe subset) — reference append, reversible
---

## Fact
Govee H6006 bulbs are cloud Platform-API-only (not LAN-capable) in govee2mqtt: high-frequency ramp/AL commands get throttled and silently dropped while HA/app/logs report optimistic state that does NOT match the physical bulb

## Context
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** govee2mqtt drives the 4 H6006 bedroom bulbs ONLY via Govee cloud Platform API (verified: ~1144 Using-Platform-API calls for H6006 in 6h vs LAN for the H610A strip and H60B2 lamp; H6006 exposes no LAN-Control toggle). The morning brightness ramp (per-60s) + Adaptive Lighting color (per-90s) x4 bulbs overload the rate-limited cloud API; it drops/misapplies commands but returns 200 success, so govee2mqtt + HA + the app report the commanded value while bulbs physically stay at power-on/last state (app showed 1% while bulbs were at 100%).
- **Fix:** Not fixable on the cloud path and not LAN-capable. Resolution: replace with Zigbee bulbs on ZHA (local, no cloud), then repoint the light.bedroom_lights HA group helper + dashboard per-bulb refs + Adaptive Lighting lights to the new entities. Until then, physical state is the only truth for these bulbs.
- **Repro / verify:** `Set light.bedroom_lights to 10pct while already on -> physically dims and holds across AL refreshes. Cold OFF then turn_on brightness 1 -> bulbs stay physically OFF while cloud reports off. Morning ramp: govee log shows brightness 1..99 climbing and app shows ~1pct, but bulbs are physically ~100pct.`
- **Tags:** govee
