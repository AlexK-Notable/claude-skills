#!/usr/bin/env bash
# =============================================================================
# organizer-guard.sh — PreToolUse hook (matcher: "Bash")
#
# Safety guard for universal-directory-organizer sessions.
# Validates every Bash command against session constraints:
#   - Absolute blocks (sudo, destructive system commands)
#   - Protected path enforcement
#   - Scope enforcement (commands must target session directory)
#   - Wildcard depth guard (prevent shallow rm -rf *)
#
# DESIGN: Fail-closed. Any unexpected error blocks the command.
# ACTIVATION: Only active when ~/.claude/organizer-session.json exists.
# FAST PATH: When no session is active, exits in <1ms.
#
# Exit codes:
#   0 = allow command
#   2 = block command (stderr message shown to user)
# =============================================================================

set -uo pipefail

MANIFEST="$HOME/.claude/organizer-session.json"

# ---------------------------------------------------------------------------
# FAST PATH: No active session — allow everything, cost ~0ms
# ---------------------------------------------------------------------------
[[ ! -f "$MANIFEST" ]] && exit 0

# ---------------------------------------------------------------------------
# FAIL-CLOSED TRAP: If ANYTHING unexpected goes wrong, block the command.
# This is the most important safety property of this script.
# We'd rather block a legitimate command than allow a dangerous one.
# ---------------------------------------------------------------------------
trap 'echo "organizer-guard: unexpected error on line $LINENO — command blocked for safety" >&2; exit 2' ERR

# ---------------------------------------------------------------------------
# DEPENDENCY CHECK: jq is required to parse JSON
# ---------------------------------------------------------------------------
if ! command -v jq &>/dev/null; then
    echo "organizer-guard: jq is required but not found." >&2
    echo "  Install with: pacman -S jq" >&2
    echo "  Or deactivate session: rm $MANIFEST" >&2
    exit 2
fi

# ---------------------------------------------------------------------------
# READ HOOK INPUT: Claude Code sends JSON on stdin for PreToolUse hooks
# Format: {"tool_name": "Bash", "tool_input": {"command": "..."}}
# ---------------------------------------------------------------------------
INPUT=$(cat)

# Extract the command string
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# No command found — not a Bash call somehow, allow it
if [[ -z "$COMMAND" ]]; then
    trap - ERR
    exit 0
fi

# ---------------------------------------------------------------------------
# NORMALIZE: Expand ~ and $HOME for consistent path comparison
# ---------------------------------------------------------------------------
NORMALIZED_CMD=$(echo "$COMMAND" | sed "s|\\\$HOME|$HOME|g; s|~/|$HOME/|g")

# ---------------------------------------------------------------------------
# DETECTION NORMALIZATION
# For *detection only* we further normalize a copy of the command so trivially
# disguised destructive verbs are still visible:
#   - strip quotes:      bash -c 'rm -rf x' / 'rm' -rf x  → rm is a real token
#   - strip env prefix:  FOO=bar rm …                     → handled by the
#                        word-boundary regex (space before the verb)
#   - strip verb paths:  /bin/rm, /usr/bin/find           → rm, find
# Path extraction for scope checks also runs on this normalized text, so the
# verb's own binary path (/bin/rm) is never mistaken for an operand.
# ---------------------------------------------------------------------------
WB='(^|[;&|()[:space:]])'   # token at a command-start-ish boundary

normalize_for_detection() {
    sed -E -e "s/[\"']//g" \
           -e "s#(^|[;&|()[:space:]])/[^[:space:]]+/(rm|rmdir|shred|unlink|truncate|mv|dd|find|rsync|git)([[:space:]]|\$)#\\1\\2\\3#g" \
        <<<"$1"
}

# Does this (already detection-normalized) command segment contain a
# destructive verb? Denylist stopgap — broader than the old rm|mv|rmdir|shred
# word match, but still not an allowlist.
seg_is_destructive() {
    local s="$1"
    grep -qE "${WB}(rm|rmdir|shred|unlink|truncate)([[:space:]]|\$)" <<<"$s" && return 0
    grep -qE "${WB}mv([[:space:]]|\$)" <<<"$s" && return 0
    grep -qE "${WB}find[[:space:]].*-delete([[:space:]]|\$)" <<<"$s" && return 0
    grep -qE "${WB}rsync[[:space:]].*--delete" <<<"$s" && return 0
    grep -qE "${WB}git[[:space:]]+([^[:space:]]+[[:space:]]+)*clean([[:space:]]|\$)" <<<"$s" && return 0
    grep -qE "${WB}dd[[:space:]]+(.*[[:space:]])?of=" <<<"$s" && return 0
    return 1
}

DETECT_CMD=$(normalize_for_detection "$NORMALIZED_CMD")

# ---------------------------------------------------------------------------
# ABSOLUTE BLOCKS: Commands that are NEVER allowed during organizer sessions
# These are blocked regardless of target_directory or protected_paths.
# (Matched against the detection-normalized text so quoting/path tricks
# don't slip past.)
# ---------------------------------------------------------------------------

