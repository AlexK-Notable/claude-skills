# Domain: Downloads Directory

## Protected Paths (Default)

Downloads directories rarely need protected paths. If the user has subdirectories they curate:

```json
[]
```

Ask the user before starting — they may have organized subdirectories worth preserving.

## Exploration Commands

```bash
# Overview
ls -la <target>/

# Size breakdown
du -sh <target>/ && du -sh <target>/*/ 2>/dev/null | sort -rh

# Count files by extension
find <target> -maxdepth 1 -type f | sed 's/.*\.//' | sort | uniq -c | sort -rn

# Files older than 90 days
find <target> -maxdepth 1 -type f -mtime +90 -exec ls -lh {} \; | sort -k5 -rh

# Files older than 365 days
find <target> -maxdepth 1 -type f -mtime +365 -exec ls -lh {} \; | sort -k5 -rh

# Largest files
find <target> -maxdepth 1 -type f -exec ls -lh {} \; | sort -k5 -rh | head -20

# Duplicate filenames (same name, might be re-downloads)
find <target> -maxdepth 1 -type f | xargs -I{} basename {} | sort | uniq -d
```

## Downloads-Specific Categories

### Age-Based Triage

| Age | Default Action | Rationale |
|-----|---------------|-----------|
| < 7 days | Keep | Recent, likely still needed |
| 7-30 days | Review | May still be relevant |
| 30-90 days | Likely stale | Offer to delete or sort |
| 90-365 days | Stale | Strong delete candidate |
| > 365 days | Very stale | Delete unless specifically valuable |

Present age groups as separate chunks for user review.

### File Type Groups

| Type | Extensions | Action |
|------|-----------|--------|
| Installers | `.AppImage`, `.deb`, `.pkg.tar.zst`, `.rpm`, `.run`, `.sh` (installers) | Delete after installing |
| Archives | `.tar.gz`, `.zip`, `.7z`, `.rar`, `.tar.xz`, `.tar.bz2` | Extract or delete |
| Disk images | `.iso`, `.img` | Delete after use |
| Documents | `.pdf`, `.docx`, `.xlsx`, `.odt` | Move to `~/Documents/` |
| Media | `.mp3`, `.mp4`, `.mkv`, `.jpg`, `.png`, `.gif` | Move to appropriate dir |
| Source code | `.tar.gz` (source), `.zip` (repos) | Move to `~/repos/` or delete |
| Temporary | `.part`, `.crdownload`, `.tmp` | Safe to delete |

### Browser Re-Download Detection

Browsers append `(1)`, `(2)`, etc. to duplicate downloads:
```bash
# Find re-downloaded files
find <target> -maxdepth 1 -type f -regex '.*([0-9]+)\..*' | head -20
```

For each re-download group:
1. Compare file sizes — if identical, keep newest, delete others
2. If sizes differ, the content may have changed — ask user

### Installer Deduplication

Look for multiple versions of the same software:
```bash
# Find similar filenames (common with version-numbered downloads)
ls <target>/*.AppImage <target>/*.deb 2>/dev/null | sort
```

Keep only the latest version unless user needs specific older versions.

## Downloads Cleanup Patterns

```bash
# Remove incomplete downloads
find <target> -maxdepth 1 -type f \( -name "*.part" -o -name "*.crdownload" -o -name "*.tmp" \) -delete

# Remove macOS metadata (if transferred from Mac)
find <target> -name ".DS_Store" -o -name "._*" -delete 2>/dev/null

# Archive old documents before deleting
tar -czf ~/archives/old-downloads-$(date +%Y%m%d).tar.gz -C <target> <files>
```
