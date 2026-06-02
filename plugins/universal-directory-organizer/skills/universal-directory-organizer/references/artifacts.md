# Reference: AI Tool Artifact Signatures

## Zombie Directory Detection

These files/directories are left by various AI coding tools. When they are the **only** contents of a directory, the entire directory is a "zombie" — safe to delete.

| Artifact | Left By | Notes |
|----------|---------|-------|
| `in-memoria.db` | In-Memoria (Claude tool) | SQLite DB, often with `-shm` and `-wal` companions |
| `in-memoria.db-shm` | In-Memoria | Shared memory file |
| `in-memoria.db-wal` | In-Memoria | Write-ahead log |
| `data/db/zettelkasten.db` | Zettelkasten MCP server | Usually nested in `data/db/` subdirectory |
| `memory_slots/` | Various AI memory systems | Empty or contains stale JSON |
| `shared_memories/` | Various AI memory systems | Empty or contains stale JSON |
| `.claude/` | Claude Code | Project markers; check if in a real project first |
| `archives/` (empty) | AI tool initialization | Created speculatively but never used |

## Detection Algorithm

```bash
# For each suspicious directory, count non-artifact items
check_zombie() {
  local dir="$1"
  local real_files
  real_files=$(find "$dir" -maxdepth 2 -type f \
    ! -name "in-memoria.db*" \
    ! -path "*/data/db/zettelkasten.db" \
    ! -path "*/.claude/*" \
    2>/dev/null | wc -l)

  local real_dirs
  real_dirs=$(find "$dir" -maxdepth 1 -type d \
    ! -name "memory_slots" \
    ! -name "shared_memories" \
    ! -name "archives" \
    ! -name "data" \
    ! -name ".claude" \
    ! -path "$dir" \
    2>/dev/null | wc -l)

  if [[ $real_files -eq 0 && $real_dirs -eq 0 ]]; then
    echo "ZOMBIE: $dir"
  else
    echo "MIXED: $dir ($real_files real files, $real_dirs real dirs)"
  fi
}
```

## Important Distinction

- **Pure zombie**: Directory contains ONLY artifacts listed above → safe to delete entirely
- **Mixed content**: Directory has real files AND artifacts → only flag the artifacts for deletion, keep the directory
- **Active project**: `.claude/` in a directory with real source code is normal — it's a project marker, not a zombie sign
