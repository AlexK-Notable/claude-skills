# Library Sources and Fetching Reference

## Table of Contents
- [SVN to GitHub Fallbacks](#svn-to-github-fallbacks)
- [Ace3 Monorepo Modules](#ace3-monorepo-modules)
- [Known GitHub Library Mirrors](#known-github-library-mirrors)
- [SVN Reliability Issues](#svn-reliability-issues)
- [Townlong Yak Libraries](#townlong-yak-libraries)
- [Git Submodule Addons](#git-submodule-addons)
- [.pkgmeta Parsing Gotchas](#pkgmeta-parsing-gotchas)
- [Common Error Patterns After Library Fetch](#common-error-patterns-after-library-fetch)
- [WoW 12.x pcall Wrapping Patterns](#wow-12x-pcall-wrapping-patterns)

## SVN to GitHub Fallbacks

`fetch-libs.py` has an `SVN_GITHUB_FALLBACKS` dict that automatically tries GitHub when SVN fails. These are keyed by the normalized SVN project slug:

| SVN Project Slug | GitHub Fallback | Type | Notes |
|------------------|----------------|------|-------|
| `libactionbutton-1-0` | `Nevcairiel/LibActionButton-1.0` | Original author | SVN always 500s |
| `libdualspec-1-0` | `AdiAddons/LibDualSpec-1.0` | Original author | Actively maintained |
| `libqtip-1-0` | `Torhal/LibQTip-1.0` | Original author | Last pushed 2023 |
| `libalts-1-0` | `sylvanaar/libalts-1-0` | Original author | Prat-3.0 author |
| `herebedragons` | `Nevcairiel/HereBeDragons` | Original author | SVN always 500s |
| `libdbicon-1-0` | `wowace-clone/LibDBIcon-1.0` | SVN mirror | git-svn mirror |
| `libsharedmedia-3-0` | `wowace-clone/LibSharedMedia-3.0` | SVN mirror | git-svn mirror |
| `ace-gui-3-0-shared-media-widgets` | `wowace-clone/AceGUI-3.0-SharedMediaWidgets` | SVN mirror | git-svn mirror |
| `libchatanims` | `wowace-clone/LibChatAnims` | SVN mirror | git-svn mirror |
| `libbuttonglow-1-0` | *(none — CurseForge cache)* | CF cache | No GitHub repo exists; uses `cf_libbuttonglow-1-0` cache dir |
| `libsink-2-0` | *(none — CurseForge cache)* | CF cache | No GitHub repo exists; uses `cf_libsink-2-0` cache dir |

### CurseForge Cache Fallbacks

Some libraries have **no GitHub repos at all**. For these, download from CurseForge and place in `.lib-cache/` with a `cf_` prefix:

| Library | CurseForge Project ID | File Pattern | Cache Dir |
|---------|----------------------|-------------|-----------|
| LibButtonGlow-1.0 | 100218 | `cf_libbuttonglow-1-0` | Latest: v1.3.4, Oct 2022 (hasn't been updated since WoW 9.1) |
| LibSink-2.0 | 13822 | `cf_libsink-2-0` | Latest: v12.0.0, Jan 2026 (actively maintained) |

Download URL pattern: `https://www.curseforge.com/api/v1/mods/{projectId}/files/{fileId}/download`

## Ace3 Monorepo Modules

**CRITICAL: Do NOT use Stanzilla/Ace3 from GitHub — it's frozen at Jan 2019 (r1200), 190 SVN revisions behind!**

The Ace3 cache at `.lib-cache/ace3-mono/` should contain CurseForge Release **r1390** (Feb 3, 2026), which supports WoW 12.0.1. Download from CurseForge project ID **13376**.

Modules in ace3-mono:
- AceAddon-3.0
- AceBucket-3.0
- AceComm-3.0
- AceConfig-3.0 (contains sub-modules: AceConfigCmd-3.0, AceConfigDialog-3.0, AceConfigDropdown-3.0, AceConfigRegistry-3.0)
- AceConsole-3.0
- AceDB-3.0
- AceDBOptions-3.0
- AceEvent-3.0
- AceGUI-3.0
- AceHook-3.0
- AceLocale-3.0
- AceSerializer-3.0
- AceTab-3.0
- AceTimer-3.0
- LibStub
- CallbackHandler-1.0

### Nested Ace3 Sub-Modules

Some addons reference Ace3 sub-modules directly (e.g., `AceConfigDialog-3.0`). These live *inside* `AceConfig-3.0/`, not at the top level of ace3-mono. The fetch script handles this by searching subdirectories when a top-level module isn't found.

## Known GitHub Library Sources

Direct GitHub sources for libraries commonly referenced in `.pkgmeta`. These are used when the URL in `.pkgmeta` points directly to GitHub:

```
libdatabroker-1-1          -> tekkub/libdatabroker-1-1
herebedragons              -> Nevcairiel/HereBeDragons
libcustomglow              -> Stanzilla/LibCustomGlow
libdeflate                 -> safeteeWow/LibDeflate
librangecheck-3.0          -> WeakAuras/LibRangeCheck-3.0
libtranslit                -> Vardex/LibTranslit
libclassicspellactioncount -> Ennea/LibClassicSpellActionCount-1.0
libclassiccasterino        -> rgd87/LibClassicCasterino
librealminfo               -> phanx-wow/LibRealmInfo
acegui-3.0-sfx-widgets     -> SFX-WoW/AceGUI-3.0_SFX-Widgets
libcopydialog              -> exochron/LibCopyDialog
mountsrarity               -> sgade/MountsRarity
libbattlepettooltipline    -> plusmouse/LibBattlePetTooltipLine
details-framework          -> Tercioo/Details-Framework
libactionbutton-1.0        -> Nevcairiel/LibActionButton-1.0
libdispel                  -> tukui-org/LibDispel
libspellrange-1.0          -> ascott18/LibSpellRange-1.0
libquestxp                 -> MrFox42/libquestxp
```

## SVN Reliability Issues

As of Feb 2026, WowAce SVN is **completely down**:

- **`svn://svn.wowace.com`**: DNS resolution fails (`Unknown hostname`)
- **`repos.wowace.com`**: HTTP 500 Internal Server Error on all requests
- **`repos.curseforge.com`**: Same infrastructure, same failures

This is NOT intermittent — the service appears permanently offline.

### Automatic Fallback (fetch-libs.py)
The `SVN_GITHUB_FALLBACKS` dict in `fetch-libs.py` handles this automatically:
1. SVN checkout is attempted first (for forward compatibility if SVN returns)
2. On failure, the script extracts the project slug from the SVN URL
3. Looks up the slug in `SVN_GITHUB_FALLBACKS`
4. If `git_url` is set: clones from GitHub to `gh_fallback_<slug>` cache dir
5. If `git_url` is None: uses a local CurseForge cache dir (for libs with no GitHub repos)
6. Copies from cached source to the addon's lib directory

### Manual Fallback Strategy (for new libraries not in the fallback dict)
1. Search GitHub: `gh search repos "<library-name>"` — check `wowace-clone` org first
2. If no GitHub source exists, find the CurseForge project page and download the latest release
3. Place in `.lib-cache/cf_<slug>` and add a `(None, "cf_<slug>")` entry to `SVN_GITHUB_FALLBACKS`

## Townlong Yak Libraries

**TaintLess** (`townlong-yak.com/addons/taintless`): Cannot be automated. Solutions:
- Manual download from `https://www.townlong-yak.com/addons/taintless`
- Copy from Scrap's embedded `Libs/TaintLess/` if available
- Copy from ElvUI's embedded copy if available

## Git Submodule Addons

Some addons use git submodules instead of `.pkgmeta` for library dependencies:

- **Scrap**: Uses submodules for `Jaliborc/LibJaliborc`, `Jaliborc/Sushi-3.2`, `Jaliborc/Poncho-2.0`
- Fix: `cd <addon_dir> && git submodule update --init --depth=1`

Symptom: `Libs/` contains empty subdirectories (the submodule checkouts haven't happened).

## .pkgmeta Parsing Gotchas

1. **Tabs vs spaces**: Some `.pkgmeta` files use tabs. Replace tabs with spaces before YAML parsing:
   ```python
   content = content.replace('\t', '  ')
   ```

2. **YAML aliases/anchors**: ElvUI uses a YAML alias `*Mainline` that `yaml.safe_load()` can't resolve (the anchor is defined in a different section). This produces a parse warning but is harmless — ElvUI works fine from CurseForge source.

3. **Fallback manual parsing**: When YAML parsing fails entirely, manually extract `externals:` block by looking for indented `key: url` lines.

4. **URL formats in externals**:
   - Simple: `libs/LibFoo: https://github.com/author/LibFoo`
   - Dict with url: `libs/LibFoo:\n  url: https://...\n  tag: v1.0`
   - The `tag` or `branch` field is informational — for shallow clones, just use HEAD.

5. **Python `rstrip()` vs `removesuffix()`**: NEVER use `rstrip(".git")` to remove a `.git` suffix from URLs. Python's `rstrip` strips *characters* from a set, not a suffix string. `"LibCopyDialog".rstrip(".git")` produces `"LibCopyDialo"` because `g` is in the character set. Always use `removesuffix(".git")` (Python 3.9+).

## Common Error Patterns After Library Fetch

Even after all libraries are fetched, some addons may still error. Common causes:

### .toc referencing wrong file
**Symptom**: `Cannot find Libs\LibFoo\LibFoo.xml`
**Cause**: `.toc` references an `.xml` wrapper that doesn't exist in the git source; the `.lua` file exists directly.
**Fix**: Edit `.toc` to reference `.lua` directly instead of `.xml`.

### Cascading library failures
**Symptom**: 20+ errors from one addon, all "Cannot find a library instance" or "API is nil"
**Cause**: One missing foundational library (LibStub, CallbackHandler) causes all dependent libraries to fail.
**Fix**: Ensure LibStub and CallbackHandler-1.0 are present. They're in the Ace3 monorepo.

### CurseForge packager stripping
**Symptom**: Git source has `#@no-lib-strip@` blocks in `.toc` with library loads inside.
**Explanation**: CurseForge packager strips these blocks in releases (users get standalone libs). In git clones, these blocks are active and the embedded libs must be present.

## WoW 12.x pcall Wrapping Patterns

### Unit Info Functions
```lua
-- BEFORE (crashes in PvP/instance):
local guid = UnitGUID(unit)

-- AFTER:
local ok, guid = pcall(UnitGUID, unit)
if not ok then guid = nil end
```

### Functions Requiring pcall in 12.x
- `UnitGUID(unit)`
- `UnitIsPlayer(unit)`
- `UnitIsUnit(unit1, unit2)`
- `UnitName(unit)` (returns secret in some contexts)
- `C_MountJournal.GetMountFromSpell(spellID)` (can error on restricted data)

### DebuffTypeColor Replacement
```lua
-- Global was removed in 12.x. Define locally:
local DebuffTypeColor = _G.DebuffTypeColor or {
    Magic   = { r = 0.20, g = 0.60, b = 1.00 },
    Curse   = { r = 0.60, g = 0.00, b = 1.00 },
    Disease = { r = 0.60, g = 0.40, b = 0.00 },
    Poison  = { r = 0.00, g = 0.60, b = 0.00 },
    none    = { r = 0.80, g = 0.00, b = 0.00 },
}
```

### GameTooltipTemplate Removal
```lua
-- Wrap in pcall with fallback:
local ok, tooltip = pcall(CreateFrame, "GameTooltip", "MyScanTooltip", UIParent, "GameTooltipTemplate")
if not ok then
    tooltip = CreateFrame("GameTooltip", "MyScanTooltip", UIParent)
    -- Manually add font strings if needed for scanning
end
```
