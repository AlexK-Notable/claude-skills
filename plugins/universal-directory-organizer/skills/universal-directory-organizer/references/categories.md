# Reference: Action Categories

Sort all discovered items into these groups during Phase 2 (Categorization).

## Group A: Safe to Delete (Regenerable)

Items that can be recreated automatically or are definitively waste:

- **Package manager caches**: `~/.cache/pip`, `~/.cache/uv`, `~/.cache/paru`, `~/.cache/yay`, `~/.npm/_cacache`, `~/.npm/_npx`
- **Build caches**: `~/.cache/go-build`, `~/.cache/cargo`, `__pycache__/`, `*.pyc`
- **Build outputs**: `build/`, `dist/`, `out/`, `target/` (in project contexts)
- **Empty directories**: `rmdir` candidates (verify they're not service placeholders)
- **Trash**: `~/.local/share/Trash/`
- **Incomplete downloads**: `.part`, `.crdownload`, `.tmp` files
- **OS metadata**: `.DS_Store`, `Thumbs.db`, `._*` files

**Action**: Present list with sizes. Offer bulk deletion with user confirmation.

## Group B: Likely Stale (Investigate First)

Items that appear unused but need verification:

- **Old tarballs/archives** sitting in unexpected locations
- **Config test directories** from migration tool experiments
- **Migration leftovers**: `from-windows/`, `from-flash-drive/`, etc.
- **Editor/IDE installs**: `~/.vscode/`, `.local/zed-preview.app/`
- **Old project directories** with no recent git activity
- **Duplicate downloads** (browser re-downloads with `(1)`, `(2)` suffixes)

**Action**: Present each item with last-modified date and brief content summary. Ask user about each.

## Group C: AI Tool Zombies

Directories containing ONLY these artifacts are zombie directories left by AI tools:

| Artifact | Left By |
|----------|---------|
| `in-memoria.db` / `-shm` / `-wal` | In-Memoria (Claude tool) |
| `data/db/zettelkasten.db` | Zettelkasten MCP server |
| `memory_slots/` (empty or stale) | Various AI memory systems |
| `shared_memories/` (empty or stale) | Various AI memory systems |
| `.claude/` (in non-project dirs) | Claude Code project markers |
| `archives/` (empty) | AI tool initialization |

**Check**: If a directory has real content AND these artifacts, only flag the artifacts. If a directory has NOTHING BUT these artifacts, the whole directory is a zombie.

**Action**: List zombie directories. Offer bulk deletion.

## Group D: Scattered Content (Needs Consolidation)

Same domain spread across multiple locations:

- 3D printing files in 3+ directories
- Music/audio across `samples/`, `Projects/Music/`, etc.
- Notes in `notes/`, `data/notes/`, random markdown files
- Screenshots in `screenshots/`, `Pictures/Screenshots/`, `Downloads/`
- Documents scattered across multiple locations

**Action**: Map the clusters. Propose consolidated target. Check for duplicates before merging.

## Group E: Archive Candidates

Data the user might want to keep but doesn't need readily accessible:

- Old project backups
- Migration data with unique content
- Completed project archives
- Large media collections not frequently accessed

**Action**: Propose compression targets. Calculate space savings. Execute archive-verify-delete pattern.

## Group F: Active (Leave Alone)

Items that are actively used and should not be touched:

- Active git repositories
- Active configuration directories
- Application data directories
- Active development toolchains (Go, Rust, Python, Node)
- User scripts directories
- Currently mounted/linked directories

**Action**: Acknowledge and skip. Include in final report for completeness.
