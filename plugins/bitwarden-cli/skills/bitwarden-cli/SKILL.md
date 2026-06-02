---
name: bitwarden-cli
description: Covers BOTH Bitwarden CLIs — they are DIFFERENT products, disambiguate first. (1) `bw`, the password-vault CLI — master-password unlock to a BW_SESSION, storing/retrieving credentials, secure notes for backups (age keys, API tokens, recovery codes, fingerprints), scripted vault lookups, auth errors (vault is locked, invalid_grant). (2) `bws`, the Secrets Manager CLI — machine-account access token (BWS_ACCESS_TOKEN, no master password), projects + secrets, creating/reading secrets, and runtime injection via `bws run` (e.g. feeding LLM API keys into Home Assistant). Triggers on bitwarden, bw, bws, secrets manager, secure note, password vault, BW_SESSION, BWS_ACCESS_TOKEN, machine account, bws run/project/secret, "store/back up to bitwarden", rotate credential, or alexkechichian1@gmail.com in a vault context. Route bw vs bws before following any recipe.
---

# Bitwarden CLI

## ⚠ First: `bw` and `bws` are different products — route before you act

Bitwarden ships **two separate CLIs**. They share a brand and almost nothing else — different binary, auth model, data model, and use case. Decide which one the task needs *before* following any recipe below.

