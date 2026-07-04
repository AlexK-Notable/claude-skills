# Topology — where Home Assistant lives and how to reach it

## Hosts

| Host | Address | Role |
|---|---|---|
| **Nova** (Indiedroid, RK3588S) | `192.168.1.232` | HA container; SenseVoice STT (NPU, :10300); openWakeWord (:10400); govee2mqtt; Mosquitto |
| **Pi 5** | `192.168.1.165` | Piper TTS (:10200); Glances |
| **KOMI** (x86 desktop) | local | where Claude Code runs; SSHes to the others |

SSH from KOMI: `ssh komi@192.168.1.232` (key auth). The Nova + Pi have **passwordless
sudo** (`sudo -n` works over SSH). KOMI does **not** — never run sudo on KOMI via a
tool (see the global sudo policy; it locks the account).

## Home Assistant

- **Runtime:** Docker container `homeassistant` (`ghcr.io/home-assistant/home-assistant:stable`), `--network host`.
- **Config dir (on Nova):** `/home/komi/homeassistant/config` (root-owned; read via `sudo -n`).
- **URL:** `http://192.168.1.232:8123` (LAN only).
- **Owner account:** username `komi`. Password in **bws** as `HA_OWNER_PASSWORD` (project `home-assistant`).
- **Version:** read live — `ha-inventory` stamps it in the snapshot front-matter
  (`ha_version`). As of last write it was **2026.5.4**. HA churns monthly; never
  hardcode it — version-sensitive gotchas are stamped against it.

### Service management (from KOMI)
```bash
ssh komi@192.168.1.232 'sudo -n docker logs --tail 50 homeassistant'
ssh komi@192.168.1.232 'sudo -n docker restart homeassistant'
# validate config BEFORE a restart/reload after any YAML edit:
ssh komi@192.168.1.232 'sudo -n docker exec homeassistant python -m homeassistant --script check_config -c /config'
# HA users (e.g. password reset):
ssh komi@192.168.1.232 'sudo -n docker exec homeassistant python -m homeassistant --script auth --config /config list'
```

> `docker start` does **not** re-read `--env-file`. To change a container's env
> (e.g. govee2mqtt creds) you must `docker rm -f` + `docker run` again — a plain
> restart keeps the old env. (See GOTCHAS.)

## Voice pipeline

| Role | Where | Endpoint |
|---|---|---|
| STT — SenseVoice **int8 ONNX on CPU** (2 threads; swapped off the NPU 2026-07-03 — see `~/repos/voice-assistant/planning/2026-07-03-voice-system-assessment.md`) | Nova | `:10300` (Wyoming; zeroconf-advertised) |
| Wake word — on-device (microWakeWord on the Voice PE); the openWakeWord container (`:10400`) is running but unused (pipeline `wake_word_entity` is null) | Nova | `:10400` |
| TTS — Piper (pipeline voice `en_US-hfc_female-medium`; container preloads lessac-medium) | Pi 5 | `:10200` |
| Conversation agent | HA | `conversation.google_ai_conversation` (gemini-3.1-flash-lite, since 2026-07-03; `conversation.claude_conversation` kept as fallback) |

Wyoming STT server: systemd **user** service `wyoming-sensevoice.service` on the Nova
(`journalctl --user -u wyoming-sensevoice`). Details in ASSIST.md.

**Bedroom satellite:** Home Assistant **Voice PE** — device "Home Assistant Voice 0a78d4"
(ESPHome), currently `192.168.1.230`. Wake/mic/speaker plus an RGB status **LED ring**
(`light.home_assistant_voice_0a78d4_led_ring`). ESPHome rediscovers via mDNS, so its IP is
informational. The LED ring is a *controllable light* — keep it **unexposed** to Assist or
"turn the lights `<color>`" will grab it (see ASSIST.md / GOTCHAS: Networking & Integrations).

