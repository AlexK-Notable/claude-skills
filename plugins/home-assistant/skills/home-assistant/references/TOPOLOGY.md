# Topology — where Home Assistant lives and how to reach it

## Hosts

| Host | Address | Role |
|---|---|---|
| **Nova** (Indiedroid, RK3588S) | `192.168.1.229` | HA container; SenseVoice STT (NPU, :10300); openWakeWord (:10400); govee2mqtt; Mosquitto |
| **Pi 5** | `192.168.1.165` | Piper TTS (:10200); Glances |
| **KOMI** (x86 desktop) | local | where Claude Code runs; SSHes to the others |

SSH from KOMI: `ssh komi@192.168.1.229` (key auth). The Nova + Pi have **passwordless
sudo** (`sudo -n` works over SSH). KOMI does **not** — never run sudo on KOMI via a
tool (see the global sudo policy; it locks the account).

## Home Assistant

- **Runtime:** Docker container `homeassistant` (`ghcr.io/home-assistant/home-assistant:stable`), `--network host`.
- **Config dir (on Nova):** `/home/komi/homeassistant/config` (root-owned; read via `sudo -n`).
- **URL:** `http://192.168.1.229:8123` (LAN only).
- **Owner account:** username `komi`. Password in **bws** as `HA_OWNER_PASSWORD` (project `home-assistant`).
- **Version:** read live — `ha-inventory` stamps it in the snapshot front-matter
  (`ha_version`). As of last write it was **2026.5.4**. HA churns monthly; never
  hardcode it — version-sensitive gotchas are stamped against it.

### Service management (from KOMI)
```bash
ssh komi@192.168.1.229 'sudo -n docker logs --tail 50 homeassistant'
ssh komi@192.168.1.229 'sudo -n docker restart homeassistant'
# validate config BEFORE a restart/reload after any YAML edit:
ssh komi@192.168.1.229 'sudo -n docker exec homeassistant python -m homeassistant --script check_config -c /config'
# HA users (e.g. password reset):
ssh komi@192.168.1.229 'sudo -n docker exec homeassistant python -m homeassistant --script auth --config /config list'
```

> `docker start` does **not** re-read `--env-file`. To change a container's env
> (e.g. govee2mqtt creds) you must `docker rm -f` + `docker run` again — a plain
> restart keeps the old env. (See GOTCHAS.)

## Voice pipeline

| Role | Where | Endpoint |
|---|---|---|
| STT — SenseVoice fp16 (NPU) | Nova | `:10300` (Wyoming; zeroconf-advertised) |
| Wake word — openWakeWord (`ok_nabu`) | Nova | `:10400` |
| TTS — Piper (`en_US-lessac-medium`) | Pi 5 | `:10200` |
| Conversation agent | HA | `conversation.claude_conversation` (Anthropic) |

Wyoming STT server: systemd **user** service `wyoming-sensevoice.service` on the Nova
(`journalctl --user -u wyoming-sensevoice`). Details in ASSIST.md.

## Secrets (all in bws, project `home-assistant` = 18f14ed9-8ba5-4cc6-bbd4-b45b01534270)

`HA_OWNER_PASSWORD`, `HA-Anthropic`, `HA-Spotify`, `MQTT_PASSWORD`, `GOVEE_API_KEY`,
`GOVEE_EMAIL`, `GOVEE_PASSWORD`, `HA_BACKUP_KEY`. Read with `bws secret get <id>`;
never echo values. There is **no** HA long-lived API token yet — `ha-inventory` v1
uses SSH+sudo file reads, not the API. (Minting an admin token → bws `HA_TOKEN` is
the documented v2 upgrade for API-based, no-sudo, remote introspection.)
