---
id: lrn-a103d52a
type: knowledge
scope: skill:home-assistant
source: backlog
status: pending
created_at: '2026-07-14T04:19:30Z'
sightings: 1
evidence:
  - origin: GOTCHAS.journal.md#2026-07-04
routing: null
supersedes: null
superseded_by: null
resolution_note: null
---

## Fact
custom_sentences wildcard slots need a lists: declaration per file; check_config does not validate custom_sentences

## Context
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** hassil resolves {item} as a slot-list reference; builtin intents declare their own lists, custom files do not inherit them. A MissingListError then breaks ALL local intent recognition at runtime while check_config still exits 0
- **Fix:** add 'lists: {item: {wildcard: true}}' to the custom_sentences yaml; verify with the conversation/agent/homeassistant/debug WS command after conversation.reload
- **Repro / verify:** `add a custom sentence using {item} without lists:, conversation.reload, then any non-trigger utterance -> hassil.errors.MissingListError in the log`
- **Tags:** assist, custom-sentences
