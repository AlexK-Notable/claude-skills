---
name: wow-addon-management
description: This skill should be used when the user asks to "update wow addons", "pull addon repos", "download from curseforge", "manage addon symlinks", "check addon status", "check addon compatibility", "fetch addon libraries", "fix addon errors", "check buggrabber", "parse savedvariables", "fix wow api changes", "secret value errors", "wow window problems", "wow wrong monitor", "gamescope wow", "wow display settings", or runs the /wow command. Provides WoW addon management workflows for Linux including git-based updates, CurseForge API downloads, symlink management, version compatibility checking, library dependency fetching, BugGrabber error analysis, WoW API migration fixes, and display/window management with gamescope.
version: 1.0.0
---

# WoW Addon Management

Manage World of Warcraft retail addons on Linux using git repositories and CurseForge API downloads.

## Architecture

Addons live in two locations:
- **Source:** `/data/battlenet/drive_c/Program Files (x86)/World of Warcraft/_retail_/Interface/` — git clones and CurseForge extractions
- **Active:** `.../Interface/AddOns/` — symlinks pointing back to source directories

WoW loads addons from `AddOns/`. Each subdirectory containing a `.toc` file is treated as a loadable addon.

## Addon Registry

The registry at `/home/komi/repos/WoW/addon-registry.json` defines all addons. Each entry has:
- `name`: Human-readable name
- `source`: `"git"` or `"curseforge"`
- For git: `repo_dir`, `git_url`, `symlink_type` (`"direct"` or `"subdirectories"`), optional `addon_dirs`
- For curseforge: `curseforge_slug`, `curseforge_project_id`, `extract_dir` or `addon_dirs`

### Symlink Patterns

**Direct:** Repo root contains `.toc` files. Symlink the entire repo dir into `AddOns/`.
```
AddOns/Auctionator -> ../../Auctionator
```

**Subdirectories:** Repo contains subdirs that each have `.toc` files. Symlink each subdir individually.
```
AddOns/Titan -> ../../titan-panel/Titan
AddOns/TitanBag -> ../../titan-panel/TitanBag
```

## Scripts

All logic lives in `/home/komi/repos/WoW/`, driven by `wow.py` (the `/wow` command calls it). Each addon has a resolved **`download` strategy** in `addon-registry.json`:

- **github-release** (default/best) — `download-github-release.py` downloads the packaged release zip, choosing the mainline non-nolib asset via the release's `release.json`. Libraries are bundled, the version is pinned, and the CurseForge reconciliation guard (`cfcheck.py`, via Firecrawl) skips installing anything clearly behind CF.
- **curseforge** — `download-curseforge.py` downloads the latest retail file via the CurseForge API (`gameVersionTypeIds` 517 client-side filter, browser headers).
- **git** — `update-git.py` (keyed on `download==git`, **not** `source`) fetch+resets source clones for the handful of addons with no packaged release; `fetch-libs.py` then resolves their `.pkgmeta` externals.
- **manual** — skipped by automation; see the entry's `note`.

