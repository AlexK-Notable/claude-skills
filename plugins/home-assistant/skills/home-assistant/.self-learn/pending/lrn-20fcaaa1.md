---
id: lrn-20fcaaa1
type: knowledge
scope: skill:home-assistant
source: backlog
status: pending
created_at: '2026-07-14T04:19:30Z'
sightings: 1
evidence:
  - origin: GOTCHAS.journal.md#sha256:e46f35a3745e
    note: journal entry dated 2026-06-14
routing: null
supersedes: null
superseded_by: null
resolution_note: null
---

## Fact
Voice PE status LED ring is a controllable rgb light (light.<device>_led_ring); if exposed to Assist, a generic 'turn the lights <color>' command sweeps it up and it stays stuck on that color

## Context
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** The HA Voice PE exposes its status ring as an rgb light entity. When that entity is exposed to the conversation agent, 'turn the lights red' targets it alongside the real room lights. The ring then holds that color indefinitely - nothing auto-resets it, and the entity is not in the recorder, so there is no history/logbook trail to trace it (looked like an unexplained red ring for a week).
- **Fix:** Keep light.<device>_led_ring UNEXPOSED to the conversation assistant. Verify by asking the agent to enumerate controllable lights (ring should be absent), and by checking it is not in .storage/homeassistant.exposed_entities with .data.assistants expose-new empty. To recover a stuck ring: light.turn_on with desired rgb_color (e.g. white 255,255,255).
- **Repro / verify:** `Ring shows a fixed rgb in its light state with no recorder history; agent's controllable-lights list excludes it once unexposed`
- **Tags:** assist
