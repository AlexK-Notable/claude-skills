# Troubleshooting

## Table of Contents

- [Diff debugging](#diff-debugging)
- [Template debugging](#template-debugging)
- [Apply went wrong](#apply-went-wrong)
- [Encryption issues](#encryption-issues)
- [Source repo issues](#source-repo-issues)
- [Permission / attribute drift](#permission--attribute-drift)
- [Run script not running](#run-script-not-running)

## Diff debugging

```bash
# Standard diff
chezmoi diff

# More detail (shows attribute changes too)
chezmoi apply --dry-run --verbose

# Compact status of pending changes
chezmoi status

# Verify nothing has drifted
chezmoi verify     # exits non-zero on drift; useful in CI
```

If `chezmoi diff` shows unexpected output:

- A managed file was edited directly → `chezmoi re-add <path>` to capture, or `chezmoi apply <path>` to revert
- A template's data input changed → check `chezmoi data | jq`
- A previously-encrypted file isn't decrypting → `chezmoi doctor`
- A file's mode changed → use `chezmoi apply <path>` or `chezmoi re-add <path>` (the latter captures the new mode)

## Template debugging

```bash
# Render a template snippet inline
chezmoi execute-template '{{ .chezmoi.hostname }}'

# Show the rendered version of a managed file
chezmoi cat ~/.gitconfig

# Render an arbitrary file with current template data
chezmoi execute-template < ~/.local/share/chezmoi/dot_gitconfig.tmpl

# Dump all template data
chezmoi data | jq
```

Common template errors:

| Error | Cause |
|---|---|
| `<.chezmoi.osRelease.id>: nil pointer evaluating` | That field doesn't exist on this OS — check with `chezmoi data \| jq '.chezmoi.osRelease'` |
| Template renders blank | Whitespace control issue — review `{{- ... -}}` placement |
| `function "X" not defined` | Sprig helper unavailable; check Sprig version compatibility |
| `executing "X" at <Y>: range can't iterate over nil` | Data source missing — confirm `.chezmoidata.toml` is loaded |

## Apply went wrong

### Recover from `--force` overwrite

If chezmoi clobbered a destination file you didn't mean to overwrite:

1. The destination file is gone, but the **source state is unchanged**
2. Edit the source: `chezmoi edit <path>` — it's still correct
3. Or check git history of the source to see if you had recent committed work: `chezmoi git -- log -p <source-path>`

If you also overwrote the source state (rare), recover from git:

```bash
chezmoi git -- log --oneline             # find the last good commit
chezmoi git -- show <hash>:<source-path> # peek at the old version
chezmoi git -- checkout <hash> -- <source-path>
```

### Apply to a single file

```bash
chezmoi apply ~/.zshrc           # one file only
chezmoi apply --dry-run ~/.zshrc # preview
```

### Skip a file temporarily

Add to `.chezmoiignore`:
```
.zshrc
```

…apply, fix the source, then remove from ignore.

## Encryption issues

### "no identity" or "decryption failed"

Check `~/.config/chezmoi/chezmoi.toml` `[age]` section:
```toml
[age]
    identity = "~/.config/chezmoi/key.txt"
    recipient = "age1..."
```

Then:
```bash
chezmoi doctor                                # should show ok for age
ls -la ~/.config/chezmoi/key.txt              # mode 600, file exists
age -d -i ~/.config/chezmoi/key.txt <some.age> # test decryption directly
```

### Lost the key

Encrypted source files are unrecoverable without the identity file. Procedure:

1. Generate a new age key
2. Update `chezmoi.toml` with the new identity/recipient
3. On a machine where plaintext destination files still exist: `chezmoi forget <encrypted-path>`, then `chezmoi add --encrypt <path>` to re-add with the new key
4. Commit and push the source repo — old encrypted blobs are now defunct

## Source repo issues

### Source dir out of sync with remote

```bash
chezmoi git -- status
chezmoi git -- fetch
chezmoi git -- log --oneline HEAD..origin/master  # what's incoming
chezmoi git -- pull
```

### Detached HEAD or weird state

```bash
chezmoi cd
git status
# fix as a normal git repo, then:
exit
```

### Apply targets a different home dir (testing)

```bash
chezmoi apply -D /tmp/test-home --dry-run
```

Useful for testing migrations on a fresh dir without touching `$HOME`.

## Permission / attribute drift

If `chezmoi diff` shows attribute-only changes (e.g., mode 0644 → 0600):

- The destination file has different permissions than the source attributes specify
- Decide which is correct:
  - Destination correct → `chezmoi re-add <path>` (captures current mode into source attributes)
  - Source correct → `chezmoi apply <path>` (resets mode to what source specifies)

## Run script not running

Symptoms: `run_once_*.sh` doesn't execute on a new machine.

Checks:

```bash
# Has it already run on this machine?
chezmoi state list-scripts

# Force re-run by clearing state for that script:
chezmoi state delete-scripts <script-name>

# Or temp-override with --force:
chezmoi apply --force
```

For `run_onchange_*.sh`: chezmoi tracks the script's content hash. If you change comments or whitespace, that counts as a change. Use `chezmoi apply --dry-run --verbose` to see decisions.
