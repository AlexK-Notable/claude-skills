# config.sh — the home-assistant skill's domain seam.
#
# The ONE file holding HA-specific operational values. `ha-inventory` reads the
# HA_* keys from here at startup (env vars still override). Kept as an explicit
# seam so that if this self-learning pattern is ever extracted into a reusable
# "operator skill" substrate, THIS file is the per-domain adapter — nothing else
# in the scripts is HA-specific by value.

# --- how to reach Home Assistant (Channel A introspection) ---
export HA_SSH="komi@192.168.1.229"               # ssh target for the HA host (Nova)
export HA_CONFIG="/home/komi/homeassistant/config"
export HA_CONTAINER="homeassistant"              # docker container name (version probe)
export HA_STALE_AFTER_DAYS="7"

# --- knowledge files (Channel B), for reference ---
# WRITABLE (ha-note appends; you curate):
#   references/GOTCHAS.journal.md   append-only capture target
#   references/GOTCHAS.md           curated wisdom, hand-promoted from the journal
# GENERATED (never hand-edit; regenerate with ha-inventory):
#   references/INVENTORY.generated.md
# FROZEN (versioned release content — change deliberately, not via capture):
#   SKILL.md, references/TOPOLOGY.md, references/STORAGE-SCHEMA.md,
#   references/ASSIST.md, references/CAPABILITY-MAP.md
