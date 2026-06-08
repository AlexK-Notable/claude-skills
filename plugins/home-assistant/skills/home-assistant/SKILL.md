---
name: home-assistant
description: Operate the user's self-hosted Home Assistant (HA in Docker on the Nova, 192.168.1.232:8123). Use when working on Home Assistant — automations, scripts, dashboards, the voice assistant / Assist pipeline, exposed entities, integrations, HACS, Govee lights, the Z-Print/Moonraker printer, Glances sensors — or editing HA config (.storage JSON, automations.yaml, configuration.yaml, scripts.yaml). Provides safe-mutation discipline (back up + validate before editing; when HA must be stopped), a secret-safe inventory snapshot (ha-inventory), append-only gotcha capture (ha-note), and references for the storage schema, the Assist voice pipeline, and what is changeable by file/API vs only the HA web UI.
---

# home-assistant

Operate a real, in-use Home Assistant instance without breaking it. HA controls
physical devices (lights, a 3D printer's power, voice) — a bad edit has blast
radius in the real world, and a malformed `.storage` file bricks startup. This
skill is the discipline + tooling to act safely and to remember what we learn.

## The system in one breath

HA runs as a Docker container (`homeassistant`, `--network host`) on the **Nova**
(`192.168.1.232:8123`), config at `/home/komi/homeassistant/config`. Reachable
from KOMI over SSH with passwordless sudo. Voice stack: SenseVoice STT (NPU) +
openWakeWord on the Nova, Piper TTS on the Pi. Full topology, access patterns,
and the HA version live in **[references/TOPOLOGY.md](references/TOPOLOGY.md)**.

## Before you touch anything: orient, don't trust stale state

1. **Read the inventory for orientation**, not for ground truth:
   [references/INVENTORY.generated.md](references/INVENTORY.generated.md) lists
   installed integrations, HACS, areas, devices, the controllable entity surface,
   and automations. It is a **snapshot** — the user edits HA in the web UI
   constantly, and those edits are invisible until regenerated.
2. **Before any *mutating* action, verify it's current:**
   ```bash
   ha-inventory --check      # exit 0 = fresh · 2 = drift (regenerate) · 1 = error
   ```
   On drift, `ha-inventory` (no args) regenerates it. The check compares content
   hashes of HA's registry files, so it catches UI-made changes too.
3. For an entity's *live* state, an exact id in a read-only domain
   (sensor/binary_sensor/button/…), or to **confirm a change took**, query HA live
   via the **API** (the snapshot omits volatile state by design). There's an admin
   token in bws (`HA_TOKEN`); the recipes — `GET /api/states/<id>`, `POST
   /api/services/<domain>/<service>`, and `POST /api/template` (to **validate
   automation Jinja before it runs live**) — are in
   [TOPOLOGY.md](references/TOPOLOGY.md#live-api-access). Never echo the token.

## Safe-mutation discipline (the core rule)

Pick the lightest tool that does the job; never reach deeper than needed.

```
What are you changing?
├─ An entity's STATE (turn on a light, set a number, run a script)
│     → call the HA service. Lowest risk. Never edit files for this.
├─ A YAML-managed config (automations.yaml, scripts.yaml, configuration.yaml)
│     → edit the file, then ALWAYS validate before reload:
│         docker exec homeassistant python -m homeassistant \
│             --script check_config -c /config        # exit 0 before you reload
│     → reload via the relevant service (automation.reload / etc.) or restart.
├─ A .storage/*.json file (registries, config_entries, exposed_entities, pipelines)
│     → SURGERY. HA holds these in memory and rewrites them on shutdown, so a
│       live edit is silently overwritten. The procedure is mandatory:
│         1. STOP HA      2. back up the file      3. edit
│         4. validate JSON 5. START HA              6. verify the change took
│       Full procedure + which file holds what: references/STORAGE-SCHEMA.md
└─ A new integration / HACS install / most config-flow setup
      → usually UI-only. You can't do it from a file; tell the user the clicks.
        What is / isn't changeable without the UI: references/CAPABILITY-MAP.md
```

**Hard rules (these are the ones that bite):**
- **Never edit a `.storage` file while HA is running** — it gets clobbered on restart.
- **Always `check_config` (exit 0) before reloading/restarting** after a YAML edit.
- **Always back up a `.storage` file before editing it** — malformed JSON stops HA from booting.
- **Never print or commit secrets.** `.storage/core.config_entries` and integration
  storage contain tokens/passwords; `ha-inventory` is built to never emit them, but if
  you read those files by hand, do not echo `data`/`options`. Secrets → bitwarden (`bws`).
- **Physical-device actions** (printer power `switch.printer_power`, anything that
  moves/heats) — confirm intent before acting; there's a template-switch guard on the
  printer that refuses "off" mid-print.

## Voice / Assist

Custom voice commands are **sentence-trigger automations** handled locally (no LLM),
with "Prefer handling commands locally" on so Assist matches them before falling back
to the Claude conversation agent. Exposed entities, the pipeline, and the
exposed-entities-need-HA-stopped gotcha are in **[references/ASSIST.md](references/ASSIST.md)**.

## Capturing what we learn (lean, no magic)

When you hit a real operational lesson, append it with `ha-note` (atomic,
append-only, no LLM rewrites — the journal is the durable store):

```bash
ha-note "exposed_entities edits need HA stopped or they're lost" \
    --cause "HA caches .storage in memory, rewrites on shutdown" \
    --fix "stop container, edit, start" \
    --repro "diff the file before/after a no-stop edit + restart" \
    --ha-version 2026.5.4 --verified --tag storage
```

**Capture checklist — append ONLY if it's one of these** (else skip; do not
manufacture findings or log successes):
- a **version-specific** behavior change in HA or an integration,
- an **undocumented** service/entity quirk you had to discover,
- a place where **documented behavior was wrong**,
- an **integration gotcha** (auth dance, env reload, a setting that fights another).

Everything re-derivable from the code, the inventory, or the official docs does
**not** belong here. `--verified` only if you actually confirmed it; otherwise it
defaults to `unverified` and must be re-checked before anyone acts on it.

Curated, well-worn lessons live in **[references/GOTCHAS.md](references/GOTCHAS.md)**;
raw captures land in `references/GOTCHAS.journal.md`. Promote journal → curated by
hand when an entry has proven itself. `ha-note --list` shows the journal;
`ha-note --selftest` proves the capture path still works (a dead path = silent
stop-learning).

## Where HA knowledge lives (routing rule — avoid memory sprawl)

The user runs several memory systems. Keep them separate:
- **HA operational gotchas + the installed inventory → THIS skill's files, and nowhere else.**
- "What was I doing last session" → `.remember/`.
- Conceptual/architectural HA write-ups worth linking → z-notes.
- Code-structure facts → anamnesis.

If it's an HA operational lesson, it goes here — don't also stash it elsewhere.

## Tooling summary

| Command | Purpose |
|---|---|
| `ha-inventory` | regenerate the secret-safe installed-state snapshot |
| `ha-inventory --check` | drift check vs the snapshot (exit 0/2/1) — run before mutating |
| `ha-inventory --diff` | same, with a human summary of what changed |
| `ha-note "…" --fix … --repro …` | append one structured gotcha to the journal |
| `ha-note --list` / `--selftest` | read the journal / verify the capture path is alive |

Config seam (HA host, paths) is `config.sh` next to this file — the one place
HA-specific values live.

## References (load on demand — one level deep)

- [TOPOLOGY.md](references/TOPOLOGY.md) — boards, what runs where, access, HA version.
- [CAPABILITY-MAP.md](references/CAPABILITY-MAP.md) — what I can change by file/API vs UI-only.
- [STORAGE-SCHEMA.md](references/STORAGE-SCHEMA.md) — the `.storage` file map + the safe-edit procedure.
- [ASSIST.md](references/ASSIST.md) — voice pipeline, sentence triggers, exposed entities.
- [GOTCHAS.md](references/GOTCHAS.md) — curated hard-won lessons.
- [INVENTORY.generated.md](references/INVENTORY.generated.md) — generated snapshot (do not hand-edit).
