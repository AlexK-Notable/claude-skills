---
id: lrn-7e8b69a2
type: knowledge
scope: skill:home-assistant
source: backlog
status: pending
created_at: '2026-07-14T04:19:30Z'
sightings: 1
evidence:
  - origin: GOTCHAS.journal.md#sha256:9f94541ed1e1
    note: journal entry dated 2026-06-03
routing: null
supersedes: null
superseded_by: null
resolution_note: null
---

## Fact
HA 'sections' dashboards use a 12-col grid; Mushroom cards default to half-width (columns:6) so you MUST set grid_options per card

## Context
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** Sections view sizes each card on a 12-unit grid via per-card grid_options.{columns,rows}. Cards expose a default through getGridOptions(); Mushroom returns columns:6 (half). Cards with no getGridOptions default to 12 (full). So Mushroom cards silently tile 2-up and 'alignment: center' chips drift off the card edge unless you set columns explicitly.
- **Fix:** Set grid_options:{columns:N} per card (N in 3/6/9/12; 12 or 'full' = full width). For dynamic-height cards (mini-graph-card, cameras/picture-entity, markdown) add rows:auto or they clip. For a wide column_span section that won't span when placed after taller columns, set view-level 'dense: true' (row-dense backfill) AND/OR put the wide section FIRST. max_columns is a cap, not a target — to pack more columns on a tablet lower theme var ha-view-sections-column-min-width (default 320px).
- **Repro / verify:** `Put two custom:mushroom-* cards in a type:grid section with no grid_options -> they render half-width side by side, not full width.`
- **Tags:** lovelace, sections
