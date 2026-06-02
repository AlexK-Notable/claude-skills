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
