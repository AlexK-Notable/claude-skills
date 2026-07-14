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
