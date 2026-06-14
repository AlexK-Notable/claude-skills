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

### 2026-06-03 — 'Did HA go down?' is usually the Nova's Wi-Fi blipping, not HA crashing
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** The Nova (HA host) runs on Wi-Fi (wlan0; RTL8821CS/rtw88, known-flaky — ethernet enP4p65s0 is down). A brief Wi-Fi drop loses DNS + all sockets for ~1-2 min: the browser websocket drops (frontend shows 'Connection lost' = looks like HA died) and moonraker/other integration entities go 'unavailable'. HA core never restarts.
- **Fix:** Diagnose: 'docker ps' (container Up), curl /api/ (API running), 'docker logs --since 5m | grep -iE DNS|Connection lost|moonraker down' shows the blip window; getent hosts on the Nova confirms DNS recovered. It self-heals in ~1-2 min (sensors return, e.g. print state back to 'printing'). The PRINT is unaffected — Klipper runs on the printer board independent of HA. Durable fix: move the Nova to wired ethernet (enP4p65s0) and optionally disable wlan0 so it can't flap.
- **Repro / verify:** `Watch docker logs during a wifi blip: spotify 'Timeout while contacting DNS servers' + BrokenPipeError/ConnectionError + moonraker 'connection down, restarting', all clearing within ~2 min.`
- **Tags:** network, nova

### 2026-06-03 — light.bedroom_lights group reports color_temp_kelvin=None → attribute-based 'active scene' detection on the dashboard doesn't work
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** HA light groups only expose an attribute when members agree; the Govee/bulb group reports color_temp_kelvin=None whenever any member is in RGB mode (or members disagree). brightness/state ARE reliable, color_temp is not. So Mushroom scene-button coloring keyed on color_temp_kelvin always evaluates false.
- **Fix:** Don't key dashboard scene-active state on the group's color_temp_kelvin. Either use fixed/always-on button colors, or drive active-state from an input_select.bedroom_scene helper set by per-scene scripts (robust source of truth). Verify any dashboard Jinja with POST /api/template before relying on it — check_config does NOT validate Lovelace templates.
- **Repro / verify:** `POST /api/template: {{ state_attr('light.bedroom_lights','color_temp_kelvin') }} -> None even with bulbs at a warm temp.`
- **Tags:** lovelace, lights

### 2026-06-03 — pyscript loads top-level .py from config/pyscript/; verify load via a log.info marker + decorators.timing DEBUG showing time_next
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** pyscript.reload only logs file compile/trigger registration at DEBUG on the child loggers (custom_components.pyscript.global_ctx / .decorators.timing). A plain reload looks silent, so you can't tell if a new ramp file actually loaded and its triggers parsed.
- **Fix:** Set logger custom_components.pyscript=debug, call pyscript.reload, and look for 'Reloaded /config/pyscript/<file>.py' + 'trigger ... time_next = <when>'. A temporary top-level log.info() marker proves module execution. NOTE: '@time_trigger(once(sunrise - 15min))' is VALID (no space needed); pyscript computes the next fire time and you can read it from the timing DEBUG log to confirm an automation is armed without waiting for the event.
- **Repro / verify:** `Deploy a pyscript file, reload with INFO logging -> looks like nothing loaded; switch to DEBUG -> see the load + time_next.`
- **Tags:** pyscript

### 2026-06-03 — lovelace.dashboards is indented 2 spaces under 'lovelace:'; a string-replace edit with the wrong anchor silently no-ops AND can falsely report success
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** A deploy script did s.replace('    dashboards:', ...) (4 spaces) but the file uses '  dashboards:' (2 spaces). str.replace returns the string unchanged when the anchor isn't found, the script still wrote the file and printed 'registered' — a false positive. check_config still passed because the (unregistered) dashboard just wasn't added.
- **Fix:** After any anchored config edit, VERIFY the change actually landed (grep for the inserted key) — never trust the editing script's success message. Match exact indentation (lovelace dashboards keys live at 4 spaces under a 2-space 'dashboards:').
- **Repro / verify:** `Register a YAML dashboard via a 4-space-anchored replace -> no-op, dashboard never appears in the sidebar.`
- **Tags:** lovelace

### 2026-06-03 — Bare relative light commands (dim / dimmer / brighter / 'lights down') have NO built-in HA intent sentence, so with prefer_local_intents the local agent finds no match and they fall through to the conversation LLM (Claude), which then verbosely enumerates every affected bulb. Built-in HassLightSet responses are already terse ('Brightness set') and every built-in sentence REQUIRES an explicit <brightness> value; HassTurnOn/Off have zero dim/bright sentences.
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** home_assistant_intents/data/en.json: all 38 HassLightSet sentences require a <brightness> slot; no relative-brightness intent exists. Verbose per-bulb output therefore always means the LLM agent handled it, not the local intents.
- **Fix:** Add local conversation sentence-trigger automations for the relative/vague phrasings, acting on the room's light group with set_conversation_response for a one-phrase reply. Standard on/off/set-percent already resolve locally + tersely via area-aware Assist because the Voice PE satellite is assigned to its area.
- **Repro / verify:** `Read en.json intents.HassLightSet.data[].sentences — none match bare 'dim the lights'. Say 'dim the lights' to a pipeline whose conversation agent is the LLM; it handles + enumerates instead of a terse local reply.`
- **Tags:** voice, assist, conversation

