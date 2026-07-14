---
id: lrn-ce37b7ee
type: knowledge
scope: skill:home-assistant
source: backlog
status: pending
created_at: '2026-07-14T04:19:30Z'
sightings: 1
evidence:
  - origin: GOTCHAS.journal.md#sha256:70207cfda93a
    note: journal entry dated 2026-06-15
routing: null
supersedes: null
superseded_by: null
resolution_note: null
---

## Fact
Adaptive Lighting intercept re-applies adaptive colour on light.turn_on — kill the AL MASTER to force a manual colour

## Context
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** With intercept:true (default), AL hooks light.turn_on and re-applies its computed colour. Turning the adapt_color (and even all sub-) switches OFF then immediately light.turn_on a manual rgb still snapped back to warm color_temp (switch-off vs turn_on race / intercept uses last adaptive value).
- **Fix:** Turn OFF the AL MASTER switch (switch.<name>_adaptive_lighting_<name>) — disables intercept + all adaptation — then set the colour; it sticks. Verified: sub-switches off alone failed; master off + rgb red held across all 6 members. The morning routine re-enables the master, so this self-heals.
- **Repro / verify:** `adapt_color off + light.turn_on rgb_color:[255,0,0] -> reads back color_temp warm; AL master off + same -> reads back rgb red.`
- **Tags:** adaptive_lighting
