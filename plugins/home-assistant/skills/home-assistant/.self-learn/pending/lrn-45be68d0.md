---
id: lrn-45be68d0
type: knowledge
scope: skill:home-assistant
source: backlog
status: pending
created_at: '2026-07-14T04:19:30Z'
sightings: 1
evidence:
  - origin: GOTCHAS.journal.md#sha256:0ac5e682db65
    note: journal entry dated 2026-06-02
routing: null
supersedes: null
superseded_by: null
resolution_note: null
---

## Fact
Adaptive Lighting switch entity_ids are DOUBLED when you set a 'name': switch.adaptive_lighting_{name}_adaptive_lighting_{type}_{name} (e.g. ..._adapt_color_bedroom), and the MASTER is switch.{name}_adaptive_lighting_{name} — NOT the README's switch.adaptive_lighting_{type}_{name}

## Context
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** AL derives switch entity_ids from the (doubled) friendly name when 'name' is set
- **Fix:** look up the real ids via /api/states (filter 'adaptive_lighting') before referencing AL switches in automations
- **Repro / verify:** `configure adaptive_lighting with name: bedroom, restart, list switch.* — see the doubled ids`
- **Tags:** adaptive-lighting, gotcha
