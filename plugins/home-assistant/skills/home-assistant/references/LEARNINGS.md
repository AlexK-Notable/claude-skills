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
