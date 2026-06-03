# GOTCHAS — journal (append-only, captured via `ha-note`)

Raw, dated operational lessons. The DURABLE store in the lean model: append here
via `ha-note`, never rewrite this file with an LLM. Promote well-worn, reconfirmed
entries up into the curated `GOTCHAS.md` by hand, then leave the journal entry in
place (provenance). `unverified` entries must be re-checked before you act on them.

---

### 2026-06-02 — govee2mqtt group devices (model BaseGroup/SameModeGroup) mirror Govee-app groups and DO have ~3 entities each — they are functional, not empty cruft
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** govee2mqtt republishes the Govee account's groups/scenes as MQTT devices
- **Fix:** do not delete/disable assuming 0 entities; to remove for real, delete the group in the Govee app so gv2mqtt stops publishing it
- **Repro / verify:** `count entities per device via core.entity_registry keyed on the FULL device_id (a truncated-prefix == match silently yields 0)`
- **Tags:** govee, govee2mqtt

### 2026-06-02 — A YAML-mode lovelace dashboard key must contain a hyphen or check_config fails: 'Url path needs to contain a hyphen (-)'
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** HA requires lovelace.dashboards.<url_path> slugs to contain '-'
- **Fix:** use e.g. 'bedroom-lighting:' not 'lighting:' as the dashboards key (the title can be anything)
- **Repro / verify:** `add lovelace.dashboards with a no-hyphen key, then run check_config`
- **Tags:** lovelace, dashboard

### 2026-06-02 — New entities (e.g. a YAML light group) don't hit on-disk core.entity_registry immediately — HA debounces registry writes, so ha-inventory (disk-based) lags by minutes
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** HA batches/debounces .storage registry saves
- **Fix:** confirm a just-created entity via the live API (GET /api/states/<id>), not the disk snapshot; the registry flushes later and ha-inventory then shows it
- **Repro / verify:** `add a light group w/ unique_id, restart, immediately grep core.entity_registry — absent though the state exists`
- **Tags:** inventory, registry

### 2026-06-02 — govee2mqtt (MQTT) light entities read 'unavailable' for a few seconds after an HA restart until state repopulates from the broker — not a fault
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** MQTT entities have no state until govee2mqtt reconnects and (re)publishes after HA boots
- **Fix:** wait ~10-20s and re-query before concluding a light broke post-restart
- **Repro / verify:** `restart HA, immediately GET /api/states/light.smart_led_bulb -> unavailable, then on`
- **Tags:** govee2mqtt, mqtt

### 2026-06-02 — govee2mqtt (Govee MQTT) lights do NOT honor light.turn_on 'transition' for smooth ramps — they snap to the target within a few seconds regardless of the transition duration
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** Govee/govee2mqtt ignores or hard-caps the transition time; long fades (min/hours) don't glide
- **Fix:** for smooth brightness/color ramps use STEPPED automations (a per-minute controller that nudges in small increments), not a single light.turn_on with a long transition
- **Repro / verify:** `set a Govee light to 5%, then light.turn_on brightness_pct:100 transition:20; poll /api/states — jumps to 255 within ~6-10s, not a 20s glide`
- **Tags:** govee2mqtt, transition, lighting

### 2026-06-02 — Adaptive Lighting switch entity_ids are DOUBLED when you set a 'name': switch.adaptive_lighting_{name}_adaptive_lighting_{type}_{name} (e.g. ..._adapt_color_bedroom), and the MASTER is switch.{name}_adaptive_lighting_{name} — NOT the README's switch.adaptive_lighting_{type}_{name}
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** AL derives switch entity_ids from the (doubled) friendly name when 'name' is set
- **Fix:** look up the real ids via /api/states (filter 'adaptive_lighting') before referencing AL switches in automations
- **Repro / verify:** `configure adaptive_lighting with name: bedroom, restart, list switch.* — see the doubled ids`
- **Tags:** adaptive-lighting, gotcha

### 2026-06-02 — Bedroom AL coexistence design (don't 'fix' it): AL owns COLOR TEMP only (adapt_brightness OFF, take_over_control FALSE so brightness steps don't pause color). Brightness + night-red owned by stepped automations. adapt_color is toggled OFF at sundown / ON at sunrise-15 so the red window isn't fought
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** AL re-adapts on an interval and would fight manual color/brightness; splitting responsibilities avoids the war
- **Fix:** keep adapt_brightness off + take_over_control false; if AL ever starts fighting the ramps, check these two settings first
- **Tags:** adaptive-lighting, design

### 2026-06-03 — Config-flow integrations can be provisioned headlessly by hand-writing .storage/core.config_entries — no UI clicks, and the API key can come from bws
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** Config-flow integrations store creds in core.config_entries (data{}), not YAML — so !secret/secrets.yaml don't apply and they can't reuse another integration's key. UI is the only *documented* path.
- **Fix:** Stop HA, append an entry whose top-level 'version' = the integration's CONFIG_VERSION (read const.py), source='user', options={}, and a 'data' dict byte-identical to what the flow's async_create_entry() builds (read config_flow.py). entry_id = a ULID. Feed the secret via stdin (printf KEY | ssh 'sudo python3 inject.py') so it never hits argv/transcript; pull it from bws. Validate JSON, start HA.
- **Repro / verify:** `AI Automation Suggester v1.5.6 (CONFIG_VERSION=3): after inject+start, sensor.*_ai_provider_status_* reads 'connected' and *_last_error_message_* = 'No Error' → the injected key authenticates. Entities + services appear normally.`
- **Tags:** storage, config-flow

### 2026-06-03 — HA 'sections' dashboards use a 12-col grid; Mushroom cards default to half-width (columns:6) so you MUST set grid_options per card
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** Sections view sizes each card on a 12-unit grid via per-card grid_options.{columns,rows}. Cards expose a default through getGridOptions(); Mushroom returns columns:6 (half). Cards with no getGridOptions default to 12 (full). So Mushroom cards silently tile 2-up and 'alignment: center' chips drift off the card edge unless you set columns explicitly.
- **Fix:** Set grid_options:{columns:N} per card (N in 3/6/9/12; 12 or 'full' = full width). For dynamic-height cards (mini-graph-card, cameras/picture-entity, markdown) add rows:auto or they clip. For a wide column_span section that won't span when placed after taller columns, set view-level 'dense: true' (row-dense backfill) AND/OR put the wide section FIRST. max_columns is a cap, not a target — to pack more columns on a tablet lower theme var ha-view-sections-column-min-width (default 320px).
- **Repro / verify:** `Put two custom:mushroom-* cards in a type:grid section with no grid_options -> they render half-width side by side, not full width.`
- **Tags:** lovelace, sections
