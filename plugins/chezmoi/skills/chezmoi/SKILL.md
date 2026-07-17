---
name: chezmoi
description: Use when managing dotfiles with chezmoi — adding files, applying source state, editing managed configs, syncing across machines, templating machine-specific configs, encrypting secrets, or running chezmoi commands (init, add, apply, diff, edit, re-add, update, managed, unmanaged, forget, status, verify, cd, git). Triggers on mentions of dotfiles, ~/.local/share/chezmoi, .chezmoiignore, .chezmoiexternal.toml, chezmoi.toml, source/target/destination state, age encryption for configs, or the AlexK-Notable/dotfiles repo.
---

# Chezmoi

Source-state dotfile manager with templating, encryption, and cross-platform support.

The user's source repo lives at `~/.local/share/chezmoi/` (remote: `git@github.com:AlexK-Notable/dotfiles.git`, branch: **`master`**) and tracks ~140 files, mostly under `~/.config/`. Tooling: `chezmoi v2.70.x`.

## Mental Model

Three states:

- **Source state** — files in `~/.local/share/chezmoi/` with prefixes (`dot_`, `private_`, `executable_`, ...). This *is* the git repo.
- **Target state** — what `chezmoi apply` would produce in `$HOME` after templating + decryption.
- **Destination state** — what currently exists on disk in `$HOME`.

`chezmoi diff` = target vs destination. **Always run it before `apply`.**

## Decision Tree

| User wants to... | Command |
|---|---|
| Start managing a file/dir | `chezmoi add <path>` |
| Edit managed file in `$EDITOR` | `chezmoi edit <path>` (add `--apply` to write on save) |
| Capture a direct edit to destination | `chezmoi re-add <path>` |
| Preview pending changes | `chezmoi diff` |
| Apply source to destination | `chezmoi diff` *then* `chezmoi apply` |
| Pull remote and apply | Commit local source first, then `chezmoi update` |
| List managed files | `chezmoi managed` |
| Find candidate files to add | `chezmoi unmanaged` |
| Detect drift | `chezmoi verify` |
| Stop managing (keep file) | `chezmoi forget <path>` |
| Run git in source dir | `chezmoi git -- <args>` |
| Show rendered (post-template) content | `chezmoi cat <path>` |

Full command surface: [references/commands.md](references/commands.md).

## Safety Doctrine

These rules protect months of customization. The user's dotfiles are not easily reproducible.

1. **Diff before apply.** `chezmoi apply` writes destination files. Run `chezmoi diff` first. Use `--force` only when you understand exactly what it will overwrite.
2. **Commit before pulling.** `chezmoi update` runs `git pull` then `apply` — uncommitted source changes are at risk. Always `chezmoi git -- status` first.
3. **Never manage generated files.** Wallust regenerates ~19 color files from wallpapers. Templates and runtime-generated state belong in `.chezmoiignore`, not source.
4. **`re-add`, don't `cp`.** When the user edits a destination file directly, run `chezmoi re-add <path>`. Don't manually copy files into the source dir — you'll bypass attribute handling (modes, encryption, templates).
5. **`forget` ≠ `purge`.** `forget` removes a file from source (file stays in `$HOME`). `purge` deletes the entire source dir + state. Never confuse them.
6. **Ask before destructive flags.** `--force`, `--remove`, `chezmoi purge`, `chezmoi apply -D <other-dir>` all have failure modes that lose work. Check with the user first.

## Files NOT to Manage

The user's `.chezmoiignore` already excludes these — preserve and extend the pattern:

- **Wallust outputs** — `colors.conf`, `colors.css`, `colors.toml`, `colors.rasi`, `colors.scss`, `style.css` (in any of 19 target dirs)
- **Wallpaper state** — `variety/wallpaper/`, `Downloaded/`, `Favorites/`, `history.txt`, `*.log`
- **Runtime caches** — `clipse/clipboard_history.json`, `micro/backups/`, `micro/buffers/`, `ncspot/userstate.cbor`
- **Anything regenerated on each launch or by another tool**

Heuristic: if the file changes without the user editing it, don't manage it. Add to `.chezmoiignore` instead.

## Daily Workflow

```bash
# After editing a managed file directly in $HOME:
chezmoi re-add ~/.zshrc
chezmoi git -- diff               # verify the change is what you expected
chezmoi git -- add -A
chezmoi git -- commit -m "..."
chezmoi git -- push

# Pulling on this machine:
chezmoi git -- status             # commit anything local FIRST
chezmoi update --dry-run          # preview pull + apply
chezmoi update                    # actually do it
```

`chezmoi git -- <args>` is preferred over `chezmoi cd && git ... && exit` — no subshell needed, output stays in the current shell, and `chezmoi cd` quirks (e.g., shell config reload) are avoided.

## New Machine Bootstrap

```bash
chezmoi init --apply git@github.com:AlexK-Notable/dotfiles.git
```

This clones the source repo to `~/.local/share/chezmoi/`, renders templates against this machine's `hostname`/`os`/`arch`, runs any `run_once_*` scripts, and writes destination files. Idempotent — safe to re-run.

## Project Context

The user's `~/.config/` repo has its own `CLAUDE.md` documenting chezmoi commands under "Configuration Management". When operating in that repo:

- Use *this* skill for chezmoi mechanics, gotchas, and reference detail
- Defer to `~/.config/CLAUDE.md` for project-specific workflow notes (e.g., which files have already been added)
- Don't duplicate guidance — link to it

## Reference Files

Load only when the topic is active:

- **[references/commands.md](references/commands.md)** — Full command reference with flags
- **[references/file-naming.md](references/file-naming.md)** — `dot_`, `private_`, `executable_`, `run_*` prefixes; `.tmpl` suffix
- **[references/templates.md](references/templates.md)** — Go templating, Sprig functions, built-in variables, examples
- **[references/encryption.md](references/encryption.md)** — age setup; recommended for SSH keys & API tokens
- **[references/externals.md](references/externals.md)** — `.chezmoiexternal.toml` for git repos, archives, URL files
- **[references/troubleshooting.md](references/troubleshooting.md)** — Diff/template debugging, recovery from `--force`, encryption failures

## Proactive Recommendations

The user does **not** currently have age encryption configured (`~/.config/chezmoi/` contains only `chezmoistate.boltdb`, no `chezmoi.toml` `[age]` block). Before adding any of:

- `~/.ssh/` private keys
- API tokens (Anthropic, GitHub PAT, OpenAI, etc.)
- Browser session/cookie files
- App secret stores

…suggest setting up encryption first — see [references/encryption.md](references/encryption.md). Encrypting after the fact requires re-adding the file.

<!-- self-learn:begin (do not hand-edit inside; managed by self-learn) -->
<!-- self-learn:end -->
