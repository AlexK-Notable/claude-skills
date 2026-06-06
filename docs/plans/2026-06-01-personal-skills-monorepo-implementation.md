# Personal Skills Monorepo — Implementation Plan

> **For agentic workers:** Execute inline (superpowers:executing-plans), task-by-task, with the verification gate at the end of each task as the checkpoint. This migration is stateful git surgery on shared repos — do NOT parallelize across subagents. Steps use `- [ ]` checkboxes.

**Goal:** Consolidate the 6 personal skills into one `source: directory` plugin marketplace at `~/repos/claude-skills` (the repurposed `your-username/claude-skills` repo), with history preserved, an idempotent `install.sh`, systemd autosync, and the old standalone repos archived.

**Architecture:** `git subtree` merges (history-preserving) into a `plugins/<name>/skills/<name>/` marketplace layout; deployment is a directory-source marketplace (live + properly installed, no skill symlinks); `~/bin` symlinks only for shell CLIs.

**Companion spec:** `~/.claude/skills/docs/specs/2026-05-31-personal-skills-monorepo.md` (authoritative for *why*; this plan is *how*).

**Reversibility:** every source repo is pushed before it's touched; old repos are archived not deleted; the runtime is flipped only after the new structure verifies.

---

## Task 0: Safety net + capture outstanding work (NON-DESTRUCTIVE)

**Files:** none created; commits to existing repos.

- [ ] **Step 1: Snapshot the runtime skills dir**

```bash
tar -C ~/.claude -czf ~/claude-skills-backup-$(date +%Y%m%d-%H%M%S).tar.gz skills
ls -lh ~/claude-skills-backup-*.tar.gz
```
Expected: a >0-byte tarball listed.

- [ ] **Step 2: Inspect what's dirty in the claude-skills checkout**

```bash
git -C ~/.claude/skills status -sb
```
Expected: `## master...origin/master [ahead 1]`, plus `M bitwarden-cli/SKILL.md`, the new `docs/` files, `M skill-rules.json`, and the user's in-progress prune deletions. Read it; confirm nothing unexpected before committing.