## Secrets (all in bws, project `home-assistant` = 18f14ed9-8ba5-4cc6-bbd4-b45b01534270)

`HA_OWNER_PASSWORD`, `HA_TOKEN`, `HA-Anthropic`, `HA-Spotify`, `MQTT_PASSWORD`,
`GOVEE_API_KEY`, `GOVEE_EMAIL`, `GOVEE_PASSWORD`, `HA_BACKUP_KEY`. Read with
`bws secret get <id>`; never echo values.

**`HA_TOKEN`** (id `74edad23-6bd2-4617-a1d8-b45d016db173`) is an **admin long-lived
access token** for the `komi` owner account, minted 2026-06-02 via the login flow.
`ha-inventory` v1 still uses SSH+sudo file reads; this token is the foundation for a
v2 that introspects via the secret-safe WebSocket API (`config_entries/get` omits
`data`/`options`) and works remotely without sudo.

### Live API access

The REST API (no SSH/sudo, works from anywhere on the LAN). Pull the token into a
var — never echo it:

```bash
# bws needs BWS_ACCESS_TOKEN, which is NOT set in non-interactive shells — source it first
# (else `bws secret get` errors "Missing access token" and every API call 401s):
set -a; source ~/.config/bws/token.env; set +a
T=$(bws secret get 74edad23-6bd2-4617-a1d8-b45d016db173 | jq -r .value)
H="http://192.168.1.232:8123/api"; A="Authorization: Bearer $T"

# read one entity's live state / list all entity ids
curl -s -H "$A" "$H/states/light.bedroom_lights" | jq '{state, attributes}'
curl -s -H "$A" "$H/states" | jq -r '.[].entity_id'

# call a service (turn on, set, run a script, toggle an AL switch, …)
curl -s -H "$A" -H 'Content-Type: application/json' -X POST "$H/services/light/turn_on" \
     -d '{"entity_id":"light.bedroom_lights","brightness_pct":50}'

# render/validate a template — the way to check automation Jinja BEFORE it runs live
curl -s -H "$A" -H 'Content-Type: application/json' -X POST "$H/template" \
     -d '{"template":"{{ today_at(\"07:45\").timestamp() }}"}'

# config sanity (also runnable on the host): exit 0 before any reload/restart
ssh komi@192.168.1.232 'sudo -n docker exec homeassistant python -m homeassistant --script check_config -c /config'

# integration health — which config entries are NOT loaded (THE first check when something
# "won't connect"). WS API; needs the `websockets` py lib (present on KOMI):
python3 - "$T" <<'PY'
import sys, json, asyncio, websockets
async def main():
    async with websockets.connect("ws://192.168.1.232:8123/api/websocket", max_size=None) as ws:
        await ws.recv(); await ws.send(json.dumps({"type":"auth","access_token":sys.argv[1]})); await ws.recv()
        await ws.send(json.dumps({"id":1,"type":"config_entries/get"}))
        for e in json.loads(await ws.recv())["result"]:
            if e["state"] != "loaded": print(e["domain"], e["title"], e["state"], e.get("reason"))
asyncio.run(main())
PY

# reload a stuck integration WITHOUT a full HA restart (after the service it talks to recovers):
curl -s -H "$A" -H 'Content-Type: application/json' -X POST \
     "$H/services/homeassistant/reload_config_entry" -d '{"entry_id":"<entry_id>"}'
# NOTE: reload re-runs setup but does NOT re-resolve a stale host in entry data —
# for an IP change you must edit core.config_entries (see GOTCHAS: Networking).
```

`/api/template` is the high-value one: it lets you prove a brightness/rgb/condition
template produces the right value across a schedule without waiting for the trigger
(used to validate the bedroom ramp curves). Mint a fresh token with the login flow if
`HA_TOKEN` is ever revoked (Profile → Security → Long-Lived Access Tokens, or the
scripted login flow against `/auth/login_flow` → `/auth/token` → WS
`auth/long_lived_access_token`).
