# TOOLS.md

Per-tool reference for the home-network skill. Each tool entry lists:
- What it's for
- Install command per distro
- Top flags worth memorizing
- Common gotcha

Tools are grouped by function.

---

## Discovery

### avahi-browse / avahi-resolve

**Purpose**: Browse and resolve mDNS (`.local`) service advertisements.

**Install**:
- Arch/CachyOS: `pacman -S avahi nss-mdns`
- Debian/Ubuntu: `apt install avahi-utils libnss-mdns`
- Fedora: `dnf install avahi-tools nss-mdns`
- macOS: built-in as `dns-sd` (different CLI)

**Top flags** (avahi-browse):
- `-a` — all service types
- `-r` — resolve (give IPs + ports, not just names)
- `-p` — parsable output (semicolon-delimited)
- `-t` — terminate after one pass

**Top flags** (avahi-resolve):
- `-n NAME` — resolve hostname to address
- `-4` — IPv4 only
- `-6` — IPv6 only

**Gotcha**: requires `avahi-daemon` running locally AND
`nss-mdns` configured in `/etc/nsswitch.conf` for `getent hosts foo.local`
to work transparently.

### arping

**Purpose**: Send ARP probes to confirm L2 presence regardless of firewall.

**Install**:
- Arch/CachyOS: `pacman -S iputils` (always contains arping on Arch)
- Debian/Ubuntu: `apt install iputils-arping` (split out as its own package on Debian)
- Fedora: `dnf install iputils`
- Alpine: `apk add arping` (standalone package in community repo)
- macOS: `brew install arping`

**Top flags**:
- `-c N` — number of requests (default: infinite)
- `-w N` — timeout in seconds
- `-I IFACE` — interface to use (REQUIRED on Linux, no default)
- `-D` — duplicate address detection mode

**Gotcha**: needs RAW sockets. Either run as root, or
`sudo setcap cap_net_raw+eip $(which arping)` once to make it
unprivileged forever.

### nmap

**Purpose**: The Swiss army knife — port scans, service detection, OS
fingerprinting, NSE scripts.

**Install**:
- Arch/CachyOS: `pacman -S nmap`
- Debian/Ubuntu: `apt install nmap`
- Fedora: `dnf install nmap`
- macOS: `brew install nmap`

**Top flags**:
- `-sn` — ping scan (no port scan)
- `-sS` — TCP SYN scan (default, fast, needs root)
- `-sT` — TCP connect scan (no root needed, slower)
- `-PR` — ARP ping (LAN only, very reliable)
- `-PS22,80,443` — TCP SYN ping on these ports
- `-T4` — aggressive timing (good for friendly networks)
- `-F` — fast: top 100 ports only
- `-A` — OS detection + version + script + traceroute (slow!)
- `-oG -` — grepable output to stdout
- `--exclude IP` — skip a host

**Gotcha**: many flags require root for raw sockets. Either run with
sudo, or `sudo setcap cap_net_raw,cap_net_admin,cap_net_bind_service+eip
$(which nmap)` to enable unprivileged operation. Zenmap (the GUI) will
still display a "non-root" warning — ignore it after setcap.

**Common usage**:
```bash
nmap -sn 192.168.1.0/24          # who's up?
nmap -PR -sn 192.168.1.0/24      # ARP-based (LAN only, most reliable)
nmap -F -sV 192.168.1.221        # fast port + version scan one host
nmap -A 192.168.1.221            # everything (slow)
```

---

## Inspection (local state)

### ip

**Purpose**: Show + manipulate routing, addresses, links, neighbor cache.

**Install**: preinstalled on every modern Linux.

**Common subcommands**:
- `ip -4 addr show` — IPv4 addresses on each interface
- `ip -6 addr show` — IPv6 addresses
- `ip -4 route show` — IPv4 routing table
- `ip -6 route show` — IPv6 routing table
- `ip neigh` — ARP / NDP cache
- `ip neigh flush all` — clear neighbor cache (force re-discovery)
- `ip link show` — interface status (up/down, MAC, MTU)

**Gotcha**: replaces older `ifconfig`, `route`, `arp` commands. Old
docs may show those; `ip` is canonical now.

### ss

**Purpose**: Show socket statistics (replaces `netstat`).

**Install**: preinstalled (part of `iproute2`).