- [ ] **Step 3: Commit + push the claude-skills checkout (preserves today's work for the fresh clone)**

```bash
cd ~/.claude/skills
git add -A
git commit -m "checkpoint: today's bitwarden-cli bws work, skill-rules updates, monorepo spec+plan, third-party prune"
git push origin master
git status -sb   # expect: clean, ahead 0
```

- [ ] **Step 4: Commit + push home-network's pending edit**

```bash
cd ~/repos/home-network          # the prior standalone repo for this skill
git status -sb
git add plugins/home-network/skills/home-network/SKILL.md
git commit -m "home-network: note Bitwarden Secrets Manager (bws) availability for machine secrets/SSH keys"
git push origin main
```

- [ ] **Step 5: Push hypr-doctor's unpushed commits + check cron-claude**

```bash
git -C ~/repos/hypr-doctor push origin main && git -C ~/repos/hypr-doctor status -sb
git -C ~/repos/cron-claude status -sb   # if ahead/dirty: add -A, commit, push
```
Expected: both report ahead 0, clean.

- [ ] **Step 6: GATE — confirm all recovery points exist**

```bash
for r in ~/.claude/skills ~/repos/home-network ~/repos/cron-claude ~/repos/hypr-doctor; do
  echo "$r: $(git -C "$r" status -sb | head -1)"
done
```
Expected: every repo clean + not ahead. **Do not proceed past this gate until true.**

---

## Task 1: Stage the umbrella clone + restructure existing skills

**Files:** new working clone at `~/repos/claude-skills`.

- [ ] **Step 1: Fresh clone of the repurposed repo**

```bash
git clone git@github.com:your-username/claude-skills.git ~/repos/claude-skills
cd ~/repos/claude-skills
ls
```
Expected: the just-pushed contents (bitwarden-cli/, chezmoi/, …, universal-directory-organizer/, any excluded-skill dirs, docs/, skill-rules.json).

- [ ] **Step 2: Restructure the 3 retained real-dir skills into plugin layout**

```bash
cd ~/repos/claude-skills
for s in bitwarden-cli chezmoi universal-directory-organizer; do
  mkdir -p "plugins/$s/skills"
  git mv "$s" "plugins/$s/skills/$s"
done
git status -s | head
```
Expected: each skill now at `plugins/<s>/skills/<s>/`.

- [ ] **Step 3: Drop excluded skills (preserved in history)**

```bash
git rm -r <excluded-skill-dirs>   # the vendored third-party skill + any project-specific one-offs
```

- [ ] **Step 4: Relocate the spec/plan + bring in bws-secret-add**

```bash
mkdir -p plugins/bitwarden-cli/scripts
cp ~/bin/bws-secret-add plugins/bitwarden-cli/scripts/bws-secret-add
chmod +x plugins/bitwarden-cli/scripts/bws-secret-add
git add plugins/bitwarden-cli/scripts/bws-secret-add
# docs/ already moved with the repo; leave specs/plans where they are
```

- [ ] **Step 5: Commit the restructure**

```bash
git add -A
git commit -m "restructure: existing skills → plugins/<name>/skills/<name>; drop excluded; vendor bws-secret-add"
```

- [ ] **Step 6: GATE — layout sane, history intact**

```bash
find plugins -maxdepth 3 -type d | sort
git log --oneline --follow plugins/bitwarden-cli/skills/bitwarden-cli/SKILL.md | head -3
```
Expected: 3 plugin dirs; `--follow` shows pre-restructure history (proof `git mv` preserved it).

---

## Task 2: Subtree-merge the external skill repos (history preserved)

These three skills previously lived in their own standalone repos. Merge each one in with `git subtree` so its full commit history is preserved in the monorepo.

**Approach per repo:** `git subtree add` into a temp `_import/` prefix (full history, no `--squash`), then `git mv` the wanted parts into `plugins/<name>/`, then `git rm` the remainder. Inspect each repo's real layout BEFORE moving — they differ. Adjust the local source paths below to wherever your prior standalone repos are checked out.

- [ ] **Step 1: home-network**

```bash
cd ~/repos/claude-skills
git subtree add --prefix=_import/hns ~/repos/home-network main   # the prior standalone repo
find _import/hns -maxdepth 2 -type d | sort          # INSPECT before moving
git mv _import/hns/plugins/home-network plugins/home-network
git rm -r _import/hns                                  # drops stale bitwarden-cli plugin + old marketplace.json
git commit -m "merge home-network (history preserved); drop old marketplace wrapper"
```
GATE: `test -f plugins/home-network/skills/home-network/SKILL.md && echo OK`; `git log --oneline plugins/home-network | wc -l` > 1.

- [ ] **Step 2: cron-claude**

```bash
git subtree add --prefix=_import/cc ~/repos/cron-claude main 2>/dev/null \
  || git subtree add --prefix=_import/cc ~/repos/cron-claude master
find _import/cc -maxdepth 2 | sort                    # INSPECT: locate the skill dir (likely _import/cc/skill) + CLI
mkdir -p plugins/cron-claude/skills
git mv _import/cc/skill plugins/cron-claude/skills/cron-claude   # adjust path per inspection
# bring the CLI/scripts (whole repo, minus rebuildable artifacts):
#   git mv remaining wanted dirs/files under plugins/cron-claude/ ; git rm any build/venv artifacts
git rm -rf _import/cc 2>/dev/null || true
git commit -m "merge cron-claude (history preserved)"
```
GATE: `plugins/cron-claude/skills/cron-claude/SKILL.md` exists; CLI entrypoint present.

- [ ] **Step 3: hypr-doctor**

```bash
git subtree add --prefix=_import/hd ~/repos/hypr-doctor main
find _import/hd -maxdepth 2 | sort                    # INSPECT: skills/hypr-doctor + bin/ + plugins.json
git mv _import/hd plugins/hypr-doctor                  # whole repo; then normalize layout below
# ensure plugins/hypr-doctor/skills/hypr-doctor/SKILL.md ; keep bin/hypr-doctor ; reconcile its plugins.json manifest
git commit -m "merge hypr-doctor (history preserved)"
```
GATE: `plugins/hypr-doctor/skills/hypr-doctor/SKILL.md` and `plugins/hypr-doctor/bin/hypr-doctor` exist.

- [ ] **Step 4: Strip rebuildable artifacts that came along (keep repo lean)**

```bash
cd ~/repos/claude-skills
git ls-files | grep -iE '(^|/)(target|node_modules|venv|\.venv|__pycache__|dist|build)/|\.(pyc|o|so)$' || echo "none tracked — good"
# if any: git rm -r --cached <paths> ; add to .gitignore ; commit
```

---

## Task 3: Promote to marketplace (manifests + rules fragments)

**Files:** `.claude-plugin/marketplace.json`; per-plugin `.claude-plugin/plugin.json`; per-plugin `skill-rules.fragment.json`.

- [ ] **Step 1: Root marketplace.json** — author listing all 6 plugins (schema mirrors a standard Claude Code marketplace manifest: `name`, `owner`, `metadata.{description,version}`, `plugins[]` with `name`/`source: ./plugins/<name>`/`description`/`version`).
- [ ] **Step 2: Per-plugin plugin.json** — one per plugin (`name`, `description`, `version`, `author`). Reuse existing ones where present (home-network, bitwarden-cli already have them); author for cron-claude/hypr-doctor/chezmoi/universal-directory-organizer.
- [ ] **Step 3: Rules fragments** — extract each of the 6 skills' entries from the current `~/.claude/skills/skill-rules.json` into `plugins/<name>/skill-rules.fragment.json`.
- [ ] **Step 4: Commit.** GATE: `jq . .claude-plugin/marketplace.json` valid; every plugin has plugin.json + fragment; `jq` valid on all.

---

## Task 4: install.sh + autosync + retarget home-net loop

**Files:** `install.sh`, `hooks/skill-activation-prompt.ts`, `systemd/claude-skills-autosync.{path,service}`, a `bin/claude-skills-sync` helper.

- [ ] **Step 1: Bundle the activation hook** — copy `~/.claude/hooks/skill-activation-prompt.ts` → `hooks/`.
- [ ] **Step 2: Write `install.sh`** (idempotent, `--dry-run`). Contract:
  1. Register `claude-skills` as `source: directory` (path `~/repos/claude-skills`) in `settings.json` `extraKnownMarketplaces` + mark plugins installed in Claude's `known_marketplaces.json`/`installed_plugins.json` (back up each first).
  2. Symlink each plugin's shell scripts → `~/bin/` (home-net-*, scan-lan, wol, port-check, find-host, hypr-doctor, bws-secret-add).
  3. Merge each `skill-rules.fragment.json` → `~/.claude/skills/skill-rules.json` (preserve unmanaged entries; jq-based).
  4. Install + register the activation hook in `settings.json` if absent.
  5. Install the systemd autosync units; `systemctl --user enable --now`.
  Safety: detect already-correct state (no-op), back up conflicts, never clobber non-symlinks.
- [ ] **Step 3: Write the autosync** — `bin/claude-skills-sync` does `git pull --rebase --autostash && git add -A && git commit -m "autosync: $(timestamp via arg)" && git push`; on rebase conflict → `notify-send` + exit non-zero (no auto-resolve). `systemd .path` watches the repo, debounced, triggers `.service` → the sync helper.
- [ ] **Step 4: Retarget the home-net capture loop** — in `plugins/home-network/scripts/home-net-capture` & `home-net-learn`, point their `git commit && git push` at the umbrella repo root (`~/repos/claude-skills`) instead of the home-network skill's old standalone origin.
- [ ] **Step 5: Commit.** GATE: `bash -n install.sh`; `./install.sh --dry-run` prints a sane plan with zero mutations.

---

## Task 5: Cutover (the only destructive-to-runtime task — checkpoint with user before running)

- [ ] **Step 1: Push the umbrella** — `git push origin master` (the big restructure lands on `your-username/claude-skills`).
- [ ] **Step 2: Convert `~/.claude/skills` from checkout → runtime dir** — remove its `.git` and the now-migrated skill dirs; keep `skill-rules.json` + `docs/`. (The 6 skills now load via the marketplace.)
- [ ] **Step 3: Run `./install.sh`** (real, not dry-run).
- [ ] **Step 4: Remove the old standalone marketplace** — delete its `settings.json` registration + its `~/.claude/plugins/marketplaces/<old-marketplace>` cache; remove the 3 stale `~/.claude/skills` skill symlinks + the 8 old `~/bin` symlinks (install.sh recreated the correct ones).
- [ ] **Step 5: GATE — verify in a fresh session** — every one of the 6 skills appears (namespaced `claude-skills:<name>`); `command -v scan-lan wol hypr-doctor bws-secret-add` all resolve; the activation hook fires; `systemctl --user status claude-skills-autosync.path` active. **Surface results to the user before Task 6.**

---

## Task 6: Archive old repos

- [ ] **Step 1:** Add a README pointer ("moved into your-username/claude-skills") to each prior standalone repo (`home-network`, `cron-claude`, `hypr-doctor`); commit + push.
- [ ] **Step 2:** Archive on GitHub: `gh repo archive your-username/<name> --yes` for each. (Archive, not delete — reversible.)
- [ ] **Step 3:** GATE — `gh repo view your-username/home-network --json isArchived` → `true` for all three.

---

## Self-review notes
- **Spec coverage:** §4 merge → Tasks 1–2; §5 install.sh → Task 4; §6 activation → Task 4; §7 sync → Task 4; §8 cutover → Task 5; §9 decommission/archive → Tasks 5–6; §10 safety → Task 0. ✓
- **Adaptation:** subtree-restructure steps (Task 2) include INSPECT-before-move because the three source repos have different internal layouts; exact `git mv` targets are confirmed at run time, not guessed.
- **Risk control:** Task 0 gate (recovery points) and Task 5 gate (verify before archive) are hard stops.
