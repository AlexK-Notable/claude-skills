# Learnings

Reference-routed lessons, appended by self-learn (newest last). Each
entry carries its record id for provenance; regenerate nothing here —
this file is append-only.

## 2026-07-13 — lrn-e2e4026b

**Fact:** HA Core debounces .storage registry writes (delayed save): after a registry mutation, the on-disk .storage file can lag live state for seconds to minutes, so a file read or backup taken immediately after a change may be stale.

**Context:** Mechanism behind the existing verify-via-live-API rule in SKILL.md; surfaced during self-learn fixture-C absence-proofing (2026-07-13), which confirmed the causal fact appears on no loaded surface.

## 2026-07-14 — lrn-01865691

**Fact:** AL transition_until_sleep with sleep_rgb_or_color_temp=color_temp stalls at the bulbs' CCT floor — sleep_rgb_color is silently unused

**Context:** - **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** The evening glide interpolates min_color_temp→sleep_color_temp in color-temp space; lights clamp requests below their hardware min (Third Reality 3RCB01057Z floor ≈2202K), so a 1000K sleep target renders as dim warm-white, never red
- **Fix:** Set sleep_rgb_or_color_temp: rgb_color — AL 1.30.1 then lerps the post-sunset glide in RGB/HSV space with force_rgb_color=True (color_and_brightness.py ~line 357), bypassing the CCT floor; sleep_rgb_color becomes the real target
- **Repro / verify:** `With color_temp mode: compare AL switch attrs (color_temp_kelvin 1105) vs the light's actual state (2168K, the bulb floor) late evening`
- **Tags:** adaptive-lighting, zha

## 2026-07-14 — lrn-10b03b00

**Fact:** Removing a config entry is a REST DELETE, not a WS command

**Context:** - **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** The WS API has config_entries/get but NO config_entries/remove (returns success:false, error code unknown_command). Deletion is what the UI's delete button calls: an HTTP DELETE.
- **Fix:** DELETE /api/config/config_entries/entry/<entry_id> (e.g. ha_lib._req('DELETE', 'config/config_entries/entry/<id>')). Returns {require_restart: bool}; HA unloads the entry and removes its entities automatically — no .storage surgery, no restart for a clean unload. Used it to drop an orphan Adaptive Lighting instance ('Ada', no lights).
- **Repro / verify:** `WS {"type":"config_entries/remove","entry_id":...} -> {success:false, error:{code:unknown_command}}; the REST DELETE on the same entry_id -> {require_restart:false}.`
- **Tags:** api

## 2026-07-14 — lrn-2692005a

**Fact:** ZHA (and other integration) *device* triggers fail check_config but load fine at runtime

**Context:** - **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** check_config runs an offline sandbox that does NOT start integrations, so ZHA device-trigger validation can't resolve the gateway/device and errors: 'Device <id> has no config entry from domain zha' — the automation is disabled IN THE CHECK ONLY
- **Fix:** Verify validity differently: confirm device is integration-bound (device_attr config_entries/identifiers) and that the trigger came from HA's own device_automation/trigger/list; then reload and confirm the automation entity is state=on at runtime
- **Repro / verify:** `Add an automation with trigger: device / domain: zha / type: remote_button_short_press, run check_config -> ERROR; reload + GET states/automation.<x> -> on`
- **Tags:** automations, zha, check_config

## 2026-07-14 — lrn-40da742d

**Fact:** Govee H6006 bulbs are cloud Platform-API-only (not LAN-capable) in govee2mqtt: high-frequency ramp/AL commands get throttled and silently dropped while HA/app/logs report optimistic state that does NOT match the physical bulb

**Context:** - **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** govee2mqtt drives the 4 H6006 bedroom bulbs ONLY via Govee cloud Platform API (verified: ~1144 Using-Platform-API calls for H6006 in 6h vs LAN for the H610A strip and H60B2 lamp; H6006 exposes no LAN-Control toggle). The morning brightness ramp (per-60s) + Adaptive Lighting color (per-90s) x4 bulbs overload the rate-limited cloud API; it drops/misapplies commands but returns 200 success, so govee2mqtt + HA + the app report the commanded value while bulbs physically stay at power-on/last state (app showed 1% while bulbs were at 100%).
- **Fix:** Not fixable on the cloud path and not LAN-capable. Resolution: replace with Zigbee bulbs on ZHA (local, no cloud), then repoint the light.bedroom_lights HA group helper + dashboard per-bulb refs + Adaptive Lighting lights to the new entities. Until then, physical state is the only truth for these bulbs.
- **Repro / verify:** `Set light.bedroom_lights to 10pct while already on -> physically dims and holds across AL refreshes. Cold OFF then turn_on brightness 1 -> bulbs stay physically OFF while cloud reports off. Morning ramp: govee log shows brightness 1..99 climbing and app shows ~1pct, but bulbs are physically ~100pct.`
- **Tags:** govee

## 2026-07-14 — lrn-60fc4560

**Fact:** Govee (govee2mqtt) light brightness is NOT in the HA recorder — reconstruct ramps from the govee2mqtt container log, minding a timezone split

