# Topology — where Home Assistant lives and how to reach it

> **EXAMPLE TOPOLOGY — fill in with your own.** The hosts, addresses, and the voice
> stack below are an illustrative layout. Replace them with yours; the values that
> the tooling actually reads live in `config.sh` (`HA_SSH`, `HA_CONFIG`,
> `HA_CONTAINER`). Round example IPs are used throughout (`192.168.1.10`, …).

## Hosts (example)

| Host | Address | Role |
|---|---|---|
| **HA host** (e.g. an SBC or mini-PC) | `192.168.1.10` | HA container; STT (Wyoming, :10300); wake word (:10400); govee2mqtt; Mosquitto |
| **Pi** | `192.168.1.30` | Piper TTS (:10200); Glances |
| **workstation** (where Claude Code runs) | local | SSHes to the others |

SSH from the workstation: `ssh user@192.168.1.10` (key auth). Give the HA host
**passwordless sudo** for `sudo -n` to work over SSH. Do **not** rely on sudo on the
workstation itself if your environment locks the account on a failed sudo.

## Home Assistant

- **Runtime:** Docker container `homeassistant` (`ghcr.io/home-assistant/home-assistant:stable`), `--network host`.
- **Config dir (on the HA host):** `/home/user/homeassistant/config` (root-owned; read via `sudo -n`). Set this as `HA_CONFIG` in `config.sh`.
- **URL:** `http://192.168.1.10:8123` (or `http://homeassistant.local:8123`) — LAN only.
- **Owner account:** your HA username. Store its password in a secret manager (e.g. bws as `HA_OWNER_PASSWORD`), never in a tracked file.
- **Version:** read live — `ha-inventory` stamps it in the snapshot front-matter
  (`ha_version`). HA churns monthly; never hardcode it — version-sensitive gotchas
  are stamped against whatever it was when observed.

### Service management (from the workstation)
```bash
ssh user@192.168.1.10 'sudo -n docker logs --tail 50 homeassistant'
ssh user@192.168.1.10 'sudo -n docker restart homeassistant'
# validate config BEFORE a restart/reload after any YAML edit:
ssh user@192.168.1.10 'sudo -n docker exec homeassistant python -m homeassistant --script check_config -c /config'
# HA users (e.g. password reset):
ssh user@192.168.1.10 'sudo -n docker exec homeassistant python -m homeassistant --script auth --config /config list'
```

> `docker start` does **not** re-read `--env-file`. To change a container's env
> (e.g. govee2mqtt creds) you must `docker rm -f` + `docker run` again — a plain
> restart keeps the old env. (See GOTCHAS.)

## Voice pipeline (example)

| Role | Where | Endpoint |
|---|---|---|
| STT (Wyoming) | HA host | `:10300` (zeroconf-advertised) |
| Wake word — openWakeWord | HA host | `:10400` |
| TTS — Piper | Pi | `:10200` |
| Conversation agent | HA | `conversation.claude_conversation` (Anthropic) |

A self-hosted Wyoming STT server can run as a systemd **user** service on the HA
host (`journalctl --user -u <your-stt>.service`). Details in ASSIST.md.

## Secrets (keep them in a secret manager, never in tracked files)

Route credentials through the `bitwarden-cli` plugin (`bws`). Typical HA secrets you
might store: `HA_OWNER_PASSWORD`, `HA_TOKEN`, conversation-agent API key, MQTT
password, integration API keys, a backup encryption key. Read with
`bws secret get <your-secret-id>`; never echo values. Use placeholder project/secret
ids in any docs (`<your-project-id>`, `<your-secret-id>`).

**`HA_TOKEN`** should be an **admin long-lived access token** for your HA owner
account, minted via the login flow. `ha-inventory` v1 uses SSH+sudo file reads; this
token is the foundation for a v2 that introspects via the secret-safe WebSocket API
(`config_entries/get` omits `data`/`options`) and works remotely without sudo.

### Live API access

The REST API (no SSH/sudo, works from anywhere on the LAN). Pull the token into a
var — never echo it:

```bash
T=$(bws secret get <your-secret-id> | jq -r .value)
H="http://192.168.1.10:8123/api"; A="Authorization: Bearer $T"

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
ssh user@192.168.1.10 'sudo -n docker exec homeassistant python -m homeassistant --script check_config -c /config'
```

`/api/template` is the high-value one: it lets you prove a brightness/rgb/condition
template produces the right value across a schedule without waiting for the trigger
(useful for validating lighting ramp curves). Mint a fresh token with the login flow
if `HA_TOKEN` is ever revoked (Profile → Security → Long-Lived Access Tokens, or the
scripted login flow against `/auth/login_flow` → `/auth/token` → WS
`auth/long_lived_access_token`).
</content>
