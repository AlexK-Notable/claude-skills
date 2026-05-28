# TROUBLESHOOTING.md

Decision trees for common LAN problems.

## Table of contents

1. "Can't reach <host>"
2. "SSH connection refused / timeout"
3. "DNS resolves but I can't connect"
4. "IPv4 works, IPv6 doesn't (or vice versa)"
5. "Wake-on-LAN doesn't work"
6. "mDNS suddenly stopped working"
7. "Wi-Fi driver doesn't survive suspend/resume (rtw88_8821cs)"
8. "Don't unload a Wi-Fi driver over the same Wi-Fi connection"
9. "SSH to a DHCP'd host that keeps changing IP" (mDNS HostName pattern)
10. "avahi-daemon shows active but mDNS doesn't resolve"

---

## 1. "Can't reach <host>"

```
Can `arping <IP>` get a reply?
├── YES → host is up. Skip to step 3.
└── NO  → step 2.

Step 2: Is the host actually on this network?
├── Try mDNS: `avahi-resolve -n <host>.local` — answer?
│   ├── YES (with IP) → use THAT IP, your IP was wrong.
│   └── NO  → host is offline / on different network / no responder.
└── Try router's DHCP lease page (http://192.168.1.254/).

Step 3: Host is up. Why can't you reach it?
├── ICMP filtered? (`ping` fails but `arping` works) → totally fine, IGNORE ICMP.
├── Port closed? (`nc -zv <IP> <port>` → "Connection refused")
│   → service isn't listening on that port. Check on the host.
├── Port filtered? (`nc -zv <IP> <port>` → hangs/timeout)
│   → firewall on the HOST is blocking you. Check `ufw status` on the host.
└── Connection works but timeouts? → MTU or routing issue (see step 4).
```

### Unprivileged "is the host present at L2 anywhere?" (when `arping` needs root)

`arping` needs `CAP_NET_RAW`/root; on a locked-down box (e.g. this
CachyOS workstation, where sudo is barred by policy and the cap isn't
set) it just prints `socket: Operation not permitted`. Unprivileged
substitute that works across BOTH IP families and survives DHCP lease
rotation — because you search by MAC, not IP:

```bash
# IPv4: fan out pings to force ARP even when ICMP echo is filtered, then read the cache
for i in $(seq 1 254); do ping -c1 -W1 192.168.1.$i >/dev/null 2>&1 & done; wait
ip neigh show | grep -i <MAC>

# IPv6: solicit all-nodes multicast, then read the neighbor cache
ping -6 -c3 -W1 -I <iface> ff02::1
ip -6 neigh show | grep -i <MAC>
```

ARP/ND are answered by the kernel *below* any host firewall, so a hit
means the host is genuinely on-LAN even if every port is filtered.
Three distinct conclusions:

- **Hit at some IP** → host is up; if you can't connect, it's
  firewalled/ICMP-filtered, not absent (back to step 3 above).
- **`INCOMPLETE` at the expected IP but a hit at another** → stale IP /
  lease moved; use the IP the MAC actually answers at.
- **Absent by MAC across BOTH families** → genuinely off-LAN (powered
  off / crashed / on another network). If a multi-homed host goes dark
  on *all* its interfaces at once, suspect a whole-device event rather
  than a per-interface driver failure.

Searching by MAC instead of IP is what makes this robust to lease
rotation. See DEVICES.md §"indiedroid nova (bredOS)" for a real case
(nova OFFLINE 2026-05-27).

## 2. "SSH connection refused / timeout"

```
ssh user@host
```

| Symptom | Likely cause | Next step |
|---------|--------------|-----------|
| `Connection refused` | sshd not running on host | Check `systemctl status sshd` on host |
| `Connection timed out` | Network unreachable OR firewall dropping | `nc -zv host 22` to confirm; check ufw on both sides |
| `No route to host` | You don't know how to reach this IP | Check `ip route get <IP>` |
| `Permission denied (publickey)` | sshd is fine, your key isn't authorized | `ssh-copy-id user@host`, or check `~/.ssh/authorized_keys` on host |
| `Host key verification failed` | Host's SSH key changed (reinstall? attack?) | `ssh-keygen -R host` then retry; verify fingerprint out-of-band |

### `Permission denied (publickey)` even though you have a working key

If `~/.ssh/config` pins an `IdentityFile` for the host and that file
isn't the right key for the target user, SSH **will not** fall back to
other keys in `~/.ssh/`. Without `IdentityFile`, ssh tries every key it
has and the right one wins; with `IdentityFile` set, it's the only key
offered (unless you also set `IdentitiesOnly no`).