### 2026-06-03 — An unclean host reboot can ZERO-FILL HA .storage files (seen: core.restore_state -> 134KB of NUL bytes) when the root ext4 is mounted data=writeback. HA detects the unparseable file at next startup, quarantines it as core.restore_state.corrupt.<ISO-ts>, auto-creates a fresh default, and raises a repair notification. Benign for restore_state (it is only a restart-restore cache); the fix is to acknowledge + delete the zeroed file, NOT restore from backup.
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** ext4 data=writeback + unclean reboot/power-loss: file metadata (size) is updated but data blocks are not flushed before reset, so the blocks read back as zeros. Root fs /dev/mmcblk1p1 (microSD) on the Nova is mounted writeback. restore_state is the usual victim because HA rewrites it constantly.
- **Fix:** Verify it's a host reboot not a manual-edit error: 'od -An -c <corrupt>' shows all \0, and dmesg shows a kernel boot at the corruption timestamp while the container has ExitCode=0 RestartCount=0. Click Submit on the repair notification (HA already recovered), delete the all-zeros .corrupt file. Confirm the OTHER .storage JSON (core.config_entries, *_registry) still parse via json.load. To reduce recurrence: clean reboots + consider remounting data=ordered.
- **Repro / verify:** `Unclean reboot while HA is running on data=writeback ext4 -> next boot: ERROR helpers.storage 'Unrecoverable error decoding storage core.restore_state ... unexpected character: line 1 column 1 (char 0)'.`
- **Tags:** storage, reboot, ext4

### 2026-06-08 — Adaptive Lighting reverting a light on a ~interval timer to ~1% = its sleep_mode switch is ON (with adapt_brightness ON); AL forces sleep_brightness+sleep_color_temp and, with take_over_control:false, ignores manual changes
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** AL applies sleep_brightness (default 1%) + 1000K every 'interval' seconds while sleep_mode is on; nothing in YAML/automations manages sleep_mode so a stray toggle stays stuck
- **Fix:** turn off switch.<instance>_adaptive_lighting_sleep_mode_<name> (and adapt_brightness if AL should be colour-only); the AL MAIN switch's brightness_pct attribute shows AL's computed target — the fastest diagnostic
- **Repro / verify:** `set the light to 100%; if it snaps back every ~interval s and switch...sleep_mode_<name>=on, that's it`
- **Tags:** adaptive_lighting

### 2026-06-08 — Re-enabling a disabled integration (pyscript here) needs core.config_entries edited with HA STOPPED — a disabled_by:user entry stays disabled across restarts
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** config entries persist disabled_by; a plain restart will not re-enable, and a live .storage edit is clobbered on shutdown
- **Fix:** stop HA, set the entry's disabled_by to null in .storage/core.config_entries, validate JSON, start HA
- **Repro / verify:** `entry shows disabled_by=user in core.config_entries; integration absent until disabled_by cleared`
- **Tags:** storage

### 2026-06-14 — Nova DHCP IP change (192.168.1.229 -> .232) silently broke zeroconf-pinned Wyoming STT + wake entries (and Glances-Nova); Piper on the Pi was unaffected
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** Wyoming + Glances config entries store the IP that was resolved at zeroconf discovery time. When the Nova's DHCP lease moved .229 -> .232, the entries kept the stale host, so HA's connect failed -> state=setup_retry 'Unable to connect'; the bedroom Voice PE then reported stt-provider-missing for stt.sensevoice_rknn. Looked like 'not connected to Anthropic' but the Anthropic entry was loaded fine - STT just never reached it.
- **Fix:** Edit .storage/core.config_entries data.host .229 -> .232 for the affected entries (HA STOPPED), then start. A config-entry RELOAD does NOT help - host is read from entry data, not re-resolved. Durable fix: give the Nova a DHCP reservation / static IP so it stops moving.
- **Repro / verify:** `config_entries/get shows wyoming entries setup_retry/Unable to connect while 'ss' on the Nova shows :10300/:10400 listening; HA container can TCP-connect to .232 but .229 times out / host-unreachable`
- **Tags:** wyoming

### SELFTEST 2026-06-14T19:38:28Z
- **Status:** verified (self-test, delete me)
