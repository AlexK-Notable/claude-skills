---
id: lrn-25f445cc
type: knowledge
scope: skill:home-assistant
source: backlog
status: pending
created_at: '2026-07-14T04:19:30Z'
sightings: 1
evidence:
  - origin: GOTCHAS.journal.md#sha256:0f93b25dbfe9
    note: journal entry dated 2026-06-03
routing: null
supersedes: null
superseded_by: null
resolution_note: null
---

## Fact
Bare relative light commands (dim / dimmer / brighter / 'lights down') have NO built-in HA intent sentence, so with prefer_local_intents the local agent finds no match and they fall through to the conversation LLM (Claude), which then verbosely enumerates every affected bulb. Built-in HassLightSet responses are already terse ('Brightness set') and every built-in sentence REQUIRES an explicit <brightness> value; HassTurnOn/Off have zero dim/bright sentences.

## Context
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** home_assistant_intents/data/en.json: all 38 HassLightSet sentences require a <brightness> slot; no relative-brightness intent exists. Verbose per-bulb output therefore always means the LLM agent handled it, not the local intents.
- **Fix:** Add local conversation sentence-trigger automations for the relative/vague phrasings, acting on the room's light group with set_conversation_response for a one-phrase reply. Standard on/off/set-percent already resolve locally + tersely via area-aware Assist because the Voice PE satellite is assigned to its area.
- **Repro / verify:** `Read en.json intents.HassLightSet.data[].sentences — none match bare 'dim the lights'. Say 'dim the lights' to a pipeline whose conversation agent is the LLM; it handles + enumerates instead of a terse local reply.`
- **Tags:** voice, assist, conversation
