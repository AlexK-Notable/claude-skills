#!/bin/bash
# UserPromptSubmit hook — suggests skills based on skill-rules.json.
# HARD REQUIREMENT: this runs on EVERY prompt, so it must NEVER block or fail
# the prompt. Every runner is wrapped in `timeout 3` and the script always
# exits 0. Runner preference:
#   1. bun        — runs TypeScript natively, ~50ms, no network
#   2. npx tsx    — --no-install only: never fetch from the network on a prompt
#   3. node + .js — if a compiled skill-activation-prompt.js exists
# If no runner works, the hook is silently a no-op.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" || exit 0
TS="$SCRIPT_DIR/skill-activation-prompt.ts"
JS="$SCRIPT_DIR/skill-activation-prompt.js"

# Capture stdin once so fallback runners can replay it.
INPUT=$(cat) || exit 0

if command -v bun >/dev/null 2>&1 && printf '%s' "$INPUT" | timeout 3 bun "$TS" 2>/dev/null; then
    : # bun handled it
elif command -v npx >/dev/null 2>&1 && printf '%s' "$INPUT" | timeout 3 npx --no-install tsx "$TS" 2>/dev/null; then
    : # tsx handled it
elif [[ -f "$JS" ]] && command -v node >/dev/null 2>&1; then
    printf '%s' "$INPUT" | timeout 3 node "$JS" 2>/dev/null
fi

exit 0
