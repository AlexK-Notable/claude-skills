# SSH Keys

Bitwarden has two distinct SSH-key features that often get conflated. Understand both before recommending a workflow.

## Table of Contents

- [Two Layers](#two-layers)
- [Layer 1 — SSH Key Item Type (Storage)](#layer-1--ssh-key-item-type-storage)
- [Layer 2 — Bitwarden SSH Agent (Runtime)](#layer-2--bitwarden-ssh-agent-runtime)
- [Recipe: Import an existing SSH key](#recipe-import-an-existing-ssh-key)
- [Recipe: Export an SSH key to a new machine](#recipe-export-an-ssh-key-to-a-new-machine)
- [Recipe: Audit which keys are in the vault](#recipe-audit-which-keys-are-in-the-vault)
- [Should you use the item type or a secure note?](#should-you-use-the-item-type-or-a-secure-note)
- [Caveats](#caveats)

## Two Layers

| Layer | What it is | Where it lives | CLI-relevant? |
|---|---|---|---|
| **SSH Key item type** | A first-class vault item that stores a key pair (`type: 5`) | Server-side vault; synced to all clients | ✅ Yes — `bw create/get/edit/list item` works |
| **Bitwarden SSH Agent** | A `ssh-agent`-protocol implementation that serves vault-stored keys to OpenSSH clients | Desktop app process (Linux/macOS/Windows) | ⚠️ Indirectly — CLI doesn't implement the agent; Desktop does |

The item type is the **storage and sync** layer. The agent is the **runtime use** layer. You can have one without the other:

- Store an SSH key item via CLI, never enable the agent → key is backed up + restorable, but `ssh` doesn't see it
- Enable the agent in Desktop with no items → agent is useless (nothing to serve)
- Both → store keys in vault, agent serves them transparently to `ssh` / `git` / etc.

## Layer 1 — SSH Key Item Type (Storage)

### Schema

Item type `5`. Nested object: `sshKey`.

```json
{
  "type": 5,
  "name": "id_ed25519 — komi-hypr",
  "notes": "Optional notes / context",
  "folderId": null,
  "organizationId": null,
  "favorite": false,
  "reprompt": 0,
  "fields": [],
  "sshKey": {
    "privateKey": "-----BEGIN OPENSSH PRIVATE KEY-----\n...\n-----END OPENSSH PRIVATE KEY-----\n",
    "publicKey": "ssh-ed25519 AAAAC3Nz... user@host",
    "keyFingerprint": "SHA256:abc..."
  }
}
```

**Fields:**
- `privateKey`: full PEM/OpenSSH private key block (multi-line, newlines as `\n` in JSON). Stored encrypted at rest like every other field.
- `publicKey`: the matching public key (single line `ssh-<algo> <base64> [<comment>]`).
- `keyFingerprint`: SHA256 fingerprint (matches `ssh-keygen -lf <pub>`). Bitwarden may compute this server-side; you can also set it explicitly.

**Supported key types** (per Bitwarden's official list):
- ed25519 (recommended — small, fast, modern)
- RSA (2048+ bits)
- ECDSA (P-256, P-384, P-521)

**NOT supported**: `ed25519-sk` / `ecdsa-sk` (FIDO2 hardware-backed). These are an open feature request. For FIDO2-backed SSH workflows, keep using traditional `ssh-agent` plus your hardware tooling — Bitwarden isn't a substitute here.

**All three `sshKey` fields are required and non-empty.** `SshKeyExport.toView()` validates this at item-creation time. There is **no server-side fingerprint computation** — you must compute `keyFingerprint` yourself (e.g., `ssh-keygen -lf <pub>` → "SHA256:..." token) and include it explicitly in the JSON. The builder script in the import recipe below does this via subprocess.

### Template — there isn't one

**`bw get template item.sshKey` does NOT exist.** Verified against the CLI source (`apps/cli/src/commands/get.command.ts`): the template registry covers `item`, `item.field`, `item.login`, `item.login.uri`, `item.card`, `item.identity`, `item.securenote`, plus a few identity sub-objects — but no `sshKey` entry. Attempting it returns `Unknown template object.`

Even the generic `bw get template item` is not a useful starting point — it returns a **Login-type** skeleton (`type: 1`) with no `sshKey` field, so the naive `bw get template item | jq '.type=5' | bw encode | bw create item` pattern fails validation. Build SSH Key JSON from scratch using the schema above (the import recipe below does exactly this).

### Reading an SSH key item

```bash
# Full item with both keys
bw get item "<name-or-id>"

# Just the public key (single line)
bw get item "<name-or-id>" | jq -r '.sshKey.publicKey'

# Just the private key (multi-line — careful with quoting if piping into ssh-add)
bw get item "<name-or-id>" | jq -r '.sshKey.privateKey'

# Just the fingerprint
bw get item "<name-or-id>" | jq -r '.sshKey.keyFingerprint'
```

## Layer 2 — Bitwarden SSH Agent (Runtime)

The Desktop app (Linux/macOS/Windows) ships an integrated SSH agent starting with version **2025.1.2** (released January 28, 2025). The SSH Key item type itself landed earlier — CLI v2024.12.0 (Dec 13, 2024) and corresponding Desktop versions — so you can store keys in the vault before enabling the agent.

Once enabled, the agent advertises itself via the standard `SSH_AUTH_SOCK` env var and serves SSH Key items from your unlocked **personal vault** — see Caveats for the organization-vault limitation.

### Enabling (Desktop app)

In Bitwarden Desktop: **Settings → SSH Agent → Enable SSH Agent**. The setting toggles a Unix socket (Linux/macOS) or named pipe (Windows). Approval prompts can be enabled in the same settings panel — per-key granularity is not formally documented and may be global-only.

### Hooking OpenSSH up to it

Add to `~/.bashrc` / `~/.zshrc`:

```bash
export SSH_AUTH_SOCK="$HOME/.bitwarden-ssh-agent.sock"
```

(Path varies by platform — check Desktop's Settings page for the actual socket path on your machine.)

Verify the agent is serving:

```bash
ssh-add -l   # should list all SSH Key items in the unlocked vault
```

Each `ssh` invocation that needs a key triggers a Desktop notification (configurable) where you approve/deny use of that specific key.

### CLI's role re: the agent

`bw` CLI does **not** implement the agent. It can:
- Create/edit/read the items the agent serves
- Be used to bulk-import SSH keys before the agent ever runs
- Be used on a new machine to audit which keys exist in the vault before deciding to install Desktop

If you want headless SSH (e.g., a server or a Docker container) without the Desktop app, you'd extract the key via `bw get item ... | jq -r '.sshKey.privateKey'` and pipe it into a traditional `ssh-agent`. The Bitwarden agent is Desktop-only.

## Recipe: Import an existing SSH key

Builder script pattern — reads key files from `~/.ssh/`, never embeds them as string literals.

Save as `/tmp/import_ssh_key.py`:

```python
#!/usr/bin/env python3
"""Build a Bitwarden SSH Key item from existing files in ~/.ssh/."""
import json
import socket
import subprocess
from datetime import date
from pathlib import Path

KEY_NAME = "id_ed25519"   # change to whichever key you're importing
SSH_DIR = Path.home() / ".ssh"

priv_path = SSH_DIR / KEY_NAME
pub_path = SSH_DIR / f"{KEY_NAME}.pub"

private_key = priv_path.read_text()
public_key = pub_path.read_text().rstrip("\n")

# Compute fingerprint via ssh-keygen (matches what Bitwarden expects)
fp = subprocess.run(
    ["ssh-keygen", "-lf", str(pub_path)],
    capture_output=True, text=True, check=True
).stdout.split()[1]  # format: "<bits> <fp> <comment> (<algo>)"

hostname = socket.gethostname()

item = {
    "type": 5,
    "name": f"{KEY_NAME} — {hostname}",
    "notes": f"Imported from {priv_path} on {date.today().isoformat()}",
    "folderId": None,
    "organizationId": None,
    "favorite": False,
    "fields": [
        {"name": "machine", "value": hostname, "type": 0},
        {"name": "path", "value": str(priv_path), "type": 0},
    ],
    "sshKey": {
        "privateKey": private_key,
        "publicKey": public_key,
        "keyFingerprint": fp,
    },
}

print(json.dumps(item))
```

Then run:

```bash
export BW_SESSION="$(bw unlock --raw)" && \
  python3 /tmp/import_ssh_key.py | bw encode | bw create item && \
  unset BW_SESSION && bw lock && \
  shred -u /tmp/import_ssh_key.py
```

## Recipe: Export an SSH key to a new machine

On the new machine, after `bw login && bw unlock`:

```bash
ITEM_NAME="id_ed25519 — komi-hypr"
mkdir -p ~/.ssh && chmod 700 ~/.ssh

export BW_SESSION="$(bw unlock --raw)"

# Private key — strict mode 600
bw get item "$ITEM_NAME" | jq -r '.sshKey.privateKey' > ~/.ssh/id_ed25519
chmod 600 ~/.ssh/id_ed25519

# Public key — mode 644 is fine
bw get item "$ITEM_NAME" | jq -r '.sshKey.publicKey' > ~/.ssh/id_ed25519.pub
chmod 644 ~/.ssh/id_ed25519.pub

# Verify
ssh-keygen -lf ~/.ssh/id_ed25519.pub   # should match the keyFingerprint field

unset BW_SESSION && bw lock
```

**Important:** verify the fingerprint matches what the vault stored before trusting the export — if the keyFingerprint field was computed by Bitwarden at import time and the file looks healthy, they should agree.

## Recipe: Audit which keys are in the vault

```bash
export BW_SESSION="$(bw unlock --raw)" && \
  bw list items 2>/dev/null | \
    jq '[.[] | select(.type == 5) | {id, name, fingerprint: .sshKey.keyFingerprint, hasPrivate: (.sshKey.privateKey != null and .sshKey.privateKey != "")}]' && \
  unset BW_SESSION && bw lock
```

Lists every SSH Key item with its fingerprint and whether the private key is populated (useful for detecting items where the import dropped the private half).

## Should you use the item type or a secure note?

| Use case | Recommendation |
|---|---|
| Modern setup, key you'll actually use via ssh | **Item type 5** — works with Bitwarden SSH Agent, structured fields, fingerprint indexed |
| Legacy archive, key that's just for the "in case I lose it" scenario | Either works; type 5 if you want the structure, secure note if you want flexible notes alongside |
| Recovery codes, ssh-keygen invocation history, README about the key | **Secure note** — these are prose, not key material |
| Need to back up alongside passphrase, comment, generation context | **Item type 5** (privateKey + publicKey) + **custom fields** on the same item for the metadata |

The item type is strictly more capable for actual key material. Use it unless you have a reason not to (older Desktop app that doesn't support type 5, or org policy that forbids it).

## Caveats

- **Passphrase-protected keys**: Bitwarden stores the private-key blob verbatim. If your key file was generated with `ssh-keygen -N "<passphrase>"`, the encrypted blob is what gets stored, and you'll still need the passphrase at use time. The vault is NOT a passphrase substitute — it's a transport layer.
- **Agent vs at-rest encryption**: when the Bitwarden SSH Agent serves a key, it briefly decrypts the private blob in process memory. The same is true of any ssh-agent. Treat the Desktop process as a sensitive surface; lock the vault when stepping away.
- **Hardware-backed keys (`ed25519-sk` / `ecdsa-sk`)**: NOT supported by Bitwarden as SSH Key items. Official supported list is Ed25519 + RSA + ECDSA only. For FIDO2-backed SSH workflows, keep using `ssh-agent` + your hardware tooling (Solo, YubiKey, etc.) — Bitwarden isn't a replacement here.
- **No built-in key generation**: Bitwarden does not generate SSH keys client-side (unlike its password generator). Use `ssh-keygen` and import.
- **CLI version**: SSH Key items (`type: 5`) were added in `bw` CLI **v2024.12.0** (Dec 13, 2024). Older bundled CLIs in distro packages won't accept `type: 5`. Verify with `bw --version` — anything ≥ 2024.12.0 is fine. The Arch package on this machine is currently 2026.x, so already covered.
- **Organization vaults — partial support**: SSH Key items can be **stored** in organization vaults (sync, history, sharing all work), but the Bitwarden SSH Agent currently **does not serve organization-owned keys** — it only serves keys from the user's personal vault. This is an open feature request (bitwarden/clients). If you need org-shared keys to work with the agent, copy the item to a personal vault or stick to traditional ssh-agent with shared key distribution.
- **Don't confuse with TOTP/WebAuthn keys**: an item's `login.totp` field stores TOTP seeds; FIDO2/WebAuthn credentials aren't currently a Bitwarden item type. The SSH Key item type is specifically for OpenSSH-format private keys.
