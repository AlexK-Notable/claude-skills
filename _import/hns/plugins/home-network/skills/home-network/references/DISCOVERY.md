# DISCOVERY.md

Deep dive on LAN device discovery. The patterns here come from real hunts
on a 192.168.1.0/24 network behind an AT&T residential gateway. Most
generalize; AT&T-specific quirks are called out inline.

## Table of contents

1. Why ICMP fails you
2. mDNS as the primary signal
3. ARP probing (force the kernel to look)
4. TCP fanout (proves a service, not just a host)
5. Putting it together — the canonical sweep
6. Case study: hunting an IPv6-only SBC

---

## 1. Why ICMP fails you

`ping` (ICMP echo) is firewalled by default on:

- Most Linux distros with `ufw enable` (drops ICMP echo on incoming chain)
- Windows 10/11 (Public profile blocks ICMP)
- macOS (configurable, often off)
- IoT devices, smart TVs, Echo, Matter hubs (some default to silent drop)
- Many SBC distros (bredOS, postmarketOS) that ship with strict defaults

Evidence: a full `/24` ICMP sweep on a populated home network commonly
returns ~10-15 alive when 25-30 hosts are actually present. The misses
are predictably the IoT and Linux side.

**What still works when ICMP is dropped:**
- ARP (layer 2 — can't be firewalled by the host without breaking IP)
- mDNS (UDP/5353 multicast — devices that advertise will answer)
- TCP SYN to listening ports

## 2. mDNS as the primary signal

mDNS = "DNS over multicast." Hosts on the same broadcast domain that run
an mDNS responder (avahi, Bonjour, etc.) advertise their services on UDP
port 5353 to the `224.0.0.251` (v4) / `ff02::fb` (v6) multicast group.

### Browse for everything

```bash
timeout 6 avahi-browse -arpt
```

Flags decoded:
- `-a` — all service types
- `-r` — resolve (give us IP + port, not just name)
- `-p` — parsable (semicolon-delimited)
- `-t` — terminate after one pass (don't loop forever)

Output line format (parsable mode):
```
=;<iface>;<proto>;<name>;<type>;<domain>;<host>;<addr>;<port>;<txt>
```

Useful awk to filter:
```bash
avahi-browse -arpt | awk -F';' '$1=="=" && $3=="IPv4" {print $4" @ "$8":"$9}'
```

### Resolve a specific name

```bash
avahi-resolve -4 -n bredos.local    # force IPv4
avahi-resolve -6 -n bredos.local    # force IPv6
```

Returns one line per address, or fails with timeout if no mDNS response.

### When mDNS says nothing

Either:
- The host isn't running an mDNS responder (most non-Linux IoT does though)
- The host is on a different broadcast domain (different VLAN, isolated SSID)
- mDNS is actively blocked (some routers gate cross-VLAN mDNS)
- The host genuinely isn't on this network

Don't conclude "down" from "mDNS silent" — try ARP/TCP next.

## 3. ARP probing (force the kernel to look)

The Linux kernel only ARPs IPs it has reason to talk to. So `ip neigh`
shows what you've recently touched, not who's on the network.

`arping` sends ARP requests at will, bypassing the IP stack's caching:

```bash
arping -c 1 -w 1 -I enp4s0 192.168.1.221
```

Flags:
- `-c 1` — one request
- `-w 1` — wait at most 1 second
- `-I <iface>` — required (no default on Linux)

A reply proves L2 presence regardless of firewall. **This is the gold
standard for "is something at this IP."**

### Sweep all of a /24 in parallel

```bash
for i in $(seq 1 254); do
  (arping -c 1 -w 1 -I enp4s0 192.168.1.$i 2>/dev/null \
    | grep -q "reply" && echo "192.168.1.$i ALIVE") &
done; wait
```

Be aware: arping uses RAW sockets → needs `cap_net_raw` or root. On
modern Linux, `setcap cap_net_raw+eip $(which arping)` lets it run
unprivileged.

### Without arping

`/proc/net/arp` shows the current ARP cache. Combine with a "warm the
cache" sweep:

```bash
# Force ARP by attempting TCP SYN to a closed port
for i in $(seq 1 254); do (timeout 0.5 bash -c "</dev/tcp/192.168.1.$i/1" 2>/dev/null) & done; wait
# Now read what the kernel learned
ip neigh | grep "192.168.1"
```

## 4. TCP fanout (proves a service, not just a host)

For "is service X reachable," nothing beats trying to connect:

```bash
# Pure bash, no nmap required
timeout 2 bash -c "</dev/tcp/192.168.1.221/22" && echo "open" || echo "closed/filtered"
```

`/dev/tcp/HOST/PORT` is a bash feature, not a real file. Available
everywhere bash is. Returns immediately on closed (RST), times out on
filtered (no response).

### Top ports to probe by device type

| Device class | Useful ports |
|--------------|--------------|
| Linux SBC / server | 22 (ssh), 80, 443, 8080 |
| Klipper 3D printer | 22, 80, 7125 (Moonraker), 7136 (Mobileraker) |
| Router admin | 80, 443, 8080, 22 (some), 5060 (SIP — AT&T quirk) |
| Apple device | 22, 5000 (AirPlay), 7000, 49152-65535 (mDNS dynamic) |
| Windows | 135, 139, 445, 3389 |
| Printer (physical) | 80, 443, 515 (LPD), 631 (IPP), 9100 (raw) |
| Smart TV / Chromecast | 8008, 8009, 9000 |
| Home Assistant | 8123 |
| Plex | 32400 |
| Sunshine / Moonlight | 47984, 47989, 47990, 48010 |

## 5. Putting it together — the canonical sweep

Order: cheapest signals first, most expensive last.

```
1. Read existing ARP cache         (free, may be stale)
   ip neigh | grep <subnet>

2. mDNS browse                     (UDP multicast, ~6s)
   avahi-browse -arpt

3. ARP probe each IP               (L2 broadcast, parallel, ~1s per /24)
   for i in $(seq 1 254); do arping ...; done

4. TCP SYN to top 5 ports on hits  (TCP, parallel)
   For each alive host, probe 22, 80, 443, 8080, 8123

5. (If still missing) full nmap    (slow but thorough)
   nmap -PR -PS22,80,443 -sn <subnet>
```

`scan-lan` (this skill) does steps 1-4 automatically. Step 5 is when you
add `--deep`.

## 6. Case study: the IPv6-only SBC hunt (2026-05-24)

Started: "find my indiedroid nova running bredOS, IP should be in .200s."

**What I tried first (failed):**
- ICMP ping sweep of `.200-.254` → only the router (.254) responded.
- Read ARP cache → no entries in .200s range. Concluded "device offline."

**What was actually happening:**
- bredOS was online but ICMP-filtered (default firewall).
- bredOS had no IPv4 address yet — DHCPv4 client had failed silently.
  Only had IPv6 SLAAC addresses (`2600:1700:4811:4e70:...`).
- `getent hosts bredos` returned IPv6 addresses *from the AT&T router's
  DNS* — these were stale leases from a previous session.
- The IPv6 addresses were unreachable because the host had since
  rebooted and re-randomized its SLAAC identifier.

**The "Aha!" came from:** running `avahi-resolve -4 -n bredos.local` and
getting **a hostname timeout** — meaning no live mDNS IPv4 advertisement
existed. Combined with three unreachable IPv6 addresses, that pointed
to "the AT&T router DNS is lying."

**Resolution:** User physically went to the device, connected to Wi-Fi.
After reconnection:
- `avahi-resolve -4 -n bredos.local` → `192.168.1.221` ✓
- `arping 192.168.1.221` → REACHABLE ✓
- TCP/22 open ✓
- ICMP still silent (firewall) — but we knew not to trust ICMP by then.

**Takeaways baked into this skill:**
- Rule 1 in [SKILL.md](../SKILL.md): ICMP is not authoritative.
- Rule 2 in [SKILL.md](../SKILL.md): DNS is not mDNS is not ARP.
- The `scan-lan` script uses mDNS + ARP + TCP, deliberately not ICMP.
- AT&T-specific note in [DEVICES.md](DEVICES.md) about `attlocal.net`
  stale DNS.

## AT&T residential gateway quirks

- DHCPv4 leases are advertised under `<hostname>.attlocal.net` (not
  `.local` or `.lan`). Resolves via system DNS, not mDNS.
- DHCPv6 + SLAAC prefix is delegated as `2600:1700:xxxx:xxxx::/64`.
  Globally routable — security implications if you don't firewall v6.
- mDNS works across the LAN (Wi-Fi ↔ Ethernet) on default config.
  Some "Advanced Networking" features can break it.
- DNS leases persist long after a device leaves — don't trust resolved
  IPs without an aliveness check.
