# home-network-skill

A Claude Code skill + script bundle for managing a home LAN — discovery,
troubleshooting, firewall recipes, and a curated device inventory. Designed
to be portable across Linux machines with graceful degradation when expected
tools aren't installed.

## What's in here

```
.claude-plugin/plugin.json       Claude Code plugin manifest
skills/home-network/
  SKILL.md                       Strategy + decision tree (auto-loads into Claude)
  references/
    DISCOVERY.md                 mDNS / ARP / TCP probe playbook
    DEVICES.md                   Device inventory (example/template — fill with your own)
    FIREWALL.md                  ufw recipes and conventions
    TROUBLESHOOTING.md           "host unreachable" decision tree
    TOOLS.md                     Per-tool reference + cross-distro install
scripts/
  home-net-doctor                Audit available networking tools on this host
  scan-lan                       Discovery sweep (mDNS + ARP + TCP fallback)
  find-host                      Resolve a name via DNS → mDNS → ARP fallback chain
  port-check                     TCP fanout port check
  wol                            Wake-on-LAN by device alias or MAC
  home-net-learn                 AGENTIC: probe a new device, draft entry,
                                 fire background verifier, merge on pass
install.sh                       Bootstrap on any machine
```

## Install

### Option A — Claude Code plugin (preferred)

```bash
# inside Claude Code (or via CLI)
claude plugin install https://github.com/your-username/claude-skills
```

Skill auto-activates on networking-related prompts.

### Option B — manual

```bash
git clone git@github.com:your-username/claude-skills.git ~/repos/claude-skills
~/repos/claude-skills/install.sh
```

`install.sh` (monorepo-wide) does:
- Symlinks each plugin's `scripts/` into `~/bin/` (backs up any real file to `.bak`)
- Symlinks each `skills/<name>/` into `~/.claude/skills/`
- Bundles per-plugin hooks into `~/.claude/hooks/` and enables the autosync watcher
- Runs `home-net-doctor` to report tool availability — installs no packages

## Tool dependencies

Detected, never auto-installed. `home-net-doctor` reports what's available
and shows install commands per distro.

| Required for | Tool | Arch/CachyOS | Debian/Ubuntu | macOS |
|--------------|------|--------------|---------------|-------|
| mDNS discovery | `avahi-utils` | `pacman -S avahi nss-mdns` | `apt install avahi-utils libnss-mdns` | built-in (`dns-sd`) |
| ARP probes | `arping` | `pacman -S iputils` | `apt install iputils-arping` | `brew install arping` |
| Port scans (advanced) | `nmap` | `pacman -S nmap` | `apt install nmap` | `brew install nmap` |
| Packet capture | `termshark` or `tcpdump` | `pacman -S termshark` | `apt install termshark` | `brew install termshark` |
| Firewall | `ufw` | `pacman -S ufw` | preinstalled | n/a (use pf) |
| Wake-on-LAN | `wakeonlan` or `etherwake` | `yay -S wakeonlan` (AUR) | `apt install wakeonlan` | `brew install wakeonlan` |

Pure-bash fallbacks exist for the most basic operations (TCP probes via
`/dev/tcp`, ARP cache via `/proc/net/arp`), so the skill is still useful on
a minimal install.

## Self-healing learn loop

The big experiment in this skill: `home-net-learn` doesn't block your shell.

```bash
home-net-learn sbc.local             # probes by hostname
home-net-learn 192.168.1.10          # probes by IP
home-net-learn                       # interactive: scan + pick from results
```

What happens:
1. Foreground (fast): probe the device, gather facts, write `DEVICES.draft.md`
2. Background: spawn `claude -p` agent that
   - re-verifies findings against live network
   - looks up MAC OUI
   - cross-references hostname for collisions
   - infers device role from open ports + mDNS services
3. On pass: agent commits to `DEVICES.md` + git commits
4. On fail: agent writes `DEVICES.draft.review.md` for you to look at
5. `notify-send` fires either way

The skill grows over time without slowing your active work.

## Privacy posture

`DEVICES.md` ships as **example/template data only** — clearly-synthetic
devices on the example `192.168.1.0/24` LAN. As you use the skill, it
fills with your own device-specific data (MACs, hostnames, SSH users) as
**plaintext**. If you fork this repo, keep your real inventory out of a
public remote: move sensitive entries to `DEVICES.local.md` (add it to
`.gitignore`) and keep only the example template tracked.

Never commit secrets (passwords, API tokens, private keys) to any
reference file — route them through the bitwarden-cli skill and store
only a pointer in `DEVICES.md`.

## License

MIT
