# Capability map — what I can change, and how

The stable answer to "what's available to adjust?" This is the *action surface* —
it changes far less than the inventory does. Know which lane a change is in before
you start; reaching for the wrong lane is how things break.

## Lane 1 — Entity state (service calls). Lowest risk, do this by default.

Turn lights on/off, set brightness/color, set a `number`, run a `script`, play
media, press a `button`, select an option. These are **service calls**, reversible,
no files touched.

- How: call the HA service (via the conversation agent, or REST `POST /api/services/<domain>/<service>` with a token, or a UI action).
- Examples here: `light.turn_on` (the Govee bedroom bulbs), `script.nightlight`,
  `switch.printer_power` (guarded), `media_player.*` (Spotify), `number.z_print_*`.
- **No file editing for state changes — ever.**

## Lane 2 — YAML config (edit file → check_config → reload). Medium risk.

Files under `/home/komi/homeassistant/config/`:

| File | Holds | Reload without restart? |
|---|---|---|
| `automations.yaml` | UI/YAML automations (incl. our sentence-trigger voice cmds) | `automation.reload` |
| `scripts.yaml` | scripts (e.g. `nightlight`) | `script.reload` |
| `configuration.yaml` | `template:`, `switch:` (WoL), `lovelace:` dashboards, includes | partial; some need restart |
| `dashboards/*.yaml` | YAML-mode dashboards (system-health, printer) | UI refresh |
| `blueprints/…` | automation blueprints (the Glances alert blueprint) | `automation.reload` |

**Always** `check_config` (exit 0) before reloading. These are editable by me directly.

## Lane 3 — `.storage/*.json` (STOP HA → back up → edit → start). Surgery — last resort.

Internal state HA normally manages itself. Edit only when there's no service/UI path.
Mandatory stop-edit-start procedure + per-file map: **STORAGE-SCHEMA.md**.
Common reasons we've gone here: exposing entities to the voice agent
(`homeassistant.exposed_entities`), per-entity unit overrides
(`core.entity_registry`), area assignment (`core.device_registry`), tweaking the
Claude conversation subentry (`core.config_entries`).

## Lane 4 — UI-only (tell the user the clicks). I cannot do these from a file.

- **Installing a new integration** via its config flow (OAuth, discovery, credential
  entry). Most integrations. The *result* lands in `.storage/core.config_entries`, but
  the flow itself is UI/-API-driven, not hand-writable.
- **Installing a HACS repository** (browse → download). Once installed, its entities
  appear and become Lane 1/2.
- **Adding a Long-Lived Access Token** (Profile → Security).
- **Most "Configure" dialogs** on an existing integration (some map to `.storage`
  edits, but the supported path is the dialog).
- **Reordering/visual dashboard editing** in the UI (vs our YAML-mode dashboards).

When a task needs Lane 4, say so plainly and give the exact navigation, rather than
half-doing it via a fragile `.storage` poke.

## Rule of thumb

Prefer the **lowest lane** that accomplishes the task: state (1) over YAML (2) over
`.storage` (3); and if it's genuinely (4), hand it to the user instead of forcing it.
