# Chezmoi Command Reference

Comprehensive command surface for chezmoi v2.70+. Defer to the [main SKILL.md decision tree](../SKILL.md#decision-tree) for routine usage.

## Table of Contents

- [Source state operations](#source-state-operations)
- [Target state operations](#target-state-operations)
- [Inspection](#inspection)
- [Source-dir & config](#source-dir--config)
- [Less common](#less-common)
- [Useful flags](#useful-flags)

## Source state operations

| Command | Purpose | Notes |
|---|---|---|
| `chezmoi add <path>` | Add file/dir to source state | Auto-detects sensible attributes |
| `chezmoi add --template <path>` | Add as Go template | Source filename gets `.tmpl` suffix |
| `chezmoi add --encrypt <path>` | Add encrypted | Requires age/gpg config |
| `chezmoi add --private <path>` | Force mode 0600/0700 | For SSH/secrets |
| `chezmoi add --autotemplate <path>` | Add and auto-templatize known values | Replaces hostname, email, etc. with template vars |
| `chezmoi re-add <path>` | Update source from destination | After direct edits in `$HOME` |
| `chezmoi edit <path>` | Edit source via `$EDITOR` | `--apply` writes destination on save |
| `chezmoi forget <path>` | Stop managing (file stays in `$HOME`) | Removes only from source |

## Target state operations

| Command | Purpose | Notes |
|---|---|---|
| `chezmoi diff` | Target vs destination | **Always run before apply** |
| `chezmoi apply [path]` | Write target to destination | Whole tree if no path |
| `chezmoi apply --dry-run --verbose` | Preview only | Verbose form of diff |
| `chezmoi apply --force` | Skip prompts | Use only after reviewing diff |
| `chezmoi update` | `git pull` then `apply` | Commit local source first |
| `chezmoi update --dry-run` | Preview pull + apply | Always safe |
| `chezmoi init [<repo>]` | Initialize source dir | Optional remote |
| `chezmoi init --apply <repo>` | New-machine bootstrap | Clone + apply in one step |

## Inspection

| Command | Purpose |
|---|---|
| `chezmoi managed` | List all managed paths |
| `chezmoi managed -i files` | Just files (skip dirs) |
| `chezmoi unmanaged` | List unmanaged files in `$HOME` |
| `chezmoi status` | Files with pending changes (similar to `git status`) |
| `chezmoi verify` | Exit non-zero if any drift |
| `chezmoi cat <path>` | Show rendered (post-template, post-decrypt) content |
| `chezmoi data` | Dump all template data as JSON |
| `chezmoi doctor` | System / config sanity check |

## Source-dir & config

| Command | Purpose |
|---|---|
| `chezmoi cd` | Subshell in source dir (use sparingly — see below) |
| `chezmoi git -- <args>` | Run git in source dir without subshell |
| `chezmoi edit-config` | Edit `~/.config/chezmoi/chezmoi.toml` |
| `chezmoi execute-template '<text>'` | Render template inline (debug) |
| `chezmoi source-path [<dest>]` | Print source path for a destination path |
| `chezmoi target-path [<source>]` | Inverse |

Prefer `chezmoi git --` over `chezmoi cd`. The subshell from `cd` reloads the user's shell config (potentially printing P10k init, prompting OMZ updates, etc.) and you must remember to `exit`.

## Less common

| Command | Purpose |
|---|---|
| `chezmoi merge <path>` | 3-way merge between source/destination/target |
| `chezmoi archive` | Export source state as tar |
| `chezmoi purge` | **DANGER** — remove source dir + state |
| `chezmoi age encrypt/decrypt` | Wrapper around the `age` tool |
| `chezmoi import <archive>` | Import files from a tar archive |
| `chezmoi state` | Inspect persistent state DB (`chezmoistate.boltdb`) |
| `chezmoi completion <shell>` | Generate completion script |

## Useful flags

| Flag | Effect |
|---|---|
| `-c <file>` | Use alternate config file |
| `-S <dir>` | Use alternate source dir |
| `-D <dir>` | Use alternate destination dir (great for testing in `/tmp`) |
| `-v` / `--verbose` | More detail |
| `-n` / `--dry-run` | Don't write anything |
| `-R, --refresh-externals [always\|auto\|never]` | Control external re-fetching (takes a value; `always` forces a re-fetch) |
| `--include` / `--exclude` | Filter by file type (`files`, `dirs`, `scripts`, `encrypted`, etc.) |
| `--keep-going` | Don't stop at first error |
