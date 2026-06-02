# Troubleshooting

Error message catalog with root-cause analysis and recovery steps.

## Table of Contents

- [Auth Errors](#auth-errors)
- [Vault State Errors](#vault-state-errors)
- [Item Errors](#item-errors)
- [Sync Errors](#sync-errors)
- [Pipeline / Encoding Errors](#pipeline--encoding-errors)
- [Noise You Can Ignore](#noise-you-can-ignore)

## Auth Errors

### `invalid_grant` + `Unable to fetch ServerConfig from https://api.bitwarden.com`

**Cause:** Server-side auth grant has been invalidated. Often happens when:
- The CLI hasn't synced in a long time (check `bw status` → `lastSync` field)
- The user logged out via web/desktop and the CLI didn't notice
- 2FA configuration changed
- Master password was changed elsewhere

**Wording is misleading**: this is NOT "wrong password." It's "the refresh token you have is no longer accepted." Password entry never even happens for the actual unlock; the failure is before that.

**Fix:**
```bash
bw logout
bw login   # interactive: email + master password [+ 2FA code]
```

After `bw login`, the new session is fresh and `bw unlock --raw` will work normally.

### `Master password unlock data was not found for the user <uuid>`

**Cause:** Same root cause as `invalid_grant`. The CLI tried to use cached unlock material that's no longer valid server-side. Often appears as the second error after `invalid_grant`.

**Fix:** `bw logout && bw login`.

### `Username or password is incorrect. Try again.`

**Cause:** Wrong master password during `bw login` or `bw unlock`. Distinct from `invalid_grant`.

**Fix:** Re-enter master password carefully. If consistently failing, verify on the Bitwarden web vault first (rules out password drift between memory and reality). 2FA prompts come after master password, so this error means the password itself is wrong.

### Two-step prompt loop on `bw login`

**Symptom:** `bw login` prompts for email, then password, then `Two-step login code:` even though you've never set up 2FA — and rejects whatever you enter.

**Cause:** Account has a 2FA method enabled that you're not expecting. Could be email OTP, authenticator app, YubiKey, FIDO2. Most likely: email OTP that was enabled long ago and forgotten.

**Fix:** Log into the Bitwarden web vault first; the 2FA prompt there will reveal which method is active. Use the matching code in the CLI prompt. If the method is FIDO2 (browser-bound), you'll need to disable it or add a non-browser fallback (TOTP) via the web vault first.

## Vault State Errors

### `Vault is locked.` on any operation

**Cause:** `BW_SESSION` not set in the current shell.

**Fix:**
```bash
export BW_SESSION="$(bw unlock --raw)"
```

Then re-run the operation.

**Common trap (Claude-specific):** If the user has unlocked their vault in their interactive shell and exported `BW_SESSION`, **that variable does NOT propagate to Bash tool calls**. Each Bash tool call spawns a fresh non-interactive shell. So even if the user says "I unlocked it already," your tool calls still get "Vault is locked." Solution: tell the user to run the operations in their own shell instead of via you.

### `bw status` shows `"status": "unauthenticated"`

**Cause:** Logged out (no cached vault info at all).

**Fix:** `bw login`. After that, `bw status` will show `"locked"`.

### Stale `lastSync` (months old)

**Cause:** CLI hasn't talked to the server in a long time. Often correlates with impending `invalid_grant` errors.

**Fix:** Try `bw sync` first. If that returns an auth error, the underlying problem is stale auth — go to `bw logout && bw login`.

## Item Errors

### `Item is required.` on `bw create item`

**Cause:** No JSON was sent to stdin, OR the JSON didn't pass through `bw encode`.

**Fix:** Verify the pipeline includes encoding:
```bash
echo '<json>' | bw encode | bw create item
```
NOT:
```bash
echo '<json>' | bw create item     # WRONG — bw expects base64
```

### `Cannot read property 'X' of undefined` (Node TypeError)

**Cause:** JSON sent to `bw create item` is malformed or missing required fields for the item type.

**Fix:** Validate the JSON first with `jq` to catch syntax errors:
```bash
jq '.' <<<"$payload"   # prints prettified JSON, errors on invalid
```

Then verify required fields:
- Type 1 (login): needs `login.password` or `login.username` (at least one)
- Type 2 (secure note): needs `secureNote: {type: 0}` block — easy to forget
- Type 3 (card): needs `card.number`
- Type 4 (identity): no strict required field

Use `bw get template item` to see a known-good skeleton.

### `Item already exists.`

**Cause:** Item with the same name already exists in the same folder (Bitwarden enforces unique names within scope).

**Fix:** Either:
- Pick a more specific name (include hostname, date, or context)
- Update the existing item instead: `bw get item "<name>" | jq '.notes = "..."' | bw encode | bw edit item <id>`
- Move into a different folder via `folderId`

### `Item not found.`

**Cause:** The name or ID provided doesn't match anything. Names are case-sensitive AND substring-sensitive for `bw get`. Use `bw list items --search` for fuzzy matching.

**Fix:**
```bash
bw list items --search "<term>" | jq '.[] | {id, name}'
# pick the right ID, then:
bw get item "<id>"
```

## Sync Errors

### Local cache appears stale (items added on web don't show in CLI)

**Cause:** Bitwarden CLI caches the vault locally. Edits made via web vault or another CLI instance aren't visible until you sync.

**Fix:**
```bash
bw sync          # gentle resync
bw sync --force  # if the gentle one doesn't take
```

`bw sync` requires the vault to be unlocked (it uses the session token).

## Pipeline / Encoding Errors

### `Invalid character` from `bw create item`

**Cause:** Sent raw JSON instead of base64-encoded JSON.

**Fix:** Pipe through `bw encode` first. See [Pipelines](scripting.md#pipelines-build--encode--createedit) in the scripting reference.

### `Unexpected token in JSON at position N`

**Cause:** JSON syntax error before encoding. Often from unescaped newlines in `notes` field or trailing commas.

**Fix:** Build JSON with a real serializer (Python's `json.dumps`, jq) instead of constructing strings by hand. Newlines in `notes` must be `\n`, not literal newlines.

### Output of `bw create item` is truncated / mangled

**Cause:** Likely terminal rendering issue with the large JSON response, not a real failure. The item probably created fine.

**Fix:** Verify with `bw list items --search "<name>" | jq '.[] | {id, name}'`. If the item is there, the create succeeded; the truncated output is cosmetic.

## Noise You Can Ignore

### `DeprecationWarning: The 'punycode' module is deprecated`

```
(node:NNNN) [DEP0040] DeprecationWarning: The `punycode` module is deprecated.
Please use a userland alternative instead.
(Use `node --trace-deprecation ...` to show where the warning was created)
```

**Cause:** Node.js v22+ deprecated the built-in `punycode` module. The Bitwarden CLI bundles a Node runtime that still uses it. Cosmetic.

**Fix:** None needed. The warning appears on every `bw` invocation. Filter it out of output parsing if it's annoying:
```bash
bw status 2>/dev/null
```
or
```bash
bw status 2>&1 | grep -v DeprecationWarning | grep -v punycode | grep -v trace-deprecation
```

### `UnhandledPromiseRejection` after `invalid_grant`

A noisy Node.js error follows the actual `invalid_grant` line. It's a CLI bug — the auth error isn't caught and bubbles up as an unhandled rejection. The cause is the auth error above it; ignore the stack trace and focus on the root cause.

### `Lock failed: vault is already locked.`

Harmless. Means you ran `bw lock` when the vault was already locked. The state you wanted is the state you have.
