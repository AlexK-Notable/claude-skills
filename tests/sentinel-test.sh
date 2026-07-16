#!/usr/bin/env bash
# Standalone test for the self-learn autosync-pause sentinel check in
# bin/claude-skills-sync (08 T12). Runs entirely in a sandbox: copies the
# script into a throwaway repo with a bare remote and a redirected
# XDG_CACHE_HOME — never touches the real repo, cache, or remote.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

export XDG_CACHE_HOME="$WORK/cache"
# doc 13 §4.4: the sentinel is GLOBAL — ${XDG_CACHE_HOME}/self-learn/…
SENTINEL_DIR="$XDG_CACHE_HOME/self-learn"
mkdir -p "$SENTINEL_DIR"

# Sandbox repo with the sync script installed at bin/, plus a bare remote.
git init -q "$WORK/remote" --bare
git init -q "$WORK/repo"
cd "$WORK/repo"
git config user.email test@local
git config user.name test
git remote add origin "$WORK/remote"
mkdir -p bin
cp "$HERE/bin/claude-skills-sync" bin/claude-skills-sync
chmod +x bin/claude-skills-sync
echo one > file.txt
git add -A
git commit -qm init
git push -qu origin master 2>/dev/null || git push -qu origin main

fail() { echo "FAIL: $1" >&2; exit 1; }

# Case 1: fresh sentinel → sync exits 0 and commits nothing.
echo two > file.txt                      # dirty tree
touch "$SENTINEL_DIR/autosync-pause"     # fresh (mtime now)
before="$(git rev-parse HEAD)"
out="$(bin/claude-skills-sync 2>&1)" || fail "sync exited non-zero under fresh sentinel"
[ "$(git rev-parse HEAD)" = "$before" ] || fail "sync committed despite fresh sentinel"
[ -n "$(git status --porcelain)" ] || fail "dirty tree vanished under fresh sentinel"
echo "$out" | grep -q "paused by self-learn sentinel" || fail "no pause log line"
echo "PASS: fresh sentinel pauses sync"

# Case 2: stale sentinel (>2 h) → sync proceeds and commits.
touch -d '3 hours ago' "$SENTINEL_DIR/autosync-pause"
bin/claude-skills-sync || fail "sync failed with stale sentinel"
[ "$(git rev-parse HEAD)" != "$before" ] || fail "sync did not commit despite stale sentinel"
[ -z "$(git status --porcelain)" ] || fail "tree still dirty after stale-sentinel sync"
echo "PASS: stale sentinel ignored, sync proceeds"

# Case 3: no sentinel → sync proceeds (regression guard for the added block).
rm -f "$SENTINEL_DIR/autosync-pause"
echo three > file.txt
before="$(git rev-parse HEAD)"
bin/claude-skills-sync || fail "sync failed with no sentinel"
[ "$(git rev-parse HEAD)" != "$before" ] || fail "sync did not commit with no sentinel"
echo "PASS: no sentinel, sync proceeds"

echo "sentinel-test: all 3 cases pass"
