---
id: lrn-266aa2f3
type: knowledge
scope: skill:home-assistant
source: backlog
status: pending
created_at: '2026-07-14T04:19:30Z'
sightings: 1
evidence:
  - origin: GOTCHAS.journal.md#sha256:3abb93e89cbc
    note: journal entry dated 2026-06-03
routing: null
supersedes: null
superseded_by: null
resolution_note: null
---

## Fact
pyscript loads top-level .py from config/pyscript/; verify load via a log.info marker + decorators.timing DEBUG showing time_next

## Context
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** pyscript.reload only logs file compile/trigger registration at DEBUG on the child loggers (custom_components.pyscript.global_ctx / .decorators.timing). A plain reload looks silent, so you can't tell if a new ramp file actually loaded and its triggers parsed.
- **Fix:** Set logger custom_components.pyscript=debug, call pyscript.reload, and look for 'Reloaded /config/pyscript/<file>.py' + 'trigger ... time_next = <when>'. A temporary top-level log.info() marker proves module execution. NOTE: '@time_trigger(once(sunrise - 15min))' is VALID (no space needed); pyscript computes the next fire time and you can read it from the timing DEBUG log to confirm an automation is armed without waiting for the event.
- **Repro / verify:** `Deploy a pyscript file, reload with INFO logging -> looks like nothing loaded; switch to DEBUG -> see the load + time_next.`
- **Tags:** pyscript
