---
name: universal-directory-organizer
description: Interactive directory cleanup and organization for any directory. Use when asked to organize, clean up, declutter, audit, or recover disk space from any directory — home (~/), downloads, projects, or arbitrary paths. Covers scanning, categorizing, deduplication, archival, merging scattered content, and removing stale data. Always interactive — never takes unilateral action. Safety-enforced via PreToolUse guard hooks during active sessions.
---

# Universal Directory Organizer

## Purpose

Systematic, interactive cleanup and organization of any directory on a Linux system. Explores what exists, categorizes by action needed, presents decisions in manageable chunks, and executes only with explicit user approval. Safety-enforced via hook system during active sessions.

## When to Use

- User asks to organize, clean up, or declutter any directory
- User wants to reclaim disk space (home, downloads, project, any path)
- User asks to audit directory contents or check for stale/duplicate files
- User mentions "directory is a mess", "need to free space", etc.
- Post-migration cleanup, project archive, downloads triage
- Explicit path: "organize /path/to/dir"

---

## Core Principles

### 1. NEVER Take Unilateral Action
Every deletion, move, or archive requires explicit user approval. Present findings, recommend actions, wait for decisions. The user's data is sacred ground.

### 2. Explore Before Planning
Read the full landscape before proposing anything. Sizes, dates, contents, relationships between directories — all matter.

### 3. Chunk the Work
Don't present a 50-item plan all at once. Break into digestible groups (5-10 items per chunk) organized by action type or domain. Present sequentially, let the user decide each chunk.

### 4. Check for Duplicates
Before merging directories, ALWAYS check for filename collisions. Compare by name, then verify by size/date if names match.

### 5. Compress Before Deleting
When archiving data the user wants to preserve but not keep loose: compress first, verify the archive, THEN delete originals.

---

## Zettelkasten Integration

znote-mcp provides persistent knowledge across sessions. All organizer notes live in the `"organizer"` project with the `"organizer"` baseline tag.

**Note types**:
- **Hub** (`"log"`): One per session — anchors all other notes via links. Disposable after session.
- **Log** (`"log"`): Working notes from agents (scouts, classification, dedup). Useful during the session, not critical long-term.
- **Permanent** (`"permanent"`): Session summaries and user decisions. These build the knowledge base — future sessions search for them to recall prior work.

**Prior work discovery**: At session start, search for existing organizer knowledge:
1. `zk_search_notes(tags=["organizer", "{domain}"])` — find prior sessions on this domain
2. `zk_fts_search("organizer {target_directory}")` — find notes mentioning this specific path
3. Read any summary or decision notes found — present relevant history to the user

---

## Agent Dispatch

Agents are dispatched via the `Task` tool with `subagent_type: "general-purpose"`. Before dispatching, read the agent prompt from `agents/<name>.md` in the skill directory using the Read tool.

**Available agents**:

| Agent | File | Purpose | Depends On |
|-------|------|---------|------------|
| directory-scout | `agents/directory-scout.md` | Parallel filesystem exploration | Nothing (dispatch in parallel) |
| content-classifier | `agents/content-classifier.md` | Group A-F categorization | Scout note IDs |
| dedup-detector | `agents/dedup-detector.md` | Duplicate/merge detection | Scout + classification note IDs |
| session-reporter | `agents/session-reporter.md` | Summary + prior work discovery | All note IDs + actions taken |

**Every dispatch must include a Session Context block**:

```
## Session Context
- session_id: {from manifest}
- project: "organizer"
- hub_note_id: {from manifest}
- target_directory: {from manifest}
- domain: {from manifest}
- baseline_tags: ["organizer", "{domain}"]
- skill_dir: ~/.claude/skills/universal-directory-organizer
```

**Dispatch rules**:
- Scouts are independent — dispatch 2-3 in parallel (e.g., visible dirs, hidden dirs, specific large subtrees)
- Classifier depends on scouts — wait for all scout note IDs before dispatching
- Dedup depends on classification — wait for classifier output
- Reporter runs last — needs all note IDs and the actions taken during execution
- Agent output includes znote note IDs — link them to the hub note via `zk_create_link`

---

## Note Schema

| Note | Type | Tags | Created By | Persists? |
|------|------|------|------------|-----------|
| Hub | log | `organizer`, `{domain}`, `hub` | Orchestrator | No (session working note) |
| Scout report | log | `organizer`, `{domain}`, `exploration` | directory-scout | No |
| Classification | log | `organizer`, `{domain}`, `categorization` | content-classifier | No |
| Dedup report | log | `organizer`, `{domain}`, `consolidation` | dedup-detector | No |
| Session summary | permanent | `organizer`, `{domain}`, `summary` | session-reporter | **Yes** |
| Decision | permanent | `organizer`, `{domain}`, `decision` | session-reporter | **Yes** |