Symptoms:
- `ssh user@host` from the command line **works** (no config pin, all
  keys tried).
- `ssh alias` using a `Host alias` block **fails** with `Permission
  denied (publickey,password)` even when the same user/host worked
  bare.

Fixes (any one):
- Point `IdentityFile` at the key that's actually in `authorized_keys`
  on the remote.
- Remove the `IdentityFile` line (lets ssh try all keys).
- Set `IdentitiesOnly no` for the host (offers keys beyond the
  configured identity).
- Run `ssh-copy-id -i ~/.ssh/configured_key.pub user@host` so the
  configured key is the right one.

This trips you up specifically when migrating from `id_rsa` to
`id_ed25519` — the old key still works bare, the new alias doesn't.

### When the host is on Wi-Fi but unstable

ARM SBCs on Wi-Fi sometimes drop and reassociate. Symptom: SSH works for
2 minutes then hangs. Try:
- `ssh -o ServerAliveInterval=30 user@host`
- On the host: check `systemctl status NetworkManager` or `iwconfig`
- Wi-Fi power management: `iw dev wlan0 set power_save off`

## 3. "DNS resolves but I can't connect"

This usually means **stale DNS**.

```bash
# Get the resolution from each layer separately:
getent hosts foo                      # System DNS (your /etc/resolv.conf chain)
avahi-resolve -n foo.local            # mDNS
dig +short foo @192.168.1.254         # Direct query to the router
dig +short foo @8.8.8.8               # Public DNS (to confirm it's not a public name)
```

If `getent hosts` and `avahi-resolve` disagree:
- Trust `avahi-resolve` for hosts that should be on the LAN.
- The router DNS may be holding a stale lease from a previous session.
- AT&T gateways are particularly prone to this — leases persist for hours.

If `getent hosts` returns an IPv6 address and you can't reach it:
- Check your own IPv6 connectivity: `ping -6 -c2 google.com`
- The address may have rotated (SLAAC privacy extensions).
- Try IPv4 explicitly: `getent hosts foo | grep -v ':' | head -1`

## 4. "IPv4 works, IPv6 doesn't" (and vice versa)

### Check your own state first

```bash
ip -4 addr show                # do you have a v4 address?
ip -4 route show default       # do you have a v4 default route?
ip -6 addr show                # do you have v6 addresses?
ip -6 route show default       # do you have a v6 default route?
ping -4 -c2 google.com         # v4 reach the world?
ping -6 -c2 google.com         # v6 reach the world?
```

If your own v6 is broken, every v6 ping will fail with "Address
unreachable" — looks like the target is down, but it's actually you.

### When v6 works for the world but not for a LAN host

The host may be advertising stale SLAAC addresses (router DNS cached
them). Try the link-local instead:
```bash
ping -6 -I enp4s0 fe80::xxxx:xxxx:xxxx:xxxx%enp4s0
```

Or just use IPv4 — most LAN services don't care.

### When v4 doesn't work for one specific host

That host's DHCPv4 client may have failed. SBCs running modern distros
sometimes default to IPv6-only when DHCPv4 doesn't get a lease in
time. Connect a monitor and check:
```bash
ip -4 addr show
sudo systemctl restart NetworkManager
# or
sudo dhclient -v <iface>
```

## 5. "Wake-on-LAN doesn't work"

WoL is fragile. Things that have to be true:

| Layer | Requirement | How to check |
|-------|-------------|--------------|
| BIOS/UEFI | "Wake on LAN" or "Wake on PCIe" enabled | reboot, look in firmware setup |
| OS (sender) | wakeonlan tool installed | `which wakeonlan` |
| Network | Target on same broadcast domain (same VLAN/subnet) | route to it now? |
| NIC | Supports WoL and has it enabled | `ethtool eth0 \| grep Wake-on` |
| OS (target) | NIC stays powered when system halts (`Supports Wake-on: g`) | same |
| OS (target) | `ethtool -s eth0 wol g` set persistently (NetworkManager / systemd) | check NM connection settings |
| Power | Some PSUs need "Erp/Energy Star" disabled to keep NIC powered | BIOS |

Diagnosis sequence:
1. On target *while it's running*: `ethtool eth0 | grep -i wake`
   - Should show `Supports Wake-on: pumbg` and `Wake-on: g`
2. Power the target off (shutdown, not reboot).
3. From sender: `wakeonlan AA:BB:CC:DD:EE:FF`
4. If nothing happens after ~30s: WoL setup on the target is broken.
   Reboot it, fix `ethtool` setting, try again.

