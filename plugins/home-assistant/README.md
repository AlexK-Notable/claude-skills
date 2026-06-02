# home-assistant

Operate the user's self-hosted Home Assistant (HA in Docker on the Nova,
`192.168.1.229:8123`) safely, and remember what we learn.

Two channels, split by volatility:

- **Inventory (deterministic, no LLM)** — `ha-inventory` reads the *safe* `.storage`
  registry files over SSH+sudo and regenerates a secret-safe markdown snapshot of
  installed state (integrations, HACS, areas, devices, the controllable entity
  surface, automations). It field-allowlists `core.config_entries` so tokens never
  leave the box. `ha-inventory --check` content-hashes HA's registry files to detect
  drift — including changes you made in the HA web UI — and exits `0` (fresh) / `2`
  (drift) / `1` (error).
- **Wisdom (lean, append-only)** — `ha-note` atomically appends one structured,
  provenance-stamped gotcha (status / HA-version / cause / fix / repro / applies-when)
  to `GOTCHAS.journal.md`. No LLM rewrites the journal; well-worn entries are promoted
  to the curated `GOTCHAS.md` by hand.

## CLIs (symlinked to `~/bin` by the repo `install.sh`)

| Command | Purpose |
|---|---|
| `ha-inventory` | regenerate the inventory snapshot |
| `ha-inventory --check` / `--diff` | drift check (run before any mutating action) |
| `ha-note "…" --fix … --repro …` | capture one gotcha |
| `ha-note --list` / `--selftest` | read the journal / verify the capture path |

## Layout

```
scripts/ha-inventory, ha-note        CLIs (→ ~/bin)
skills/home-assistant/
  SKILL.md                           strategy: safe-mutation discipline, decision tree, capture checklist
  config.sh                          the ONE HA-specific seam (host, paths) — adapter point for future reuse
  references/
    TOPOLOGY.md                      hosts, services, access, HA version, secrets pointers
    CAPABILITY-MAP.md                what's changeable by file/API vs UI-only
    STORAGE-SCHEMA.md                .storage file map + the stop→backup→edit→start procedure
    ASSIST.md                        voice pipeline, sentence triggers, exposed entities
    GOTCHAS.md                       curated lessons (seeded from the buildout)
    GOTCHAS.journal.md               append-only capture target (created on first ha-note)
    INVENTORY.generated.md           generated snapshot — DO NOT hand-edit
```

## Notes

- **v1 introspection is SSH+sudo file reads**, not the HA API. The clean v2 upgrade
  (admin long-lived token → bws `HA_TOKEN`, WebSocket `config_entries/get` which is
  secret-safe by construction, remote/no-sudo) is described in TOPOLOGY.md.
- No event hooks ship in v1 (deliberate — see the design history). Staleness is
  surfaced on demand via `ha-inventory --check`, per the capture discipline in SKILL.md.
- Secrets never enter tracked files; route them through the `bitwarden-cli` plugin.
