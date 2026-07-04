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

**Current state (canonical — as of 2026-06-08; narrative history below):**

| Field | Value |
|-------|-------|
| IPv4 (preferred) | 192.168.1.232 *(wired ethernet, DHCP, metric 100)* |
| MAC (ethernet) | 66:02:35:01:cc:21 *(stable — u-boot/SoC-derived; interface `enP4p65s0`)* |
| IPv4 (fallback) | 192.168.1.229 *(Wi-Fi `wlan0`, MAC 60:fb:00:37:57:56, metric 600)* |
| SSH | `ssh komi@192.168.1.232` (user `komi`, key auth via `id_ed25519`) |
| Hostname | `indiedroid-nova` |
| OS / kernel | Armbian vendor, Debian 13 Trixie, `6.1.115-vendor-rk35xx`, running from eMMC |
| mDNS | does **NOT** resolve on this flash — IP-pin required |

**⚠ Status 2026-06-08: DUAL-HOMED again — wired Ethernet is BACK and is now the PREFERRED route. Live-verified over SSH from KOMI 2026-06-08.** The Nova picked up a **wired Ethernet** lease and is now dual-homed: eth `enP4p65s0` **`192.168.1.232`** (metric 100 — preferred default route) + Wi-Fi `wlan0` **`192.168.1.229`** (metric 600 — fallback), *both* UP and both carrying a default route via `.254`. The `.229 → .232` "IP change" was simply the eth NIC coming back online (different interface = different MAC = different DHCP lease), **not** lease instability. Hostname `indiedroid-nova`, kernel `6.1.115-vendor-rk35xx` — same OS as the 2026-05-31 block below, **but now running from eMMC** (`/dev/mmcblk0p1`; `mmcblk0boot0`/`boot1` present ⇒ eMMC, not SD) — migrated off the microSD. **This supersedes the "single-homed Wi-Fi `.229`, running from SD, eMMC removed" state in the 2026-05-31 block below.**
  - **Ethernet identity (live-verified from KOMI 2026-06-08):**
    - `enP4p65s0` = Realtek RTL8111/8168 PCIe Gigabit NIC, driver **`r8168`** (8.051.02-NAPI), bus `platform-fe190000.pcie-pci-0004:41:00.0`.
    - IPv4 **`192.168.1.232`** (DHCP, metric 100 — preferred). Eth MAC **`66:02:35:01:cc:21`** (locally-administered).
    - **Eth MAC is STABLE / deterministic across reboots** — set by u-boot (device-tree `local-mac-address`, deterministically derived from the RK3588 SoC) and applied ~2 s into boot, *before* userspace networkd (dmesg shows the interface coming up with `66:..` at ~5.5 s). It is **NOT** the r8168 driver's random fallback: the chip has no programmed MAC (`dmesg`: `Invalid ether addr 00:00:..` → `Random ether addr 2a:8e:88:79:95:fd`), and that random `2a:..` is exactly what **`ethtool -P` misreports as the "Permanent address"** — a trap (see [TROUBLESHOOTING.md §12](TROUBLESHOOTING.md#12-is-an-sbcs-mac-stable-or-randomized-per-boot)). systemd-networkd's `99-default.link` is `MACAddressPolicy=persistent` (NOT `random`), so networkd keeps the firmware-set MAC. Empirically `66:02:35:01:cc:21` has held unchanged across the SD→eMMC migration reboots and the relocation power-cycle.
    - **Recommended:** add a DHCP reservation on the AT&T gateway binding `66:02:35:01:cc:21` → `192.168.1.232` for a hard guarantee (the eth lease is currently un-reserved).
  - **Wi-Fi `wlan0` still UP**, IPv4 `192.168.1.229` (metric 600 — fallback), MAC `60:fb:00:37:57:56` (real Realtek hardware MAC, OUI 60:FB:00 Shenzhen Bilian — unchanged across every reflash). Because both interfaces sit on the same L2 segment, a host-side ARP probe for `.229` may answer with the *eth* MAC `66:..` rather than the Wi-Fi MAC (Linux weak-host-model — see [TROUBLESHOOTING.md §1](TROUBLESHOOTING.md#1-cant-reach-host)); read the per-interface MAC on the device itself to disambiguate.
  - **Home Assistant `:8123` is reachable on BOTH `192.168.1.232:8123` and `192.168.1.229:8123`** (Docker host-network binds all interfaces) — both verified OPEN live from KOMI 2026-06-08. Prefer `.232` (wired) going forward.
  - SSH: `ssh komi@192.168.1.232` works (key auth, `id_ed25519`). The `nova`/`zbred` alias in `~/.ssh/config` on KOMI still points at `.229` (Wi-Fi) — that keeps working while wlan0 is up, but consider repointing it to `.232` for the wired path. mDNS still does not resolve on this vendor flash, so IP-pinning remains necessary.

**⚠ Status 2026-05-31: REFLASHED to Armbian vendor 6.1.115 SD — now Wi-Fi `.229`, hostname `indiedroid-nova`, NPU FUNCTIONAL. Live-verified from KOMI 2026-05-31 (ICMP ~5ms, ARP lladdr matches the Wi-Fi MAC, `.228` dead, SSH banner Debian 13).** Migrated off the mainline-6.18 Armbian-on-SD (the `.228`/eMMC-removed state below) onto a freshly flashed **Armbian vendor 6.1.115** microSD — chosen for the in-tree RKNPU driver. The Armbian first-run wizard **overwrote the entire prebake**: hostname reset to `indiedroid-nova` (was baked `nova`), and the deployed SSH key, NOPASSWD sudo, and ethernet-MAC pin were ALL wiped by first-run (re-applied by hand afterward). This **supersedes the `.228` ethernet identity** documented in the 2026-05-28 block below.
  - **Current verified network identity (Armbian vendor 6.1.115 SD; live-confirmed from KOMI 2026-05-31):**
    - Hostname `indiedroid-nova` (set by the Armbian first-run wizard; was `nova`).
    - IPv4 **`192.168.1.229` via Wi-Fi** (`wlan0`, MAC `60:fb:00:37:57:56` — the real Realtek hardware MAC, OUI 60:FB:00 Shenzhen Bilian, unchanged across every reflash). Plain DHCP, **not** reserved. ICMP responds (~5ms; Wi-Fi slightly flaky — one SSH attempt timed out then retried OK).
    - **Ethernet did NOT get a DHCP lease** (via the PoE splitter): the baked eth MAC `be:9e:7a:4c:d1:52` did not survive the first-run wipe, so the old `.228` reservation no longer matches and `.228` is **dead** (confirmed `FAILED` / no ARP / 100% ICMP loss from KOMI 2026-05-31).
    - OS: Armbian, Debian 13 Trixie, kernel **`6.1.115-vendor-rk35xx`** (Rockchip BSP — switched from the 6.18 mainline build specifically to get the in-tree RKNPU driver). SSH banner `OpenSSH 10.0p2 Debian-7+deb13u2`.
    - SSH user `komi`, port 22, key auth works (KOMI `id_ed25519` re-deployed via `ssh-copy-id`). **NOPASSWD sudo re-enabled** (`/etc/sudoers.d/komi-nopasswd`) — same homelab-convenience tradeoff as before. `komi` is in groups `video,render`.
    - **NPU FUNCTIONAL:** RKNPU driver **v0.9.8** bound at `fdab0000.npu`, exposed via **`/dev/dri/renderD129`** (NOT `/dev/rknpu` on this vendor build — important gotcha). Userspace stack: librknnrt 2.3.2 + sherpa-onnx 1.13.2 (RKNN). SenseVoice speech-to-text smoke test ran at **RTF 0.091** — on-NPU STT confirmed working.
    - **Services (Home Assistant stack; verified live OPEN from KOMI 2026-05-31):** Home Assistant web UI `:8123` (Docker, host network); Wyoming STT `:10300` — SenseVoice on the NPU (mDNS `_wyoming._tcp` as `sensevoice-rknn`); Wyoming openWakeWord `:10400`. (Piper TTS runs on the Pi 5 `192.168.1.165:10200`, not here.) See the Home Assistant entry below.
    - **Peripheral:** SONOFF Zigbee 3.0 Dongle Plus MG24 (Silicon Labs EFR32MG24, USB `10c4:ea60`) on `/dev/ttyUSB0` — by-id `usb-SONOFF_SONOFF_Dongle_Plus_MG24_64b8b3a3f2a2ef119fca926661ce3355`; passed into the HA container for ZHA (Zigbee).
  - **Local-side config on KOMI — SSH alias repoint DONE 2026-06-03:** the `nova`/`zbred` alias in `~/.ssh/config` was repointed off the stale `.228`/`.224` to **`HostName 192.168.1.229`** (`StrictHostKeyChecking accept-new`), and the stale comment block was rewritten to the current Wi-Fi `.229` / vendor-6.1.115 state. This closed the standing TODO from this entry — `ssh komi@nova` had been failing because the alias still pointed at the dead ethernet `.228` (the config was last edited 2026-05-28, before the 2026-05-31 reflash). mDNS still does NOT resolve `nova.local`/`indiedroid-nova.local`/`zbred.local` from the LAN (no avahi responder on this vendor flash — re-verified non-resolving 2026-06-03), so IP-pinning the SSH config to `.229` remains the only option.
  - **Freshness 2026-06-03 (live-verified from KOMI 192.168.1.139):** `.229` / `60:fb:00:37:57:56` re-confirmed — ARP `REACHABLE` (MAC matches inventory), port 22 OPEN, key-auth SSH OK (`hostname` = `indiedroid-nova`, kernel `6.1.115-vendor-rk35xx`). The **non-reserved** Wi-Fi DHCP lease has held stable across 3 days (2026-05-31 → 2026-06-03) despite no reservation. `.228` ethernet identity **still dead** (ARP `FAILED`, port 22 filtered). known_hosts on KOMI already held valid `.229` host keys, so no host-key conflict on reconnect.

**[The 2026-05-28 block below is SUPERSEDED by the 2026-05-31 reflash above — `.228`/ethernet/kernel-6.18 are no longer current. Kept as history; the baseline table at the bottom remains the pre-flux record.]**

**Dual-homed: ethernet + Wi-Fi simultaneously active, each with its own DHCP lease.** *(bredOS-era baseline — see the 2026-05-31 block above for the current single-homed Wi-Fi state.)*

**Status 2026-05-27: OFFLINE** — absent from LAN on both interfaces (ethernet .224 + Wi-Fi .221 both `INCOMPLETE`, no ARP reply) and on IPv6 (no ND entry for either MAC after an all-nodes solicit). Both transports going dark *simultaneously* points to a whole-device event (powered off / crashed / hung), NOT the lone `rtw88_8821cs` Wi-Fi failure mode. Searched by MAC, so a lease swap wouldn't hide it. Re-verify with the dual-stack L2-presence-by-MAC check ([TROUBLESHOOTING.md §1](TROUBLESHOOTING.md#1-cant-reach-host)) before assuming it's back — and remember device-side mDNS is broken (§10), so a `*.local` timeout is uninformative about aliveness.

**⚠ Status 2026-05-28: RESOLVED root cause + CONFIGURED & REBOOT-VERIFIED — but STILL PROVISIONAL (eMMC decision pending; values below NOT final).** The 2026-05-27 outage was the **bredOS install on the eMMC failing in early boot** (corrupt — consistent with a write interrupted during the earlier power-supply incident), NOT a hardware or power fault. Proven by a controlled SD swap-test (see [TROUBLESHOOTING.md §11](TROUBLESHOOTING.md#11-corrupt-os-install-vs-board-failure-on-an-sbc-sd-swap-test)): flashed verified **Armbian Trixie minimal** (Debian 13, kernel 6.18) to SD, **physically removed the eMMC**, booted SD-only on the same board/power/cable — nova came up on the LAN and serves SSH (banner `OpenSSH 10.0p2 Debian 7+deb13u2` = Debian 13, matches the flashed image via `nmap -sV`). Only OS storage changed between "dead" and "alive", so the board is **verified good**. The earlier "loading ramdisk → display cuts → no network" was the broken eMMC system dying early; HDMI blanking at kernel handoff is normal RK3588 (console on serial UART), so the real error was invisible without serial.

  - **DEVICE FATE UNDECIDED — eMMC module remains PHYSICALLY REMOVED.** The user has NOT chosen whether to keep running Armbian-from-SD, salvage the old bredOS eMMC, or reflash Armbian onto the eMMC. Everything below is **current + verified 2026-05-28 (post-reboot), but provisional** pending that decision. This supersedes the prior "just-flashed, identity transient" observation: the config is now set up and survives a reboot, but it is not permanent.
  - **Current verified network identity (Armbian-on-SD, eMMC removed; re-confirmed live from KOMI 2026-05-28):**
    - Hostname `nova` (set via `hostnamectl set-hostname nova`; was `indiedroid-nova`).
    - IPv4 `192.168.1.228` — now **DHCP-RESERVED** at the AT&T gateway (Home Network → IP Allocation) keyed to the ethernet MAC below.
    - Ethernet `enP4p65s0`, MAC `be:9e:7a:4c:d1:52`. **Stability PROVEN across a reboot** — Armbian uses systemd-networkd with `MACAddressPolicy=persistent` (`99-default.link`) + a fixed `/etc/machine-id` (`514f3e75f06e488fb2d862078979fa96`); RK3588 has no burned-in eth MAC, so networkd deterministically generates this same one every boot. **CAVEAT:** stable only for *this* SD rootfs/machine-id — reflashing Armbian to eMMC = new machine-id = new generated MAC = the DHCP reservation must be updated. (This is *why* it differs from the bredOS-era ethernet MAC `c6:65:5c:3a:45:3e`, also board-generated, not vendor.)
    - Wi-Fi `wlan0` **DOWN**, MAC `60:fb:00:37:57:56` (real Realtek hardware MAC, OUI 60:FB:00 Shenzhen Bilian — unchanged from the bredOS era). Not in use; left alone.
    - mDNS: avahi-daemon installed + **active**, `nova.local` resolves to `192.168.1.228` from other LAN hosts (verified via `avahi-resolve` from KOMI). **Behavior change from the bredOS era**, where device-side mDNS was broken (see §10) — it now works.
    - OS: Armbian, Debian 13 Trixie, mainline kernel `6.18.33-current-rockchip64` (booted 6.18.30, apt pulled 6.18.33, reboots clean on the new kernel). Running from **SD card; eMMC removed**.
    - SSH user `komi`, key auth via `~/.ssh/id_ed25519` (deployed this session). **NOPASSWD sudo ENABLED** for komi (`/etc/sudoers.d/komi-nopasswd`) — security tradeoff accepted by user for homelab convenience. SSH banner `OpenSSH 10.0p2 Debian 7+deb13u2`.
  - **Local-side config on KOMI already updated** (for reference, out of scope to re-pin): `~/.ssh/config` `nova`/`zbred` alias → `192.168.1.228` with `StrictHostKeyChecking accept-new`; `~/.config/ssh-mcp/servers.json` nova host → `192.168.1.228`. These now point at the current boot, not the stale `.224`.
  - **All of IP / MAC / hostname above remain provisional** and WILL change if the eMMC question is settled by a reflash (reinsert+recover keeps the SD identity; reflashing eMMC to Armbian = new machine-id = new MAC + lease). The stable facts in the table below (.224/.221, bredOS MACs) are the **pre-flux baseline** — keep them, don't overwrite.

**Reflashed 2026-05-25**: hostname `bredos` → `zbred`, default user `bred` → `komi`, SSH host keys regenerated. MAC addresses survived the reflash unchanged. mDNS currently broken on the device (avahi-daemon active but D-Bus interface dead — see [TROUBLESHOOTING.md §10](TROUBLESHOOTING.md#10-avahi-daemon-shows-active-but-mdns-doesnt-resolve)); pin SSH config to the wired IP until that's fixed.

| Field | Value |
|-------|-------|
| IPv4 (ethernet) | 192.168.1.224 *(DHCP, metric 100 — PREFERRED default route; re-verified 2026-05-25)* |
| IPv4 (Wi-Fi) | 192.168.1.221 *(DHCP, metric 600 — fallback; re-verified 2026-05-25)* |
| IPv6 (global) | 2600:1700:4811:4e70:b6c8:c1a0:de27:97ee *(SLAAC, may rotate)* |
| MAC (ethernet `enP4p65s0`) | `c6:65:5c:3a:45:3e` *(locally-administered / randomized — unusual for an SBC; survived 2026-05-25 reflash)* |
| MAC (Wi-Fi `wlan0`) | `60:fb:00:37:57:56` *(survived 2026-05-25 reflash)* |
| OUI (Wi-Fi) | 60:FB:00 — Shenzhen Bilian Electronic (consistent with indiedroid Wi-Fi NIC) |
| Hostname (mDNS) | `zbred.local` *(currently NOT resolving — avahi-daemon's D-Bus interface is broken even though the unit reports active; see TROUBLESHOOTING §10)* |
| Hostname (system) | `zbred` (set during 2026-05-25 reflash — was `bredos`; `hostname` command still NOT installed on bredOS, use `cat /etc/hostname`) |
| Hostname (DNS) | `zbred.attlocal.net` *(expected once the AT&T gateway picks up the new DHCP hostname; previously `bredos.attlocal.net`)* |
| Hardware | indiedroid nova (RK3588-class SoC) |
| Kernel | `Linux 6.1.75-rkr3 aarch64` (rkr3 = Rockchip BSP build) |
| Role | SBC, exploratory / dev |
| OS | bredOS |
| SSH | enabled, port 22 (only open port observed) |
| SSH user | `komi` *(set during 2026-05-25 reflash — was `bred`; the `bred` default user appears to be gone on the rebuilt system)* |
| SSH host keys | regenerated 2026-05-25 (reflash). If you see `Host key verification failed`, run `ssh-keygen -R 192.168.1.224 && ssh-keygen -R 192.168.1.221 && ssh-keygen -R bredos.local` and accept the new key. |
| SSH key auth | passwordless via `~/.ssh/id_ed25519` (re-deployed 2026-05-25 post-reflash) |
| SSH alias | `~/.ssh/config` defines `nova` and `zbred` aliases → `komi@192.168.1.224` w/ `~/.ssh/id_ed25519`. Pinned to the wired IP (not `zbred.local`) because device-side mDNS is currently broken. |
| Bitwarden | Historical secure note "nova SSH password (bred user)" holds the old `bred/bred` factory default — stale, since the `bred` user is gone post-reflash. Not deleted from Bitwarden by automation. |
| ICMP | **filtered** — use mDNS/ARP for aliveness |
| Wi-Fi driver | `rtw88_8821cs` (Realtek RTL8821CS combo Wi-Fi+BT via SDIO). Needs a `modprobe` workaround for both BOOT (boot-time race) and SLEEP (suspend/resume); both hooks are now installed. See [TROUBLESHOOTING.md §7](TROUBLESHOOTING.md#7-wi-fi-driver-doesnt-survive-suspendresume-rtw88_8821cs). |
| Notes | Once device-side mDNS is fixed, prefer `zbred.local` in SSH config so lease rotation and ethernet↔Wi-Fi swaps become transparent (use `StrictHostKeyChecking accept-new` since mDNS may map to multiple IPs over time). Until then, the wired IP is the stable target. The `nova` alias is preserved across reflashes — it's user-facing muscle memory, not tied to the system hostname. |

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
| Open ports | 22 (SSH), 445 (SMB), 10200 (Piper TTS — Wyoming) |
| Services | **Piper TTS** `:10200` (Wyoming, Docker) — verified live OPEN from KOMI 2026-05-31; serves the Home Assistant voice stack (STT + wakeword run on the Nova). Per session narrative, this Pi also hosts a RustDesk relay (hbbs/hbbr) — not independently re-verified here. |
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
| Freshness 2026-05-31 | Moonraker `:80` + `:7125` were observed **filtered** earlier on 2026-05-31 (printer likely powered off), but a later same-day live re-probe from KOMI found both **OPEN** again — treat as power-cycle intermittency, not a fault. Port reachability tracks whether the printer is powered on. |

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

### EZPlug (Tasmota smart plug — Z-Print / 3D-printer corner)

| Field | Value |
|-------|-------|
| IPv4 | 192.168.1.177 *(DHCP — the MAC is the stable key)* |
| IPv6 (global) | 2600:1700:4811:4e70:e6b3:23ff:fe74:3198 *(EUI-64 from MAC)* |
| MAC | e4:b3:23:74:31:98 |
| OUI | E4:B3:23 — Espressif (ESP8685 v0.4 = ESP32-C3 class) |
| Hostname (DHCP) | `ezplug-printer-4504` |
| Hostname (mDNS) | `E4B323743198.local` *(resolves from KOMI; also carries the Matter advert)* |
| Hardware / FW | EZPlug (Tasmota module `EZPLUG_V2`), Tasmota **14.4.1** (tasmota32) |
| Role | Smart plug in the Z-Print corner (3D-printer area, per HA area assignment) |
| Open ports | 80 (Tasmota web UI + **unauthenticated** HTTP API) |
| HTTP API | `curl 'http://192.168.1.177/cm?cmnd=Power'` (relay state), `…cmnd=Status%206` (MQTT health), `…cmnd=Status%200` (everything) — read commands are safe; commands with an argument WRITE config |
| HA integration | `tasmota` via MQTT — broker is Mosquitto on the Nova `192.168.1.232:1883`, MqttUser `ha`, client `DVES_743198` |
| Matter | Advertises `_matterc._udp` port 5540 (Tasmota's built-in Matter endpoint, test VID 0xFFF1, commissionable) — this advert is what the 2026-05-24 audit logged as an unidentified "Matter/Thread hub" at .177 (same MAC; it was this plug all along, and it's an endpoint, not a hub) |
| Security note | The HTTP API is unauthenticated — anyone on the LAN can toggle the relay or rewrite its MQTT config. Set a `WebPassword` if that ever matters. |
| Incident 2026-07-04 | Showed **"unavailable" in HA** while the user assumed it was just switched off. Actual cause: stale `MqttHost 192.168.1.229` (the Nova's old Wi-Fi IP — broker moved to wired `.232` on 2026-06-08), `MqttCount: 0` = never connected. Fixed via `/cm?cmnd=MqttHost%20192.168.1.232`; re-verified same day: `MqttHost 192.168.1.232`, `MqttCount: 1` (connected). "Unavailable" tracks broker connectivity, NOT relay state — see [TROUBLESHOOTING.md §13](TROUBLESHOOTING.md#13-tasmota-device-shows-unavailable-in-home-assistant). |
| Verified | 2026-07-04 live from KOMI (ARP REACHABLE, web UI HTTP 200, Status 0/2/5/6 queried; first couple of `/cm` requests timed out then all answered in ~0.1 s — treat one slow reply as transient, not absence) |

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
| 192.168.1.85 | 44:6d:7f:22:59:5b | Amazon Echo — SpotifyConnect #2 + Matter + `_meshcop._udp` (Thread border router). **Advertises Thread mesh ULA `fd43:c8e2:678:1::/64` via ICMPv6 RA** — shows up on neighboring hosts as `ip -6 route` entry via `fe80::466d:7fff:fe22:595b` (link-local derived from Echo's MAC). Unusual but correct TBR behavior. |
| 192.168.1.151 | 0e:7b:9c:c9:3e:97 *(randomized)* | iPad on Wi-Fi (`iPad.local`) |
| 192.168.1.160 | d6:77:f4:f4:b3:fa *(randomized)* | MacBook Pro — `Alexs-MacBook-Pro.local`, AirPlay port 7000 |
| 192.168.1.177 | e4:b3:23:74:31:98 | **EZPlug** — Tasmota smart plug, promoted to a verified entry above (2026-07-04). The `_matterc._udp` port 5540 advert that suggested "Matter/Thread hub" is the plug's own Tasmota Matter endpoint. |
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
| 192.168.1.142 | d4:ad:fc:42:89:d0 | **Govee bulb** (OUI D4:AD:FC = Shenzhen Intellirocks Tech = Govee's manufacturer; earlier audits misattributed this OUI to LIFX). Was at .141 before lease rotation. |
| 192.168.1.143 | d4:ad:fc:18:fb:38 | Govee bulb (was at .142) |
| 192.168.1.145 | d4:ad:fc:43:15:92 | Govee bulb (was at .143; resolves the 2026-06-10 "MAC unverified" flag — the old duplicate wasn't a copy-paste error, the DHCP leases had rotated) |
| 192.168.1.146 | d4:ad:fc:41:19:68 | Govee bulb (lease unchanged) |

> Bulb IP↔MAC mapping verified 2026-06-11 via `arp-scan --localnet` (vendor-decoded). These are DHCP clients whose leases rotate — **the MAC is the stable key, not the IP**. Re-verify with `scan-lan` before relying on an IP.
| 192.168.1.144 | 0e:c5:4e:38:25:fc *(randomized)* | Android device — advertises mDNS `Android_LBTMCTRB.local` (name seen 2026-05-27; MAC unchanged from 2026-05-24 audit) |
| 192.168.1.148 | 1c:69:20:85:e0:90 | ESP32-based IoT (OUI: Espressif) |
| 192.168.1.180 | 3c:dc:75:0e:ce:38 | ESP32-based IoT |
| 192.168.1.192 | 36:be:fe:48:f3:f5 | Unknown (randomized MAC) |
| 192.168.1.223 | 28:94:01:89:5d:4e | **NETGEAR** networking gear — OUI 28:94:01 = NETGEAR (confirmed 2026-05-28 via OUI + nmap; was the "unidentified web device" placeholder). HTTP-only admin (port 80 open, redirects to `/login.cgi`; 22 closed). Likely Wi-Fi extender / AP / managed switch behind the AT&T gateway. (NOT nova, despite being adjacent to nova's old .224 lease.) |
| 192.168.1.225 | ea:39:03:a2:aa:52 *(locally-administered)* | iPad #2 — mDNS reverse `iPad-2.local`, port 22 filtered. New since prior audits (seen + ARP-confirmed 2026-05-28). Possibly DHCP-transient. |
| 192.168.1.227 | ac:a7:04:e9:d1:c0 | ESP32-class IoT (OUI `AC:A7:04` = Espressif Inc., confirmed 2026-05-28), port 22 closed. New (seen + ARP-confirmed 2026-05-28). Possibly DHCP-transient. |
| 2600:1700:4811:4e70::48 | (IPv6-only) | Matter endpoint — `none-3.local`, advertises `_matter._tcp` |

---

## Expected / not currently on LAN

*(none pending — Home Assistant was deployed and moved to active below on 2026-05-31)*

### Home Assistant — ACTIVE (deployed 2026-05-31)

| Field | Value |
|-------|-------|
| Host | Nova — wired **`192.168.1.232:8123`** (preferred) + Wi-Fi `192.168.1.229:8123` fallback; Docker host-network binds both interfaces (dual-homed since 2026-06-08) |
| Web UI | `:8123` — verified OPEN live on **BOTH** `.232` and `.229` from KOMI 2026-06-08 (was `.229`-only 2026-05-31) |
| Voice (Wyoming) | STT on the Nova `:10300` (SenseVoice/NPU, mDNS `_wyoming._tcp` as `sensevoice-rknn`); openWakeWord on the Nova `:10400`; **Piper TTS on the Pi 5 `192.168.1.165:10200`** — all three verified OPEN live 2026-05-31 |
| Integrations | Zigbee via ZHA (SONOFF MG24 dongle on the Nova — see the nova block); Govee LAN light (`govee_light_local`) |
| mDNS | expected `homeassistant.local` |
| Notes | Was the "incoming / not yet deployed" placeholder before 2026-05-31. Run `home-net-learn 192.168.1.232` for a fuller verified entry. |

---

## Departed / historical

(Empty for now. Entries are moved here manually when a device is
confirmed gone — there is no automated staleness sweep.)

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
