# DEVICES.md

Personal device inventory for the home LAN. **Edit via `home-net-learn`
when possible** so the verification loop runs. Direct edits are fine
for corrections.

**Network**: `192.168.1.0/24` behind AT&T residential gateway
**This machine**: `KOMI` (192.168.1.139)
**Last full audit**: 2026-05-24 (by the build-time verification agent)

---

## Active devices (verified)

### KOMI (this machine)

| Field | Value |
|-------|-------|
| IPv4 | 192.168.1.139 |
| MAC (eth) | 9c:6b:00:3c:5f:2d |
| Interface | enp4s0 |
| Hostname | komi-hypr |
| Role | Workstation; Sunshine streaming host; Weylus screen-input target |
| OS | CachyOS (Arch-based) |
| SSH | enabled, port 22 |
| UFW allows | Sunshine 47984-48010, Weylus 1701 (LAN-only), mDNS 5353 |
| Notes | The UFW *allows* listed above are the firewall policy. Whether the corresponding daemons are actually listening at any moment depends on whether you've started Sunshine / Weylus. Check with `ss -tulpen \| grep LISTEN`. Hyprland desktop — see `~/.config/CLAUDE.md` for full setup. |

### indiedroid nova (bredOS)

| Field | Value |
|-------|-------|
| IPv4 | 192.168.1.221 *(DHCP — may change)* |
| IPv6 (global) | 2600:1700:4811:4e70:b6c8:c1a0:de27:97ee *(SLAAC, may rotate)* |
| MAC (Wi-Fi) | 60:fb:00:37:57:56 |
| OUI | 60:FB:00 — Shenzhen Bilian Electronic (consistent with indiedroid Wi-Fi NIC) |
| Hostname (mDNS) | `bredos.local` |
| Hostname (DNS) | `bredos.attlocal.net` (AT&T router DNS — may be stale) |
| Role | SBC, exploratory / dev |
| OS | bredOS |
| SSH | enabled, port 22 (only open port observed) |
| SSH user | `bredos` (bredOS distro default) |
| SSH key auth | **not yet set up** — needs `ssh-copy-id bredos@192.168.1.221` (interactive password required) |
| SSH alias | `~/.ssh/config` defines `nova` and `bredos` aliases → `bredos@192.168.1.221` w/ `~/.ssh/id_ed25519` |
| ICMP | **filtered** — use mDNS/ARP for aliveness |
| Notes | Connects via Wi-Fi, frequently off-network. If `getent hosts bredos` returns IPv6 addresses but ping fails, the lease may be stale — re-verify with `find-host bredos`. |
| Freshness | offline during 2026-05-24 afternoon audit; back online same day (transient — probably a power/Wi-Fi blip). Port 22 reachable but SSH banner exchange may time out until key is provisioned. |

### Raspberry Pi (komi-2 — Samba host)

| Field | Value |
|-------|-------|
| IPv4 | 192.168.1.165 |
| MAC | 88:a2:9e:02:55:a3 |
| OUI | 88:A2:9E — **Raspberry Pi Trading Ltd** |
| Hostname (mDNS) | `komi-2.local` |
| Hostname (on device) | `komi` (system hostname — `komi-2.local` is just the mDNS advertisement) |
| Hardware | Raspberry Pi 5 (kernel `6.12.62+rpt-rpi-2712`, aarch64) |
| OS | Raspberry Pi OS (Debian Bookworm derivative) |
| Role | Samba/SMB server (advertises `model=MacSamba` device-info) |
| SSH | enabled, port 22 |
| SSH user | `komi` |
| SSH key auth | passwordless via `~/.ssh/id_ed25519` (added 2026-05-24; previously only id_rsa was authorized) |
| SSH alias | `~/.ssh/config` defines `pi` and `komi` aliases → `komi@192.168.1.165` w/ `~/.ssh/id_ed25519` |
| Open ports | 22 (SSH), 445 (SMB) |
| mDNS services | `_smb._tcp` + `_ssh._tcp` + `_device-info._tcp` |
| Notes | Device's actual system hostname is `komi` (not `komi-2`); mDNS responder publishes `komi-2.local`. This was previously (incorrectly) listed as "KOMI second adapter" — it's actually the Raspberry Pi. |

### BIGTREETECH CB2 (3D printer host — Klipper / Moonraker)

