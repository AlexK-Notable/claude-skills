---
id: lrn-ffcca33d
type: knowledge
scope: skill:home-assistant
source: backlog
status: pending
created_at: '2026-07-14T04:19:30Z'
sightings: 1
evidence:
  - origin: GOTCHAS.journal.md#sha256:6baee8c1abbc
    note: journal entry dated 2026-06-03
routing: null
supersedes: null
superseded_by: null
resolution_note: null
---

## Fact
'Did HA go down?' is usually the Nova's Wi-Fi blipping, not HA crashing

## Context
- **Status:** verified
- **HA version:** 2026.5.4
- **Cause:** The Nova (HA host) runs on Wi-Fi (wlan0; RTL8821CS/rtw88, known-flaky — ethernet enP4p65s0 is down). A brief Wi-Fi drop loses DNS + all sockets for ~1-2 min: the browser websocket drops (frontend shows 'Connection lost' = looks like HA died) and moonraker/other integration entities go 'unavailable'. HA core never restarts.
- **Fix:** Diagnose: 'docker ps' (container Up), curl /api/ (API running), 'docker logs --since 5m | grep -iE DNS|Connection lost|moonraker down' shows the blip window; getent hosts on the Nova confirms DNS recovered. It self-heals in ~1-2 min (sensors return, e.g. print state back to 'printing'). The PRINT is unaffected — Klipper runs on the printer board independent of HA. Durable fix: move the Nova to wired ethernet (enP4p65s0) and optionally disable wlan0 so it can't flap.
- **Repro / verify:** `Watch docker logs during a wifi blip: spotify 'Timeout while contacting DNS servers' + BrokenPipeError/ConnectionError + moonraker 'connection down, restarting', all clearing within ~2 min.`
- **Tags:** network, nova
