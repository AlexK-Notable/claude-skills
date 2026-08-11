# FIREWALL.md

UFW (Uncomplicated Firewall) recipes and conventions — the authoritative home
for rule conventions, recipes, and diagnosis. `~/.config/CLAUDE.md` keeps only
the machine's network identity, the deny-by-default posture landmine, and the
open-ports inventory (mirrored below).

## Posture

```
Default: deny (incoming), allow (outgoing), deny (routed)
```

**Do not disable UFW.** The default-deny stance is load-bearing for every
service that's been opened — Sunshine, Weylus, mDNS, future Home
Assistant. Disabling UFW removes that protection silently.

## Rule conventions

Every rule on this machine follows these patterns. Match them when
adding new ones.

1. **Every rule has a comment.** Set via `--comment 'description'`.
2. **TCP and UDP are explicit.** Separate rules per protocol — not the
   bare `ufw allow PORT` shorthand which adds both implicitly.
3. **IPv4 and IPv6 are paired.** UFW adds both by default when no `from`
   clause is specified. Keep this default unless intentionally scoping.
4. **Service rules are grouped.** All rules for one service are added
   contiguously and share a comment prefix (e.g. `# Sunshine ...`).
5. **Prefer LAN-scoped for new services.** WAN exposure must be a
   conscious choice, not a default.

## Recipes

### LAN-scoped service (preferred for most things)

```bash
sudo ufw allow from 192.168.1.0/24 to any port 8123 proto tcp \
  comment 'Home Assistant web UI'
```

Allows only hosts on your subnet. Best default for home-lab services
that shouldn't be reachable from the WAN side of your router.

### WAN-exposed service (use only when needed)

```bash
sudo ufw allow 47984/tcp comment 'Sunshine HTTPS (WAN for Moonlight)'
sudo ufw allow 47989/tcp comment 'Sunshine HTTP'
```

Use cases: game streaming you actually use off-LAN, reverse-proxy
endpoints, anything that legitimately needs external reachability. Be
deliberate.

### Allow from one specific host

```bash
sudo ufw allow from 192.168.1.221 to any port 80 proto tcp \
  comment 'bredos dev tunnel'
```

### Allow a port range

```bash
sudo ufw allow 47998:48000/udp comment 'Sunshine Video/Audio'
```

### mDNS (already open by default with avahi)

```bash
sudo ufw allow 5353/udp comment 'mDNS (Avahi discovery)'
```

### Wake-on-LAN listener (only if you want this machine to be a magic-packet target)

```bash
sudo ufw allow 9/udp comment 'Wake-on-LAN'
```

## Inspect existing rules

```bash
sudo ufw status verbose       # full list with defaults
sudo ufw status numbered      # numbered for targeted deletion
```

## Delete a rule

```bash
sudo ufw status numbered      # find the [N] of the rule
sudo ufw delete N             # delete by number
```

Or by full reproduction of the rule:
```bash
sudo ufw delete allow 8123/tcp
```

## What's actually listening?

UFW is policy; `ss` is reality. They should match:

```bash
ss -tulpen | grep LISTEN
```

If `ss` shows something listening on a port that UFW doesn't allow,
that's a firewalled-but-running service — usually fine, often the goal.

If UFW allows a port nothing listens on, the rule is a no-op. Delete it.

## Docker published ports bypass UFW

**A Docker `-p`-published port is LAN-reachable even under default-deny with
NO ufw allow rule — and `ufw deny` cannot block it.**

Mechanism: `docker run -p 8096:8096` inserts iptables DNAT + FORWARD rules
(the `DOCKER` chain) that route the traffic to the container *before* it
would reach the host's INPUT chain, which is where ufw filters. The packets
never traverse ufw's rules at all, so ufw is silent in both directions:
it neither blocks the port nor shows it as open.

Empirically verified 2026-08-10 on KOMI: Jellyfin container published
`0.0.0.0:8096->8096/tcp`, ufw ACTIVE with no rule for 8096, yet
`curl http://192.168.1.139:8096/health` from the pi (192.168.1.165)
returned "Healthy" (re-confirmed same result on a later re-probe).

**To scope a container port, bind the publish address — don't reach for ufw:**

```bash
# LAN-facing on one interface only (still bypasses ufw, but binds narrowly)
docker run -p 192.168.1.139:8096:8096 ...

# host-only (container reachable from this machine, invisible to the LAN)
docker run -p 127.0.0.1:8096:8096 ...
```

Heavier alternative if per-source filtering is ever needed: add rules to the
iptables `DOCKER-USER` chain (which Docker evaluates before its own DNAT and
leaves alone). Not needed for current LAN-only services.

**Audit implication:** the "Currently open ports" table below and
`ufw status` only describe ufw policy — **Docker-published ports are an
invisible second inventory.** Enumerate them with
`docker ps --format '{{.Names}} {{.Ports}}'` when auditing exposure.

## Currently open ports on this machine

(See `~/.config/CLAUDE.md` "Currently Open Ports" table — authoritative
source. Snapshot for reference:)

| Port(s) | Proto | Source | Purpose |
|---------|-------|--------|---------|
| 47984 | tcp | Anywhere | Sunshine HTTPS |
| 47989 | tcp | Anywhere | Sunshine HTTP |
| 47990 | tcp | Anywhere | Sunshine Web UI |
| 48010 | tcp/udp | Anywhere | Sunshine RTSP |
| 47998:48000 | udp | Anywhere | Sunshine Video/Audio |
| 48002 | udp | Anywhere | Sunshine Control |
| 1701 | tcp | 192.168.1.0/24 | Weylus web UI |
| 5353 | udp | Anywhere | mDNS (Avahi) |

## Reset workflow (nuclear)

If rules drift badly:

```bash
sudo ufw status numbered > ~/ufw-backup-$(date +%F).txt   # save first
sudo ufw reset                                              # wipe all rules
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw enable
# then re-add your service rules from the recipes above
```

## Cross-distro note

- **CachyOS / Arch** — `pacman -S ufw && sudo systemctl enable --now ufw.service`
- **Debian / Ubuntu** — preinstalled, `sudo ufw enable`
- **Fedora** — UFW is in repos but `firewalld` is the default; consider
  using `firewall-cmd` instead if on Fedora.
- **macOS** — UFW does not exist. Use `pf` via `/etc/pf.conf` and the
  GUI System Settings → Network → Firewall.

## Always verify after changes

```bash
sudo ufw status verbose
ss -tulpen | grep LISTEN
```
