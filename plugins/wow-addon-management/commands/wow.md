---
description: Update WoW addons — packaged GitHub releases + CurseForge API + git source, with CurseForge reconciliation, symlink management, and library fetching.
argument-hint: "[status|update|ghrel|curseforge|git|libs|link|check|bugs]" or blank for status
---

# WoW Addon Manager

All logic lives in the repo at `/home/komi/repos/WoW/`, driven by one dispatcher:
`python3 /home/komi/repos/WoW/wow.py <subcommand>`.

Each addon in `addon-registry.json` has a resolved `download` strategy:
- **github-release** — download the packaged release zip (libs bundled, version pinned). Selected via the release's `release.json` (mainline, non-nolib). The default and best path.
- **curseforge** — download the latest retail file from the CurseForge API (numeric `curseforge_project_id`).
- **git** — clone source + `fetch-libs.py` (only addons that publish no packaged release).
- **manual** — needs human attention (e.g. upstream repo gone); skipped by automation.

## Subcommands

Run the matching dispatcher call and report its output. With no argument, run `status`.

| arg | command | what it does |
|-----|---------|--------------|
| `status` (default) | `wow.py status` | registry counts, lockfile, symlink/TOC health — no changes |
| `update` | `wow.py update` | full pass: ghrel → curseforge → git → libs → link, then status |
| `ghrel` | `wow.py ghrel` | download packaged GitHub releases (guarded against CF staleness) |
| `curseforge` | `wow.py curseforge` | download latest retail from CurseForge |
| `git` | `wow.py git` | fetch+reset the source-only clones |
| `libs` | `wow.py libs` | fetch `.pkgmeta` libraries for git clones |
| `link` | `wow.py link` | (re)create relative `AddOns/` symlinks, prune orphans |
| `check` | `wow.py check` | CurseForge reconciliation — flag any GitHub release now behind CF |
| `bugs` | (see skill) | parse BugGrabber SavedVariables and analyze errors |

Pass-through flags work: `wow.py ghrel --addon Bartender4`, `wow.py curseforge --dry-run`.

## Notes

- **Symlinks are relative** (`AddOns/Auctionator -> ../Auctionator`) so moving the WoW install never breaks them. `link` also prunes stale/mis-named links and links each addon by its real folder name (matching WoW's `AddOns/<Folder>/<Folder>.toc` rule).
- **The CF reconciliation guard** (`check`, and built into `ghrel`) uses Firecrawl (`FIRECRAWL_API_KEY`) to read CurseForge's current version and skip installing a GitHub release that is clearly behind CF. This replaces the old Playwright approach.
- **Provenance** for every addon is recorded in `addon-lock.json` (version/tag/date) for pinning and rollback.
- For BugGrabber analysis (`bugs`) and WoW 12.x API-fix patterns, follow the `wow-addon-management` skill.
