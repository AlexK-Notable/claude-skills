---
id: lrn-e2e4026b
type: knowledge
scope: skill:home-assistant
source: teach
status: routed
created_at: '2026-07-13T22:40:59Z'
sightings: 1
evidence:
  - session: f687d7ce-a89a-439a-abb5-b18d8e2f43c9
    ts: '2026-07-13T22:40:59Z'
routing:
  routed_at: '2026-07-13T22:41:06Z'
  destination: reference
  by: human
supersedes: null
superseded_by: null
resolution_note: 'M1 exit (a) protocol run: one-motion teach --route, analyst-chosen destination'
---

## Fact
HA Core debounces .storage registry writes (delayed save): after a registry mutation, the on-disk .storage file can lag live state for seconds to minutes, so a file read or backup taken immediately after a change may be stale.

## Context
Mechanism behind the existing verify-via-live-API rule in SKILL.md; surfaced during self-learn fixture-C absence-proofing (2026-07-13), which confirmed the causal fact appears on no loaded surface.