## 6. "mDNS suddenly stopped working"

mDNS works on UDP/5353 multicast. Things that break it:

- **avahi-daemon stopped.** `systemctl status avahi-daemon` →
  `systemctl restart avahi-daemon`.
- **Firewall added a default-deny on UDP/5353.** `sudo ufw allow
  5353/udp` if missing.
- **Wi-Fi router has "AP Isolation" or "Client Isolation" enabled.**
  Disable in router admin.
- **Multiple SSIDs / VLANs without mDNS reflector.** Devices on
  different VLANs can't see each other's mDNS unless the router runs an
  mDNS reflector / Bonjour relay.
- **NSS not configured for mDNS.** `/etc/nsswitch.conf` should have
  `hosts: ... mdns4_minimal [NOTFOUND=return] ... dns ...`.
- **Recent NetworkManager / systemd-resolved upgrade.** Either may
  start owning DNS resolution and bypass `/etc/nsswitch.conf`. Check
  `resolvectl status`.

## 7. "Wi-Fi driver doesn't survive suspend/resume" (rtw88_8821cs)

Realtek RTL8821CS is a Wi-Fi+Bluetooth combo chip attached via SDIO bus,
sharing SDIO + an internal UART. Boot-time races are common; the kernel
module (`rtw88_8821cs`) often needs to be loaded **late** rather than
during the normal hotplug path. Distros like bredOS commonly ship with
the module either disabled or loaded with a delay.

If you've already handled the boot case (e.g., a systemd unit that
`modprobe`s after `multi-user.target` with a 1 s settle), suspend/resume
will still kill Wi-Fi until you also add a system-sleep hook:

```bash
sudo install -m 0755 /dev/stdin /usr/lib/systemd/system-sleep/rtw8821cs <<'EOF'
#!/bin/sh
# systemd-sleep hook: unload before sleep, reload after resume
case "$1" in
  pre/*)  modprobe -r rtw88_8821cs ;;
  post/*) sleep 1 && modprobe rtw88_8821cs ;;
esac
EOF
```

Test from a DIFFERENT transport (ethernet, serial console) — see §8 for
why you must not test this over the same Wi-Fi.

Verify after a `sudo systemctl suspend` + wake cycle:
- `ip link show wlan0` — UP
- `iw dev wlan0 link` — associated
- mDNS still answers (`avahi-resolve -4 -n <host>.local`)

Same pattern applies to any SDIO-attached Wi-Fi (Allwinner, Rockchip,
Amlogic SBCs frequently hit this).

### Alternative: mask sleep targets for always-on devices

If the host is a server-class SBC plugged into wall power 24/7 with no
battery (Pi, nova, CB2, etc.), the simpler fix is to prevent sleep from
ever happening:

```bash
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
```

This catches every path that could trigger a suspend: `systemctl
suspend`, logind idle-timeout, power-button short-press, lid switch,
and any other service that pulls in a sleep target. After masking, even
`sudo systemctl suspend` returns `Call to Suspend failed: Access
denied`. Uptime grows monotonically and the driver never has to
unload/reload after first boot.

Reverse with:
```bash
sudo systemctl unmask sleep.target suspend.target hibernate.target hybrid-sleep.target
```

Tradeoffs:
- **Cost**: ~2-3W extra idle power vs sleep mode (~$2-3/year). Negligible at home.
- **Benefit**: eliminates an entire class of bugs — sleep/resume races,
  BT-Wi-Fi-SDIO conflicts, alarm/timer-based wake failures.

When to use which:
- **Always-on server SBC** (no battery, plugged in 24/7): mask sleep
  targets. Simpler, no moving parts.
- **Laptop / battery device**: must keep sleep working — use the
  system-sleep hook above instead.
- **Hybrid (mostly-on but occasionally suspended)**: install BOTH (mask
  + hook). If you later unmask sleep, the hook still protects you.
  Belt-and-suspenders.

## 8. "Don't unload a Wi-Fi driver over the same Wi-Fi connection"

If you `modprobe -r <wifi_driver>` while SSHed in over that exact Wi-Fi
interface, the kernel tears down `wlanN` immediately. Your TCP socket
dies; bash gets `SIGHUP` before any reload command can run. The host is
now unreachable until console intervention or reboot.

Same hazard with: `ip link set wlan0 down`, `systemctl restart
NetworkManager` (on a Wi-Fi-only host), `iw dev wlan0 disconnect`,
`rfkill block wifi`.

**Safer patterns**:
- Install the script that does the unload, then trigger it indirectly:
  `sudo systemctl suspend` (kernel runs your sleep hook AFTER your SSH
  session has been cleaned up) — see §7.