| If the task involves… | Product | Binary | Auth | Where to read |
|---|---|---|---|---|
| Personal credentials, **secure notes**, backups, master password, vault unlock, `BW_SESSION`, `invalid_grant` | Password Manager | `bw` | master password → `BW_SESSION` (needs the user's TTY) | the rest of this file ↓ |
| **Machine secrets**, `BWS_ACCESS_TOKEN`, projects, `bws run`, injecting API keys into apps / services / CI | Secrets Manager | `bws` | machine-account **access token** (non-interactive) | [Secrets Manager — the `bws` CLI](#secrets-manager--the-bws-cli) + [references/secrets-manager.md](references/secrets-manager.md) |

**Rule of thumb:** `bw` = *your* passwords (human, interactive). `bws` = *machines'* secrets (automation, injected at runtime). A `bws` access token is **not** a vault login — it cannot read secure notes; a `bw` session **cannot** read Secrets Manager projects. Their commands never mix, and a credential for one is useless to the other.

## This machine

Both CLIs are installed here:

- **`bw`** (password vault, v2026.x via Arch) — logged in as `alexkechichian1@gmail.com`. Primary use: **storing secure notes** (backups, recovery instructions, key material, fingerprints); secondary: reading credentials, scripted lookups.
- **`bws`** 2.1.0 (Secrets Manager, binary `~/bin/bws`) — configured 2026-05-31. Token at `~/.config/bws/token.env` (mode 600). Project `home-assistant` = `18f14ed9-8ba5-4cc6-bbd4-b45b01534270`. Driving use case: **LLM API keys for Home Assistant**.

Everything from here to the Secrets Manager section is the **`bw` vault**. For `bws`, jump to [Secrets Manager — the `bws` CLI](#secrets-manager--the-bws-cli).

## Mental Model

Three lifecycle phases:

| Phase | State | How to reach it | How to leave |
|---|---|---|---|
| **Logged out** | No vault info on disk | `bw login` (interactive: email + master password [+ 2FA]) | `bw logout` |
| **Locked** | Vault metadata cached, content encrypted at rest | After login or after `bw lock`. Persists across reboots. | `bw unlock` |
| **Unlocked** | Session token issued, can read/write items | `bw unlock --raw` returns session token | `bw lock`, expiry, or session-token unset |

The **session token** (`BW_SESSION`) is what authorizes operations. It's exported into the environment, used by subsequent `bw` calls, and should be unset + the vault re-locked when done.

```
bw login            # → logged out → locked
bw unlock --raw     # → locked → unlocked (prints session token)
bw lock             # → unlocked → locked
bw logout           # → any state → logged out
```

`bw status` shows the current phase + last-sync time + user email. Run it any time you're unsure.

## Why this skill exists

Bitwarden CLI is **not friendly to one-shot scripting**:

1. Auth state can go stale server-side without warning — past sessions saw `invalid_grant` errors months after last sync (need `bw logout && bw login` to recover).
2. `bw unlock` requires a TTY for the password prompt — Claude's Bash tool has no TTY, so the **user must run unlock themselves** in their terminal. We can never invoke `bw unlock` from a Bash tool call and expect it to work.
3. Item creation expects base64-encoded JSON via `bw encode | bw create item` — non-obvious pipeline.
4. Decrypted item contents (including secrets) appear in tool output when you `get` or `create` — transcript hygiene matters.

This skill encodes the patterns that work and the failure modes to anticipate.

## Decision Tree

| Goal | Approach |
|---|---|
| Save a one-time secure note (key, token, instructions) | Build JSON → `bw encode \| bw create item` — see [Recipe: Create a secure note](#recipe-create-a-secure-note) below |
| Look up a credential by name | `bw list items --search "<term>" \| jq '...'` |
| Read full item by ID | `bw get item <id>` (returns JSON; or `bw get password <id>` for just the password field) |
| Update an existing item | `bw get item <id> \| jq '.<field> = "<value>"' \| bw encode \| bw edit item <id>` |
| Delete an item | `bw delete item <id>` (soft delete to Trash by default; `--permanent` to skip Trash) |
| Generate a strong password | `bw generate --length 32 --uppercase --lowercase --number --special` |
| Verify auth state | `bw status` |
| Sync local cache with server | `bw sync` |
| Store an SSH key in the vault | Item type `5` (`sshKey`) — see [references/ssh-keys.md](references/ssh-keys.md) |
| Restore an SSH key on a new machine | `bw get item <name> \| jq -r '.sshKey.privateKey' > ~/.ssh/<name>` — see [references/ssh-keys.md](references/ssh-keys.md) |

## Auth Patterns

### Pattern A — Single-operation one-liner (typical case)

For one-shot ops, wrap the whole thing so unlock + work + lock all happen in one user-invoked command:

```bash
export BW_SESSION="$(bw unlock --raw)" && \
  <your-bw-operation-here> && \
  unset BW_SESSION && \
  bw lock
```

`bw unlock --raw` prompts the user for the master password on their TTY, then returns ONLY the session token (no decorative output). The shell captures it. Then `unset` + `bw lock` clean up afterward.

**Critical:** this is the pattern you give the user to run — NOT the pattern you run yourself via Bash tool. Because Bash tool has no TTY, the password prompt fails silently.

### Pattern B — Multi-operation session (user already unlocked)

If the user has already unlocked their vault and exported `BW_SESSION` in their shell, subsequent commands can be plain `bw <op>` calls in their terminal. Useful for "do a few things in a row" workflows.

Tell the user upfront: "Unlock once with `export BW_SESSION=\"$(bw unlock --raw)\"`, then I'll send you the operations." After the operations, they run `unset BW_SESSION && bw lock`.

### Pattern C — Builder script for secrets

When the JSON payload contains secrets (key files, tokens), **build the payload from disk at runtime** rather than embedding it inline. A Python builder script reads `~/.config/<secret-path>` and emits JSON; the secret never lives standalone in a /tmp file.

Pattern (see [references/scripting.md](references/scripting.md) for the full template):

```bash
# Builder script reads secret file at runtime, emits JSON to stdout
python3 /tmp/build_note.py | bw encode | bw create item
```

The script gets shredded after use: `shred -u /tmp/build_note.py`.

## Recipe: Create a secure note

The primary use case. Three parts: build JSON template, hand the user a one-liner that pipes it through bw, clean up.

### 1. Build the JSON (Python heredoc or `/tmp` script)

Schema for secure notes (`type: 2`):

```json
{
  "type": 2,
  "name": "Note name — host/context",
  "notes": "Markdown-friendly body. Newlines as \\n in JSON.",
  "secureNote": {"type": 0},
  "folderId": null,
  "organizationId": null,
  "favorite": false,
  "fields": [
    {"name": "field_label", "value": "field_value", "type": 0}
  ]
}
```

`fields[].type`: `0`=text, `1`=hidden (masked in UI), `2`=boolean, `3`=linked. Use `1` for fingerprints/keys you want masked by default in the Bitwarden UI.

See [references/item-schema.md](references/item-schema.md) for all item types and fields.

### 2. The pipeline

```bash
export BW_SESSION="$(bw unlock --raw)" && \
  <command-that-outputs-the-json> | bw encode | bw create item && \
  unset BW_SESSION && \
  bw lock
```

`<command-that-outputs-the-json>` is either:
- A short heredoc: `cat <<'EOF'\n{...json...}\nEOF`
- A Python one-liner: `python3 -c "import json; print(json.dumps({...}))"`
- A `/tmp` builder script for anything involving secrets read from disk

### 3. Confirm + cleanup

`bw create item` returns the created item's JSON on success — including a UUID `id` field. **The decrypted notes/fields appear in this output**, which is fine for non-secret operations but means **don't paste the output back into a chat or screenshare if the note contains secrets**.

To verify without re-exposing secrets:
```bash
export BW_SESSION="$(bw unlock --raw)" && \
  bw list items --search "<note name>" | jq '.[] | {id, name, fields: .fields}' && \
  unset BW_SESSION && bw lock
```
`jq` omits the `notes` field; you see metadata only.

## Recipe: Self-destructing handoff script

When **another tool generates the content** (a Claude Code session, another script, a CI job) but **only the user can unlock the vault**, you can't use Pattern A — your generator process won't see the user's `BW_SESSION`. The clean solution is a two-file handoff: the generator writes a secret stash to `/tmp` plus a small wrapper script. The user fires the wrapper one-shot from their unlocked shell; both files self-destruct on success.

### When to use this vs Pattern A

| Pattern | When |
|---|---|
| **A (one-liner)** | The secret originates in the user's own shell context — they can run unlock + write + lock in one command |
| **Self-destructing handoff** | The secret was generated by another process (Claude, automation, CI) and needs to land in the user's vault, but only the user holds the master password |

### The template

The generator (Claude, or whatever produced the secret) writes two files:

1. **The stash** — `/tmp/<secret-name>-<pid>` (mode 600) containing only the raw secret value.
2. **The wrapper** — `/tmp/<wrapper-name>` (chmod +x) implementing the pattern below.

```bash
#!/usr/bin/env bash
# Self-destructing handoff: read SECRET_FILE, create bw item, shred both files.
set -euo pipefail

SECRET_FILE="/tmp/<stash-name>"
SELF="$0"

cleanup() {
  for f in "$SECRET_FILE" "$SELF"; do
    [[ -f "$f" ]] && (shred -u "$f" 2>/dev/null || rm -f "$f")
  done
}
trap cleanup EXIT

# Preflight: vault unlocked in THIS shell?
if ! bw status 2>/dev/null | grep -q '"status":"unlocked"'; then
  echo "✗ Vault locked. Unlock + retry:"
  echo "    export BW_SESSION=\"\$(bw unlock --raw)\" && $SELF"
  trap - EXIT  # preserve files so the user can re-run after unlocking
  exit 1
fi

# Preflight: stash present + non-empty?
[[ -r "$SECRET_FILE" ]] || { echo "✗ Stash $SECRET_FILE missing"; exit 1; }
SECRET=$(cat "$SECRET_FILE")
[[ -n "$SECRET" ]] || { echo "✗ Stash empty"; exit 1; }

# Build + create + metadata-only output (jq strips secrets from scrollback)
jq -n --arg s "$SECRET" '{
  type: 2,
  name: "<descriptive name>",
  notes: "<context: where the secret came from, when, what depends on it>",
  secureNote: {type: 0},
  favorite: false,
  fields: [
    {name: "<label>", value: $s, type: 1}
  ]
}' | bw encode | bw create item \
   | jq '{id, name, type, created: .creationDate, fields: [.fields[] | {name, type}]}'

echo "✓ stored in vault; self-destructing"
```

The user just fires `/tmp/<wrapper-name>`. The script either succeeds (note created, both files shredded, metadata printed) or exits cleanly on a locked vault (preserving files so they can `bw unlock` and retry).

### Why two files instead of one

Inlining the secret into the wrapper would put it in the user's shell history when they press ↑ to retry. Two files keep history clean: only the wrapper's pathname shows, never the secret value.

### Why `trap cleanup EXIT` plus `trap - EXIT` for retry

The unconditional `trap cleanup EXIT` guarantees both files get shredded whether the script succeeds, errors out, or is signalled — no cleanup branches scattered through the code.

The `trap - EXIT` inside the locked-vault branch explicitly disables that cleanup for the one case where keeping the files is correct: the user just needs to unlock and re-run. Without the explicit cancel, a retry-able failure would consume the stash.

### Why metadata-only output

`bw create item` prints the entire created item as JSON — including the decrypted secret. Piping through `jq '{id, name, type, created, fields: [.fields[] | {name, type}]}'` extracts only the field labels and types, never the values. Safe to leave in the user's scrollback; safe to paste back into a chat for confirmation.

### Variants worth knowing

- **Login item instead of secure note**: change `type: 2` → `type: 1`, replace `secureNote` with `login: {username: "...", password: $s, uris: [{uri: "...", match: null}]}`. See [references/item-schema.md](references/item-schema.md).
- **SSH key item**: change `type: 5`, see [references/ssh-keys.md](references/ssh-keys.md). Useful for the "we just generated a new keypair on a remote machine, save the private key in the vault" case.
- **Multi-secret stash**: write multiple `/tmp/<name>-*` files; loop over them inside the wrapper to create multiple items in one user invocation.

## Reading items

```bash
# All items matching a search term, metadata only
bw list items --search "<term>" | jq '.[] | {id, name, type}'

# Get one item by ID, full JSON
bw get item <uuid>

# Get just the password from a login item
bw get password <name-or-id>

# Get just the secure-note body
bw get notes <name-or-id>

# Get a specific custom field
bw get item <id> | jq '.fields[] | select(.name=="<field>") | .value'
```

All of these require `BW_SESSION` exported.

## Common Errors

Quick reference; full diagnoses in [references/troubleshooting.md](references/troubleshooting.md).

| Error | Likely cause | Fix |
|---|---|---|
| `Vault is locked.` | No `BW_SESSION` set | `export BW_SESSION="$(bw unlock --raw)"` |
| `invalid_grant` + `Unable to fetch ServerConfig` | Stale auth token, vault hasn't synced in a long time | `bw logout && bw login` |
| `Master password unlock data was not found` | Same as above — server invalidated session | `bw logout && bw login` |
| `Item already exists` on create | Duplicate by name in same folder | Use a more specific name, or `bw edit item <id>` to update |
| `Cannot read property 'X' of undefined` | Malformed JSON sent to `bw create item` | Validate JSON with `jq '.' <<<"$payload"` first |
| `bw sync` not picking up new items | Local cache stale | `bw sync --force` |

## Safety / Transcript Hygiene

- **Don't paste the output of `bw get`, `bw create item`, or `bw edit item` into chats** if the item contains secrets — the decrypted content shows up in the response.
- **Builder scripts in /tmp must be shredded after use**: `shred -u /tmp/<script>`. Even if the script doesn't embed secrets directly, treat any code that touched secrets as hot.
- **Never log `BW_SESSION`**: it's a bearer token for the duration of the unlock. Use `unset` + `bw lock` to retire it.
- **Master password never appears in scripts** — `bw unlock --raw` prompts the user interactively for it; the password never round-trips through your code.
- **Repo context matters**: a "leaked" Wallhaven API key in a private repo with one collaborator has a very different threat profile than a leaked AWS root key in any context. See `project_variety_api_keys_low_risk.md` in memory — broad-net secret scanners can't differentiate; user-driven threat modeling can.

## Proactive Recommendations

- **Always run `bw status` first** before any bw operation if you're not sure of state. It's free and avoids the "unlock prompt that silently fails" trap.
- **For frequent use, suggest a shell function** in `~/.zshrc`:
  ```bash
  bw-do() {
      export BW_SESSION="$(bw unlock --raw)" && "$@"
      unset BW_SESSION && bw lock
  }
  # Usage: bw-do bw list items --search foo
  ```
  This bundles the unlock-do-lock dance into one verb.
- **If the user mentions storing something larger (file, multi-line key)** — secure notes are the right item type (`type: 2`), not custom fields. Custom fields cap at ~1KB; notes have no practical limit.
- **If the user has many small items going in** — consider creating a folder first (`bw create folder`) so they're grouped in the UI.

---

## Secrets Manager — the `bws` CLI

> **Different product from everything above.** The `bw` lifecycle (login/lock/unlock, master password, `BW_SESSION`, secure notes, `bw encode | bw create item`) **does not apply here.** If the task is `bws`, this section + **[references/secrets-manager.md](references/secrets-manager.md)** are your sources; ignore the `bw` recipes.

### Mental model

| `bws` concept | What it is |
|---|---|
| **Machine account** | A non-human identity (older docs say "service account"). What the token authenticates *as*. |
| **Project** | The access boundary. A machine account can see secrets **only** in projects it's been granted. |
| **Access token** | The credential, format `0.<id>.<secret>:<key>`, shown **once** at creation. It *is* the identity — guard it like a password. |
| **Secret** | A `KEY` / `value` pair that lives inside a project. |

Unlike `bw`, there is **no logged-out/locked/unlocked lifecycle and no master password.** The token is static and non-interactive — which is exactly why `bws` *is* friendly to one-shot scripting (the inverse of `bw`'s TTY problem). An agent may run `bws` directly via the Bash tool **provided the token is in its environment**.

### Auth & token storage (this machine)

- The token reaches `bws` **only** via `BWS_ACCESS_TOKEN` (env) or `--access-token`. **`bws config` does NOT store the token** — its only keys are `server-base` / `server-api` / `server-identity` / `state-dir` / `state-opt-out`.
- Operational copy: **`~/.config/bws/token.env`**, mode 600, one line: `BWS_ACCESS_TOKEN=0.…`
- Load it for a shell/op, then verify auth:
  ```bash
  set -a; source ~/.config/bws/token.env; set +a
  bws project list -o table
  ```
- **Bootstrap-secret caveat:** the token must exist in readable form for unattended use, so it can't be sealed inside the vault it bootstraps. Keep a **recovery copy as a `bw` secure note** — operational copy in the 600 file, recovery copy master-password-protected. (Use the secure-note recipe above; this is the one place the two products usefully meet.)

### Core commands (bws 2.1.0)

| Goal | Command |
|---|---|
| List projects (find a project ID) | `bws project list -o table` |
| List secrets, metadata | `bws secret list -o table` |
| Dump secrets as `KEY=value` | `bws secret list -o env` |
| Read one secret | `bws secret get <secret-id>` |
| **Create** a secret | `bws secret create <KEY> <VALUE> <PROJECT_ID>` |
| Run a command with a project's secrets injected as env vars | `bws run --project-id <id> -- <command>` |

Default output is JSON; `-o` accepts `json`, `yaml`, `env`, `table`, `tsv`, `none`.

### Hygiene (bws-specific)

- **`bws secret create` takes the value as a positional arg → it lands in shell history.** Easiest safe path is the wrapper **`~/bin/bws-secret-add KEY [PROJECT_ID]`** (reads the value hidden, auto-loads the token, auto-resolves the project, strips plaintext from output — see `references/secrets-manager.md`). The underlying manual pattern, if you need it:
  ```bash
  read -rs 'val?Paste value: '
  bws secret create OPENAI_API_KEY "$val" 18f14ed9-8ba5-4cc6-bbd4-b45b01534270
  unset val
  ```
  (History keeps the literal `"$val"`, never the expansion.)
- `bws secret get` / `bws secret list` print **plaintext secret values** — same rule as `bw get`: don't paste their output into chats or screenshares.
- `BWS_ACCESS_TOKEN` is a bearer credential: never echo it, never commit it. **Rotate** by issuing a new token in the web UI and revoking the old one, then updating `~/.config/bws/token.env`.

Full operations — token-storage patterns (600 file, systemd `EnvironmentFile`/`LoadCredential`), `bws run` injection, **Home Assistant LLM-key wiring**, rotation, and bws-specific errors — are in **[references/secrets-manager.md](references/secrets-manager.md)**.

## Reference Files

Load only when the topic is active:

- **[references/item-schema.md](references/item-schema.md)** — Full item type table (login=1, secure_note=2, card=3, identity=4), custom field types, complete JSON templates for each
- **[references/scripting.md](references/scripting.md)** — Builder script template, session lifecycle helpers, pipeline patterns, output parsing with jq, cleanup hygiene
- **[references/troubleshooting.md](references/troubleshooting.md)** — Error message catalog with root-cause analysis and recovery steps; the punycode deprecation noise you can ignore
- **[references/ssh-keys.md](references/ssh-keys.md)** — Item type 5 (`sshKey`) schema + Bitwarden SSH Agent (Desktop) integration + recipes for importing existing keys, exporting to a new machine, and auditing vault contents
- **[references/secrets-manager.md](references/secrets-manager.md)** — **`bws` (Secrets Manager) — the *other* product.** Machine-account / project / token lifecycle, token-storage patterns (600 file, systemd `EnvironmentFile`/`LoadCredential`, recovery-to-vault), `bws run` injection, Home Assistant LLM-API-key integration, token rotation, and bws-specific errors (401/invalid token, project-access denied, empty `run` output)
