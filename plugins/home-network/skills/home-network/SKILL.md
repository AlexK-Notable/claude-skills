---
name: home-network
description: Use when working with the home LAN — discovering devices, troubleshooting connectivity, configuring ufw firewall rules, opening/closing ports, looking up IPs/hostnames/MAC addresses, scanning subnets, probing services with mDNS/avahi/arping/nmap/dig, working with router DHCP leases, debugging "can't reach" or "host unreachable" symptoms, managing wake-on-LAN, or referencing known devices (an ARM single-board computer / SBC, a Raspberry Pi, a 3D printer / Klipper / Moonraker controller, your router/gateway, laptops/tablets/phones, Matter/Thread IoT, smart speakers, a game-streaming host). The skill is SELF-UPDATING: it includes home-net-learn for device-specific discovery and home-net-capture for general findings — both spawn background `claude -p` agents that verify and merge new knowledge into the skill's reference docs without blocking your shell. At the end of any meaningful /home-network task, follow the Knowledge Capture Protocol section to keep the skill growing with use.
---

# home-network

Operator's manual for the home LAN. This skill teaches *strategy* — when to
reach for which tool, how to interpret the results, what to do when nothing
responds. Device-specific facts live in [DEVICES.md](references/DEVICES.md).

## The Mental Model

Three rules, in order of importance:

### 1. ICMP is not authoritative

`ping` is the wrong default for "is this host alive?" Modern devices —
especially anything running a default firewall — drop ICMP echo silently.
A failed `ping` does NOT mean the host is down.

**Better signals, ordered by reliability:**

| Signal | What it proves | Tool |
|--------|----------------|------|
| ARP REACHABLE entry | L2 presence — kernel got a MAC for this IP | `ip neigh` |
| mDNS response | Host actively answers multicast on UDP/5353 | `avahi-resolve`, `avahi-browse` |
| TCP SYN-ACK | Specific service is listening | `nc -z`, `/dev/tcp/HOST/PORT` |
| `arping` reply | L2 ARP request answered | `arping -c1 IP` |
| ICMP echo reply | Host is up AND not firewalled | `ping` |

ICMP being unreachable + ARP REACHABLE + open TCP port = host is fine,
you're just being firewalled.

### 2. DNS is not mDNS is not ARP

When a name resolves, ask *which resolver answered*. Different layers store
different state with different freshness:

- **System DNS** (`getent hosts foo`) → asks `/etc/resolv.conf` chain →
  usually the router → may return **stale leases** for hours after a device
  leaves the network. Don't trust a resolved IP without an aliveness check.
- **mDNS** (`avahi-resolve -n foo.local`) → multicast on UDP/5353 → the
  host *itself* answers in real-time. If mDNS resolves, the host is on
  the LAN right now.
- **ARP cache** (`ip neigh`) → only populated for IPs the kernel has
  recently tried to talk to. Empty cache ≠ empty network. Use `arping` to
  force a fresh probe.

### 3. Verify your own connectivity before blaming the target

If IPv6 pings fail with "Address unreachable," check `ip -6 route show
default` first — your own routing might be the problem. Same for v4: if
nothing on the LAN responds, check `ip -4 addr show` and `ip -4 route`
before assuming a network-wide outage.

## Toolchain (with availability detection)

Never assume a tool is present. Use this pattern in scripts:

```bash
have() { command -v "$1" >/dev/null 2>&1; }
prefer() {
  for t in "$@"; do have "$t" && { echo "$t"; return 0; }; done
  return 1
}

# Example: pick whichever ARP prober is available
ARP=$(prefer arping nping) || { echo "no ARP tool — falling back to ping"; ARP=ping; }
```

Run `home-net-doctor` on a fresh machine to see what's available and what
to install. Full per-tool reference in [TOOLS.md](references/TOOLS.md).

## Decision Tree

**"What's the IP of <device>?"**
1. Known device? Check [DEVICES.md](references/DEVICES.md) first.
2. Has a `.local` mDNS name? → `avahi-resolve -4 -n <name>.local`
3. Router knows it? → `getent hosts <name>` (warning: may be stale)
4. None of the above? → `scan-lan` to sweep + match.

