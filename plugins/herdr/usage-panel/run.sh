#!/usr/bin/env bash
# Launch the usage panel renderer.
#
# Resolves the script explicitly rather than trusting PATH. A plugin command
# inherits the herdr SERVER's environment, which is whatever shell started the
# server — not necessarily an interactive one carrying ~/bin. The same class of
# bug made a Hyprland exec bind fail silently, so don't assume it here either.
set -uo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

for cand in \
  "$here/../bin/herdr-usage-panel" \
  "$HOME/bin/herdr-usage-panel" \
  "$HOME/.local/bin/herdr-usage-panel"; do
  if [ -x "$cand" ]; then exec "$cand" "$@"; fi
done

if command -v herdr-usage-panel >/dev/null 2>&1; then
  exec herdr-usage-panel "$@"
fi

echo "herdr-usage-panel not found. Looked beside this plugin, in ~/bin," >&2
echo "in ~/.local/bin, and on PATH (PATH=$PATH)" >&2
# Stay up so the pane shows the error instead of closing instantly.
read -r -p "press enter to close " _ || sleep 30
exit 127
