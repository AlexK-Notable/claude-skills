# config.sh — the home-assistant skill's domain seam.
#
# The ONE file holding HA-specific operational values. `ha-inventory` reads the
# HA_* keys from here at startup (env vars still override). Kept as an explicit
# seam so that if this self-learning pattern is ever extracted into a reusable
# "operator skill" substrate, THIS file is the per-domain adapter — nothing else
# in the scripts is HA-specific by value.

# --- how to reach Home Assistant (Channel A introspection) ---
export HA_SSH="komi@192.168.1.232"               # ssh target for the HA host (Nova; was .229 — moved to wired eth 2026-06)
export HA_CONFIG="/home/komi/homeassistant/config"
export HA_CONTAINER="homeassistant"              # docker container name (version probe)
export HA_STALE_AFTER_DAYS="7"

# --- live REST/WS API access (ha-api, ha-doctor) ---
export HA_URL="http://192.168.1.232:8123"        # LAN base URL (no trailing /api)
export HA_TOKEN_BWS_ID="74edad23-6bd2-4617-a1d8-b45d016db173"  # bws secret id: admin long-lived token
export HA_BWS_TOKEN_ENV=~/.config/bws/token.env  # file exporting BWS_ACCESS_TOKEN (bws machine account)
# token resolution order in the scripts: $HA_LLAT override → bws (needs the env above). Never printed.

# --- knowledge files (Channel B), for reference ---
# WRITABLE (ha-note appends; you curate):
#   references/GOTCHAS.journal.md   append-only meta-record (paths/attempts); never rewritten
#   references/GOTCHAS.revisions.md append-only correction layer (ha-note --supersede <ref>)
#   references/GOTCHAS.md           curated wisdom, hand-promoted from the journal
# GENERATED (never hand-edit; regenerate with ha-inventory):
#   references/INVENTORY.generated.md
# FROZEN (versioned release content — change deliberately, not via capture):
#   SKILL.md, references/TOPOLOGY.md, references/STORAGE-SCHEMA.md,
#   references/ASSIST.md, references/CAPABILITY-MAP.md