**"Is <host> up?"**
1. Try mDNS resolve. If it answers, yes.
2. `arping -c1 -w1 <IP>` from a known-good interface.
3. TCP SYN to a likely port (`nc -zv <IP> 22 80 443`).
4. `ping` only as last resort.

**"Can't reach <host> over SSH"**
See [TROUBLESHOOTING.md](references/TROUBLESHOOTING.md) for the full
decision tree. First three checks:
1. Is the host actually up? (see above)
2. Is port 22 open from your network? (`nc -zv host 22`)
3. Is *your* firewall blocking outbound? (`ufw status verbose` on this end)

**"I want to open port N for service X"**
See [FIREWALL.md](references/FIREWALL.md). Default to **LAN-scoped**, not
WAN-exposed:
```bash
sudo ufw allow from 192.168.1.0/24 to any port N proto tcp comment 'X'
```

**"I just discovered a new device, want to remember it"**
```bash
home-net-learn <name-or-IP>
```
Returns immediately. Background agent verifies and merges into
[DEVICES.md](references/DEVICES.md).

## Common Workflows

### Discover everything on the LAN

```bash
scan-lan                    # default subnet from `ip route`
scan-lan 10.0.0.0/24        # specific subnet
scan-lan --quick            # mDNS browse only, no probes
```

Combines mDNS browse + ARP probe + TCP fanout on the top 5 ports.
Avoids ICMP because of Rule 1.

### Resolve a name reliably

```bash
find-host sbc               # tries DNS → mDNS → ARP cache → reverse lookup
find-host 192.168.1.10      # tries reverse DNS → mDNS PTR → ARP
```

### Probe service availability

```bash
port-check 192.168.1.10 22 80 443 8080
port-check printer 80 7125 7136    # Klipper / Moonraker / Mobileraker
```

### Wake a sleeping machine

```bash
wol sbc                     # uses alias from DEVICES.md
wol AA:BB:CC:DD:EE:FF       # raw MAC
```

