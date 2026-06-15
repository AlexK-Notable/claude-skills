# GOTCHAS — curated operational lessons

Hard-won, reconfirmed lessons worth keeping. Raw captures land in
`GOTCHAS.journal.md` via `ha-note`; promote them here by hand once proven.
Each entry: what bit us, why, the fix, and when it applies. `unverified` entries
(if any) must be re-checked before acting on them.

> Seeded 2026-06-02 from the initial HA buildout (HA 2026.5.4). These are
> verified — we lived them.

---

## Containers & process

### `docker start` does not re-read `--env-file`
- **Status:** verified · **Applies when:** any HA-adjacent container whose config is in env (govee2mqtt, etc.)
- **Cause:** Docker bakes env at `create` time; `start`/`restart` reuse it.
- **Fix:** to change env you must `docker rm -f <name>` then `docker run …` again. A plain restart silently keeps the old env — which looks like "my config change did nothing."
- **Repro:** change a value in the env file, `docker restart`, observe the old value still in effect.

### Never edit `.storage/*.json` while HA is running
- **Status:** verified · **Applies when:** all `.storage` edits, every HA version
- **Cause:** HA holds these in memory and rewrites on save/shutdown.
- **Fix:** stop → back up → edit → validate JSON → start → verify (see STORAGE-SCHEMA.md). A live edit is silently overwritten on the next restart; malformed JSON bricks boot.

## Units & sensors

