---
id: lrn-d5f6b31b
type: behavior
scope: user
kind: anti-pattern
source: teach
status: routed
created_at: '2026-07-15T22:53:47Z'
sightings: 1
evidence:
  - session: f687d7ce-a89a-439a-abb5-b18d8e2f43c9
    ts: '2026-07-15T22:53:47Z'
    quote: sudo npm install -g self-updated npm to 11.17.0 while pacman still thought it owned 11.16.0-1
routing:
  routed_at: '2026-07-15T22:53:47Z'
  destination: claude-md
  by: human
supersedes: null
superseded_by: null
resolution_note: null
verified: true
verified_how: 'diagnosed live in post-update triage: pacman -Q npm vs /usr/lib/node_modules/npm/package.json mismatch; three pacman -Syu runs blocked over three weeks'
incident_cost: three weeks of silently blocked system updates (~180 MiB never applied)
generality: environment-specific
---

## Trigger
About to run sudo npm install -g (or any sudo-driven global package install that bypasses pacman) on this Arch/CachyOS system

## Instruction
Don't — install through pacman/paru or a user-level prefix instead; a sudo global install lets the tool overwrite pacman-owned files (e.g. /usr/lib/node_modules), creating a version split-brain that silently blocks every later system update until manually repaired
