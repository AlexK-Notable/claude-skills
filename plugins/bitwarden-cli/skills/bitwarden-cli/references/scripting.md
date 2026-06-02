# Scripting Patterns

How to drive `bw` non-interactively from inside a Claude Code session, including session-token handling, secrets hygiene, and pipeline construction.

## Table of Contents

- [The Core Problem: No TTY](#the-core-problem-no-tty)
- [Pattern 1 — One-shot from User's Terminal](#pattern-1--one-shot-from-users-terminal)
- [Pattern 2 — Builder Script for Secrets](#pattern-2--builder-script-for-secrets)
- [Pattern 3 — Multi-Op Session](#pattern-3--multi-op-session)
- [Pipelines: build → encode → create/edit](#pipelines-build--encode--createedit)
- [Output Parsing](#output-parsing)
- [Cleanup Hygiene](#cleanup-hygiene)
- [Shell Helpers](#shell-helpers)

## The Core Problem: No TTY

`bw unlock` reads the master password from the TTY. Claude's `Bash` tool runs commands without a TTY, so `bw unlock` will hang or fail there. **You can never unlock the vault from a Bash tool call.**

What works:
- Provide the user a one-liner they run in their terminal (their TTY is real)
- Read items / list / status from Bash tool calls **after** the user has unlocked AND exported `BW_SESSION` in a way that propagates to your tool calls (which doesn't happen with most shells — see Pattern 3)

What does NOT work:
- Running `bw unlock --raw` inside `Bash(...)` and capturing the token
- Piping the master password to `bw unlock` from inside a tool call (the CLI explicitly does not support `--passwordfile` for unlock — only for login)

Practical consequence: **almost all bw operations require the user to be in the loop for unlock**, then you can provide them the actual operation as a one-liner.

## Pattern 1 — One-shot from User's Terminal

The most common pattern. The user runs everything in their terminal in one command.

```bash
export BW_SESSION="$(bw unlock --raw)" && \
  <do-the-work> && \
  unset BW_SESSION && \
  bw lock
```

The work payload is whatever you'd normally run with `BW_SESSION` set. Examples:

```bash
# Create a secure note from inline JSON
export BW_SESSION="$(bw unlock --raw)" && \
  echo '{"type":2,"name":"Foo","notes":"bar","secureNote":{"type":0}}' | \
  bw encode | bw create item && \
  unset BW_SESSION && bw lock

# Look up an item, full record
export BW_SESSION="$(bw unlock --raw)" && \
  bw get item "<id-or-name>" && \
  unset BW_SESSION && bw lock

# Generate a password and save as a login item
export BW_SESSION="$(bw unlock --raw)" && \
  bw generate --length 32 --uppercase --lowercase --number --special | \
    xargs -I {} jq -n --arg pw "{}" '{type:1,name:"New service",login:{password:$pw}}' | \
    bw encode | bw create item && \
  unset BW_SESSION && bw lock
```

## Pattern 2 — Builder Script for Secrets

When the payload includes secrets read from disk (key files, token files), build the payload at runtime via a Python (or jq) script. **The script reads the secret at runtime — it never embeds the secret as a literal.**

Template (saved to `/tmp/<descriptive-name>.py`):

```python
#!/usr/bin/env python3
"""Build a Bitwarden item from runtime-read secret files."""
import json
import socket
from datetime import date
from pathlib import Path

# Read secrets from their disk locations
SECRET_FILE = Path.home() / ".config/some-app/secret.txt"
secret = SECRET_FILE.read_text().rstrip("\n")

hostname = socket.gethostname()
today = date.today().isoformat()

notes = f"""# Note title

Body explaining what this is, how to use it,
and the restore steps if applicable.

## Origin
Machine: {hostname}
Date: {today}

## Secret value
```
{secret}
```
"""

item = {
    "type": 2,
    "name": f"<descriptive name> — {hostname}",
    "notes": notes,
    "secureNote": {"type": 0},
    "folderId": None,
    "organizationId": None,
    "favorite": False,
    "fields": [
        {"name": "machine", "value": hostname, "type": 0},
        {"name": "generated", "value": today, "type": 0},
    ],
}

print(json.dumps(item))
```

Then the user runs:

```bash
export BW_SESSION="$(bw unlock --raw)" && \
  python3 /tmp/<script>.py | bw encode | bw create item && \
  unset BW_SESSION && bw lock && \
  shred -u /tmp/<script>.py
```

The script never contains the secret as a string literal — it reads from disk at runtime. After successful creation, `shred -u` securely removes the script.

**Why a builder script vs an inline heredoc?**
- JSON escaping multi-line content with embedded backticks/quotes is painful
- Python's `json.dumps` handles all the escaping automatically
- The script file can be inspected before running (the user sees what's being built)
- Easy to add metadata (hostname, date, public fingerprints) without complicating the one-liner

## Pattern 3 — Multi-Op Session

When the user has multiple bw ops to do in a row, set up once:

**User runs in their terminal:**
```bash
export BW_SESSION="$(bw unlock --raw)"
```

**Then for each op, they run (no unlock/lock wrapper needed):**
```bash
bw list items --search foo
bw get item <id>
echo '{"type":2,"name":"thing","notes":"..."}' | bw encode | bw create item
```

**At the end, they clean up:**
```bash
unset BW_SESSION && bw lock
```

This avoids repeated master-password prompts when doing several ops back-to-back.

**Note for Claude:** `BW_SESSION` set in the user's interactive shell **does not propagate to your Bash tool calls** — each Bash invocation spawns a fresh non-interactive shell that doesn't inherit the user's exported env. So if you `Bash("bw list items")` while the user has an unlocked session, you'll get "Vault is locked" because your shell doesn't see their `BW_SESSION`. Tell the user to run the commands themselves; don't run them on their behalf via Bash tool.

## Pipelines: build → encode → create/edit

Bitwarden CLI's mutation commands take a **base64-encoded JSON** argument. The pipeline:

```
<source of raw JSON> | bw encode | bw <create|edit> <item|folder> [id]
```

- `bw encode` reads JSON from stdin, base64-encodes, prints to stdout
- `bw create item` reads base64 from stdin (or first arg), decodes, creates
- `bw edit item <id>` reads base64 from stdin (or first arg), decodes, updates

Equivalent without `bw encode` (manual):
```bash
echo '{"type":2,"name":"x"}' | base64 -w0 | bw create item
```

`bw encode` is just a convenience wrapper.

### Edit pattern (preserve existing fields)

When updating, **start from the existing item** so you don't drop fields:

```bash
ITEM_ID="<uuid>"
bw get item "$ITEM_ID" | \
  jq '.notes = "new body" | .fields += [{"name":"new_field","value":"x","type":0}]' | \
  bw encode | bw edit item "$ITEM_ID"
```

If you build an edit payload from scratch and post it, any field you omit gets reset. `bw get item` returns the canonical full record; `jq` modifies just what you want.

## Output Parsing

Mutation commands (`create`, `edit`, `delete`) return the affected object's JSON on success. Filter with `jq` to avoid exposing secrets in your terminal output:

```bash
# Just confirm creation, no body
... | bw create item | jq '{id, name, type}'

# List items with metadata only
bw list items | jq '.[] | {id, name, type, fields: (.fields // [] | map({name, type}))}'

# Get just a password without printing the rest of the item
bw get password "<name-or-id>"

# Get a specific field's value
bw get item "<id>" | jq -r '.fields[] | select(.name=="public_key") | .value'
```

## Cleanup Hygiene

After any bw operation that touches secrets:

1. **`unset BW_SESSION`** — clears the bearer token from the env var
2. **`bw lock`** — server-side invalidation of the session token (belt-and-suspenders)
3. **`shred -u /tmp/<builder>.py`** — for any script that handled secrets (even if it just read them from disk)
4. **`history -c` or `fc -p`** — if a secret accidentally ended up in shell history (rare with proper patterns above, but worth knowing)

Do NOT clear shell history routinely — it's destructive of useful state. Only when you know a secret got there.

## Shell Helpers

For users who do this often, suggest a `bw-do` shell function in their `.zshrc`:

```bash
bw-do() {
    if [ -z "$BW_SESSION" ]; then
        export BW_SESSION="$(bw unlock --raw)" || return 1
        local _started_unlocked=0
    else
        local _started_unlocked=1
    fi
    "$@"
    local _rc=$?
    if [ "$_started_unlocked" = "0" ]; then
        unset BW_SESSION
        bw lock >/dev/null
    fi
    return $_rc
}
```

Usage:
```bash
bw-do bw list items --search foo
bw-do bash -c 'echo "{...}" | bw encode | bw create item'
```

If `BW_SESSION` is already set when `bw-do` is called, it leaves the session alone (multi-op mode); otherwise it does the full unlock-do-lock dance.
