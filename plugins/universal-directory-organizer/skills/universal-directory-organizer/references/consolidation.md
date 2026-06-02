# Reference: Directory Consolidation

## Merge Checklist

Before merging any directories:

1. **List all top-level directories** in the target
2. **Identify domain clusters** — multiple dirs serving the same purpose
3. **Propose merges** with clear target structure (show the user)
4. **Check for duplicates** between source and target:

```bash
# Find duplicate filenames between two directories
comm -12 <(ls source/ | sort) <(ls target/ | sort)

# For each duplicate, compare sizes
for f in $(comm -12 <(ls source/ | sort) <(ls target/ | sort)); do
  echo "=== $f ==="
  ls -lh source/"$f" target/"$f"
done
```

5. **Resolve collisions** — ask user which to keep (or rename)
6. **Execute moves** — `mv source/* target/`
7. **Remove empty source dirs** — `rmdir source/` (fails safely if not empty)

## Common Consolidation Patterns

| Scattered | Consolidated | Subdirecture Suggestion |
|-----------|-------------|------------------------|
| `samples/`, `ableton-things/`, `Projects/Music/` | `~/music/` | `samples/`, `projects/`, `misc/` |
| Multiple 3D printing dirs | `~/3d-printing/` | `models/`, `prints/`, `firmware/` |
| `notes/`, `data/notes/`, loose `.md` files | `~/notes/` | By topic or tool |
| `archives/`, `backups/`, scattered `.tar.gz` | `~/archives/` | By date or project |
| Random PDFs, ebooks across dirs | `~/documents/` | `books/`, `manuals/`, `papers/` |
| Screenshots in multiple locations | `~/screenshots/` | Already XDG default |

## XDG Directory Behavior

Some directories are auto-recreated by desktop environments:

| Directory | XDG Recreates? | Recommendation |
|-----------|---------------|---------------|
| `~/Desktop/` | Yes | Leave alone even if empty |
| `~/Documents/` | Yes | Use as consolidation target |
| `~/Downloads/` | Yes | Leave alone, clean contents |
| `~/Pictures/` | Yes | Use as consolidation target |
| `~/Music/` | Yes | Use as consolidation target |
| `~/Videos/` | Yes | Use as consolidation target |

Deleting XDG directories just triggers recreation — don't fight it.

## Post-Merge Verification

After consolidation:
1. Verify all files arrived: `ls target/ | wc -l`
2. Check source is empty: `ls source/` (should error or be empty)
3. Remove source: `rmdir source/`
4. Update any references (symlinks, scripts, bookmarks) pointing to old paths