# Block sudo — Claude Code has no tty, and failures lock pam_faillock
if echo "$DETECT_CMD" | grep -qE '(^|\s|;|&&|\|\|)sudo(\s|$)'; then
    echo "organizer-guard: BLOCKED — sudo is never allowed during organizer sessions" >&2
    echo "  (Claude Code has no tty; sudo failures lock pam_faillock)" >&2
    exit 2
fi

# Block other absolutely dangerous commands
ABSOLUTE_BLOCKS=(
    '(^|\s|;|&&|\|\|)chmod\s+-R\s+777\b'
    '(^|\s|;|&&|\|\|)chown\s+'
    '(^|\s|;|&&|\|\|)dd\s+if='
    '(^|\s|;|&&|\|\|)mkfs\b'
    '(^|\s|;|&&|\|\|)shred\b'
    '(^|\s|;|&&|\|\|)rm\s+(-[a-zA-Z]*)?-rf?\s+/\s'
    '(^|\s|;|&&|\|\|)rm\s+(-[a-zA-Z]*)?-rf?\s+/$'
)

for pattern in "${ABSOLUTE_BLOCKS[@]}"; do
    if echo "$DETECT_CMD" | grep -qE "$pattern"; then
        echo "organizer-guard: BLOCKED — command matches absolute block: $pattern" >&2
        exit 2
    fi
done

# ---------------------------------------------------------------------------
# READ SESSION MANIFEST
# ---------------------------------------------------------------------------
TARGET_DIR=$(jq -r '.target_directory // empty' "$MANIFEST")

# Optional additional allowed scope: where archives/consolidation moves land
# (e.g. ~/archives). Destructive-command operands may live here too.
ARCHIVE_DIR=$(jq -r '.archive_dir // empty' "$MANIFEST")

# Read protected paths into array
PROTECTED_PATHS=()
while IFS= read -r path; do
    [[ -n "$path" ]] && PROTECTED_PATHS+=("$path")
done < <(jq -r '.protected_paths[]? // empty' "$MANIFEST")

# ---------------------------------------------------------------------------
# DETECT DESTRUCTIVE COMMANDS + COLLECT THEIR OPERAND PATHS
# We only apply scope/protection checks to destructive commands, and only to
# the operand paths of the destructive *segment* of a compound command.
# Splitting on && ; || means a documented workflow like
#   tar -czf ~/archives/x.tgz -C target sub && rm -rf target/sub
# only scope-checks the rm segment — the tar destination is not an rm operand.
# Read-only commands (ls, du, df, cat, stat, wc, etc.) are always allowed.
# ---------------------------------------------------------------------------
IS_DESTRUCTIVE=false
DESTRUCTIVE_PATHS=()
while IFS= read -r seg; do
    [[ -z "${seg//[[:space:]]/}" ]] && continue
    norm_seg=$(normalize_for_detection "$seg")
    seg_is_destructive "$norm_seg" || continue
    IS_DESTRUCTIVE=true
    # Drop option tokens (-x, --opt, --opt=/path) so option arguments are not
    # treated as operands, then collect the remaining absolute paths.
    operands=$(sed -E 's/(^|[[:space:]])-[^[:space:]]*/\1/g' <<<"$norm_seg" | grep -oE '/[^ ";|&>]+' || true)
    while IFS= read -r p; do
        [[ -n "$p" ]] && DESTRUCTIVE_PATHS+=("$p")
    done <<<"$operands"
done < <(sed 's/&&/\n/g; s/||/\n/g; s/;/\n/g' <<<"$NORMALIZED_CMD")

if [[ "$IS_DESTRUCTIVE" == "false" ]]; then
    # Non-destructive command — allow
    trap - ERR
    exit 0
fi

# ---------------------------------------------------------------------------
# SESSION FILE EXEMPTION
# The manifest and log files must be writable so sessions can be updated,
# completed, and deactivated. Without this, the guard creates a deadlock
# where protected_paths block removal of the manifest itself.
# ---------------------------------------------------------------------------
SESSION_ID=$(jq -r '.session_id // empty' "$MANIFEST" 2>/dev/null)
SESSION_FILES=(
    "$MANIFEST"
    "$HOME/.claude/organizer-log-${SESSION_ID}.jsonl"
    "/tmp/org-manifest.json"
)

# Check if the command ONLY targets session files (no other paths)
is_session_file_only=true
while IFS= read -r raw_path; do
    [[ -z "$raw_path" ]] && continue
    [[ "$raw_path" == -* ]] && continue
    resolved=$(realpath -m "$raw_path" 2>/dev/null || echo "$raw_path")
    is_exempt=false
    for sf in "${SESSION_FILES[@]}"; do
        [[ "$resolved" == "$sf" ]] && is_exempt=true && break
    done
    if [[ "$is_exempt" == "false" ]]; then
        is_session_file_only=false
        break
    fi
