#!/usr/bin/env bash
# install.sh — deploy claude-skills into the runtime (idempotent, re-runnable).
#
# Deploys via LIVE SYMLINKS, not `claude plugin install` (see CLAUDE.md "Deployment model"):
#   - ~/.claude/skills/<name>  -> plugins/<name>/skills/<name>      (skills load live)
#   - ~/bin/<script>           -> plugins/<name>/{scripts,bin}/<exe> (shell CLIs)
#   - merges plugins/*/skill-rules.fragment.json -> ~/.claude/skills/skill-rules.json
#   - bundles the activation hook into ~/.claude/hooks (live symlink)
#   - installs + enables the systemd --user autosync watcher (OPTIONAL — see below)
#
# The repo is assumed to live at ~/repos/claude-skills, but that path is yours to
# customize (REPO is derived from this script's own location, so a move just works for
# the symlinks; the systemd unit hardcodes %h/repos/claude-skills — edit it if you relocate).
#
# Usage: ./install.sh [--dry-run]
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$HOME/.claude/skills"
BIN_DIR="$HOME/bin"
HOOKS_DIR="$HOME/.claude/hooks"
SETTINGS="$HOME/.claude/settings.json"
UNIT_DIR="$HOME/.config/systemd/user"
RULES="$SKILLS_DIR/skill-rules.json"

DRY=0; [ "${1:-}" = "--dry-run" ] && DRY=1
say() { printf '%s\n' "$*"; }
run() { if [ "$DRY" = 1 ]; then say "  [dry] $*"; else eval "$*"; fi; }

# idempotent symlink with conflict backup
link() { # $1=real src  $2=link path
  local src="$1" dst="$2"
  if [ -L "$dst" ] && [ "$(readlink -f "$dst" 2>/dev/null)" = "$(readlink -f "$src")" ]; then
    say "  ok    ${dst/#$HOME/\~}"; return; fi
  if [ -e "$dst" ] && [ ! -L "$dst" ]; then
    say "  bak   ${dst/#$HOME/\~} -> .bak"; run "mv -n '$dst' '$dst.bak'"; fi
  run "ln -sfn '$src' '$dst'"; say "  link  ${dst/#$HOME/\~} -> ${src/#$HOME/\~}"
}

command -v jq >/dev/null || { echo "jq required"; exit 1; }
mkdir -p "$SKILLS_DIR" "$BIN_DIR" "$HOOKS_DIR" "$UNIT_DIR"
PLUGINS="$(jq -r '.plugins[].name' "$REPO/.claude-plugin/marketplace.json")"

say "== skills (live symlinks) =="
for name in $PLUGINS; do
  skill="$REPO/plugins/$name/skills/$name"
  if [ -d "$skill" ]; then link "$skill" "$SKILLS_DIR/$name"; else say "  WARN  no skill dir for $name"; fi
done

say "== shell CLIs (~/bin) =="
while IFS= read -r f; do
  [ -f "$f" ] && [ -x "$f" ] && link "$f" "$BIN_DIR/$(basename "$f")"
done < <(find "$REPO"/plugins/*/scripts "$REPO"/plugins/*/bin -maxdepth 1 -type f 2>/dev/null || true)

say "== merge skill-rules fragments =="
if [ "$DRY" = 1 ]; then
  say "  [dry] merge $(ls "$REPO"/plugins/*/skill-rules.fragment.json 2>/dev/null | wc -l) fragments -> ${RULES/#$HOME/\~}"
else
  [ -f "$RULES" ] || echo '{"skills":{}}' > "$RULES"
  frag="$(jq -s 'add // {}' "$REPO"/plugins/*/skill-rules.fragment.json 2>/dev/null || echo '{}')"
  tmp="$(mktemp)"; cp "$RULES" "$RULES.bak"
  jq --argjson frag "$frag" '.skills = ((.skills // {}) + $frag)' "$RULES" > "$tmp" && mv "$tmp" "$RULES"
  say "  merged $(echo "$frag" | jq 'length') fragment entries (backup at skill-rules.json.bak)"
fi

say "== activation hook (bundled, live) =="
for h in skill-activation-prompt.sh skill-activation-prompt.ts; do
  [ -f "$REPO/hooks/$h" ] && link "$REPO/hooks/$h" "$HOOKS_DIR/$h"
done
if [ -f "$SETTINGS" ] && ! grep -q 'skill-activation-prompt' "$SETTINGS" 2>/dev/null; then
  say "  ACTION NEEDED: register the hook in $SETTINGS as a UserPromptSubmit hook ->"
  say "                 $HOOKS_DIR/skill-activation-prompt.sh   (left manual — settings.json is load-bearing)"
fi

say "== python plugins (uv sync) =="
if command -v uv >/dev/null; then
  while IFS= read -r pyproj; do
    pdir="$(dirname "$pyproj")"
    say "  uv sync  ${pdir/#$HOME/\~}"
    run "uv sync --project '$pdir' --all-extras"
  done < <(find "$REPO"/plugins -maxdepth 2 -name pyproject.toml 2>/dev/null || true)
else
  say "  NOTE: 'uv' not found — skipping; install uv to build Python plugins (cron-claude)"
fi

say "== per-plugin hooks (bundled, live) =="
while IFS= read -r hk; do
  [ -n "$hk" ] && [ -f "$hk" ] && link "$hk" "$HOOKS_DIR/$(basename "$hk")"
done < <(find "$REPO"/plugins/*/hooks -maxdepth 1 -type f -name '*.sh' 2>/dev/null || true)
say "  (register each per-plugin hook in $SETTINGS with its event — see the plugin's README/SKILL)"

say "== autosync (systemd --user inotify watcher) — OPTIONAL =="
# Autosync is a convenience that commits + pushes to YOUR OWN fork's remote on change.
# It is OPTIONAL: comment out the enable line below (or `systemctl --user disable
# claude-skills-autosync.service`) if you'd rather commit/push by hand. Customize the
# repo path/remote to taste.
command -v inotifywait >/dev/null || say "  NOTE: install 'inotify-tools' for the watcher to run"
link "$REPO/systemd/claude-skills-autosync.service" "$UNIT_DIR/claude-skills-autosync.service"
run "systemctl --user daemon-reload"
run "systemctl --user enable --now claude-skills-autosync.service"

say ""
if [ "$DRY" = 1 ]; then say "done. (dry-run — no changes made)"; else say "done."; fi