**Top flags**:
- `-t` — TCP
- `-u` — UDP
- `-l` — listening only
- `-p` — show owning process (needs root for others' procs)
- `-e` — extended info (uid, inode)
- `-n` — numeric (don't resolve names)

**Common usage**:
```bash
ss -tulpen | grep LISTEN                  # what's listening on this box
ss -t state established                   # active TCP connections
ss -tn dport = :443                       # TCP connections to port 443
```

### dig / host / getent

**Purpose**: DNS resolution queries.

**Install**:
- Arch/CachyOS: `pacman -S bind` (provides `dig`)
- Debian/Ubuntu: `apt install dnsutils`
- `getent` is part of glibc, always present.

**When to use which**:
- `getent hosts foo` — uses NSS chain (mDNS, DNS, hosts file) — best
  for "resolve like a normal program would"
- `dig +short foo @SERVER` — direct DNS query to a specific server,
  bypasses NSS
- `host foo` — simpler dig wrapper, good for quick lookups
- `avahi-resolve -n foo.local` — mDNS-only

---

## Firewall

### ufw

**Purpose**: Uncomplicated Firewall — wrapper around netfilter/nftables.

**Install**:
- Arch/CachyOS: `pacman -S ufw && sudo systemctl enable --now ufw.service`
- Debian/Ubuntu: preinstalled
- Fedora: prefers `firewalld` — consider that instead

**Top commands**:
- `sudo ufw status verbose` — full rules + defaults
- `sudo ufw status numbered` — numbered for deletion
- `sudo ufw allow PORT/PROTO` — open a port
- `sudo ufw allow from CIDR to any port PORT proto PROTO` — scoped
- `sudo ufw delete N` — remove rule by number
- `sudo ufw reset` — wipe all rules (DANGER)

**Gotcha**: rules added without `--comment` are confusing to audit
later. ALWAYS comment.

### nft (nftables)

**Purpose**: Direct nftables management — what UFW is built on.

**Install**: preinstalled on modern Linux.

**Common commands**:
- `sudo nft list ruleset` — show entire ruleset
- `sudo nft list table inet filter` — one table

**When to use**: when ufw isn't expressive enough (e.g., rate-limiting,
log-and-drop). Otherwise stick with ufw.

---

## Capture & inspection

### tcpdump

**Purpose**: Packet capture from CLI.

**Install**:
- Arch/CachyOS: `pacman -S tcpdump`
- Debian/Ubuntu: `apt install tcpdump`
- macOS: built-in

**Common usage**:
- `sudo tcpdump -i any -nn port 53` — DNS traffic
- `sudo tcpdump -i enp4s0 -nn 'arp'` — ARP traffic only
- `sudo tcpdump -i any -nn 'port 5353'` — mDNS traffic
- `sudo tcpdump -w capture.pcap` — write to file, open in wireshark later

### termshark

**Purpose**: Wireshark in the terminal.

**Install**:
- Arch/CachyOS: `pacman -S termshark`
- Debian/Ubuntu: `apt install termshark`
- macOS: `brew install termshark`

**Usage**: `sudo termshark -i enp4s0` — full Wireshark-like TUI.

---

## Misc

### wakeonlan / etherwake / wol

**Purpose**: Send WoL magic packet.

**Install**:
- Arch/CachyOS: AUR only — `yay -S wakeonlan` or `yay -S etherwake-git`
  (Arch's `net-tools` does NOT contain `etherwake`, despite older docs)
- Debian/Ubuntu: `apt install wakeonlan` (perl-based, works well)
- Fedora: `dnf install wol`
- Alpine: `apk add wol`
- macOS: `brew install wakeonlan`

**Usage**:
- `wakeonlan AA:BB:CC:DD:EE:FF` — send magic packet to MAC
- `wakeonlan -i 192.168.1.255 AA:BB:CC:DD:EE:FF` — specify broadcast

**Gotcha**: WoL needs the target's NIC kept powered and BIOS WoL on.
See [TROUBLESHOOTING.md §5](TROUBLESHOOTING.md#5-wake-on-lan-doesnt-work).

### nc (netcat)

**Purpose**: Read/write TCP and UDP.

**Install**: preinstalled almost everywhere (different flavors: OpenBSD nc, ncat, traditional nc).

**Top usage**:
- `nc -zv HOST PORT` — test if port is open (verbose, zero-IO)
- `nc -l PORT` — listen on a port
- `nc -u HOST PORT` — UDP instead of TCP

**Gotcha**: flag semantics differ between flavors. If `-z` doesn't work,
you have a flavor that needs `--probe`.

### `/dev/tcp` (bash builtin)

**Purpose**: TCP probing without any external tool.

**Install**: bash itself. Not available in dash/posh.

**Usage**:
```bash
timeout 2 bash -c "</dev/tcp/HOST/PORT" && echo open || echo closed
```

**Gotcha**: not a real device — `/dev/tcp` doesn't exist as a file. It's
a bash redirection special. Won't work in `sh` if `sh` is dash.

### whois

**Purpose**: Domain / IP / OUI lookups.

**Install**:
- Arch: `pacman -S whois`
- Debian: `apt install whois`

**Usage**:
- `whois 8.8.8.8` — IP owner
- `whois -h whois.iana.org "60:fb:00"` — MAC OUI lookup (vendor)

**Alternative for OUI**: the `home-net-learn` script uses the
IEEE OUI registry over HTTPS — no `whois` required.