**Context:** - **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** These Govee lights record only on/off to HA history; historical on-states carry attributes=['friendly_name'] only (no brightness/color_mode), so /api/history shows brightness=None throughout a ramp. The real per-command brightness lives in 'docker logs govee2mqtt' ({"state":"ON","brightness":N}). TZ TRAP: govee2mqtt log timestamps AND 'docker logs --since/--until' are LOCAL (America/Los_Angeles), but the HA /api/history JSON returns UTC — querying govee with a UTC time silently returns the wrong hour of data.
- **Fix:** For Govee brightness/ramp debugging use: docker logs --since <LOCAL ISO> --until <LOCAL ISO> govee2mqtt | grep 'Command for' (brightness vs color_temp commands) and the 'DeviceState { ... brightness: N }' poll lines. Treat HA history as on/off-only for these lights.
- **Repro / verify:** `Pull light.smart_led_bulb HA history across a known morning ramp -> every on-state bri=None, attrs=['friendly_name']; same window in govee2mqtt shows brightness:1,3,4,5,7... climbing.`
- **Tags:** govee

## 2026-07-14 — lrn-926390e9

**Fact:** HA Lovelace frontend auth != API auth: a long-lived token works for the REST API via the Authorization: Bearer header, but the frontend reads its session from localStorage key 'hassTokens', NOT the bearer header. A LLAT alone won't log a browser into the UI.

**Context:** - **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** frontend uses home-assistant-js-websocket Auth, which loads saved tokens from localStorage.hassTokens (access_token + refresh_token + expires); LLATs are only accepted on API calls
- **Fix:** inject localStorage.hassTokens = {access_token: <LLAT>, token_type: 'Bearer', hassUrl: <url>, clientId: null, expires: <far-future-ms>, expires_in: 1800, refresh_token: ''} on the HA origin, then reload. clientId:null + far-future expires => frontend uses access_token directly and never tries to refresh. Used to drive dashboards via Playwright.
- **Repro / verify:** `navigate Playwright to http://192.168.1.232:8123 (redirects to /auth/authorize), set hassTokens in localStorage, reload -> lands authenticated on /home/overview`
- **Tags:** frontend, auth

## 2026-07-14 — lrn-4c961d32

**Fact:** pyscript @time_trigger('startup') fires on EVERY reload, not just HA boot

**Context:** - **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** pyscript.reload and homeassistant.reload_all re-run the module and re-fire the startup trigger. bedroom_ramps' startup handler blindly called _al_color_mode(), so every reload at night re-armed Adaptive Lighting colour and overrode the red wind-down with ~2000K warm white; with adapt_color left on, AL then reverted any manual red each 90s interval.
- **Fix:** startup handler must reconcile to the CURRENT time-of-day state, not blindly arm AL colour. Refactored: _resync_to_now() (night -> _apply_night red) is now shared by both the master OFF->ON state trigger and the startup trigger. A reload/restart at night now keeps red.
- **Repro / verify:** `Run homeassistant.reload_all (or pyscript.reload) after 22:00 with master ON -> bedroom flips red->warm white; the reload's startup is the trigger.`
- **Tags:** pyscript

## 2026-07-14 — lrn-d1723a48

**Fact:** pyscript cannot evaluate generator expressions — runtime crash, not load error

**Context:** - **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** pyscript's AST interpreter has no ast.GeneratorExp handler; tuple(f(x) for x in y) parses fine at (re)load and only raises NotImplementedError 'not implemented ast ast_generatorexp' when the line first executes — a path that looks deployed can be dead for days
- **Fix:** use list comprehensions inside tuple()/any()/etc: tuple([f(x) for x in y]); scan with python3 ast.walk for GeneratorExp before shipping pyscript code
- **Repro / verify:** `put tuple(int(x) for x in [1,2]) in a @service, reload, call it, see NotImplementedError in home-assistant.log (bedroom_autopilot night ramp crashed 4 nights straight this way)`
- **Tags:** pyscript

## 2026-07-14 — lrn-ce37b7ee

**Fact:** Adaptive Lighting intercept re-applies adaptive colour on light.turn_on — kill the AL MASTER to force a manual colour

**Context:** - **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** With intercept:true (default), AL hooks light.turn_on and re-applies its computed colour. Turning the adapt_color (and even all sub-) switches OFF then immediately light.turn_on a manual rgb still snapped back to warm color_temp (switch-off vs turn_on race / intercept uses last adaptive value).
- **Fix:** Turn OFF the AL MASTER switch (switch.<name>_adaptive_lighting_<name>) — disables intercept + all adaptation — then set the colour; it sticks. Verified: sub-switches off alone failed; master off + rgb red held across all 6 members. The morning routine re-enables the master, so this self-heals.
- **Repro / verify:** `adapt_color off + light.turn_on rgb_color:[255,0,0] -> reads back color_temp warm; AL master off + same -> reads back rgb red.`
- **Tags:** adaptive_lighting

## 2026-07-14 — lrn-6b53a403

**Fact:** HA check_config prints ERROR for ZHA device-trigger automations but exits 0 — false positive, do not 'fix'

**Context:** - **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** check_config runs in an isolated context without the live device registry, so device_id triggers from domain zha fail to resolve there; the running instance loads the same automations fine
- **Fix:** Treat exit code 0 as the verdict; confirm the automation entities are loaded/on in the live instance instead
- **Repro / verify:** `check_config on a config with SNZB-01P device triggers: 2 ERROR lines, exit 0, automations work live`
- **Tags:** config-validation, zha
