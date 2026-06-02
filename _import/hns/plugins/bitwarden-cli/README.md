# bitwarden-cli plugin

Patterns and recipes for using the [Bitwarden CLI](https://bitwarden.com/help/cli/) (`bw`) effectively from Claude Code sessions.

## What this gives you

A skill (`bitwarden-cli`) that auto-activates whenever you mention:
- Bitwarden, `bw`, the vault, secure notes
- Storing credentials, API tokens, recovery codes, key material
- The master-password unlock dance
- The "vault is locked" / "invalid_grant" failure modes

## Reference scope

The main SKILL.md covers:
- The three lifecycle phases (logged out / locked / unlocked) and how to navigate them
- **Recipe: Create a secure note** — the canonical pattern for storing a one-time secret
- **Recipe: Self-destructing handoff script** — for when another process (Claude, automation, CI) generates a secret but only the user can unlock the vault
- Reading items, common errors, transcript hygiene

Reference docs (loaded on demand):
- `references/item-schema.md` — full item type table + JSON templates per type
- `references/scripting.md` — builder script template, session lifecycle helpers, pipeline patterns
- `references/troubleshooting.md` — error catalog with root causes + recovery
- `references/ssh-keys.md` — item type 5 (sshKey) + Bitwarden SSH Agent integration

## How this companions with `home-network`

The two plugins in this marketplace cooperate when you discover credentials during a network onboarding session. The home-network skill's Knowledge Capture Protocol explicitly routes secrets to Bitwarden (not docs) via this skill's self-destructing handoff recipe. See the marketplace root README for the cross-plugin workflow.

## Install

Via the marketplace:
```bash
# inside Claude Code:
/plugin marketplace add https://github.com/AlexK-Notable/home-network-skill
/plugin install bitwarden-cli
```

## License

MIT
