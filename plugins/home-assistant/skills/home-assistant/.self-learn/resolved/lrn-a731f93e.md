---
id: lrn-a731f93e
type: knowledge
scope: skill:home-assistant
source: backlog
status: superseded
created_at: '2026-07-14T04:19:30Z'
sightings: 1
evidence:
  - origin: GOTCHAS.journal.md#sha256:313a5b309ceb
    note: journal entry dated 2026-06-08
routing: null
supersedes: null
superseded_by: canon
resolution_note: overnight batch per user authorization 2026-07-14 (safe subset)
---

## Fact
Re-enabling a disabled integration (pyscript here) needs core.config_entries edited with HA STOPPED — a disabled_by:user entry stays disabled across restarts

## Context
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** config entries persist disabled_by; a plain restart will not re-enable, and a live .storage edit is clobbered on shutdown
- **Fix:** stop HA, set the entry's disabled_by to null in .storage/core.config_entries, validate JSON, start HA
- **Repro / verify:** `entry shows disabled_by=user in core.config_entries; integration absent until disabled_by cleared`
- **Tags:** storage