| Field | Value |
|-------|-------|
| IPv4 | 192.168.1.188 |
| MAC | 02:00:cb:21:cb:21 *(locally-administered — typical for Wi-Fi)* |
| Hostname (mDNS) | `bigtreetech-cb2.local` |
| Hostname (on device) | `bigtreetech-cb2` |
| Hardware | RK35xx-based BIGTREETECH CB2 (kernel `6.1.115-btt-rk35xx`, aarch64) |
| Role | 3D printer controller (Klipper firmware; Moonraker web API) |
| OS | Armbian-derivative for BIGTREETECH CB2 |
| SSH | enabled, port 22 |
| SSH user | `biqu` |
| SSH key auth | passwordless via `~/.ssh/id_ed25519` |
| SSH alias | `~/.ssh/config` defines `cb2` and `printer` aliases → `biqu@192.168.1.188` w/ `~/.ssh/id_ed25519` |
| SSH shortcut | `~/bin/ssh-cb2` also exists |
| Open ports | 22 (SSH), 80 (Mainsail/Fluidd web UI), 7125 (Moonraker API) |
| **Security note** | Factory default credentials are `biqu` / `biqu` — anyone on the LAN with default creds can SSH in. Change the password if WAN-exposed, or restrict via firewall. |
| Notes | The "3D printer" referenced in skill triggers. `port-check 192.168.1.188 --klipper` covers the relevant ports. |

### iPhone (Wi-Fi)

