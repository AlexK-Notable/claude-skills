---
id: lrn-26ca9f13
type: knowledge
scope: skill:home-assistant
source: backlog
status: pending
created_at: '2026-07-14T04:19:30Z'
sightings: 1
evidence:
  - origin: GOTCHAS.journal.md#2026-06-03
routing: null
supersedes: null
superseded_by: null
resolution_note: null
---

## Fact
Config-flow integrations can be provisioned headlessly by hand-writing .storage/core.config_entries — no UI clicks, and the API key can come from bws

## Context
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** Config-flow integrations store creds in core.config_entries (data{}), not YAML — so !secret/secrets.yaml don't apply and they can't reuse another integration's key. UI is the only *documented* path.
- **Fix:** Stop HA, append an entry whose top-level 'version' = the integration's CONFIG_VERSION (read const.py), source='user', options={}, and a 'data' dict byte-identical to what the flow's async_create_entry() builds (read config_flow.py). entry_id = a ULID. Feed the secret via stdin (printf KEY | ssh 'sudo python3 inject.py') so it never hits argv/transcript; pull it from bws. Validate JSON, start HA.
- **Repro / verify:** `AI Automation Suggester v1.5.6 (CONFIG_VERSION=3): after inject+start, sensor.*_ai_provider_status_* reads 'connected' and *_last_error_message_* = 'No Error' → the injected key authenticates. Entities + services appear normally.`
- **Tags:** storage, config-flow
