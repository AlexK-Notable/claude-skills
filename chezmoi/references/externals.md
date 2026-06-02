# External Files (`.chezmoiexternal.toml`)

For files chezmoi shouldn't *contain* but should *fetch* — large binaries, vendored deps, plugin managers, theme repos. Defined in `~/.local/share/chezmoi/.chezmoiexternal.toml` (this file is template-aware by default).

## Table of Contents

- [External types](#external-types)
- [Common patterns](#common-patterns)
- [Refresh behavior](#refresh-behavior)
- [Templating](#templating)
- [When NOT to use externals](#when-not-to-use-externals)

## External types

| Type | Use for |
|---|---|
| `file` | Single file from URL |
| `archive` | Tarball/zip — extract entire archive |
| `archive-file` | Tarball/zip — extract one file |
| `git-repo` | Clone or pull a git repo |

## Common patterns

### Vim-plug (single file)

```toml
[".vim/autoload/plug.vim"]
    type = "file"
    url = "https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim"
    refreshPeriod = "168h"
```

### Tmux plugin manager (git repo)

```toml
[".tmux/plugins/tpm"]
    type = "git-repo"
    url = "https://github.com/tmux-plugins/tpm.git"
    refreshPeriod = "168h"
```

`git-repo` clones if missing, `git pull`s if present.

### Oh-My-Zsh (archive)

```toml
[".oh-my-zsh"]
    type = "archive"
    url = "https://github.com/ohmyzsh/ohmyzsh/archive/master.tar.gz"
    exact = true
    stripComponents = 1
    refreshPeriod = "168h"
```

- `exact = true` — unmanaged children get removed (so the dir matches the archive exactly)
- `stripComponents = 1` — peels the `ohmyzsh-master/` top dir from the tar

### Single binary from a release tarball

```toml
[".local/bin/age"]
    type = "archive-file"
    url = "https://github.com/FiloSottile/age/releases/download/v1.1.1/age-v1.1.1-linux-amd64.tar.gz"
    path = "age/age"            # path inside the archive
    executable = true
    refreshPeriod = "720h"      # 30 days
```

### Conditional checksum verification

```toml
[".local/bin/age"]
    type = "archive-file"
    url = "https://github.com/FiloSottile/age/releases/download/v1.1.1/age-v1.1.1-linux-amd64.tar.gz"
    path = "age/age"
    executable = true
    checksum.sha256 = "..."     # halt if upstream tampering
```

## Refresh behavior

| Trigger | Outcome |
|---|---|
| First `apply` after adding the external | Always fetched |
| `apply` within `refreshPeriod` | Cached (in `~/.cache/chezmoi/`), not re-fetched |
| `chezmoi apply -R` or `--refresh-externals` | Force re-fetch all |
| Cache cleared manually | Re-fetched on next apply |

`refreshPeriod` accepts Go duration strings: `"24h"`, `"168h"` (week), `"720h"` (~month).

## Templating

`.chezmoiexternal.toml` is template-aware — conditionals based on OS/host work directly:

```toml
{{- if eq .chezmoi.os "linux" }}
[".local/bin/age"]
    type = "archive-file"
    url = "https://github.com/FiloSottile/age/releases/download/v1.1.1/age-v1.1.1-linux-amd64.tar.gz"
    path = "age/age"
    executable = true
{{- else if eq .chezmoi.os "darwin" }}
[".local/bin/age"]
    type = "archive-file"
    url = "https://github.com/FiloSottile/age/releases/download/v1.1.1/age-v1.1.1-darwin-amd64.tar.gz"
    path = "age/age"
    executable = true
{{- end }}
```

## When NOT to use externals

- **You want pinned-by-version reproducibility** — vendor the file directly into source
- **You need offline machine setup** — vendor it
- **The upstream URL is unstable or rate-limited** — vendor it
- **The file is small text** (< few KB) — just commit it

Externals shine for "I want the latest stable" with weekly-ish refresh, or for binaries too large to commit.
