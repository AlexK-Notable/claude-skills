# Assist / voice pipeline

## Shape of it

```
"ok nabu" (microWakeWord ON-DEVICE on the Voice PE — the openWakeWord container on
           Nova:10400 is running but UNUSED: the pipeline's wake_word_entity is null)
   → STT SenseVoice int8 ONNX on CPU, 2 threads (Nova:10300, Wyoming; off the NPU since 2026-07-03)
   → conversation agent (local Assist intents first, then conversation.claude_conversation)
   → TTS Piper (Pi:10200, voice en_US-hfc_female-medium per the pipeline setting)
```

> Latency + model-choice benchmarks (2026-07-03): `~/repos/voice-assistant/research/`
> `2026-07-03-voice-benchmarks.md` — STT decode is now ~120 ms (CPU int8; was ~650 ms on
> the NPU pre-swap); the Claude leg is 1.6–5.8 s and dominates the round trip.

Two Anthropic subentries exist — **don't confuse them**:
- `conversation.claude_conversation` — the **voice agent** (`llm_hass_api: ['assist']`,
  can read + control exposed entities). This is what answers voice.
- `ai_task.claude_ai_task` — **not** a voice agent; it's for the `ai_task.generate_data`
  service. Routing a voice command here does nothing.

## Custom voice commands = local sentence-trigger automations (no LLM)

The reliable, scalable pattern for "when I say X, do Y" is a **sentence-trigger
automation**, handled by the built-in local Assist — not the LLM. With **"Prefer
handling commands locally"** on (`prefer_local_intents: true` on the conversation
subentry), Assist matches these first and only falls back to Claude for open-ended
requests.

Example (in `automations.yaml`) — the working `nightlight` command:
```yaml
- id: voice_nightlight
  alias: "Voice: nightlight (local sentence trigger)"
  triggers:
    - trigger: conversation
      command:
        - "nightlight"
        - "night light"
        - "[turn on|activate|set] [the] nightlight"
  actions:
    - action: script.nightlight
  mode: single
```
Grammar: `[optional]`, `(alt|alt)`. Every future custom command is just another
sentence-trigger automation — no per-command prompt-fiddling, no exposure needed.

## Exposure (what the LLM agent can see/control)

- Entities are exposed via `.storage/homeassistant.exposed_entities`:
  `{"<entity_id>": {"assistants": {"conversation": {"should_expose": true}}}}`.
- **Editing the file requires HA stopped** (it's a `.storage` file — see STORAGE-SCHEMA.md).
  The UI's **Settings → Voice assistants → Expose** tab (and the WS `homeassistant/expose_entity`
  it calls) changes exposure **live** — only direct file edits need HA stopped.
- HA does **not** auto-expose everything (privacy + LLM-context bloat). Sentence
  triggers need **no** exposure — that's why they're the primitive for phrase→action.
- **Gotcha:** exposed *scripts* are not reliably surfaced to the LLM as callable
  tools. "Run the nightlight script" via the LLM failed even though the script was
  exposed and worked when called directly. The fix was the sentence-trigger above,
  not more exposure. Prefer sentence triggers for deterministic commands.
- **Gotcha — the satellite's own LED ring is a "light":** the Voice PE exposes its
  status ring as `light.home_assistant_voice_0a78d4_led_ring` (rgb). If it's exposed,
  "turn the lights `<color>`" sweeps it up with the room lights and it **stays** that
  color (the ring holds state, and it isn't recorded — no history to trace it). Keep it
  **unexposed**; recover a stuck ring with `light.turn_on` + `rgb_color` (white = 255,255,255).

**Verify what the agent can *actually* control** (effective exposure, defaults included):
ask it. `POST /api/conversation/process` with `agent_id: conversation.claude_conversation`
and text *"list every entity you can control"* — what it enumerates IS its controllable
surface, faster and more truthful than reading `exposed_entities` by hand.

## Where it's configured

- Pipeline: `.storage/assist_pipeline.pipelines` (wake/STT/conversation/TTS selection).
- Conversation agent prompt + flags: `.storage/core.config_entries`, the `anthropic`
  entry's conversation subentry (`prompt`, `llm_hass_api`, `prefer_local_intents`,
  `recommended`). If `prefer_local_intents` doesn't seem to take in `recommended`
  mode, the UI toggle is **Settings → Devices & Services → Anthropic →
  (conversation entry) → Configure → "Prefer handling commands locally"** (may need
  to uncheck "recommended settings" to see it).