done < <(echo "$NORMALIZED_CMD" | grep -oE '/[^ ";|&>]+')

if [[ "$is_session_file_only" == "true" ]]; then
    trap - ERR
    exit 0
fi

# ---------------------------------------------------------------------------
# PROTECTED PATH CHECK
# Block destructive operands that touch a protected path. Uses path-boundary
# semantics (equal, inside, or ancestor of a protected path) — NOT substring
# matching, so protecting /x/keep no longer also blocks /x/keeper, while
# deleting an ancestor of a protected path is still caught.
# ---------------------------------------------------------------------------
for raw_path in "${DESTRUCTIVE_PATHS[@]}"; do
    resolved=$(realpath -m "$raw_path" 2>/dev/null || echo "$raw_path")
    resolved="${resolved%/}"
    for protected in "${PROTECTED_PATHS[@]}"; do
        [[ -z "$protected" ]] && continue
        prot="${protected%/}"
        if [[ "$resolved" == "$prot" || "$resolved" == "$prot"/* || "$prot" == "$resolved"/* ]]; then
            echo "organizer-guard: BLOCKED — command targets protected path: $protected" >&2
            echo "  Offending operand: $resolved" >&2
            echo "  Protected paths are defined in $MANIFEST" >&2
            exit 2
        fi
    done
done

# ---------------------------------------------------------------------------
# SCOPE CHECK
# Operand paths of destructive segments must be under target_directory, the
# optional archive_dir, or be a session file. This prevents an organizer
# session from deleting/overwriting files in unrelated parts of the
# filesystem while still allowing documented archive/consolidation moves.
# ---------------------------------------------------------------------------
if [[ -n "$TARGET_DIR" ]]; then
    target_norm="${TARGET_DIR%/}"
    archive_norm="${ARCHIVE_DIR%/}"

    for raw_path in "${DESTRUCTIVE_PATHS[@]}"; do
        # Resolve to canonical path (without requiring existence)
        resolved=$(realpath -m "$raw_path" 2>/dev/null || echo "$raw_path")
        resolved="${resolved%/}"

        in_scope=false
        if [[ "$resolved" == "$target_norm" || "$resolved" == "$target_norm"/* ]]; then
            in_scope=true
        elif [[ -n "$archive_norm" && ( "$resolved" == "$archive_norm" || "$resolved" == "$archive_norm"/* ) ]]; then
            in_scope=true
        else
            for sf in "${SESSION_FILES[@]}"; do
                [[ "$resolved" == "$sf" ]] && in_scope=true && break
            done
        fi

        if [[ "$in_scope" == "false" ]]; then
            echo "organizer-guard: BLOCKED — destructive command targets path outside session scope" >&2
            echo "  Session scope: $TARGET_DIR" >&2
            [[ -n "$archive_norm" ]] && echo "  Archive scope: $ARCHIVE_DIR" >&2
            echo "  Offending path: $resolved" >&2
            exit 2
        fi
    done
fi

# ---------------------------------------------------------------------------
# WILDCARD DEPTH GUARD
# Prevent rm -rf with wildcards at shallow depths from the target root.
# This catches commands like: rm -rf ~/*/  or  rm -rf /home/user/*
# which would wipe all top-level directories.
# Only block when the wildcard is < 2 directory levels deep from target root.
# ---------------------------------------------------------------------------
if [[ -n "$TARGET_DIR" ]] && echo "$NORMALIZED_CMD" | grep -qE '\brm\s.*\*'; then
    # Extract paths containing wildcards
    while IFS= read -r wild_path; do
        [[ -z "$wild_path" ]] && continue

        # Get the directory portion (everything before the *)
        dir_part="${wild_path%%\**}"
        # Remove trailing slash
        dir_part="${dir_part%/}"

        # Resolve
        resolved_dir=$(realpath -m "$dir_part" 2>/dev/null || echo "$dir_part")

        # Calculate depth from target_directory
        target_norm="${TARGET_DIR%/}"
        if [[ "$resolved_dir" == "$target_norm"* ]]; then
            relative="${resolved_dir#$target_norm}"
            # Count slashes = depth
            depth=$(echo "$relative" | tr -cd '/' | wc -c)

            if [[ $depth -lt 2 ]]; then
                echo "organizer-guard: BLOCKED — rm with wildcard at shallow depth ($depth) from target root" >&2
                echo "  Target root: $TARGET_DIR" >&2
                echo "  Wildcard path: $wild_path" >&2
                echo "  Use explicit paths instead of wildcards at this depth" >&2
                exit 2
            fi
        fi
    done < <(echo "$NORMALIZED_CMD" | grep -oE '/[^ ";|&>]*\*[^ ";|&>]*')
fi

# ---------------------------------------------------------------------------
# ALL CHECKS PASSED — Allow the command
# ---------------------------------------------------------------------------
trap - ERR
exit 0
