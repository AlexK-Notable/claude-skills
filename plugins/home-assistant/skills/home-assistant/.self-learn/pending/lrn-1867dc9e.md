---
id: lrn-1867dc9e
type: knowledge
scope: skill:home-assistant
source: backlog
status: pending
created_at: '2026-07-14T04:19:30Z'
sightings: 1
evidence:
  - origin: GOTCHAS.journal.md#sha256:ad88b7dfffb7
    note: journal entry dated 2026-06-02
routing: null
supersedes: null
superseded_by: null
resolution_note: null
---

## Fact
New entities (e.g. a YAML light group) don't hit on-disk core.entity_registry immediately — HA debounces registry writes, so ha-inventory (disk-based) lags by minutes

## Context
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** HA batches/debounces .storage registry saves
- **Fix:** confirm a just-created entity via the live API (GET /api/states/<id>), not the disk snapshot; the registry flushes later and ha-inventory then shows it
- **Repro / verify:** `add a light group w/ unique_id, restart, immediately grep core.entity_registry — absent though the state exists`
- **Tags:** inventory, registry
