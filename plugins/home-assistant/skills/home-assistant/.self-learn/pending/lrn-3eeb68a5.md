---
id: lrn-3eeb68a5
type: knowledge
scope: skill:home-assistant
source: backlog
status: pending
created_at: '2026-07-14T04:19:30Z'
sightings: 1
evidence:
  - origin: GOTCHAS.journal.md#2026-06-14
routing: null
supersedes: null
superseded_by: null
resolution_note: null
---

## Fact
Nova DHCP IP change (192.168.1.229 -> .232) silently broke zeroconf-pinned Wyoming STT + wake entries (and Glances-Nova); Piper on the Pi was unaffected

## Context
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** Wyoming + Glances config entries store the IP that was resolved at zeroconf discovery time. When the Nova's DHCP lease moved .229 -> .232, the entries kept the stale host, so HA's connect failed -> state=setup_retry 'Unable to connect'; the bedroom Voice PE then reported stt-provider-missing for stt.sensevoice_rknn. Looked like 'not connected to Anthropic' but the Anthropic entry was loaded fine - STT just never reached it.
- **Fix:** Edit .storage/core.config_entries data.host .229 -> .232 for the affected entries (HA STOPPED), then start. A config-entry RELOAD does NOT help - host is read from entry data, not re-resolved. Durable fix: give the Nova a DHCP reservation / static IP so it stops moving.
- **Repro / verify:** `config_entries/get shows wyoming entries setup_retry/Unable to connect while 'ss' on the Nova shows :10300/:10400 listening; HA container can TCP-connect to .232 but .229 times out / host-unreachable`
- **Tags:** wyoming
