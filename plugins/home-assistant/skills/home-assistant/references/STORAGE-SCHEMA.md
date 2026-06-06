# .storage schema + the safe-edit procedure

`/home/user/homeassistant/config/.storage/` (your `HA_CONFIG`) holds HA's internal state as JSON.
HA keeps these **in memory** and rewrites them on save/shutdown — so a live edit is
silently lost on the next restart, and a malformed file stops HA from booting.
Treat editing here as surgery.

## The mandatory procedure (every `.storage` edit)

```bash
H="ssh user@192.168.1.10 sudo -n"     # your HA_SSH from config.sh
F=/home/user/homeassistant/config/.storage/<file>

# 1. STOP HA  (so your edit isn't clobbered on its next save)
$H docker stop homeassistant

# 2. BACK UP  (malformed JSON bricks startup — always have a rollback)
$H cp "$F" "$F.bak.$(date +%s)"

# 3. EDIT     (jq/python for surgical changes; never reformat the whole file blindly)
# 4. VALIDATE JSON  (must parse before you start HA)
$H "python3 -c 'import json,sys; json.load(open(\"$F\"))' && echo OK"

# 5. START HA
$H docker start homeassistant

# 6. VERIFY the change actually took (read it back / check the behavior)
```

If HA won't boot after a start: `docker logs homeassistant` will show a JSON/parse
error → restore the `.bak` and start again.

## File map (the ones we actually touch)

| File | Holds | Secrets? | Why we edit it |
|---|---|---|---|
| `core.config_entries` | one entry per integration instance: `domain`, `title`, `source`, **`data`/`options` (← tokens/passwords)** | **YES** | tweak the Claude conversation subentry (`prompt`, `llm_hass_api`, `prefer_local_intents`); disable/remove an integration |
| `core.entity_registry` | every entity: `entity_id`, `platform`, `device_id`, `area_id`, `disabled_by`, `hidden_by`, `options` (e.g. unit override) | no | per-entity unit override (`options.sensor.unit_of_measurement`); rename; area override |
| `core.device_registry` | devices: `id`, `name`/`name_by_user`, `manufacturer`, `model`, `area_id` | no | assign a device to an area (e.g. smart bulbs → Bedroom) |
| `core.area_registry` | areas: **`id`** (referenced elsewhere as `area_id`), `name` | no | rarely; areas are usually UI-made |
| `homeassistant.exposed_entities` | which entities are exposed to assistants (`{"assistants":{"conversation":{"should_expose":true}}}`) | no | expose an entity/script to the voice agent |
| `assist_pipeline.pipelines` | Assist pipeline config (wake/STT/conversation/TTS) | no | inspect/adjust the voice pipeline |
| `hacs.repositories` | HACS repos (installed flag, category, version) | no | **read-only** for `ha-inventory`; don't edit by hand |
| `core.config` | unit system, country, location, time zone | no | unit-system / locale issues |

### Secret-safety reminder
Only `core.config_entries` (and some integration-specific storage files) carry
secrets, inside the `data`/`options` dicts. When you
read that file by hand, extract only `domain`/`title`/`source`/`disabled_by` — never
echo or commit `data`/`options`. `ha-inventory` already enforces this allowlist.

## Structure quirks that have bitten us

- **Area id key mismatch:** the area registry stores the id as **`id`**, but
  everything else *references* it as `area_id`. (This broke an early `ha-inventory`.)
- **Entities inherit area from their device.** An entity's own `area_id` is usually
  `null`; its effective area comes from `device_registry[device_id].area_id` unless
  explicitly overridden per-entity.
- **`device_class: temperature` auto-converts to the system unit.** With country=US the
  unit system is Imperial, so °C sensors render °F. Fix per-entity via
  `core.entity_registry` → `options.sensor.unit_of_measurement: "°C"` (apply it to each
  affected temp sensor). Gauge labels must match the chosen unit.
- **Editing `exposed_entities` requires HA stopped** like any `.storage` file — a
  running HA overwrites it on the next save.