(Requires the target NIC to have WoL enabled in BIOS + OS. See
[TROUBLESHOOTING.md §5](references/TROUBLESHOOTING.md#5-wake-on-lan-doesnt-work).)

## Knowledge Capture Protocol (read this every session)

**Standard practice for /home-network: at the end of any task that
produced new knowledge, fire a capture.** The skill grows in proportion
to its use only if you keep this habit.

### When to capture (decision heuristic)

After helping the user, ask yourself: *did I learn something the docs
don't already have?* Check against these categories:

| Category | Capture if… | Goes into |
|----------|-------------|-----------|
| **New device** | A previously-unknown IP / MAC / hostname appeared and was confirmed | DEVICES.md |
| **Device drift** | An existing entry's IP, MAC, services, or role changed | DEVICES.md |
| **Device status** | A documented device is now offline / back online / on Wi-Fi vs Ethernet | DEVICES.md (freshness/notes) |
| **Diagnostic technique** | You used a working diagnostic step the docs don't describe | TROUBLESHOOTING.md |
| **Firewall change** | A UFW rule was added/removed/scoped during this session | FIREWALL.md |
| **Tool quirk** | You hit an undocumented flag, gotcha, distro packaging surprise | TOOLS.md |
| **Docs were wrong** | A documented fact was contradicted by reality | (the file with the wrong fact) |
| **Secret discovered** | A password / API token / private key / vault credential emerged or was changed | **Bitwarden (NOT docs)** — see [Storing credentials in Bitwarden](#storing-credentials-in-bitwarden) below |

If yes to ANY: capture. If no to all: skip — don't manufacture findings.

### Storing credentials in Bitwarden

Anything secret — host passwords, API tokens, SSH private keys, vault recovery codes — goes into Bitwarden, **never into `DEVICES.md` or any reference file in this repo**. The repo gets cloned across machines (and your fork may be public); secrets in a versioned doc are permanent leaks waiting to happen.

**Two Bitwarden tools are available — pick by *who reads the secret back*:**

- **`bw` (password vault)** — the default for host passwords, SSH keys, and recovery codes that *you* retrieve later, interactively, with the master password. This is what the self-destructing-handoff recipe below uses, and what the `bwu` / `bw-ssh` / `bw-get-key` zsh helpers pull from (handy for the "can't reach a host over SSH" case — `bwu` then `bw-ssh '<item>' user@host`). Right for almost everything a network admin stores by hand.
- **`bws` (Secrets Manager)** — for secrets a *machine* consumes unattended: a daemon on a LAN host (an SBC, a Pi, the Klipper controller) that needs an API key or SSH key injected at boot with no human present. Store it as a secret in a `bws` project and inject via `bws run`. Reach for this only when there's no interactive unlock in the loop — it's a separate product with token-based (not master-password) auth.

Both are documented in the [bitwarden-cli skill](../../bitwarden-cli/SKILL.md), which routes between them; `bws`-specific operations live in its `references/secrets-manager.md`.

For the common case (a credential you'll retrieve by hand), the pattern is the [bitwarden-cli skill](../../bitwarden-cli/SKILL.md)'s **Self-destructing handoff script** recipe. The flow:

1. Generate or capture the secret (e.g., `bw generate --length 28 --uppercase --lowercase --number --special`, or read it from somewhere)
2. Write it to `/tmp/<secret-name>-<pid>` (mode 600)
3. Write a wrapper script to `/tmp/<wrapper-name>` (chmod +x) that reads the stash, builds the bw JSON, pipes through `bw encode | bw create item`, and shreds both files on success
4. Tell the user the wrapper path — they fire it one-shot in their unlocked shell
5. Metadata-only output prints; both files self-destruct

What goes into `DEVICES.md` instead: a *pointer* — "Password stored in Bitwarden as `sbc SSH password (user)`. Key auth is the primary access method (`~/.ssh/id_ed25519`)." That tells future-you where to retrieve it without leaking the value.

### How to capture

1. Write a freeform markdown narrative of findings to a temp file:

   ```bash
   cat > /tmp/capture-$$.md <<'EOF'
   # Findings: <one-line summary>

   ## Context
   What was the user asking about? What did I do?

   ## What I learned
   - <fact 1, with specific values: IPs, MACs, ports, etc.>
   - <fact 2>

   ## Where this belongs
   - DEVICES.md: update <entry name> with <field changes>
   - TROUBLESHOOTING.md: add new section under <heading>
   - (etc.)

   ## What was already documented (skip)
   - <fact that's already in docs — list so the agent doesn't re-add>
   EOF
   ```

2. Fire the capture (foreground returns in <1s):

   ```bash
   home-net-capture --findings /tmp/capture-$$.md
   ```

3. The background `claude -p` agent does the work:
   - Identifies which file(s) to update
   - Re-verifies claims against live network where possible
   - Conservative-merges: additions/freshness auto-apply;
     contradictions/deletions go to a `.review.md`
   - Git commits AND pushes to origin/main on success
   - notify-send fires with verdict

4. Continue with the user's next request. The agent works in parallel
   to your conversation.

### What's IN scope for auto-update

- `DEVICES.md` — device facts (IP, MAC, role, ports, freshness)
- `TROUBLESHOOTING.md` — new diagnostic techniques
- `FIREWALL.md` — new rules + rationale
- `TOOLS.md` — newly-learned quirks

### What's OUT of scope

- `SKILL.md` — versioned release content (this file)
- `README.md` — versioned release content
- `DISCOVERY.md` — core mental model (curated manually)
- `.claude-plugin/plugin.json` — manifest

### Anti-patterns

- ❌ Capturing trivial confirmations ("I confirmed the router is at .254")
  when no docs change is warranted
- ❌ Writing a narrative without specific values (vague narratives produce
  vague updates — the agent needs concrete facts)
- ❌ Editing reference files inline during the session, then ALSO
  capturing — the agent will see your edits as already-applied
  (acceptable but wasteful; one path is better)
- ❌ Skipping capture because "the user didn't ask me to" — the user has
  already authorized this pattern by adopting the skill

## The Original Self-Healing Loop (home-net-learn)

`home-net-learn` is the device-specific entry point — narrower than the
general capture, optimized for the "I just found a new IP" case. Goal:
the skill's device inventory grows with use, without blocking your shell.

```
┌──────────────────────────────────────────────────────────────┐
│ User runs:  home-net-learn sbc                               │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼  (synchronous, < 5s)
┌──────────────────────────────────────────────────────────────┐
│ Probe: mDNS browse, ARP, TCP fanout, OUI lookup              │
│ Output: DEVICES.draft.md (staging file)                      │
│ Spawn:  claude -p "<verify prompt>" &                        │
│ Return immediately — shell is yours again                    │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼  (background, agentic, 30-90s)
┌──────────────────────────────────────────────────────────────┐
│ Agent re-verifies against live network                       │
│ Checks naming collisions in DEVICES.md                       │
│ Looks up MAC OUI (vendor identification)                     │
│ Infers role from open ports + mDNS services                  │
│ On pass:  merges draft → DEVICES.md, git commits             │
│ On fail:  writes DEVICES.draft.review.md, leaves for user    │
│ Always:   notify-send shows outcome                          │
└──────────────────────────────────────────────────────────────┘
```

**Why agentic background?** The goal is to not slow your main
workflow. The verification work (cross-checking, OUI lookup, role
inference) takes ~30-90s — too long to block on, but boring enough that
an LLM can do it well without supervision.

**Safety**: the foreground probe only writes a *draft*. Nothing touches
`DEVICES.md` until the agent passes verification. Failed verifications
leave a review file with the discrepancies highlighted.

## References (Progressive Disclosure)

Load on demand:

- [DISCOVERY.md](references/DISCOVERY.md) — Deep dive on mDNS/ARP/TCP
  probing patterns, including a worked case study of hunting an
  IPv6-only SBC.
- [DEVICES.md](references/DEVICES.md) — The device inventory (ships as an
  example/template): hostnames, IPs, MACs, roles, SSH users, notes.
- [FIREWALL.md](references/FIREWALL.md) — ufw recipes, rule conventions,
  the LAN-scoped vs WAN-exposed decision.
- [TROUBLESHOOTING.md](references/TROUBLESHOOTING.md) — "host unreachable"
  decision tree, WoL gotchas, IPv6 vs IPv4 fallback logic.
- [TOOLS.md](references/TOOLS.md) — Per-tool reference (nmap, arping,
  avahi, ufw, etc.) with cross-distro install commands.

## Anti-Patterns (Don't Do This)

- ❌ `ping -c 1 host && echo "up"` — ICMP is unreliable (Rule 1).
- ❌ `getent hosts foo` as proof of aliveness — DNS lies (Rule 2).
- ❌ `nmap -sP 192.168.1.0/24` to find a device — `-sP` (now `-sn`) is
  ICMP+ARP and may miss firewalled hosts. Prefer `nmap -PR -PS22,80,443
  -sn <subnet>` or `scan-lan`.
- ❌ Editing `DEVICES.md` directly when adding a new device — use
  `home-net-learn` so the verification loop runs.
- ❌ Opening a port WAN-side without thinking — default to LAN-scoped
  unless you genuinely need off-LAN access. See FIREWALL.md.
- ❌ Putting passwords, API tokens, or private keys in `DEVICES.md` (or
  any reference file). The repo gets cloned across machines and your fork
  may be public — versioned secrets are permanent leaks. Route credentials
  to Bitwarden via the bitwarden-cli skill's self-destructing handoff
  recipe; put a *pointer* in DEVICES.md, not the value.

## Where this skill came from

Built out of a session-long hunt for an ARM SBC that turned out to be
IPv6-only, then offline, then back on Wi-Fi. The lessons about ICMP
unreliability, DNS-vs-mDNS, and self-verifying your own IPv6 state all
came from that hunt — see [DISCOVERY.md §6](references/DISCOVERY.md) for
the worked case study.
