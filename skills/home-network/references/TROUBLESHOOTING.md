# TROUBLESHOOTING.md

Decision trees for common LAN problems.

## Table of contents

1. "Can't reach <host>"
2. "SSH connection refused / timeout"
3. "DNS resolves but I can't connect"
4. "IPv4 works, IPv6 doesn't (or vice versa)"
5. "Wake-on-LAN doesn't work"
6. "mDNS suddenly stopped working"

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
