#!/usr/bin/env bash
# =============================================================================
# organizer-logger.sh — PostToolUse hook (matcher: "Bash")
#
# Logs all Bash operations during active organizer sessions to a JSONL file.
# Used for session audit trails, resume capability, and post-session review.
#
# DESIGN: Never blocks. Always exits 0 regardless of errors.
# ACTIVATION: Only active when ~/.claude/organizer-session.json exists.
# FAST PATH: When no session is active, exits in <1ms.
#
# Log location: ~/.claude/organizer-log-{session_id}.jsonl
# =============================================================================

MANIFEST="$HOME/.claude/organizer-session.json"

# ---------------------------------------------------------------------------
# FAST PATH: No active session
# ---------------------------------------------------------------------------
[[ ! -f "$MANIFEST" ]] && exit 0

# ---------------------------------------------------------------------------
# NEVER BLOCK: Wrap everything in a function that can't fail the hook
# ---------------------------------------------------------------------------
log_operation() {
    # Check for jq silently — if missing, skip logging
    command -v jq &>/dev/null || return 0

    # Read hook input from stdin
    local input
    input=$(cat)

    # Read session ID from manifest
    local session_id
    session_id=$(jq -r '.session_id // "unknown"' "$MANIFEST" 2>/dev/null) || session_id="unknown"

    local log_file="$HOME/.claude/organizer-log-${session_id}.jsonl"

    # Extract command from hook input
    local command_str
    command_str=$(echo "$input" | jq -r '.tool_input.command // "unknown"' 2>/dev/null) || command_str="unknown"

    # Classify operation type from the command
    local op_type="other"
    if echo "$command_str" | grep -qE '\brm\b'; then
        op_type="delete"
    elif echo "$command_str" | grep -qE '\bmv\b'; then
        op_type="move"
    elif echo "$command_str" | grep -qE '\btar\b|\bgzip\b|\bzip\b|\bbzip2\b|\bxz\b'; then
        op_type="archive"
    elif echo "$command_str" | grep -qE '\bcp\b|\brsync\b'; then
        op_type="copy"
    elif echo "$command_str" | grep -qE '\bmkdir\b'; then
        op_type="create_dir"
    elif echo "$command_str" | grep -qE '\brmdir\b'; then
        op_type="remove_dir"
    elif echo "$command_str" | grep -qE '\bdu\b|\bdf\b|\bls\b|\bfind\b|\bstat\b|\bwc\b|\bfile\b'; then
        op_type="inspect"
    elif echo "$command_str" | grep -qE '\bjq\b.*organizer-session'; then
        op_type="session_update"
    fi

    # Get timestamp
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")

    # Append log entry as JSONL
    jq -nc \
        --arg ts "$timestamp" \
        --arg op "$op_type" \
        --arg cmd "$command_str" \
        '{timestamp: $ts, operation: $op, command: $cmd}' >> "$log_file" 2>/dev/null

    return 0
}

# Run the logger — any failure is silently ignored
log_operation || true

exit 0
