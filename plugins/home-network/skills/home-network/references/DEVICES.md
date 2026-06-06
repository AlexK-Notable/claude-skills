# DEVICES.md

> **EXAMPLE DATA — this file is a template.** Replace these illustrative
> entries with your own devices (or let the skill's `home-net-learn` agent
> populate it). Every IP, MAC, hostname, and role below is fictional and
> exists only to show the format. Keep the columns; change the contents.

Device inventory for your home LAN. **Edit via `home-net-learn` when
possible** so the verification loop runs. Direct edits are fine for
corrections.

**Network**: `192.168.1.0/24` behind your router/gateway *(example)*
**This machine**: `workstation` (192.168.1.50) *(example)*
**Last full audit**: 2026-01-01 *(example — set this when you run an audit)*

---

## Active devices (verified)

> The entries below are **illustrative examples**. Swap in your real
> devices, or delete them and let `home-net-learn` rebuild the inventory.

### workstation (this machine)

| Field | Value |
|-------|-------|
| IPv4 | 192.168.1.50 *(example)* |
| MAC (eth) | aa:bb:cc:00:00:50 *(example placeholder)* |
| Interface | eth0 |
| Hostname | workstation |
| Role | Desktop workstation; optional game-streaming host |
| OS | a Linux distribution (e.g. Arch/CachyOS, Debian) |
| SSH | enabled, port 22 |
| UFW allows | mDNS 5353; plus whatever services you expose (LAN-scoped by default) |
| Notes | The UFW *allows* are firewall policy. Whether a daemon is actually listening at any moment depends on whether you've started it — check with `ss -tulpen \| grep LISTEN`. |

### sbc (an ARM single-board computer)

*(example — a generic SBC such as a Rockchip/Allwinner board running a
Linux distro. Replace with your own, or run `home-net-learn sbc.local`.)*