- SSH in over a DIFFERENT transport (ethernet, USB-gadget RNDIS, serial
  console) and do the destructive work from there.
- Chain commands so the reload happens even if the connection drops:
  `nohup sh -c 'modprobe -r rtw88_8821cs; sleep 2; modprobe rtw88_8821cs' &`
  (still risky — your `nohup` may itself be killed before the second
  modprobe lands if the shell dies fast enough).
- Use `at now + 1 minute` to schedule the reload independently of your
  session, so the unload is decoupled from your TTY.

## 9. "SSH to a DHCP'd host that keeps changing IP" (mDNS HostName)


SBCs and laptops on DHCP can swap IPs (lease rotation, ethernet ↔
Wi-Fi failover, router reboot). Hard-coding `HostName 192.168.1.X` in
`~/.ssh/config` breaks the moment that happens.

**Use the mDNS name as `HostName`**:

```sshconfig
Host nova
  HostName bredos.local
  User bred
  IdentityFile ~/.ssh/id_ed25519
  StrictHostKeyChecking accept-new
```

Why `accept-new`: mDNS can resolve to multiple IPs over time (e.g., the
host's ethernet today, Wi-Fi tomorrow). Each IP is a fresh entry in
`~/.ssh/known_hosts`. `accept-new` trusts a new IP on first encounter
but still rejects a key CHANGE for an existing IP — the security
property you actually want (TOFU per IP, alarm on key change).

Caveats:
- Requires `nss-mdns` configured locally (`/etc/nsswitch.conf` has
  `mdns4_minimal` in the `hosts:` line) — see [TOOLS.md §avahi](TOOLS.md#avahi-browse--avahi-resolve).
- Requires `avahi-daemon` running on the target.
- mDNS is racy on multi-homed hosts — `avahi-resolve -4 -n foo.local`
  returns whichever interface answers first. Functionally fine if both
  IPs reach the same sshd.
- Same pattern applies to per-host SSH MCP config (e.g.,
  `~/.config/ssh-mcp/servers.json` — use `bredos.local` not `192.168.1.221`).
- If the target host's mDNS is broken (see §10), this pattern fails open
  — fall back to a pinned IP until you fix avahi on the target.

## 10. "avahi-daemon shows active but mDNS doesn't resolve"

A subtler failure mode than §6: the systemd unit reports healthy, but
mDNS is silently dead — both on the host itself and from every other
LAN client trying to resolve it.

**Symptom pattern**:

```bash
# On the affected host:
systemctl is-active avahi-daemon         # → active
avahi-resolve -n $(hostname).local       # → "Failed to create client object: Daemon not running"

# From another LAN client:
avahi-resolve -4 -n <host>.local         # → "Failed to resolve host name" (timeout)
```

The contradiction is the diagnostic: systemd thinks it's running, the
daemon's own resolver client thinks it isn't.

**Root cause**: avahi-daemon talks to clients (including `avahi-resolve`
and other LAN devices doing mDNS lookups) over D-Bus. The daemon's
systemd unit can remain `active` while its D-Bus connection breaks —
process alive, interface dead. Common triggers: D-Bus restart without
restarting avahi, dbus-daemon socket churn during heavy reconfiguration,
package upgrades that swap dbus mid-boot.

**Diagnostic principle (general)**: `systemctl is-active` only tells you
the process exists. For daemons that expose a D-Bus or socket interface,
**always exercise the interface itself** to confirm functional health.
Same lesson applies to `pulseaudio`, `bluetoothd`, `NetworkManager`,
`polkit`, `udisks2`, etc.

**Recovery**:

```bash
sudo systemctl restart avahi-daemon
# then re-test:
avahi-resolve -n $(hostname).local
```

If a plain restart doesn't fix it, the D-Bus side may be the culprit:

```bash
systemctl status avahi-daemon                 # look for "Failed to register"
journalctl -u avahi-daemon -n 50              # D-Bus connection errors here
sudo systemctl restart dbus && sudo systemctl restart avahi-daemon
```

Restarting `dbus` is heavy-handed (it can disturb session services), so
try the avahi-only restart first.

**Don't be fooled into thinking the host is down.** Per DISCOVERY.md
Rule 1 / Rule 2, a broken mDNS responder doesn't mean the host is
offline — fall back to ARP (`ip neigh show <IP>`) or the pinned IP via
SSH while diagnosing.

See also DEVICES.md §"indiedroid nova (bredOS)" for a real case (post-reflash 2026-05-25).
