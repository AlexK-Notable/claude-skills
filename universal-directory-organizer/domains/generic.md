# Domain: Generic Directory

## When This Applies

Use this profile when the target directory doesn't match home, project, or downloads patterns. Examples:
- Arbitrary data directories (`/mnt/data/`, `/tmp/workspace/`)
- Shared directories, external drives
- Directories the user points you at with no clear domain

## Protected Paths (Default)

Start with an empty list — ask the user what (if anything) should be protected:

```json
[]
```

**Always ask** before starting: "Are there any subdirectories I should never modify?"

## Exploration Commands

```bash
# Overview
ls -la <target>/

# Size breakdown
du -sh <target>/ && du -sh <target>/*/ 2>/dev/null | sort -rh

# File count and types
find <target> -maxdepth 2 -type f | wc -l
find <target> -maxdepth 2 -type f | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -20

# Age distribution
echo "=== Last 7 days ===" && find <target> -maxdepth 1 -mtime -7 | wc -l
echo "=== 7-30 days ===" && find <target> -maxdepth 1 -mtime +7 -mtime -30 | wc -l
echo "=== 30-90 days ===" && find <target> -maxdepth 1 -mtime +30 -mtime -90 | wc -l
echo "=== 90+ days ===" && find <target> -maxdepth 1 -mtime +90 | wc -l

# Largest items
du -sh <target>/*/ 2>/dev/null | sort -rh | head -10
find <target> -maxdepth 1 -type f -size +10M -exec ls -lh {} \; | sort -k5 -rh
```

## Conservative Defaults

Since we don't know the domain:

1. **Never assume anything is safe to delete** — ask about everything
2. **Present smaller chunks** (3-5 items instead of 5-10)
3. **Describe what you see** before categorizing — let the user correct your assumptions
4. **Check for symlinks** — the directory may be part of a larger structure
5. **Check permissions** — you may not own all files

```bash
# Check for symlinks
find <target> -maxdepth 1 -type l -exec ls -la {} \;

# Check ownership
ls -la <target>/ | awk '{print $3}' | sort | uniq -c | sort -rn
```

## Generic Categorization

Apply the standard Groups A-F from `references/categories.md` but with more caution:
- Group A (Safe to Delete): Only empty dirs and clearly temporary files
- Group B (Investigate): Everything else — present to user for classification
- Group F (Leave Alone): Anything you're unsure about

When in doubt, classify as Group B (investigate) rather than Group A (safe to delete).
