# Addon Repository Structure Patterns

## Pattern A: Direct (Single Addon at Root)

Most common pattern. The repo IS the addon — `.toc` files at the root level.

Examples: Auctionator, HandyNotes, Bartender4, WarpDeplete, Rarity

```
repo-root/
├── AddonName.toc
├── AddonName_Mainline.toc  (optional, for retail)
├── AddonName_Vanilla.toc   (optional, for classic)
├── Core.lua
├── ...
└── .git/
```

Symlink strategy: `AddOns/repo-root -> ../../repo-root`

## Pattern B: Subdirectories (Multi-Addon Package)

The repo contains multiple addon directories, each with their own `.toc` files.

### titan-panel (10 sub-addons)
```
titan-panel/
├── Titan/Titan.toc
├── TitanBag/TitanBag.toc
├── TitanClock/TitanClock.toc
├── TitanGold/TitanGold.toc
├── TitanLocation/TitanLocation.toc
├── TitanLootType/TitanLootType.toc
├── TitanPerformance/TitanPerformance.toc
├── TitanRepair/TitanRepair.toc
├── TitanVolume/TitanVolume.toc
└── TitanXP/TitanXP.toc
```

### ElvUI (3 sub-addons)
```
ElvUI/
├── ElvUI/ElvUI_Mainline.toc
├── ElvUI_Libraries/ElvUI_Libraries_Mainline.toc
└── ElvUI_Options/ElvUI_Options_Mainline.toc
```

### TipTac (4 sub-addons)
```
TipTac/
├── TipTac/TipTac.toc
├── TipTacItemRef/TipTacItemRef.toc
├── TipTacOptions/TipTacOptions.toc
└── TipTacTalents/TipTacTalents.toc
```

### OmniCC (2 sub-addons)
```
OmniCC/
├── OmniCC/OmniCC.toc
└── OmniCC_Config/OmniCC_Config.toc
```

### Shadowed Unit Frames (2 sub-addons) — ABANDONED for 12.0.x
```
ShadowedUnitFrames/
├── ShadowedUnitFrames/ShadowedUnitFrames.toc
└── ShadowedUF_Options/ShadowedUF_Options.toc
```
**Note:** Author explicitly stated SUF will NOT be updated for Midnight (12.0.x) due to Blizzard's addon restrictions. Last retail version targets 11.2.7.

Symlink strategy: One symlink per sub-addon directory.

## Pattern C: Single Addon in Subdirectory

Some repos wrap a single addon in a subdirectory (often matching the addon name).

Examples: SavedInstances, MinimapButtonButton, TokenChecker, Farm-Friend, FastAccountGold, BetterVendorPrice

```
SavedInstances/
└── SavedInstances/SavedInstances.toc
```

Symlink strategy: `AddOns/SavedInstances -> ../../SavedInstances/SavedInstances`

## TOC Version Formats

WoW uses `## Interface:` in `.toc` files to determine compatibility. There are three formats:

### Format 1: Suffix Files
Separate `.toc` files per game version, identified by filename suffix:
- `*_Mainline.toc` — Retail (current expansion)
- `*_Mists.toc` — MoP Remix Classic
- `*_TBC.toc` — TBC Classic
- `*_Vanilla.toc` — Classic Era
- `*_Wrath.toc` — WotLK Classic
- `*_Cata.toc` — Cataclysm Classic

WoW loads the `.toc` matching the client version. All files coexist in the same directory.

### Format 2: Multi-Interface Directives
A single `.toc` file with version-specific directives:
```
## Interface: 120000
## Interface-Vanilla: 11507
## Interface-Cata: 40402
```

### Format 3: Comma-Separated (Newest)
A single `## Interface:` line listing all supported versions:
```
## Interface: 11508, 20505, 38000, 50503, 120000, 120001
```

WoW reads the full list and matches against the client. This format is common for lightweight utility addons that work identically across all game versions (e.g., BugGrabber, Better Fishing, NPC Time).

**Important for version scanning:** A regex like `re.search(r"^## Interface:\s*(\d+)")` only captures the first number. For comma-separated format, this could return a Classic version (11508) even though the addon fully supports Retail (120000). Always parse the full comma-separated list.

## CurseForge Addon Extraction

CurseForge zips typically extract to a directory matching the addon name. Multi-addon packages extract to multiple directories. After unzipping, scan for `.toc` files to verify correct extraction.

Common extraction patterns:
- Single addon: `BugGrabber.zip` -> `!BugGrabber/!BugGrabber.toc`
- Multi-addon: `titan-panel.zip` -> `Titan/Titan.toc`, `TitanBag/TitanBag.toc`, etc.
- Simple: `Leatrix_Plus.zip` -> `Leatrix_Plus/Leatrix_Plus.toc`

## Accountant Special Case

The Accountant git repo contains only a LICENSE and README — no actual addon code. It must be sourced from CurseForge.

## Git vs CurseForge Freshness

Some addon authors publish to CurseForge via the CurseForge packager but don't push the built/tagged versions back to their GitHub repo. The packager auto-generates:
- Multi-version `.toc` files with correct Interface numbers
- Version strings (replacing `@project-version@` placeholders)
- Library stripping (removing bundled libs marked with `#@no-lib-strip@`)

This means the GitHub repo can appear outdated while the CurseForge release is fully current. When an addon seems incompatible, always check CurseForge before assuming the author hasn't updated.

## .toc XML vs Lua References

Some `.toc` files reference library `.xml` wrapper files that don't exist in the git source. The CurseForge packager may generate these wrappers, or the git repo may have switched from `.xml` to direct `.lua` without updating the `.toc`.

**Example (Syndicator):**
```
# .toc had:
Libs\LibBattlePetTooltipLine\LibBattlePetTooltipLine.xml
# But only this existed:
Libs\LibBattlePetTooltipLine\LibBattlePetTooltipLine.lua
```

**Fix:** Edit `.toc` to reference `.lua` directly. This is safe — the `.xml` wrapper typically just loads the `.lua` file anyway.

## #@no-lib-strip@ Blocks

In git clones, `#@no-lib-strip@` blocks in `.toc` files are NOT processed — they're treated as comments and the lines inside them ARE loaded. This means embedded libraries inside these blocks must actually exist in git clones, unlike CurseForge releases where the packager strips them (users get standalone libs instead).

If a git-cloned addon errors on library files referenced inside `#@no-lib-strip@` blocks, the libraries need to be fetched via `.pkgmeta` externals or git submodules.