`manage-symlinks.py` creates **relative** `AddOns/` symlinks (so install moves don't break them), prunes orphans, and links each addon by its real WoW folder name. `addon-lock.json` records the resolved version/date per addon. Run `wow.py check` to re-verify GitHub releases against CurseForge.

## Version Compatibility

### Interface Versions
WoW uses `## Interface:` in `.toc` files to determine addon compatibility. Current retail: **120000** (12.0.0 Midnight pre-patch, launched Jan 20, 2026).

### Three TOC Version Formats
When checking addon compatibility, ALL three formats must be handled:

1. **Suffix files:** `AddonName_Mainline.toc` / `AddonName_Vanilla.toc` — separate `.toc` per game version
2. **Directive format:** `## Interface-Mainline: 120000` — separate directives per version within one file
3. **Comma-separated:** `## Interface: 11508, 50503, 120000, 120001` — single line listing all supported versions

Format 3 is newer (common since Midnight). WoW reads the full list and picks the matching version. A version scanner that only captures the first number will produce false negatives.

### Git vs CurseForge Version Discrepancies
Some addon authors use the CurseForge packager to build releases but don't push updated TOC versions back to GitHub. The packager can auto-inject Interface version numbers at build time. This means:
- The GitHub source may show `## Interface: 110207`
- The CurseForge release may have `## Interface: 120000`

When a git addon appears outdated, always check the CurseForge version before concluding the addon is truly out of date. If CurseForge is ahead, switch the addon to `source: "curseforge"` in the registry.

### Known Cases (as of Feb 2026)

**CurseForge ahead of GitHub — use CurseForge source:**
- **Home Bound / Bounty Helper** (st182dt): CurseForge has 12.0.0 versions, GitHub repos are stale
- **Titan Panel / TomTom / DejaCharacterStats**: GitHub repos unmaintained for years, CurseForge versions are current
- **OmniCC** (tullamods): CurseForge has v11.2.8 (Dec 2025), GitHub only at 110207. CF project ID 2057. Author has 12.0 beta in pipeline
- **Quartz** (Nevcairiel): CurseForge has v3.7.17 (Jan 2026), GitHub only at 110207. CF project ID 4558

**Abandoned for Midnight (12.0.x) — need replacement:**
- **Shadowed Unit Frames** (Nevcairiel): Author explicitly stated "SUF will NOT be updated" for Midnight due to Blizzard's new addon restrictions. Last retail release v4.4.14 targets 11.2.7. Consider ElvUI unit frames or Blizzard default frames as replacement
- **Addon Control Panel** (Sylvanaar): Original author passed away; last update Jul 2025, targets 11.2.0 only. No successor maintaining for 12.0. Consider Blizzard's built-in addon manager or SimpleAddonManager

**Stale but no CurseForge advantage — stay on git, monitor:**
- **BetterVendorPrice** (MooreaTV): Both git and CF at 11.2.0, no updates since Aug 2025. CF project ID 332558
- **PGFinder** (AnTr95): Both git and CF at 11.2.5, last update Oct 2025. CF project ID 91733
- **KillTrack** (Sharparam): Both git and CF at 11.1.5, no updates since Jun 2025. CF project ID 33976

## Library Dependencies (.pkgmeta Externals)

Git-cloned addons have empty `Libs/` directories because `.pkgmeta` externals are only fetched during CurseForge's packaging pipeline. These must be fetched manually for git clones to work.

### How .pkgmeta Works
The `.pkgmeta` file (YAML) defines an `externals:` block mapping local paths to remote URLs:
```yaml
externals:
  libs/AceAddon-3.0: https://repos.wowace.com/wow/ace3/trunk/AceAddon-3.0
  libs/LibDataBroker-1.1: https://github.com/tekkub/libdatabroker-1-1
```

### Library Fetch Script
`/home/komi/repos/WoW/fetch-libs.py` — Parses all `.pkgmeta` files and downloads missing libraries using a shared cache at `.lib-cache/`.

### Library Source Types

| Source | URL Pattern | Notes |
|--------|------------|-------|
| **Ace3 (CurseForge cache)** | `/ace3/trunk/...` or `/ace3/mainline/trunk/...` | Uses `.lib-cache/ace3-mono/` — **must be CurseForge Release r1390+ (Feb 2026)**. The Stanzilla/Ace3 GitHub mirror is frozen at 2019 (r1200) — do NOT use it |
| **GitHub** | `github.com/...` | `git clone --depth=1`. Some URLs point to subdirs of repos (e.g., `user/repo/subdir`) |
| **SVN (wowace/curseforge)** | `repos.wowace.com/...`, `repos.curseforge.com/...`, `svn://svn.wowace.com/...` | **Completely offline as of Feb 2026**. `fetch-libs.py` automatically falls back to GitHub alternatives via `SVN_GITHUB_FALLBACKS` dict |
| **CurseForge cache** | N/A (local) | For 2 libraries with no GitHub repos (LibButtonGlow-1.0, LibSink-2.0), pre-downloaded from CurseForge into `.lib-cache/cf_*` dirs |
| **Townlong Yak** | `townlong-yak.com/...` | No automated fetch available. Download manually (TaintLess) |

### Key Libraries and Their Sources

- **LibStub, CallbackHandler-1.0**: Inside the Ace3 CurseForge cache (`ace3-mono/`)
- **AceConfigDialog-3.0, AceConfigRegistry-3.0**: Nested inside `ace3-mono/AceConfig-3.0/` (not top-level)
- **LibActionButton-1.0**: `Nevcairiel/LibActionButton-1.0` on GitHub
- **LibDualSpec-1.0**: `AdiAddons/LibDualSpec-1.0` on GitHub (actively maintained)
- **LibQTip-1.0**: `Torhal/LibQTip-1.0` on GitHub (original author)
- **HereBeDragons**: `Nevcairiel/HereBeDragons` on GitHub
- **LibDBIcon-1.0**: `wowace-clone/LibDBIcon-1.0` on GitHub (SVN mirror)
- **LibSharedMedia-3.0**: `wowace-clone/LibSharedMedia-3.0` on GitHub (SVN mirror)
- **LibButtonGlow-1.0**: CurseForge only (project 100218) — no GitHub repo exists
- **LibSink-2.0**: CurseForge only (project 13822) — actively maintained, supports 12.0.1
- **TaintLess**: Only from `townlong-yak.com`. Can copy from Scrap's or ElvUI's embedded version as fallback

### Git Submodules
Some addons (notably **Scrap** and its Jaliborc libraries) use git submodules instead of `.pkgmeta`. These require:
```bash
git submodule update --init --depth=1
```

### Cache Structure
Libraries are cached at `.../Interface/.lib-cache/` with naming conventions:
- `ace3-mono` — Ace3 monorepo (from CurseForge, NOT Stanzilla/Ace3 GitHub)
- `gh_user_repo` — Direct GitHub clones (from `.pkgmeta` GitHub URLs)
- `gh_fallback_<slug>` — GitHub fallbacks for failed SVN checkouts
- `cf_<slug>` — CurseForge downloads for libs with no GitHub source
- `svn_<name>` — Old SVN checkouts (may be stale, kept for reference)
- `<svn-path-based-key>` — Legacy SVN cache entries

The fetch script checks cache before downloading. Cache is shared across all addons — a library fetched for one addon is reused by all others.

## BugGrabber Error Analysis

### SavedVariables Location
BugGrabber errors are stored as plain Lua tables at:
```
WTF/Account/<AccountID>/SavedVariables/!BugGrabber.lua
```

### Parsing Strategy
The file is a Lua table dump. **Do not use brace-counting** to parse entries — the `["locals"]` field contains deeply nested `{}` from Lua table serialization that breaks structural parsers.

Instead, use regex on `["message"]` fields:
```python
re.findall(r'\["message"\]\s*=\s*"(.*?)"', content)
```

### Error Categories
When analyzing BugGrabber output, errors typically fall into:
1. **Missing libraries** — `Cannot find a library instance` / loaded API is nil. Cascading failures from one missing lib cause many errors
2. **WoW API changes** — Secret values, removed globals (see below)
3. **Nil access** — Missing nil guards on toon data, tooltip objects, databroker objects
4. **Load order** — `.toc` referencing wrong file (`.xml` wrapper vs direct `.lua`)

## WoW 12.x API Breaking Changes

### Secret Values (PvP/Instance Restrictions)
Since WoW 12.x, unit-info functions return **restricted/secret values** in PvP and instance contexts. Calling these without protection causes errors:

**Affected functions:** `UnitGUID()`, `UnitIsPlayer()`, `UnitIsUnit()`, `UnitName()`, and other unit-query APIs.

**Fix pattern — always wrap in pcall:**
```lua
local ok, result = pcall(UnitGUID, unitID)
if not ok then return nil end
```

### Removed Globals (12.x)
| Removed Global | Replacement |
|---------------|-------------|
| `DebuffTypeColor` | Define local fallback table: `{Magic={r=0.2,g=0.6,b=1}, Curse={r=0.6,g=0,b=1}, ...}` |
| `GameTooltipTemplate` | Wrap `CreateFrame("GameTooltip",name,parent,"GameTooltipTemplate")` in pcall with fallback |

### Common Fix Locations
- **TipTac/LibFroznFunctions**: Heavy use of `UnitGUID`, `UnitIsPlayer`, `UnitIsUnit` — all need pcall wrapping
- **IRememberYou**: `UnitIsPlayer()` and `UnitName()` in tooltip handlers
- **SavedInstances**: `GameTooltipTemplate` removal, nil toon data throughout

## CurseForge API Notes

- **No auth required.** The public API at `curseforge.com/api/v1/mods/` works without API keys.
- **Direct page scraping returns 403** for plain clients, and the search/project API endpoints are blocked too — only `/files` and `/download` answer (with browser headers). To read a *version* for an addon whose numeric id is unknown, use **Firecrawl** (`FIRECRAWL_API_KEY` → `POST api.firecrawl.dev/v1/scrape` on the addon's files page); `cfcheck.py` wraps this. This supersedes the old Playwright approach.
- **Retail filter unreliable server-side.** The `gameVersionTypeId=517` URL parameter doesn't exclude files with empty `gameVersionTypeIds`. Always filter client-side: check that `517` is in the file's `gameVersionTypeIds` array.
- **Some latest files have empty typeIds.** When an author uploads without tagging game versions, the `gameVersionTypeIds` array is `[]`. The download script correctly skips these and falls back to the most recent properly-tagged file.

## Display & Window Management

WoW runs via Lutris (Wine/GE-Proton) on Hyprland (Wayland) with an NVIDIA RTX 4070 Ti SUPER. Multi-monitor window placement and floating issues are solved with gamescope + Hyprland window rules + Config.wtf settings. See **`references/display-config.md`** for full details.

**Key points:**
- Gamescope wraps WoW in a single virtual display, eliminating multi-monitor confusion
- Hyprland rules pin gamescope to DP-1 (AOC 2560x1440@180, primary gaming monitor)
- No `--force-grab-cursor` — cursor naturally escapes on NVIDIA/Wayland, allowing multi-monitor mouse navigation
- CachyOS + nvidia-open 590+ already has `nvidia_drm.modeset` enabled by default — do NOT add kernel cmdline flags

## Additional Resources

### Reference Files
- **`references/addon-patterns.md`** — Detailed multi-addon repo structures and edge cases
- **`references/library-sources.md`** — Complete library-to-source mapping and SVN fallback strategies
- **`references/display-config.md`** — Gamescope, Hyprland window rules, Config.wtf, and NVIDIA display setup

### Scripts
- **`/home/komi/repos/WoW/fetch-libs.py`** — Library dependency fetcher (parses .pkgmeta, downloads from GitHub/SVN/Ace3)

### Report
- **`/home/komi/repos/WoW/addon-report.md`** — Full addon research with descriptions, version compatibility, overlaps