---

## Session Lifecycle

### Starting a Session

1. Create `~/.claude/organizer-session.json` with this schema:

```json
{
  "version": "1.1",
  "session_id": "<unique-id>",
  "started_at": "<ISO-8601>",
  "target_directory": "/absolute/path",
  "archive_dir": "/absolute/path (optional — additional allowed destination for archives and consolidation moves, e.g. ~/archives)",
  "domain": "home|project|downloads|generic",
  "protected_paths": ["<absolute paths that must not be modified>"],
  "phase": "setup",
  "hub_note_id": null
}
```

2. Search znote for prior sessions: `zk_search_notes(tags=["organizer", "{domain}"])` and `zk_fts_search("organizer {target_directory}")`
3. Create a hub note via `zk_create_note` (title: `"Session: {target} — {date}"`, type: `"log"`, tags: `["organizer", "{domain}", "hub"]`, project: `"organizer"`). Store its ID in the manifest:

```bash
jq '.hub_note_id = "NOTE_ID_HERE"' ~/.claude/organizer-session.json > /tmp/org-manifest.json && mv /tmp/org-manifest.json ~/.claude/organizer-session.json
```

4. Present prior work findings + session plan to user
5. The manifest activates the PreToolUse guard hook — all Bash commands are now validated
6. Protected paths are blocked from destructive operations; destructive commands with operands outside target_directory (or the optional archive_dir) are blocked

**Session ID**: Use `date +%Y%m%d-%H%M%S` for uniqueness.

**Domain selection**: Choose based on target directory or ask the user if ambiguous. Load the corresponding `domains/<domain>.md` profile for domain-specific guidance.

**Protected paths**: Load defaults from the domain profile. Ask the user if they want to add/remove any before starting.

### During a Session

Update `phase` in the manifest as work progresses:

`setup` → `exploration` → `categorization` → `execution` → `consolidation` → `reporting` → `complete`

```bash
# Update phase (use jq to modify in-place)
jq '.phase = "exploration"' ~/.claude/organizer-session.json > /tmp/org-manifest.json && mv /tmp/org-manifest.json ~/.claude/organizer-session.json
```

### Ending a Session

Set `phase: "complete"` in the manifest. The Stop hook will:
- Archive the session manifest + log to `~/.cache/claude-organize/`
- Remove the manifest (deactivating hooks)

### Resuming a Session

Check `~/.cache/claude-organize/` for previous session logs. If a manifest exists at `~/.claude/organizer-session.json`, a session is already active — read it and continue from the current phase.

Also search znote for recent sessions on the same target: `zk_search_notes(tags=["organizer", "summary"])`. Prior session summaries contain before/after data, decisions made, and maintenance recommendations that inform the current session.

---

## Phase Overview

### Phase 1: Session Setup (`setup`)
Create manifest, search znote for prior work on this target/domain, create hub note. Present prior findings and session plan to user before proceeding.

### Phase 2: Exploration (`exploration`)
Dispatch 2-3 **directory-scout** agents in parallel. For `~/`: Scout A handles visible directories (`~/*`), Scout B handles hidden directories (`~/.[!.]*`), Scout C (optional) handles specific large subtrees identified by a quick initial `du -sh ~/`. Collect scout note IDs, link each to the hub note via `zk_create_link`.

### Phase 3: Categorization (`categorization`)
Dispatch **content-classifier** agent with all scout note IDs. Classifier reads scout notes from znote, applies domain profile + Group A-F rules, creates classification note. Present groups to user in chunks (5-10 items per group).

### Phase 4: Execution (`execution`)
User approves/rejects items per chunk. Orchestrator executes approved actions directly (this phase is NOT delegated to an agent — user interaction requires the main context). Create **decision notes** in znote for significant user decisions (e.g., "keep ~/old-projects for hardware schematics"). Track running tally throughout.

### Phase 5: Consolidation (`consolidation`)
Dispatch **dedup-detector** agent with scout + classification note IDs. Detector finds duplicates, re-downloads, version duplicates, and merge opportunities. Present merge proposals to user with collision warnings. Execute approved merges.

### Phase 6: Reporting (`reporting`)
Dispatch **session-reporter** agent with all note IDs + list of actions taken. Reporter creates a **permanent** summary note (persists for future sessions) and optional decision notes. Update hub note with final status. Set phase to `complete`.

---

## Domain Profiles