| Field | Value |
|-------|-------|
| IPv4 | 192.168.1.10 *(example, DHCP)* |
| MAC (Wi-Fi) | aa:bb:cc:00:00:10 *(example placeholder)* |
| Hostname (mDNS) | `sbc.local` |
| Hostname (system) | `sbc` |
| Hardware | an ARM single-board computer (SBC) |
| Kernel | a vendor BSP or mainline kernel (e.g. 6.x aarch64) |
| Role | SBC — exploratory / dev / home-automation host |
| OS | a Debian/Armbian-style distro |
| SSH | enabled, port 22 |
| SSH user | `user` |
| SSH key auth | passwordless via `~/.ssh/id_ed25519` |
| SSH alias | `~/.ssh/config` defines an `sbc` alias → `user@sbc.local` w/ `~/.ssh/id_ed25519`. Prefer the mDNS name so lease rotation and ethernet↔Wi-Fi swaps stay transparent (use `StrictHostKeyChecking accept-new`). |
| ICMP | may be **filtered** — use mDNS/ARP for aliveness |
| Notes | If the SBC has an SDIO Wi-Fi chip, it may need a modprobe workaround for boot/suspend — see [TROUBLESHOOTING.md §7](TROUBLESHOOTING.md#7-wi-fi-driver-doesnt-survive-suspendresume-rtw88_8821cs). If device-side mDNS breaks (see §10), pin SSH config to the wired IP until it's fixed. |
| Peripheral (example) | a Zigbee USB coordinator on `/dev/ttyUSB0`, passed into a Home Assistant container for ZHA |

### printer (a 3D-printer controller — Klipper / Moonraker)

*(example — a Klipper/Moonraker controller board. Replace with your own,
or run `home-net-learn printer.local`.)*

| Field | Value |
|-------|-------|
| IPv4 | 192.168.1.20 *(example)* |
| MAC | aa:bb:cc:00:00:20 *(example placeholder)* |
| Hostname (mDNS) | `printer.local` |
| Hostname (system) | `printer` |
| Hardware | a 3D-printer controller board (ARM SBC) |
| Role | 3D printer controller (Klipper firmware; Moonraker web API) |
| OS | an Armbian-derivative distro |
| SSH | enabled, port 22 |
| SSH user | `user` |
| SSH key auth | passwordless via `~/.ssh/id_ed25519` |
| SSH alias | `~/.ssh/config` defines `printer` → `user@printer.local` w/ `~/.ssh/id_ed25519` |
| Open ports | 22 (SSH), 80 (Mainsail/Fluidd web UI), 7125 (Moonraker API) |
| **Security note** | Klipper controller boards often ship with weak factory default credentials — anyone on the LAN with default creds can SSH in. Change the password, and restrict via firewall if WAN-exposed. |
| Notes | The "3D printer" referenced in skill triggers. `port-check 192.168.1.20 --klipper` covers the relevant ports. Port reachability tracks whether the printer is powered on. |

### pi (a Raspberry Pi — Samba / file host)

*(example — a Raspberry Pi acting as a file/voice host. Replace with your
own, or run `home-net-learn pi.local`.)*

| Field | Value |
|-------|-------|
| IPv4 | 192.168.1.30 *(example)* |
| MAC | aa:bb:cc:00:00:30 *(example placeholder)* |
| Hostname (mDNS) | `pi.local` |
| Hardware | a Raspberry Pi |
| OS | Raspberry Pi OS (Debian derivative) |
| Role | Samba/SMB server; optional Piper TTS host for a voice assistant |
| SSH | enabled, port 22 |
| SSH user | `user` |
| SSH key auth | passwordless via `~/.ssh/id_ed25519` |
| SSH alias | `~/.ssh/config` defines `pi` → `user@pi.local` w/ `~/.ssh/id_ed25519` |
| Open ports | 22 (SSH), 445 (SMB), 10200 (Piper TTS — Wyoming, optional) |
| mDNS services | `_smb._tcp` + `_ssh._tcp` + `_device-info._tcp` |
| Notes | Generic always-on file server. Good candidate for masking sleep targets (see [TROUBLESHOOTING.md §7](TROUBLESHOOTING.md#7-wi-fi-driver-doesnt-survive-suspendresume-rtw88_8821cs)). |

### router (your router / gateway)

| Field | Value |
|-------|-------|
| IPv4 | 192.168.1.1 *(example — many gateways use .1 or .254)* |
| MAC | aa:bb:cc:00:00:01 *(example placeholder)* |
| Hostname (PTR) | `gateway.local` *(example — varies by ISP/router)* |
| Role | Router / DHCP / DNS / IPv6 PD |
| Admin URL | http://192.168.1.1/ |
| Open ports (LAN) | 80 (web admin) |
| Notes | DHCP leases visible via the admin UI. Some ISP gateways append a vendor DNS suffix (e.g. `.<provider>.net`) to local hostnames. **Stale DNS lease lifetimes can be hours** — don't trust resolved IPs without an aliveness check. |

---

## Active devices (seen on LAN, not formally owned)

> These are **example smart-home / IoT entries** to show the format that
> `avahi-browse` discovery produces. Replace with your own findings.

| IP | MAC | Identity |
|----|-----|----------|
| 192.168.1.60 | aa:bb:cc:00:00:60 | a smart speaker — SpotifyConnect + Matter (`_matter._tcp` port 5541) |
| 192.168.1.61 | aa:bb:cc:00:00:61 | a smart speaker / Thread border router — advertises `_meshcop._udp`; a TBR will inject a Thread mesh ULA route via ICMPv6 RA (shows up on neighboring hosts as an `ip -6 route` entry via the device's link-local). Unusual but correct behavior. |
| 192.168.1.40 | aa:bb:cc:00:00:40 | a laptop — `laptop.local`, AirPlay port 7000 |
| 192.168.1.41 | aa:bb:cc:00:00:41 | a tablet on Wi-Fi (`tablet.local`) |
| 192.168.1.42 | aa:bb:cc:00:00:42 | a phone (DHCP; mobile OSes often use a per-SSID randomized "private" MAC) |
| 192.168.1.70 | aa:bb:cc:00:00:70 | a Matter/Thread hub — `_matterc._udp` port 5540 |
| 192.168.1.71 | aa:bb:cc:00:00:71 | a DIY ESP32 device — custom `_*._tcp` service |
| 192.168.1.72 | aa:bb:cc:00:00:72 | a smart camera / doorbell |

### Networking gear cluster (example)

A run of adjacent IPs may share one OUI prefix (e.g. access points /
switches from a single vendor). Group them rather than enumerating each:
"hosts at .64–.69 share OUI `aa:bb:cc` — likely APs/switches."

### Additional active devices (auto-discovered, not yet documented)

> **Run `home-net-learn` on each when you want a verified entry.**

| IP | MAC | Probable identity |
|----|-----|-------------------|
| 192.168.1.80 | aa:bb:cc:00:00:80 | a smart bulb (vendor identified by OUI) |
| 192.168.1.81 | aa:bb:cc:00:00:81 | an ESP32-based IoT device |
| 192.168.1.82 | aa:bb:cc:00:00:82 | a smart-home device (randomized MAC) |
| 192.168.1.83 | aa:bb:cc:00:00:83 | a Wi-Fi extender / managed switch (HTTP-only admin on port 80) |

---

## Expected / not currently on LAN

*(Empty in this template. List devices you expect but that aren't
currently online here.)*

### Home Assistant — example entry

| Field | Value |
|-------|-------|
| Host | the SBC `192.168.1.10:8123` (Docker, host network) *(example)* |
| Web UI | `:8123` |
| Voice (Wyoming) | STT on the SBC `:10300`; wakeword on the SBC `:10400`; Piper TTS on the Pi `192.168.1.30:10200` *(example layout)* |
| Integrations | Zigbee via ZHA (USB coordinator on the SBC); LAN smart-bulb integration |
| mDNS | expected `homeassistant.local` |
| Notes | Run `home-net-learn 192.168.1.10` for a fuller verified entry once deployed. |

---

## Departed / historical

(Empty for now. The learn loop will move stale entries here if a device
hasn't responded to verification in N days.)

---

## Conventions observed (example)

These are *example* addressing patterns — yours will differ. Many routers
just hand out from the bottom of the DHCP pool unless you reserve:

- **.1 / .254** — router (depends on vendor)
- **.10–.30** — static/reserved infrastructure (SBCs, printer, Pi)
- **.40s** — laptops, tablets, phones
- **.60s–.70s** — AV / smart-home endpoints + networking gear
- **.80s** — bulbs / IoT
- **.200s** — DHCP pool for new devices

## How to update this file

1. **Preferred**: `home-net-learn <name-or-ip>` — handles the
   draft-verify-merge cycle. Concurrent invocations are safe (per-task
   draft filenames).
2. **Direct edit**: fine for corrections, role notes, hostnames. The
   verification agent will still flag inconsistencies on the next
   `home-net-learn` run.
3. **Keep real data out of a public fork**: if you publish your fork, move
   sensitive real entries to a git-ignored `DEVICES.local.md` and keep
   only this example template tracked.
