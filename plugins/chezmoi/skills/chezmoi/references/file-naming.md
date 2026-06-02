# File Naming Conventions

Chezmoi uses **prefixes** in source filenames to control destination attributes. Multiple prefixes combine in a fixed order. The `.tmpl` suffix marks templates.

## Table of Contents

- [Prefix order](#prefix-order)
- [File prefixes](#file-prefixes)
- [Directory prefixes](#directory-prefixes)
- [Special types](#special-types)
- [Suffixes](#suffixes)
- [Run scripts](#run-scripts)
- [Examples from this user's repo](#examples-from-this-users-repo)

## Prefix order

Prefixes must appear in this order in the filename:

```
encrypted_ → private_/readonly_/executable_/empty_/symlink_ → dot_
```

So `encrypted_private_dot_ssh_id_rsa` is valid; `dot_private_ssh` is not.

## File prefixes

| Prefix | Meaning | Example |
|---|---|---|
| `encrypted_` | Encrypted in source | `encrypted_dot_ssh/private_id_rsa` |
| `private_` | Mode 0600 (no group/world) | `private_dot_netrc` |
| `readonly_` | Strip write perms | `readonly_dot_config_locked` |
| `empty_` | Keep destination even if file is empty | `empty_dot_placeholder` |
| `executable_` | Mode 0755 | `executable_dot_local/bin/script` |
| `symlink_` | Create destination as symlink (file content = link target) | `symlink_dot_vimrc` |
| `dot_` | Becomes `.` | `dot_bashrc` → `~/.bashrc` |

## Directory prefixes

| Prefix | Meaning |
|---|---|
| `exact_` | Remove unmanaged children at apply time |
| `external_` | Children come from `.chezmoiexternal.toml`; don't apply attributes |
| `private_` | Mode 0700 |
| `readonly_` | Strip write perms |
| `dot_` | Becomes `.` |

## Special types

These are mutually exclusive with the standard prefixes — they change *what kind of thing* the source represents.

| Prefix | Behavior | Example |
|---|---|---|
| `create_` | Create only if destination is absent (don't overwrite) | `create_dot_bashrc` |
| `modify_` | Source is a script that modifies the existing destination | `modify_dot_bashrc` |
| `remove_` | Delete destination if it exists | `remove_dot_old_config` |

## Suffixes

| Suffix | Meaning |
|---|---|
| `.tmpl` | Process as Go template |
| `.literal` | Stop parsing further suffixes (escape) |
| `.age` / `.asc` | Encrypted blob (auto-applied with `encrypted_` prefix) |

Suffixes can chain: `dot_gitconfig.tmpl.literal` is a templated file ending in literal `.literal`.

## Run scripts

Format: `run_` `[once_|onchange_]` `[before_|after_]` `<name>` `[.tmpl]`

| Filename | When it runs |
|---|---|
| `run_install.sh` | On every `chezmoi apply` |
| `run_once_install.sh` | First time only (tracked by SHA256 of script content) |
| `run_onchange_update.sh` | Whenever the script's content changes |
| `run_before_check.sh` | Before applying file changes |
| `run_after_cleanup.sh` | After applying file changes |
| `run_once_before_install-packages.sh.tmpl` | Once, before changes, with templating |

Notes:

- `run_once_*` execution is tracked in `~/.config/chezmoi/chezmoistate.boltdb`
- Scripts run with the shell from their shebang (`#!/usr/bin/env bash`, etc.)
- A script's exit code matters — non-zero halts apply unless `--keep-going` is set
- Run scripts execute *every machine, every apply* (modulo `once_` / `onchange_`) — be idempotent

## Examples from this user's repo

Currently in `~/.local/share/chezmoi/`:

| Source filename | Destination |
|---|---|
| `dot_zshrc` | `~/.zshrc` |
| `dot_bashrc` | `~/.bashrc` |
| `dot_p10k.zsh` | `~/.p10k.zsh` |
| `dot_profile` | `~/.profile` |
| `dot_config/` | `~/.config/` (with all managed children inside) |

To add an SSH key encrypted with the user's age key (once configured):

```bash
chezmoi add --encrypt --private ~/.ssh/id_ed25519
# Source filename becomes: encrypted_private_dot_ssh/private_id_ed25519.age
```
