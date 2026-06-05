# Bitwarden Secrets Manager — the `bws` CLI

> **This file is about `bws`, NOT `bw`.** They are different products (see the routing table at the top of `SKILL.md`). `bws` has no master password, no vault unlock, no secure notes, and no `BW_SESSION`. If you came here looking for password-vault operations, you want `SKILL.md`.

Verified against **`bws` 2.1.0** (binary `~/bin/bws`). Re-check the command surface with `bws <cmd> --help` after any upgrade — the CLI has changed argument shapes across majors.

## Contents

- [Mental model](#mental-model)
- [One-time setup (web UI)](#one-time-setup-web-ui)
- [Token storage patterns](#token-storage-patterns)
- [Command reference](#command-reference)
- [Helpers & ergonomics](#helpers--ergonomics)
- [`bws run` — runtime injection](#bws-run--runtime-injection)
- [Home Assistant: LLM API keys](#home-assistant-llm-api-keys)
- [Rotation](#rotation)
- [Errors](#errors)
- [This machine's config](#this-machines-config)

---

## Mental model

```
Bitwarden account
└── Secrets Manager (a product you enable, separate from the vault)
    ├── Project "home-assistant"        ← access boundary
    │   ├── Secret OPENAI_API_KEY = sk-…
    │   └── Secret ANTHROPIC_API_KEY = sk-ant-…
    └── Machine account "cachyos-desktop" ← non-human identity
        └── Access token 0.<id>.<secret>:<key>   ← the credential
            (granted read/write on project "home-assistant")
```

- A **machine account** is granted access to specific **projects**. It can read/write secrets only in those projects — never the whole Secrets Manager org, and never the `bw` vault.
- An **access token** authenticates *as* a machine account. One machine account can hold several tokens (that's how you rotate). The token is displayed **once** at creation; if lost, you issue a new one.
- Read vs read/write is set when you grant the machine account access to a project. **Creating secrets from the CLI requires write**; read-only is enough for `bws run` injection.

Contrast with `bw`: no master password, no lock/unlock, no TTY requirement. The token is a static bearer credential, so `bws` is automation-first — you can wire it into services, timers, and CI that have no human to type a passphrase.

## One-time setup (web UI)

Only a human can do these — there is no CLI to bootstrap a first token.

1. **vault.bitwarden.com → Secrets Manager** (product switcher, top of the page).
2. **Projects → New project** → name it (e.g. `home-assistant`).
3. **Machine accounts → New machine account** → name it per host (e.g. `cachyos-desktop`).
4. Open it → **Projects** tab → add the project with **Can read/write** (write needed for CLI secret creation; downgrade to read-only later if the host only consumes).
5. **Access tokens** tab → **New access token** → name + expiration (`Never` or a date) → copy the `0.<id>.<secret>:<key>` string shown **once**.
6. Hand the token to the CLI via [token storage](#token-storage-patterns) below — don't paste it into a chat or commit it.

## Token storage patterns

The token is the bootstrap secret: whatever runs `bws` unattended must read it in cleartext, so it can't be sealed inside Secrets Manager itself. Pick the storage that matches the consumer.

### A — 600 env file (interactive / scripts run as the user)

```bash
mkdir -p ~/.config/bws
read -rs 'tok?Paste bws access token: '       # hidden input, not in history
umask 177; print -r -- "BWS_ACCESS_TOKEN=$tok" > ~/.config/bws/token.env
unset tok; chmod 600 ~/.config/bws/token.env
```
Use it:
```bash
set -a; source ~/.config/bws/token.env; set +a
bws project list -o table
```

### B — systemd unit (services / timers)

For a service that should boot with secrets, **don't** export the token globally. Hand it to just that unit:

```ini
# ~/.config/systemd/user/<svc>.service  (drop-in or unit)
[Service]
EnvironmentFile=%h/.config/bws/token.env       # provides BWS_ACCESS_TOKEN
ExecStart=/home/komi/bin/bws run --project-id <PROJECT_ID> -- /path/to/real/program
```

Stronger: systemd **credentials** keep the token out of the process environment block (so it won't show in `/proc/<pid>/environ` of children):

```ini
[Service]
LoadCredential=bws-token:%h/.config/bws/token.env
ExecStart=/usr/bin/env BWS_ACCESS_TOKEN="$(cat ${CREDENTIALS_DIRECTORY}/bws-token)" \
          /home/komi/bin/bws run --project-id <PROJECT_ID> -- /path/to/real/program
```

### C — recovery copy in the `bw` vault

The 600 file is the *operational* copy. Keep a *recovery* copy as a `bw` secure note so a wiped `~/.config` isn't a lockout. This is the one place the two Bitwarden products cooperate — see the secure-note recipe in `SKILL.md`. Store the token in a **hidden** field (`type: 1`) and note which machine account + projects it maps to.

### What NOT to do

- ❌ `export BWS_ACCESS_TOKEN=…` in `~/.zshrc` — puts a bearer credential in a chezmoi-managed dotfile and every interactive shell's environment.
- ❌ Pass `--access-token 0.…` on a command line — lands in shell history and `ps` output.
- ❌ Commit `token.env` to chezmoi unencrypted. If you want it in chezmoi, age-encrypt it (`chezmoi add --encrypt`) — but per-host machine accounts are usually cleaner than syncing one token everywhere.

## Command reference

All commands need `BWS_ACCESS_TOKEN` in the environment (or `-t`). Add `-o env|table|json|yaml|tsv|none` to shape output.

| Goal | Command |
|---|---|
| List projects | `bws project list -o table` |
| Get a project | `bws project get <project-id>` |
| Create / edit / delete project | `bws project create <name>` · `bws project edit <id> …` · `bws project delete <id>` |
| List secrets (metadata) | `bws secret list -o table` |
| List secrets as `KEY=value` | `bws secret list -o env` |
| Get one secret (prints plaintext) | `bws secret get <secret-id>` |
| Create a secret | `bws secret create <KEY> <VALUE> <PROJECT_ID> [--note "…"]` |
| Edit / delete a secret | `bws secret edit <id> …` · `bws secret delete <id>` |
| Inject and run | `bws run --project-id <id> -- <command>` |

**Secret creation hygiene** (the value is positional → history):
```bash
read -rs 'val?Paste value: '
bws secret create ANTHROPIC_API_KEY "$val" 18f14ed9-8ba5-4cc6-bbd4-b45b01534270 --note "Claude API, HA conversation agent"
unset val
```
Secret **keys** become environment-variable names under `bws run`, so name them like env vars: `UPPER_SNAKE_CASE`, valid identifier characters only.

## Helpers & ergonomics

### `~/bin/bws-secret-add` — hygienic secret creation

`bws secret create <KEY> <VALUE> <PROJECT_ID>` takes the value as a positional arg, so typing it drops the plaintext into shell history. This wrapper reads the value hidden (TTY) or from a pipe, auto-loads the token from `~/.config/bws/token.env`, auto-resolves the project when only one is accessible, and strips the plaintext from the result:

```bash
bws-secret-add OPENAI_API_KEY                       # prompts hidden, picks the lone project
bws-secret-add ANTHROPIC_API_KEY <project-id> --note "Claude API, HA agent"
printf '%s' "$KEY" | bws-secret-add SOME_TOKEN      # non-interactive (CI / another script)
```

Project resolution order: the positional arg → `$BWS_PROJECT_ID` → the only project if exactly one is accessible. Output is metadata only (`id`/`key`/`projectId`/`creationDate`) — safe to show. Verified end-to-end against bws 2.1.0 (create + delete).

> The value still passes through `bws`'s own argv (bws 2.1.0 has no stdin input for the value), so it's momentarily visible to local `ps`/`/proc` for this user. The wrapper removes the *persistent* exposure (shell history + on-screen echo); the transient argv hop is unavoidable until upstream adds stdin input.

Lives at `~/bin/bws-secret-add` (scripts policy: `~/bin`, no extension, shebang).

### Shell completions

`bws` generates its own completion scripts (`bash`, `zsh`, `fish`, `elvish`, `powershell`):

```bash
bws completions zsh  > ~/.zsh/completions/_bws       # dir must be on $fpath BEFORE compinit
bws completions bash > ~/.local/share/bash-completion/completions/bws
```

⚠ This machine's zsh has a **strict zinit load order** (`zsh-completions` must precede `compinit` — see the zshrc "Zinit Plugin Load Order" notes). Drop `_bws` into a directory already on `$fpath` *before* `compinit` runs; don't bolt a late `compdef` into a turbo tier. If completions don't appear: `rm -f ~/.zcompdump* && exec zsh`.

### Optional: load the token into your shell (zsh function)

Mirrors the existing `bwu` helper for `bw`. Add it near `bwu` in `~/.zshrc` (the plain-function region, *after* the zinit block):

```bash
# Load the Bitwarden Secrets Manager token into this shell
bwsu() { set -a; source ~/.config/bws/token.env; set +a; bws project list -o table; }
```

Then run `bwsu` once per shell and plain `bws …` commands work for the session. Unlike `bw`, there's nothing to unlock — this only exports the static token.

## `bws run` — runtime injection

`bws run` fetches the accessible secrets, sets them as environment variables, and execs your command — the plaintext never touches disk.

```bash
bws run --project-id 18f14ed9-8ba5-4cc6-bbd4-b45b01534270 -- printenv OPENAI_API_KEY
bws run --project-id <id> -- python my_agent.py
```

Flags worth knowing:

- `--project-id <id>` — scope to one project. Without it, `bws run` injects every secret the token can reach (collisions across projects are possible — prefer scoping).
- `--no-inherit-env` — start from a clean environment containing only the injected secrets (good for reproducible/CI runs).
- `--uuids-as-keynames` — name the vars after secret UUIDs instead of keys (rarely what you want; only when keys aren't valid identifiers).
- `--shell <shell>` — run the command string through a shell instead of exec'ing it directly.

Mental note: the consuming program reads `os.environ["OPENAI_API_KEY"]` (or the framework's env mechanism). `bws run` is a *wrapper around process launch* — it can only inject into processes **it starts**.

## Home Assistant: LLM API keys

The driving use case on this machine: keep OpenAI/Anthropic/etc. keys in the `home-assistant` project and feed them to HA instead of hardcoding in `configuration.yaml` / `secrets.yaml`. The right mechanism depends on **how HA runs** — confirm topology first (this box vs a separate host; bare process vs Docker vs HA OS appliance).

HA can read environment variables in YAML:
```yaml
# configuration.yaml — HA expands env vars referenced this way
conversation:
  # ...
openai_conversation:
  api_key: !env_var OPENAI_API_KEY
```

### Pattern 1 — HA Core as a systemd service on *this* machine

Wrap HA's launch in `bws run` so the keys exist only inside the HA process:
```ini
[Service]
EnvironmentFile=%h/.config/bws/token.env
ExecStart=/home/komi/bin/bws run --project-id 18f14ed9-8ba5-4cc6-bbd4-b45b01534270 -- \
          /srv/homeassistant/bin/hass -c /home/komi/.homeassistant
```
HA's `!env_var OPENAI_API_KEY` then resolves. Rotating a key in Secrets Manager + restarting the unit is the whole update path — nothing on disk to edit.

### Pattern 2 — HA in Docker / Podman

Inject at container start:
```bash
bws run --project-id <id> -- \
  docker run --rm -e OPENAI_API_KEY -e ANTHROPIC_API_KEY ghcr.io/home-assistant/home-assistant:stable
```
`-e VAR` with no value passes the variable through from the (bws-injected) environment. Or render an `--env-file` from `bws secret list -o env` immediately before `docker run` and delete it after.

### Pattern 3 — HA OS / Supervised appliance (separate host)

You can't wrap the HA process on an appliance, and `bws` on *this* desktop can't inject into a process on *another* host. Options:
- Run `bws` **on the HA host** with its own machine account + token, on a timer that writes `secrets.yaml` from `bws secret list -o env` (reformatted to HA's `key: value`), then reloads HA. The token still lives on the HA host — Secrets Manager centralizes management and rotation, not on-host storage.
- Or treat HA's native `secrets.yaml` as the source of truth and use Secrets Manager only as the backup/rotation registry.

> Don't assume Pattern 1. Ask which topology applies before wiring anything — the injection mechanism is entirely different per case, and a desktop `bws` cannot reach a separate HA box's process.

## Rotation

1. Web UI → machine account → **Access tokens → New access token** (keep the old one alive briefly).
2. Update `~/.config/bws/token.env` (Pattern A snippet) and the `bw` recovery note.
3. Restart any service whose `EnvironmentFile`/`LoadCredential` carried the old token.
4. Verify with `bws project list`, then **revoke the old token** in the web UI.
5. Rotating a *secret's value* (e.g. a leaked API key) is independent: `bws secret edit <id>` with the new value, then restart consumers.

## Errors

| Symptom | Likely cause | Fix |
|---|---|---|
| `401` / `Access token is not valid` / `invalid` | Token mistyped, truncated, expired, or revoked | Re-copy from web UI; reissue if expired/revoked; confirm `~/.config/bws/token.env` has the full `0.<id>.<secret>:<key>` |
| `Received error message from server` / access denied on a project | Machine account not granted that project (or read-only when you need write) | Web UI → machine account → Projects → add/upgrade the grant |
| `bws run` injects nothing | Wrong `--project-id`, or token has no read access to it | `bws project list` to confirm the ID and that the token can see it |
| `bws secret create` fails with permission error | Project grant is read-only | Upgrade to read/write in the web UI |
| Variable absent inside the wrapped program | Secret key isn't a valid env-var name, or program reads a different name | Rename the secret to `UPPER_SNAKE_CASE`; confirm the program's expected var |
| Token works from your shell but not from a service | Service didn't load the token | Add `EnvironmentFile=`/`LoadCredential=`; remember user services don't inherit your interactive env |

## This machine's config

Snapshot (verified 2026-05-31 — re-derive with `bws project list` if in doubt):

| Item | Value |
|---|---|
| Binary | `~/bin/bws` (v2.1.0) |
| Token file | `~/.config/bws/token.env` (mode 600, `BWS_ACCESS_TOKEN=…`) |
| Projects | `home-assistant` = `18f14ed9-8ba5-4cc6-bbd4-b45b01534270`<br>`system` = `42bc5902-a0d6-43f4-b832-b460000651e5` (misc/general env-injectable keys, created 2026-06-05) |
| Machine account | this desktop (read/write on `home-assistant`) |
| `bws config` | default (`~/.config/bws/config`); server is Bitwarden cloud — no overrides set |
| Driving use case | LLM API keys (OpenAI/Anthropic/…) for Home Assistant |
