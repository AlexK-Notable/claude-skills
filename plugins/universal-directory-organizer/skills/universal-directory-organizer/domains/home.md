# Domain: Home Directory (~/)

## Protected Paths (Default)

These paths must be listed in `protected_paths` when organizing `~/`:

```json
[
  "~/.config",
  "~/.local",
  "~/.ssh",
  "~/.gnupg",
  "~/.claude",
  "~/repos",
  "~/bin"
]
```

> Shown with `~` for portability. Expand `~` to the absolute `$HOME` when you
> write these into `protected_paths` — the guard hook matches literal absolute
> paths and does **not** expand `~` or `$HOME`.

Ask the user if they want to add more (e.g., `~/.steam`, `~/.wine` if actively gaming).

## Exploration Commands

```bash
# Top-level listing (visible + hidden)
ls -la ~/

# Size of each visible directory (sorted)
du -sh ~/*/ 2>/dev/null | sort -rh

# Size of significant hidden directories
du -sh ~/.cache ~/.local ~/.config ~/.wine* ~/.steam 2>/dev/null | sort -rh

# Total home directory size
du -sh ~/

# Drive capacity context
df -h /home

# Find large files (>100MB) directly in ~/
find ~/ -maxdepth 1 -type f -size +100M -exec ls -lh {} \;

# Find empty directories (depth 1 only)
find ~/ -maxdepth 1 -type d -empty
```

## Home-Specific Categories

### System-Managed (Leave Alone)
- `~/.config/` — active configuration (Wallust generates files here)
- `~/.local/` — application data, user binaries
- `~/.ssh/`, `~/.gnupg/` — security keys
- `~/.claude/` — Claude Code configuration and skills
- `~/repos/` — active git repositories
- `~/bin/` — user scripts (in PATH)
- `~/screenshots/` — screenshot directory (XDG_SCREENSHOTS_DIR)

### Likely Stale
- Old tarballs/archives sitting directly in ~/
- Config test directories (migration tool experiments)
- Migration leftovers: `from-windows/`, `from-flash-drive/`, etc.
- Editor/IDE installs: `~/.vscode/`, `.local/zed-preview.app/`
- Directories with only AI tool artifacts (see `references/artifacts.md`)

### Cache Directories
See `references/caches.md` for the full table. Key ones for home:
- `~/.cache/pip`, `~/.cache/uv` — Python package caches
- `~/.cache/paru`, `~/.cache/yay` — AUR helper caches
- `~/.npm/_cacache` — npm cache
- `~/.cache/huggingface` — ML model cache (can be huge)
- `~/.local/share/Trash/` — trash (regenerable by definition)

## Home-Specific Anti-Patterns

- **Don't touch `~/.config/` generated files** — Wallust templates generate 19+ files
- **Don't delete `~/.steam` symlinks** — Steam manages its own directory structure
- **Don't rm -rf `~/.cache` entirely** — Some caches (playwright, wallust) are slow to rebuild
- **XDG directories** (`Desktop/`, `Documents/`, `Downloads/`, `Pictures/`) get auto-recreated — if empty after cleanup, just leave them

## Consolidation Targets

Common scattered-content patterns in home directories:

| Scattered | Consolidate To |
|-----------|---------------|
| `samples/`, `ableton-things/`, `Projects/Music/` | `~/music/` |
| Multiple 3D printing directories | `~/3d-printing/` |
| `notes/`, `data/notes/`, loose `.md` files | `~/notes/` |
| `archives/`, `backups/`, scattered `.tar.gz` | `~/archives/` |
| Random PDFs, ebooks across multiple dirs | `~/documents/` |