| Field | Value |
|-------|-------|
| IPv4 | 192.168.1.97 *(DHCP)* |
| MAC (Wi-Fi) | a6:f3:f0:0d:4e:ed *(locally-administered — iOS Private Wi-Fi Address, per-SSID stable)* |
| OUI | none — locally-administered MAC, no IEEE assignment expected |
| Hostname (DNS) | `iPhone.attlocal.net` *(AT&T gateway appends `.attlocal.net` to DHCP hostname `iPhone`)* |
| Hostname (mDNS) | not observed at probe time; iOS may advertise `iPhone.local` while in active use |
| Role | Personal mobile device (iPhone) |
| Open ports | none observed *(iOS exposes no services by default)* |
| mDNS services | none observed; possible `_companion-link._tcp`, `_apple-mobdev2._tcp`, `_airplay._tcp` when in use |
| Notes | DHCP — IP may change. MAC is stable on this SSID but differs on other Wi-Fi networks (iOS MAC privacy). |
| Verified | 2026-05-24 via home-net-learn (agent verdict review-needed due to permission issue; manually promoted with agent's analysis) |

### Moug (Intel-NIC client device)

| Field | Value |
|-------|-------|
| IPv4 | 192.168.1.101 *(DHCP)* |
| IPv6 (global) | 2600:1700:4811:4e70::2a |
| MAC | 28:6b:35:14:ac:9e |
| OUI | 28:6B:35 — **Intel Corporate** (registered 2022; consistent with an Intel Wi-Fi/Ethernet NIC in a PC/laptop) |
| Hostname (DNS) | `Moug.attlocal.net` *(AT&T gateway appends `.attlocal.net` to DHCP hostname `Moug`)* |
| Hostname (mDNS) | not observed at probe time |
| Role | Personal computer / client device — no listening services exposed |
| ICMP | **filtered** — use ARP for aliveness (`ip neigh show 192.168.1.101`) |
| Open ports | none observed on common service ports (22, 80, 443, 445, 631, 7000, 7100, 8008, 8009, 8060, 8123, 8443, 9100, 32400, 5540, 7125) |
| mDNS services | none observed |
| Notes | DHCP — IP may change. Default firewall posture (block-all-inbound) consistent with a Windows or Linux desktop/laptop. The hostname "Moug" is the DHCP-supplied name; rename if the actual identity becomes clear. |
| Verified | 2026-05-24 via home-net-learn |

### AT&T residential gateway (router)

| Field | Value |
|-------|-------|
| IPv4 | 192.168.1.254 |
| MAC | 48:e2:ad:dd:ef:51 |
| IPv6 link-local | fe80::4ae2:adff:fedd:ef51 |
| Hostname (PTR) | `dsldevice.attlocal.net` |
| Role | Router / DHCP / DNS / IPv6 PD |
| Admin URL | http://192.168.1.254/ |
| Open ports (LAN) | 80 (web admin) |
| Notes | DHCPv4 leases visible via admin UI. Adds `.attlocal.net` suffix to local DNS. **Stale DNS lease lifetimes can be hours** — don't trust resolved IPs without arping. IPv6 PD prefix: `2600:1700:4811:4e70::/64`. |

---

## Active devices (seen on LAN, not formally owned)

These appeared on `avahi-browse` during 2026-05-24 audit.

| IP | MAC | Identity |
|----|-----|----------|
| 192.168.1.76 | e8:d8:7e:31:ae:e7 | Speaker — SpotifyConnect + Matter (`_matter._tcp` port 5541) |
| 192.168.1.84 | 90:23:5b:fa:62:dc | Speaker — SpotifyConnect #3 + Matter |
| 192.168.1.85 | 44:6d:7f:22:59:5b | Amazon Echo — SpotifyConnect #2 + Matter + `_meshcop._udp` (Thread border router) |
| 192.168.1.151 | 0e:7b:9c:c9:3e:97 *(randomized)* | iPad on Wi-Fi (`iPad.local`) |
| 192.168.1.160 | d6:77:f4:f4:b3:fa *(randomized)* | MacBook Pro — `Alexs-MacBook-Pro.local`, AirPlay port 7000 |
| 192.168.1.177 | e4:b3:23:74:31:98 | Matter/Thread hub — `_matterc._udp` port 5540 (OUI: Espressif) |
| 192.168.1.179 | 00:4b:12:4e:62:5c | DIY ESP32 device — `_ekg._tcp` port 8888 (`EKG-4e-62-5c.local`) |
| 192.168.1.187 | ac:9f:c3:* | **Ring (Amazon)** doorbell or camera — OUI AC:9F:C3 is Ring LLC |

### Ubiquiti gear cluster

Hosts at .64, .67, .68, .69 share OUI `D0:C9:07` (Ubiquiti Networks). Likely access points / switches — not enumerated individually.

**Note**: .66 was previously grouped here but its OUI is `60:74:F4` (vendor returns "Private", not Ubiquiti). Treat as separate, unidentified.

### Additional active devices (auto-discovered, not yet documented)

Found by Agent 1 during 2026-05-24 audit. **Run `home-net-learn` on each
when you want a verified entry.**

| IP | MAC | Probable identity |
|----|-----|-------------------|
| 192.168.1.141 | d4:ad:fc:42:89:d0 | **LIFX bulb** (OUI D4:AD:FC = Shenzhen Intellirocks / LIFX) |
| 192.168.1.142 | d4:ad:fc:18:fb:38 | LIFX bulb |
| 192.168.1.143 | d4:ad:fc:43:15:92 | LIFX bulb |
| 192.168.1.145 | d4:ad:fc:43:15:92 | LIFX bulb |
| 192.168.1.146 | d4:ad:fc:41:19:68 | LIFX bulb |
| 192.168.1.144 | 0e:c5:4e:38:25:fc | Unknown (randomized MAC) |
| 192.168.1.148 | 1c:69:20:85:e0:90 | ESP32-based IoT (OUI: Espressif) |
| 192.168.1.180 | 3c:dc:75:0e:ce:38 | ESP32-based IoT |
| 192.168.1.192 | 36:be:fe:48:f3:f5 | Unknown (randomized MAC) |
| 2600:1700:4811:4e70::48 | (IPv6-only) | Matter endpoint — `none-3.local`, advertises `_matter._tcp` |

---

## Expected / not currently on LAN

### Home Assistant (incoming)

| Field | Value |
|-------|-------|
| IP | *not yet deployed* |
| Expected port | 8123 (web UI) |
| Expected mDNS | `homeassistant.local` |
| Notes | User mentioned this is being added soon. After deployment, run `home-net-learn homeassistant.local` to capture the verified entry. The skill's `port-check HOST 8123` will confirm the web UI is reachable. |

---

## Departed / historical

(Empty for now. The learn loop will move stale entries here if a device
hasn't responded to verification in N days.)

---

## Conventions observed

- **.60s-.90s** — AV / streaming endpoints + Ubiquiti gear
- **.140s** — LIFX bulb cluster
- **.150s-.180s** — laptops, tablets, IoT
- **.180s-.190s** — Ring / IoT
- **.200s** — DHCP pool for SBCs and new devices
- **.254** — router

These are *observed patterns*, not router-enforced. The AT&T gateway hands
out from the bottom of its pool unless reserved.

## How to update this file

1. **Preferred**: `home-net-learn <name-or-ip>` — handles the
   draft-verify-merge cycle. Concurrent invocations are safe (per-task
   draft filenames).
2. **Direct edit**: fine for corrections, role notes, hostnames. The
   verification agent will still flag inconsistencies on the next
   `home-net-learn` run.
3. **Bulk re-audit**: `scan-lan --update-devices` (TODO — not in v0.1.0).
