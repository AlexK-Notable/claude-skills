#!/usr/bin/env bash
# =============================================================================
# session-complete.sh — Stop hook (no matcher — fires every turn)
#
# Handles organizer session lifecycle on conversation stop:
#   - If phase is "complete": archives session data and deactivates hooks
#   - If phase is anything else: emits a status reminder
#   - If no session is active: exits silently
#
# DESIGN: Never blocks conversation. Always exits 0.
# ACTIVATION: Only active when ~/.claude/organizer-session.json exists.
# FAST PATH: When no session is active, exits in <1ms.
#
# Archive location: ~/.cache/claude-organize/session-{date}.json
# =============================================================================

MANIFEST="$HOME/.claude/organizer-session.json"
ARCHIVE_DIR="$HOME/.cache/claude-organize"

# ---------------------------------------------------------------------------
# FAST PATH: No active session
# ---------------------------------------------------------------------------
[[ ! -f "$MANIFEST" ]] && exit 0

# ---------------------------------------------------------------------------
# NEVER BLOCK: Wrap everything so errors don't affect the conversation
# ---------------------------------------------------------------------------
handle_session_stop() {
    # Check for jq silently
    command -v jq &>/dev/null || {
        echo "organizer: session active but jq not found — cannot process session state" >&2
        return 0
    }

    # Read session state
    local phase session_id target_dir
    phase=$(jq -r '.phase // "unknown"' "$MANIFEST" 2>/dev/null) || phase="unknown"
    session_id=$(jq -r '.session_id // "unknown"' "$MANIFEST" 2>/dev/null) || session_id="unknown"
    target_dir=$(jq -r '.target_directory // "unknown"' "$MANIFEST" 2>/dev/null) || target_dir="unknown"

    if [[ "$phase" == "complete" ]]; then
        # -----------------------------------------------------------------
        # SESSION COMPLETE: Archive and deactivate
        # -----------------------------------------------------------------
        mkdir -p "$ARCHIVE_DIR"

        local archive_file="$ARCHIVE_DIR/session-$(date +%Y%m%d-%H%M%S).json"
        local log_file="$HOME/.claude/organizer-log-${session_id}.jsonl"

        # Build archive JSON
        {
            echo '{'
            echo '  "manifest":'

            # Include the manifest
            cat "$MANIFEST"

            echo ','
            echo '  "log": ['

            # Include log entries if they exist
            if [[ -f "$log_file" ]]; then
                local first=true
                while IFS= read -r line; do
                    if [[ "$first" == "true" ]]; then
                        first=false
                    else
                        echo ","
                    fi
                    echo "    $line"
                done < "$log_file"
            fi

            echo '  ],'

            # Metadata
            local archived_at
            archived_at=$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")
            echo "  \"archived_at\": \"$archived_at\""
            echo '}'
        } > "$archive_file" 2>/dev/null

        # Validate the archive was written AND is well-formed JSON before
        # deleting the live session files — a non-empty but corrupt archive
        # (e.g. malformed log line) must not cost us the manifest.
        if [[ -s "$archive_file" ]] && jq empty "$archive_file" >/dev/null 2>&1; then
            # Clean up active session files
            rm -f "$MANIFEST"
            rm -f "$log_file"
            echo "Organizer session archived: $archive_file" >&2
        else
            echo "organizer: WARNING — failed to archive session, keeping manifest active" >&2
            rm -f "$archive_file"  # Remove empty/broken archive
        fi

    else
        # -----------------------------------------------------------------
        # SESSION STILL ACTIVE: Remind the user
        # -----------------------------------------------------------------
        echo "Active organizer session: $target_dir (phase: $phase)" >&2
        echo "  Set phase to 'complete' when done, or remove $MANIFEST to deactivate." >&2
    fi

    return 0
}

# Run handler — any failure is silently absorbed
handle_session_stop || true

exit 0
