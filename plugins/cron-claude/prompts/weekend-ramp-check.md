# Weekend bedroom-light ramp verification — 2026-06-27 (Saturday)

You are a scheduled check running on KOMI. Goal: confirm the bedroom lights did a
GRADUAL weekend wake-ramp this morning (08:30 → 10:00, 0% → 100%) instead of
snapping straight to 100%.

## Background
On 2026-06-22 a fix was deployed to `pyscript/bedroom_ramps.py` on the Home
Assistant host (the "Nova"):
- Weekends now ramp 08:30→10:00 via trigger `bedroom_weekend_morning` (cron `30 8 * * 0,6`).
- `_resync_to_now()` was changed to RESUME the ramp instead of hard-setting
  `brightness_pct=100` (the old bug that slammed weekend mornings to full).
Today (Sat 2026-06-27) is the first weekend it runs live. Verify it worked.

## Key facts
- HA + the `govee2mqtt` Docker container run on the Nova: `komi@192.168.1.232`
  (passwordless SSH; passwordless `sudo -n` THERE — never use local sudo).
- govee2mqtt logs are in LOCAL time (America/Los_Angeles); `docker logs
  --since/--until` are also local.
- These Govee lights do NOT record brightness to HA's recorder — per-command
  brightness is ONLY in the govee2mqtt log, as lines like:
  `Command for Smart LED Bulb (...): {"state":"ON","brightness":N}`.
- One bedroom bulb's MAC prefix is `B1:51` (an H6006). Master switch:
  `input_boolean.bedroom_auto_lighting`.

## Steps
1. Pull this morning's brightness commands for one bulb (run exactly this):
   ```
   ssh -o ConnectTimeout=8 komi@192.168.1.232 'sudo -n docker logs --since 2026-06-27T08:25:00 --until 2026-06-27T10:10:00 govee2mqtt 2>&1 | grep B1:51 | grep brightness | head -120'
   ```
   Read the `"brightness":N` values in time order.
2. (Best-effort) Confirm the master switch was ON this morning so the ramp was
   eligible. Try on KOMI (ha-api is in PATH via the login shell):
   `ha-api get "history/period/2026-06-27T08:25:00-07:00?filter_entity_id=input_boolean.bedroom_auto_lighting&end_time=2026-06-27T08:40:00-07:00"`
   If `ha-api` isn't found, skip and note it.

## Verdict
- **PASS** — brightness climbs gradually from ~0/1 toward ~100 across the window
  (e.g. 1, 3, 5, … , 99). The weekend ramp worked.
- **FAIL** — the first brightness value is already ~100 (a slam), or values are
  pinned high with no low start. The bug is NOT fixed.
- **SKIPPED (not a failure)** — no brightness commands AND master was OFF at 08:30.
  Adaptive was off so the ramp correctly didn't run. Say so clearly.
- **INCONCLUSIVE** — no commands and master state unknown/unreachable. State what
  you couldn't determine.

## Report
1. Write a concise report to `~/weekend-ramp-check-2026-06-27.md`: the verdict, the
   brightness sequence you saw, and the master state if known.
2. Fire a desktop notification with the verdict:
   ```
   notify-send "Weekend ramp check: <PASS|FAIL|SKIPPED|INCONCLUSIVE>" "<one-line summary>"
   ```

Do NOT modify any Home Assistant config, pyscript, or lights. Read-only
verification only. Keep it brief.
