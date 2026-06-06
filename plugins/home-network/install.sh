#!/usr/bin/env bash
# install.sh — bootstrap the home-network-skill on this machine.
#
# Symlinks scripts → ~/bin/ and skill → ~/.claude/skills/.
# Does NOT install any packages. Runs home-net-doctor at the end to report
# what's available + what to install.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/bin"
SKILLS_DIR="${HOME}/.claude/skills"

if [[ -t 1 ]] && command -v tput >/dev/null 2>&1; then
  C_OK=$(tput setaf 2); C_WARN=$(tput setaf 3); C_BAD=$(tput setaf 1)
  C_DIM=$(tput dim); C_BOLD=$(tput bold); C_RESET=$(tput sgr0)
else
  C_OK=""; C_WARN=""; C_BAD=""; C_DIM=""; C_BOLD=""; C_RESET=""
fi

FORCE=0
NO_DOCTOR=0
for arg in "$@"; do
  case "$arg" in
    -h|--help)
      cat <<EOF
install.sh — bootstrap home-network-skill on this machine

USAGE:
  ./install.sh                # symlink scripts + skill; run doctor
  ./install.sh --force        # overwrite existing symlinks/files
  ./install.sh --no-doctor    # skip the doctor report

WHAT IT DOES:
  1. Symlinks each script in ./scripts/ → ~/bin/  (refuses to clobber unless --force)
  2. Symlinks ./skills/home-network → ~/.claude/skills/home-network
  3. Runs home-net-doctor to report toolchain status

EOF
      exit 0
      ;;
    --force) FORCE=1 ;;
    --no-doctor) NO_DOCTOR=1 ;;
    *) echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done

echo "${C_BOLD}home-network-skill installer${C_RESET}"
echo "  repo:    $REPO_DIR"
echo "  bin:     $BIN_DIR"
echo "  skills:  $SKILLS_DIR"
echo

# --- step 1: ~/bin/ symlinks ---
mkdir -p "$BIN_DIR"
echo "${C_BOLD}1. Symlinking scripts → $BIN_DIR${C_RESET}"
for script in "$REPO_DIR"/scripts/*; do
  [[ -f "$script" && -x "$script" ]] || continue
  name=$(basename "$script")
  target="$BIN_DIR/$name"

  if [[ -e "$target" || -L "$target" ]]; then
    if [[ -L "$target" ]] && [[ "$(readlink "$target")" == "$script" ]]; then
      echo "  ${C_DIM}= $name (already linked correctly)${C_RESET}"
      continue
    fi
    if (( FORCE )); then
      rm -f "$target"
    else
      echo "  ${C_WARN}⚠ $name exists at $target — skipping (use --force to overwrite)${C_RESET}"
      continue
    fi
  fi
  ln -s "$script" "$target"
  echo "  ${C_OK}+ $name${C_RESET}"
done

# --- step 2: ~/.claude/skills symlink ---
echo
echo "${C_BOLD}2. Symlinking skill → $SKILLS_DIR/home-network${C_RESET}"
mkdir -p "$SKILLS_DIR"
target="$SKILLS_DIR/home-network"
src="$REPO_DIR/skills/home-network"

if [[ -e "$target" || -L "$target" ]]; then
  if [[ -L "$target" ]] && [[ "$(readlink "$target")" == "$src" ]]; then
    echo "  ${C_DIM}= already linked correctly${C_RESET}"
  elif (( FORCE )); then
    rm -rf "$target"
    ln -s "$src" "$target"
    echo "  ${C_OK}+ linked (forced over existing)${C_RESET}"
  else
    echo "  ${C_WARN}⚠ $target exists — skipping (use --force to overwrite)${C_RESET}"
  fi
else
  ln -s "$src" "$target"
  echo "  ${C_OK}+ linked${C_RESET}"
fi

# --- step 3: PATH check ---
echo
echo "${C_BOLD}3. PATH sanity check${C_RESET}"
if [[ ":$PATH:" == *":$BIN_DIR:"* ]]; then
  echo "  ${C_OK}✓ $BIN_DIR is in PATH${C_RESET}"
else
  echo "  ${C_WARN}⚠ $BIN_DIR is NOT in PATH${C_RESET}"
  echo "    add to your shell rc:  export PATH=\"\$HOME/bin:\$PATH\""
fi

# --- step 4: optional env var hint ---
echo
echo "${C_BOLD}4. Optional environment hint${C_RESET}"
echo "  ${C_DIM}consider adding to your shell rc for explicit DEVICES.md path:${C_RESET}"
echo "    export HOME_NETWORK_SKILL_DEVICES=\"$REPO_DIR/skills/home-network/references/DEVICES.md\""

# --- step 5: tool audit ---
if (( ! NO_DOCTOR )); then
  echo
  echo "${C_BOLD}5. Toolchain audit (home-net-doctor)${C_RESET}"
  echo
  if [[ -x "$REPO_DIR/scripts/home-net-doctor" ]]; then
    set +e
    "$REPO_DIR/scripts/home-net-doctor"
    doctor_rc=$?
    set -e
    echo
    case "$doctor_rc" in
      0) echo "  ${C_OK}✓ toolchain fully ready${C_RESET}" ;;
      1) echo "  ${C_WARN}⚠ toolchain degraded but usable${C_RESET}" ;;
      2) echo "  ${C_BAD}✗ toolchain missing required tools — see install commands above${C_RESET}" ;;
    esac
  fi
fi

echo
echo "${C_OK}${C_BOLD}install complete${C_RESET}"
echo "${C_DIM}try: scan-lan --quick    or    find-host sbc    or    home-net-doctor${C_RESET}"
