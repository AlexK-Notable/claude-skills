---
id: lrn-c9044f8c
type: behavior
scope: user
kind: surface-rule
source: teach
status: routed
created_at: '2026-07-14T07:32:27Z'
sightings: 1
evidence: []
routing:
  routed_at: '2026-07-14T07:32:27Z'
  destination: claude-md
  by: human
supersedes: null
superseded_by: null
resolution_note: fixture B3 adoption (provisional, overnight authorization; user ratification pending — supersede to veto). Qualified 3/3 baseline FAIL, trials.md Phase 0 round 3.
---

## Trigger
About to call notify-send with action buttons (-A) from a script or agent on this host (swaync daemon)

## Instruction
Bound the wait: finite -t <ms> (on expiry returns rc 0, stderr 'Wait timeout expired', EMPTY action output — branch on the output, not rc), or -e/transient, or a timeout(1) wrapper. Unbounded (-A with no -t, -t 0, or critical urgency), swaync shelves the expired popup without emitting NotificationClosed and the call blocks forever — never leave unattended prompts unbounded.
