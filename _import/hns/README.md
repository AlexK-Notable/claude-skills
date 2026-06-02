# komi-home-toolkit

A Claude Code plugin marketplace bundling two cooperating skills for personal home infrastructure:

| Plugin | What it does |
|--------|--------------|
| **[home-network](plugins/home-network/README.md)** | LAN discovery, troubleshooting, firewall recipes, and a self-updating device inventory that grows via background `claude -p` agents |
| **[bitwarden-cli](plugins/bitwarden-cli/README.md)** | Patterns for using the Bitwarden CLI — secure note creation, secret routing, the self-destructing handoff script pattern |

They're packaged together because they routinely cooperate: during a network onboarding session, you discover credentials (default passwords, API tokens, vault recovery codes) that should land in Bitwarden rather than in any reference file. The `home-network` skill's Knowledge Capture Protocol explicitly routes secrets to the `bitwarden-cli` skill's self-destructing handoff recipe.

## Install

### As a marketplace (recommended — gives you both plugins to pick from)

```bash
# inside Claude Code:
/plugin marketplace add https://github.com/AlexK-Notable/home-network-skill
/plugin install home-network
/plugin install bitwarden-cli
```

Or just install whichever subset you want. Plugins can be installed independently.

### Direct git clone (for hacking on the plugins)

```bash
git clone git@github.com:AlexK-Notable/home-network-skill.git ~/repos/home-network-skill

# For the home-network plugin: symlinks scripts into ~/bin/ + the skill into ~/.claude/skills/
~/repos/home-network-skill/plugins/home-network/install.sh
```

The `bitwarden-cli` plugin is documentation-only (no scripts), so no install step is needed beyond cloning — the SKILL.md auto-discovers when the plugin is loaded.

## Cross-plugin workflow

The canonical example: changing a default factory password on a newly-onboarded device.

1. `/home-network onboard the new SBC at 192.168.1.221` — the skill helps you SSH in, sets up key auth, etc.
2. During the session, you discover the factory password is `bred/bred` and want to change it.
3. The skill's anti-pattern rule: **don't put the new password in `DEVICES.md`**.
4. Instead, follow the **Knowledge Capture Protocol → Secret discovered** row, which points at the `bitwarden-cli` skill's **Self-destructing handoff script** recipe.
5. Claude generates a strong password with `bw generate`, sets it on the device via `chpasswd`, stashes it in `/tmp/secret-XXX`, and writes a wrapper script that you fire from your unlocked shell.
6. The wrapper creates a Bitwarden secure note and shreds both files.
7. `DEVICES.md` gets a *pointer*: "Password stored in Bitwarden as `<item name>`. Key auth via `~/.ssh/id_ed25519`."

This whole flow is described in both skills' SKILL.md files, with the same recipe referenced from both sides.

## Repository layout

```
.claude-plugin/
  marketplace.json              ← lists both plugins for the Claude plugin system
plugins/
  home-network/
    .claude-plugin/plugin.json
    skills/home-network/{SKILL.md, references/}
    scripts/{home-net-doctor, scan-lan, find-host, port-check, wol,
             home-net-learn, home-net-capture}
    install.sh                  ← optional ~/bin + ~/.claude/skills symlink helper
    README.md
  bitwarden-cli/
    .claude-plugin/plugin.json
    skills/bitwarden-cli/{SKILL.md, references/}
    README.md
README.md                       ← this file
```

## Why a marketplace and not one plugin

Each skill has a distinct lifecycle. The `home-network` skill mutates frequently (every `home-net-capture` or `home-net-learn` invocation can produce a commit). The `bitwarden-cli` skill is more stable. Packaging them as separate plugins under one marketplace lets:
- Either be installed independently if a user wants only one
- Each evolve at its own pace with independent semver
- Future skills (3D printer / Klipper, smart-home / Matter, etc.) be added to the marketplace without disrupting either current plugin

## License

MIT