### `device_class: temperature` renders °F under a US unit system
- **Status:** verified · **Applies when:** country=US (Imperial), any °C source sensor
- **Cause:** HA auto-converts temperature entities to the system unit; US → Imperial → °F. So a Pi reporting 50 °C showed "122".
- **Fix:** per-entity override in `core.entity_registry` → `options.sensor.unit_of_measurement: "°C"` (we set ~51 Glances sensors). Make dashboard gauge labels match, and make alert thresholds compare the same unit (we'd been comparing °C numbers to °F values).

## Integrations

### Govee account API returns 454 → use API-key + LAN mode
- **Status:** verified · **Applies when:** govee2mqtt, Govee blocking account login
- **Cause:** `app2.govee.com/account/rest/account/v1/login` returns status **454** (blocked). With `GOVEE_EMAIL`/`GOVEE_PASSWORD` set, govee2mqtt fatally restart-loops.
- **Fix:** remove `GOVEE_EMAIL`/`GOVEE_PASSWORD` from the env (keep them in bws); run API-key (`GOVEE_API_KEY`) + LAN only. Then `docker rm -f` + `docker run` (env-file gotcha above). Only LAN-capable models control locally; others go via the cloud API.

### Exposed scripts aren't reliably surfaced to the LLM voice agent
- **Status:** verified · **Applies when:** want a deterministic phrase→action voice command
- **Cause:** the Claude conversation agent has control, but an exposed *script* didn't appear as a callable tool ("script isn't available in this configuration"), while direct light control worked.
- **Fix:** use a **sentence-trigger automation** + `prefer_local_intents: true` instead of routing through the LLM (see ASSIST.md). Sentence triggers need no exposure and are handled locally.

### The Voice PE status LED ring is a controllable light — keep it UNEXPOSED to Assist
- **Status:** verified · **Applies when:** an HA Voice PE (or similar satellite with a status light) is exposed to the conversation agent
- **Cause:** the Voice PE exposes its status ring as `light.<device>_led_ring` (rgb). If that entity is exposed, a generic "turn the lights `<color>`" sweeps it up alongside the real room lights, and the ring then **holds that color indefinitely** — nothing auto-resets it, and the entity isn't in the recorder, so there's no history/logbook to trace it (presented as an unexplained red ring for a week).
- **Fix:** keep `light.<device>_led_ring` unexposed (confirm it's absent from `.storage/homeassistant.exposed_entities` and that `.data.assistants` expose-new is empty). Verify *effective* exposure by **asking the agent to enumerate controllable entities** (the ring should not appear). Recover a stuck ring with `light.turn_on` + `rgb_color` (white = `255,255,255`).

### govee2mqtt does NOT honor `transition` — long fades snap
- **Status:** verified · **Applies when:** any Govee light via govee2mqtt, smooth multi-second-plus ramps
- **Cause:** Govee/govee2mqtt ignores or hard-caps the transition time.
- **Fix:** for smooth brightness/color ramps use **stepped automations** (a loop that nudges in small increments every 1–5 min), not one `light.turn_on` with a long `transition`. (Verified: 5%→100% `transition:20` jumped to full within ~6–10 s.)

### govee2mqtt group devices (BaseGroup/SameModeGroup) are functional, not cruft
- **Status:** verified · **Applies when:** auditing Govee devices
- **Cause:** they mirror Govee-app groups and each expose ~3 entities (power switch + status sensor + refresh button) — not zero.
- **Fix:** don't delete/disable assuming they're empty. Count entities per device via the **full** `device_id` (a truncated-prefix `==` match silently yields 0). To remove for real, delete the group in the Govee app so govee2mqtt stops publishing it.

### govee2mqtt lights read `unavailable` for ~10–20 s after an HA restart
- **Status:** verified · **Applies when:** just restarted HA
- **Cause:** MQTT entities have no state until govee2mqtt reconnects and republishes.
- **Fix:** wait and re-query before concluding a light broke — it self-heals.

## Networking

### A host's DHCP IP change silently breaks integrations pinned to the old IP
- **Status:** verified · **Applies when:** any zeroconf/IP-configured integration after a host's lease moves (Wyoming, Glances, ESPHome-by-IP, …)
- **Cause:** config entries store the IP **resolved at discovery time**. When the Nova moved `.229 → .232`, the Wyoming STT + wake and Glances-Nova entries kept the stale host → `state=setup_retry`, reason "Unable to connect". The bedroom Voice PE then showed `stt-provider-missing`; it *looked* like "not connected to Anthropic", but the Anthropic entry was loaded fine — STT just never reached it. Piper (on the Pi, IP unchanged) stayed loaded.
- **Fix:** edit `.storage/core.config_entries` `data.host` → new IP for the affected entries (HA **stopped**), then start. A config-entry **reload does NOT help** — host is read from entry data, not re-resolved. Durable fix: DHCP-reserve the host (the Nova is now reserved to `.232`).
- **Repro / diagnose:** WS `config_entries/get` shows the entries `setup_retry`/"Unable to connect" while `ss -ltn` on the host shows the ports listening and a container TCP-connect test reaches the **new** IP but times out on the **old** one.

## Lovelace / dashboards

### YAML dashboard keys must contain a hyphen
- **Status:** verified · **Applies when:** adding a `lovelace.dashboards.<key>` in configuration.yaml
- **Cause:** HA requires the dashboard url-path slug to contain `-`.
- **Fix:** use e.g. `bedroom-lighting:` not `lighting:` (the `title:` can be anything). Otherwise check_config fails: "Url path needs to contain a hyphen (-)".

## Adaptive Lighting

### AL switch entity_ids are DOUBLED when you set `name`
- **Status:** verified · **Applies when:** referencing AL switches in automations
- **Cause:** AL derives the entity_id from the (doubled) friendly name.
- **Fix:** the real ids are `switch.adaptive_lighting_{name}_adaptive_lighting_{adapt_color|adapt_brightness|sleep_mode}_{name}` and the **master** is `switch.{name}_adaptive_lighting_{name}` — NOT the README's `switch.adaptive_lighting_{type}_{name}`. Look them up via `/api/states` (filter `adaptive_lighting`) before wiring automations.

### Bedroom AL coexistence design — don't "fix" it
- **Status:** verified · **Applies when:** touching the bedroom lighting
- **Cause:** AL re-adapts on an interval and would fight manual color/brightness.
- **Fix:** AL owns **color temp only** (`adapt_brightness` switch OFF, `take_over_control: false` so brightness steps don't pause color). Brightness + the night red are owned by **stepped** automations (`bedroom_morning_ramp`, `bedroom_evening_wind_down`); `adapt_color` is toggled OFF at sundown / ON at sunrise−15 (daily, via `bedroom_al_color_resume`). If AL starts fighting the ramps, check `adapt_brightness` and `take_over_control` first.

## Hardware (Nova / RK3588)

### Onboard Bluetooth (RTL8821CS) BLE won't power on — dead end
- **Status:** verified · **Applies when:** Nova onboard radio, current BSP kernel
- **Cause:** the radio is **RTL8821CS** (not AIC8800 — `aic8800_bsp` is a red herring, refcount 0). BT via UART (`/dev/ttyS9`, `rtk_hciattach`). `hci0` comes UP, but `bluetoothctl power on` → `org.bluez.Error.Failed`, kernel `Opcode 0x0c7a failed: -56` (EBADRQC) — firmware-level LE power-on failure.
- **Fix:** none at the firmware level. We **dropped onboard BT**; HA left dongle-ready (container has `--cap-add NET_ADMIN --cap-add NET_RAW -v /run/dbus:/run/dbus:ro`). To fully silence HA's `habluetooth` errors you must also disable `bluetooth-rtl8821cs.service` + `killall rtk_hciattach` (remove hci0) + remove the bluetooth config entry — disabling the entry alone isn't enough (habluetooth auto-manages any present adapter).
- **Note:** the `bluetooth-rtl8821cs.service` is `Type=oneshot` backgrounding `rtk_hciattach`; default `KillMode=control-group` reaped it → fixed with a `KillMode=process` drop-in. (Mooted by dropping BT, but documents the systemd quirk.)

### Wi-Fi (rtw88) deep-power-save instability
- **Status:** verified · **Applies when:** Nova onboard Wi-Fi (RTL8821CS combo)
- **Cause:** deep LPS causes instability.
- **Fix:** `/etc/modprobe.d/rtw88.conf` → `options rtw88_core disable_lps_deep=1` (applies on reboot).

## Inventory tooling (this skill)

### Area registry keys the id as `id`, not `area_id`
- **Status:** verified · **Applies when:** parsing `core.area_registry`
- **Cause:** the area registry stores `id`; every other registry *references* it as `area_id`. An early `ha-inventory` mapped `{None: <name>}` and tagged every entity with one wrong area.
- **Fix:** read `a["id"]` for the area's own id; resolve an entity's effective area as `entity.area_id or device_registry[entity.device_id].area_id`.

### New entities lag the on-disk registry (HA debounces saves)
- **Status:** verified · **Applies when:** just created an entity (e.g. a YAML light group) and `ha-inventory` doesn't show it
- **Cause:** HA batches `.storage` registry writes; the entity exists live but isn't on disk yet.
- **Fix:** confirm via `GET /api/states/<id>`, not the disk snapshot; the registry flushes within minutes and `ha-inventory` then shows it.
