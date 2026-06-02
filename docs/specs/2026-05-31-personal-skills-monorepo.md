# Personal Skills Monorepo — Design Spec

- **Date:** 2026-05-31
- **Status:** Proposed — awaiting your approval before any implementation
- **Repo:** `AlexK-Notable/claude-skills` (repurposed as the umbrella)

## 1. Goal

Consolidate every personally-authored Claude Code skill into **one private, transportable git repo**, registered as a Claude Code **`source: directory` marketplace** — plugins *properly installed* yet **read live** from the repo (verified mechanic) — with `~/bin` CLI symlinks, a **one-command setup script**, and a **"remote always current"** sync. The repo is the portable source of truth; Claude loads its plugins live from it.

## 2. Scope

### In — merged into the umbrella, commit history preserved
| Skill | Current home |
|---|---|
| `bitwarden-cli` | real dir in `~/.claude/skills` (today's bws work) + stale dup in komi-home-toolkit |
| `home-network` | `~/repos/home-network-skill` (the komi-home-toolkit marketplace) |
| `cron-claude` | `~/repos/claude-dirs/cron-claude` |
| `hypr-doctor` | `~/repos/claude-dirs/hypr-doctor` |
| `chezmoi` | real dir in `~/.claude/skills` |
| `universal-directory-organizer` | real dir in `~/.claude/skills` |

### Out
- **`obsidian-plugin-dev`**, **`qmk-zmk-animation-conversion`** — yours, but too project-specific for a daily-driver / maintenance umbrella. **Preserved, not deleted** (retained in `claude-skills` git history; one symlink to reactivate if ever needed) — just not in the active umbrella.
- **`skill-developer`** — third-party. `SKILL.md` is byte-identical to `claude-code-infrastructure-showcase`; Prisma/React/`database-verification` examples; zero personal markers. *Its activation system (hook + rules) is still ported — see §6.*
- **`ccx`** — a tool, not a skill (your call).
- **`claude-nirvana`** — not a skill (in-memoria/MCP memory experiment, no `SKILL.md`).
- All other third-party repos under `~/repos/claude-dirs/`.

## 3. Target architecture

```
~/repos/claude-skills/                    AlexK-Notable/claude-skills — a marketplace
├── .claude-plugin/marketplace.json       lists each skill as a plugin
├── install.sh                            idempotent setup (symlinks, rules merge, hook, autosync)
├── hooks/
│   └── skill-activation-prompt.ts        bundled for portability
├── plugins/
│   ├── bitwarden-cli/
│   │   ├── .claude-plugin/plugin.json
│   │   ├── skill-rules.fragment.json
│   │   ├── skills/bitwarden-cli/         SKILL.md + references/
│   │   └── scripts/bws-secret-add
│   ├── home-network/                     skills/… + scripts/… (capture loop → umbrella remote)
│   ├── cron-claude/                      skills/… + CLI       (subtree, history preserved)
│   ├── hypr-doctor/                      skills/… + bin/      (subtree, history preserved)
│   ├── chezmoi/   universal-directory-organizer/
└── docs/specs/2026-05-31-personal-skills-monorepo.md   (this file)
```

**Deployment — `source: directory` marketplace (verified live):** registering `~/repos/claude-skills` as a directory-source marketplace makes its plugins *properly installed* yet **read live from the repo** — edits take effect next session / after `/reload-plugins`, with **no skill symlinks** (Claude Code reads directory-source marketplaces in place; confirmed against the `nsys-marketplace` directory source on this machine). Plugin skills are namespaced (`claude-skills:<name>`), so they can't collide. Symlinks are used **only for `~/bin` shell CLIs** (`scan-lan`, etc.), not for skill loading. `komi-home-toolkit/marketplace.json` is the schema reference.

## 4. Merge mechanics

- `git subtree add --prefix=plugins/<name> <local-repo-path> <branch>` per external repo → **full history preserved**.
- **No `git filter-repo` / history rewriting needed:** audited `.git` sizes are all <1 MB (home-network 924K, cron-claude 240K, hypr-doctor 364K, claude-skills 332K); no committed binaries. Untracked build artifacts (e.g. cron-claude's 41 MB venv) are simply not brought along.
- Existing real-dir skills (`bitwarden-cli`, `chezmoi`, …) → `git mv` into `plugins/<name>/skills/<name>/` (history preserved in-repo).
- The `home-network` subtree comes from the komi-home-toolkit repo, which also contains the *stale* `bitwarden-cli` plugin and the old root `marketplace.json` — those are dropped during/after the subtree merge (the live `bitwarden-cli` is canonical).
- **Pre-merge capture (must run first):** commit + push all outstanding work — `claude-skills` is ahead 1 + dirty (today's bitwarden edits, `skill-rules.json`, your in-progress prune); `hypr-doctor` is ahead 6; the `home-network` `SKILL.md` edit is uncommitted; `bws-secret-add` is untracked in `~/bin`.

## 5. Deployment — `install.sh` (idempotent, re-runnable)

1. **Register the marketplace + install its plugins** — `~/repos/claude-skills` as a `source: directory` marketplace; idempotent edits to `settings.json` (`extraKnownMarketplaces`) and Claude Code's `known_marketplaces.json` / `installed_plugins.json`. Directory-source reads live, so **no skill symlinks** are created.
2. Symlink each plugin's shell scripts → `~/bin/` (`home-net-*`, `scan-lan`, `wol`, `port-check`, `find-host`, `hypr-doctor`, `bws-secret-add`, …) — shell-invoked CLIs, distinct from skill loading.
3. Merge each plugin's `skill-rules.fragment.json` into `~/.claude/skills/skill-rules.json` (kept as the activation hook's config path), **preserving** entries it doesn't own.
4. Install + register the activation hook: copy `hooks/skill-activation-prompt.ts` into place; idempotent `settings.json` merge (add the hook registration if absent; back up first).
5. Safety: detect already-correct state (no-op), back up conflicts, never clobber silently. `--dry-run` shows planned actions; `/reload-plugins` (or a new session) picks up live edits.

## 6. Activation portability

- Each skill owns its triggers via `plugins/<name>/skill-rules.fragment.json`.
- `install.sh` merges fragments → runtime `skill-rules.json`. The aggregate also holds third-party skills' rules; the merge is additive/keyed-by-skill-name so those survive.
- The activation hook (`skill-activation-prompt.ts`, originally from the showcase) is bundled under `hooks/` and registered idempotently. We port the *system* `skill-developer` documented, not the skill.
- Skills load as **namespaced plugin skills** (`claude-skills:<name>`); `skill-rules.json` stays at `~/.claude/skills/skill-rules.json` as the hook's config (it isn't itself a skill), so the activation hook keeps firing unchanged.
- Result: on a fresh machine, `git clone … && ./install.sh` yields working, auto-recommended skills.

## 7. Sync — two layers

1. **`home-network` capture loop (retained):** `home-net-capture` / `home-net-learn` keep their verify-against-live-network + conservative-merge behavior, retargeted to push the **umbrella** remote.
2. **Generic "remote always current" autosync (new):** a debounced `systemd --user` path unit watching `~/repos/claude-skills`. On change: `git pull --rebase --autostash` → `git add -A` → commit (timestamped message) → `push`. On rebase conflict: **stop + `notify-send`**, never auto-resolve. Accepts WIP commits on `main` (this is a personal repo, not a release artifact). Multi-machine-safe via pull-rebase-before-push.

## 8. Cutover — path-reference repointing

Relocating the source repos orphans references; `install.sh` is the single source of truth that re-creates them:
- **8 `~/bin` symlinks**: `find-host`, `home-net-capture`, `home-net-doctor`, `home-net-learn`, `port-check`, `scan-lan`, `wol` (→ home-network), `hypr-doctor` (→ claude-dirs).
- **3 `~/.claude/skills` skill symlinks** (`home-network`, `cron-claude`, `hypr-doctor`): **removed** — these now load via the installed marketplace, not personal-skill symlinks.
- **`settings.json`**: remove the `komi-home-toolkit` marketplace registration (git source → `home-network-skill.git`); **register `claude-skills` as a properly-installed marketplace** (git source → `claude-skills.git`), handled idempotently by `install.sh`.

## 9. Decommission & archive

- Remove the installed `komi-home-toolkit` marketplace (settings.json entry + `~/.claude/plugins/marketplaces/komi-home-toolkit` cache) to prevent skill-collision with the symlinked versions.
- **Archive (not delete)** on GitHub: `home-network-skill`, `cron-claude`, `hypr-doctor` — after a final push. Add a README pointer to the umbrella in each.

## 10. Safety / reversibility

- `tar` snapshot of `~/.claude/skills` before any surgery.
- Push every source repo to its remote before archiving (recovery points).
- Do the restructure in a **fresh clone** at `~/repos/claude-skills`; only flip the runtime (`~/.claude/skills`) once the new structure is verified to load.
- Old repos are archived, not deleted — the whole migration is reversible.

## 11. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Activation hook registration edits machine-level `settings.json` | idempotent merge + backup; `--dry-run` |
| Autosync pushes WIP / multi-machine divergence | rebase-before-push; conflict → stop + notify |
| A path reference missed at cutover | `install.sh` is the single symlink source; audit found exactly 8 bin + 3 skills + 1 settings |
| Marketplace schema drift | validate against the known-good `komi-home-toolkit/marketplace.json` |
| Skill double-loads | resolved: marketplace plugin skills are namespaced (`claude-skills:<name>`) and can't collide; no skill symlinks are kept. Verified via claude-code-guide + on-disk inspection of the `nsys-marketplace` directory source. |

## 12. Phased execution (feeds the implementation plan)

0. **Backup** + commit/push all outstanding work (§4 pre-merge).
1. Clone `claude-skills` → `~/repos/claude-skills`; `git mv` the 3 retained real-dir skills (`bitwarden-cli`, `chezmoi`, `universal-directory-organizer`) into `plugins/<name>/`; `git rm` excluded ones (`skill-developer`, `obsidian-plugin-dev`, `qmk-zmk-animation-conversion`) — all preserved in history.
2. `subtree`-merge `home-network`, `cron-claude`, `hypr-doctor`; strip the stale `bitwarden-cli` plugin + old marketplace wrapper from the home-network subtree.
3. Promote to marketplace: root `marketplace.json`, per-plugin `plugin.json`, per-skill rules fragments.
4. Author `install.sh`, the autosync unit, and retarget the `home-net` loop.
5. **Cutover**: run `install.sh`; verify every skill loads, every script resolves, activation fires; remove old marketplace; flip runtime.
6. Archive old repos; add pointers.

## 13. Decisions locked

- **Deployment:** `source: directory` marketplace at `~/repos/claude-skills` — *verified* to read live (edits effective next session / `/reload-plugins`) while being properly installed. No skill symlinks; `~/bin` symlinks only for shell CLIs.
- **Autosync trigger:** `systemd --user` path watch.
- **Marketplace:** `claude-skills` registered as a properly-installed marketplace in `settings.json`.
- **Roster curation:** umbrella = daily-driver / maintenance skills only (6). `obsidian-plugin-dev` and `qmk-zmk-animation-conversion` excluded as too project-specific — preserved in history, not deleted.
