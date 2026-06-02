#!/usr/bin/env bash
# SessionStart hook — surface post-update drift detected by hypr-doctor.
#
# hypr-doctor abi-drift prints to stdout only when drift is detected
# (silent if everything is healthy). Stdout from this hook becomes
# additionalContext injected into the next user prompt.
#
# Safety: 5-second timeout, errors swallowed, exit 0 always —
# a broken doctor must NEVER block a Claude session from starting.

timeout 5 "$HOME/bin/hypr-doctor" abi-drift 2>/dev/null || true
exit 0