| Domain | File | When to Use |
|--------|------|-------------|
| Home | `domains/home.md` | Organizing `~/` — protected system paths, home-specific patterns |
| Project | `domains/project.md` | Cleaning build artifacts, dep caches, IDE files in project dirs |
| Downloads | `domains/downloads.md` | Triaging downloads by age, type, installer deduplication |
| Generic | `domains/generic.md` | Any other directory — conservative defaults, asks for context |

Select domain based on target directory. If ambiguous, ask the user.

## Reference Files

| Reference | File | Content |
|-----------|------|---------|
| Categories | `references/categories.md` | Standard action groups A-F for categorization |
| Consolidation | `references/consolidation.md` | Directory merge checklist and common patterns |
| Caches | `references/caches.md` | Common cache directories and regenerability table |
| Artifacts | `references/artifacts.md` | AI tool signatures and zombie directory detection |

## Agent Prompts

| Agent | File | Dispatched In |
|-------|------|---------------|
| Directory Scout | `agents/directory-scout.md` | Phase 2 (parallel) |
| Content Classifier | `agents/content-classifier.md` | Phase 3 |
| Dedup Detector | `agents/dedup-detector.md` | Phase 5 |
| Session Reporter | `agents/session-reporter.md` | Phase 6 |

---

## Safety

During active sessions, a PreToolUse guard hook validates every Bash command:

- **Absolute blocks**: `sudo`, `chmod -R 777`, `chown`, `dd if=`, `mkfs`, `shred`
- **Destructive detection**: `rm`, `rmdir`, `shred`, `unlink`, `truncate`, `mv`, `find … -delete`, `rsync … --delete*`, `git clean`, `dd … of=` — including path-prefixed (`/bin/rm`), quoted, and `bash -c '…'` forms
- **Protected paths**: destructive operands blocked on paths listed in manifest (path-boundary matching — equal, inside, or ancestor of a protected path)
- **Scope enforcement**: operand paths of the destructive segment of a command must be under `target_directory` or the optional `archive_dir` (so `tar … && rm` archival and consolidation moves to the archive dir work)
- **Wildcard depth guard**: `rm -rf` with `*` blocked at depth < 2 from target root

The guard is **fail-closed** — any unexpected error in the hook blocks the command rather than allowing it through. Requires `jq` to be installed.

**Coverage limits**: the guard validates **Bash commands only** — content overwrites made through the Write/Edit tools are not guarded, and the destructive detection is a denylist stopgap, not an allowlist. Explicit user approval before every destructive step remains the primary safety mechanism.

**Hook deployment**: the three hooks live in the plugin at
`plugins/universal-directory-organizer/hooks/` and are symlinked into
`~/.claude/hooks/` by the monorepo's `install.sh`. They must be registered in
`~/.claude/settings.json` (left manual — it is load-bearing):

| Hook | Event | Matcher |
|------|-------|---------|
| `organizer-guard.sh` | `PreToolUse` | `Bash` |
| `organizer-logger.sh` | `PostToolUse` | `Bash` |
| `session-complete.sh` | `Stop` | — |

All three are dormant until a session manifest (`~/.claude/organizer-session.json`)
exists, so they add no overhead outside an active organize session.

---

## Anti-Patterns

1. **Don't delete .steam symlinks** — Steam manages these
2. **Don't touch generated config files** — Wallust/templating outputs
3. **Don't rm -rf caches entirely** — Some are expensive to rebuild
4. **Don't assume empty = useless** — Some dirs are placeholders for running services
5. **Don't chase rolling backups** — `.backup.*` files rotate automatically
6. **Don't fight XDG** — `Desktop/` etc. will be recreated by the desktop environment
7. **Don't delete without checking contents** — Small dirs can hold irreplaceable data
8. **Don't merge without duplicate checking** — Collisions cause silent data loss

---

## Execution Safety Patterns

```bash
# For deletions: explicit paths only, never bare globs
rm -rf /full/path/to/specific/directory

# For archival: compress FIRST, verify, THEN delete
tar -czf ~/archives/name.tar.gz -C /parent directory/
ls -lh ~/archives/name.tar.gz  # verify exists and has size
rm -rf /original/path/

# For moves: verify destination exists
ls /destination/path/
mv /source/item /destination/path/

# For merging: check duplicates FIRST
for item in /source/*; do
  name=$(basename "$item")
  if [[ -e /dest/"$name" ]]; then
    echo "COLLISION: $name"
  fi
done
```

## Running Tally

Track space throughout the session:
```
Before: XXX GB
After:  YYY GB
Recovered: ZZZ GB
```
