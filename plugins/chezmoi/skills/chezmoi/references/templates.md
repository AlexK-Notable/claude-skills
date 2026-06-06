# Templates

Chezmoi templates use Go's [text/template](https://pkg.go.dev/text/template) syntax with [Sprig](http://masterminds.github.io/sprig/) functions.

## Table of Contents

- [How templating works](#how-templating-works)
- [Data sources](#data-sources)
- [Built-in variables](#built-in-variables)
- [Common patterns](#common-patterns)
- [Template-aware files (no `.tmpl` needed)](#template-aware-files-no-tmpl-needed)
- [Whitespace control](#whitespace-control)
- [Debugging](#debugging)

## How templating works

A source file with `.tmpl` suffix is rendered through the template engine before being written to destination. The rendered output is what `chezmoi diff` shows and what `chezmoi apply` writes.

```
Source: ~/.local/share/chezmoi/dot_gitconfig.tmpl
  ↓ template render with {{ .chezmoi.* }} data
Target: rendered text
  ↓ chezmoi apply
Destination: ~/.gitconfig
```

## Data sources

Listed in priority order (later overrides earlier):

1. Built-in `chezmoi.*` namespace (hostname, OS, etc.) — always present
2. `.chezmoidata.{toml,yaml,json}` files in the source dir
3. `[data]` section in `~/.config/chezmoi/chezmoi.toml`
4. Promptable values (set via `chezmoi init` interactive prompts)

View everything: `chezmoi data | jq '.'`

## Built-in variables

```
{{ .chezmoi.hostname }}        e.g., "workstation"
{{ .chezmoi.fqdnHostname }}    Fully qualified hostname
{{ .chezmoi.os }}              "linux" / "darwin" / "windows"
{{ .chezmoi.arch }}            "amd64" / "arm64"
{{ .chezmoi.username }}        "user"
{{ .chezmoi.homeDir }}         "/home/user"
{{ .chezmoi.sourceDir }}       "/home/user/.local/share/chezmoi"
{{ .chezmoi.cacheDir }}        "/home/user/.cache/chezmoi"
{{ .chezmoi.osRelease.id }}    Linux distro id (e.g., "cachyos", "arch")
{{ .chezmoi.osRelease.idLike }} Distro family (e.g., "arch")
{{ .chezmoi.kernel }}          Kernel info struct
```

## Common patterns

### Machine-specific email in gitconfig

```
# dot_gitconfig.tmpl
[user]
    name = Your Name
{{- if eq .chezmoi.hostname "work-laptop" }}
    email = you@company.com
{{- else }}
    email = you@example.com
{{- end }}
```

### OS-conditional path setup

```
# dot_zshrc.tmpl
{{- if eq .chezmoi.os "darwin" }}
export PATH="/opt/homebrew/bin:$PATH"
{{- else if eq .chezmoi.os "linux" }}
export PATH="$HOME/bin:$PATH"
{{- end }}
```

### Distro-conditional package install

```bash
# run_once_before_install-packages.sh.tmpl
#!/bin/bash
{{- if and (eq .chezmoi.os "linux") (eq .chezmoi.osRelease.id "cachyos") }}
# User runs sudo themselves — never sudo from Claude
echo "Run: sudo pacman -S --needed git neovim tmux"
{{- end }}
```

### File existence check

```
# dot_zshrc.tmpl
{{- if stat (joinPath .chezmoi.homeDir ".cargo/env") }}
source "$HOME/.cargo/env"
{{- end }}
```

### Lookup in custom data

In `.chezmoidata.toml`:
```toml
[machines.workstation]
    role = "personal"
    monitor_count = 3
```

In a template:
```
{{- $machine := index .machines .chezmoi.hostname -}}
# Role: {{ $machine.role }}, monitors: {{ $machine.monitor_count }}
```

## Template-aware files (no `.tmpl` needed)

These files are templated by default:

- `.chezmoiignore`
- `.chezmoiremove`
- `.chezmoiexternal.toml`
- `.chezmoidata.*` (with restrictions)

This lets ignore patterns be machine-conditional:

```
# .chezmoiignore
{{- if ne .chezmoi.os "darwin" }}
.config/macos-only-app/
{{- end }}
```

## Whitespace control

`{{- ... }}` trims whitespace *before* the tag. `{{ ... -}}` trims *after*. Without trim, template tags leave blank lines in output. For multi-line conditionals, prefer `{{- ... }}` on the opening tag and `{{- end }}` on the close.

## Debugging

```bash
# Render a snippet inline
chezmoi execute-template '{{ .chezmoi.hostname }}'

# Show the rendered version of a managed file (post-template, post-decrypt)
chezmoi cat ~/.gitconfig

# Show diff including template expansion
chezmoi diff ~/.gitconfig

# Render an arbitrary template file with current data
chezmoi execute-template < ~/.local/share/chezmoi/dot_gitconfig.tmpl

# Dump all available data
chezmoi data | jq
```
