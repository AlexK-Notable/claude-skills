# Replicating this herdr setup on a new machine

A runbook to rebuild the herdr configuration from zero. Written 2026-08-14 from the
working setup on `komi`'s personal host, for use on a second machine (e.g. work).

Read [local-idioms.md](local-idioms.md) for the *why* behind these choices. This file is
the *how*, in order, with a verification step after anything that can fail silently.

---

## What you end up with

- herdr running with a two-line agent sidebar you can actually read at a glance
- four vetted plugins (file viewer, browser, auto-rename, Claude usage) bound to keys,
  because plugin actions ship **unbound** and are otherwise unreachable without a shell
- a usage strip showing one bar per AI provider — Anthropic, Codex, Antigravity — from a
  single file-drop feed, with no duplicated gauges
- optional: wheel-scroll agent cycling (Wayland/Hyprland only), and a source build for
  testing unreleased features safely

---

## Before you start — what is portable and what is not

| Piece | Portable? | Notes |
|---|---|---|
| herdr config, sidebar rows, keybinds | **Yes** | Pure TOML, no host assumptions |
| The four plugins + pins | **Yes** | |
| `houser.claude-usage` patch | **Yes** | Re-apply by hand after install |
| Usage feed + panel + collectors | **Yes** | Python 3, stdlib only |
| Codex collector | **Yes** | Reads local files; no network, no credentials |
| Antigravity collector | **Yes** | Requires the `agy` CLI installed and logged in |
| Wheel-scroll agent cycling | **Hyprland only** | Needs a compositor that can bind a wheel |
| Screenshot iteration loop | **Wayland only** | Uses `grim`; irrelevant to the setup working |
| Source build | Any | But needs an exact zig; skip unless you need it |

**Absolute paths.** Two lines in the config below hardcode `/home/komi`. Substitute your
own home directory — herdr does not reliably expand `~` inside `[[keys.command]]`.

**On a work machine, check policy first.** The Anthropic collector polls an OAuth endpoint
using Claude Code's own token, and the Antigravity collector shells out to `agy`, which
makes a network call. Everything else is local file reads. Nothing stores or transmits
credentials anywhere new, but a corporate environment may govern this differently — worth
confirming before you wire up usage tracking on a work account.

---

## Step 0 — Prerequisites

```bash
herdr --version        # the multiplexer itself
jq --version           # required by install.sh
python3 --version      # 3.9+; collectors and the panel are stdlib-only
git --version
```

Install herdr per https://herdr.dev. This setup was built against
`0.8.0-preview.2026-08-04-d78e3d3b5126`.

A terminal supporting the **Kitty graphics protocol** is required for the browser plugin
only (Ghostty and Kitty both work). Everything else is plain text.

---

## Step 1 — Clone claude-skills and install

This deploys the scripts, the skill, and the autosync watcher in one go.

```bash
git clone git@github.com:AlexK-Notable/claude-skills.git ~/repos/claude-skills
cd ~/repos/claude-skills
./install.sh --dry-run     # read what it will do first
./install.sh
```

`install.sh` is idempotent and re-runnable. It creates **live symlinks** — the scripts in
`~/bin` point at the repo, so a `git pull` updates them with no reinstall.

It also installs and enables `claude-skills-autosync.service`, which commits and pushes
changes automatically. That service does `git pull --rebase --autostash` before pushing
and **stops and notifies on conflict rather than auto-resolving**, which is what makes it
safe to run the same repo on two machines.

**Verify:**

```bash
command -v herdr-usage-panel          # must resolve, via ~/bin
systemctl --user is-active claude-skills-autosync.service    # -> active
systemctl --user is-enabled claude-skills-autosync.service   # -> enabled
```

If `~/bin` is not on your PATH, add it (this setup gets it from `.zshrc`). Note that a
graphical session's `exec` environment does **not** inherit an interactive shell's PATH —
see the Hyprland step.

---

## Step 2 — herdr config

Write `~/.config/herdr/config.toml`. The commentary below is load-bearing: it records
which tokens were deliberately removed and why, so they do not creep back in.

```toml
onboarding = false

[ui]
agent_panel_sort = "priority"
show_agent_labels_on_pane_borders = true

[theme]
name = "catppuccin"
auto_switch = false

[ui.toast]
delivery = "herdr"
delay_seconds = 3       # suppress states that flicker back within 3s

[ui.sidebar.agents]
rows = [
  ["state_icon", "agent", "state_text"],
  [{ token = "$summary", fg = "#89b4fa", bold = true }],
  ["workspace", "tab"],
]

[ui.sidebar.agents.rows_by_agent]
# Two lines, not three. Rationale for each thing REMOVED:
#   "agent"  — always the literal "claude" for every Claude row: distinguished
#              nothing and cost a whole line.
#   $model   — a dead token. herdr-cc-meta only sets it from $ANTHROPIC_MODEL,
#              which is unset because the model is chosen in-app via /model.
#              It rendered empty forever.
#   "tab"    — auto-rename names a tab after its foreground program, which for
#              an agent pane is always "claude", duplicating "agent".
# What's left: the workspace (the thing that actually differs between rows) on
# the identity line, and the prompt as the content line — coloured, so content
# outranks location instead of the reverse.
claude = [
  ["state_icon", "workspace", "state_text"],
  [{ token = "$summary", fg = "#89b4fa" }],
]

[ui.sidebar.spaces]
# Do NOT add $cu / $cu_warn / $cu_hot / $cu_out rows here. Plan usage is
# account-wide, but herdr metadata has only workspace and pane scope — no
# account/global scope — so a workspace token repeats the identical number on
# every space row. The gauge lives once, in the usage-panel pane
# (prefix+shift+u), rendering one bar per provider.
rows = [
  ["state_icon", "workspace"],
  ["branch", "git_status"],
]

[keys]
# agent-navigation bindings that ship unbound
focus_agent      = "prefix+alt+1..9"
next_agent       = "prefix+]"
previous_agent   = "prefix+["
switch_workspace = "prefix+shift+1..9"
open_worktree    = "prefix+shift+o"
last_pane        = "prefix+;"

# ── Plugin bindings ──────────────────────────────────────────────────────────
# Plugin actions and panes ship UNBOUND, and herdr has no action-picker key, so
# without these the only way to reach them is `herdr plugin action invoke` /
# `herdr plugin pane open` from a shell.
#
# prefix+b is taken by toggle_sidebar, so the browser uses prefix+shift+b —
# NOT the prefix+b its README suggests.
#
# type = "plugin_action" takes a qualified <plugin_id>.<action_id>. Panes have
# no plugin_action equivalent, so they go through type = "shell".

[[keys.command]]
key = "prefix+f"
type = "plugin_action"
command = "herdr-file-viewer.open-file-viewer"
description = "file viewer (split)"

[[keys.command]]
key = "prefix+shift+f"
type = "plugin_action"
command = "herdr-file-viewer.open-file-viewer-tab"
description = "file viewer (own tab)"

[[keys.command]]
key = "prefix+u"
type = "shell"
command = '"$HERDR_BIN_PATH" plugin pane open --plugin houser.claude-usage --entrypoint usage'
description = "Claude usage detail popup"

[[keys.command]]
key = "prefix+shift+u"
type = "shell"
command = "/home/komi/bin/herdr-usage-panel-open"   # <-- CHANGE to your $HOME
description = "usage strip (toggle)"

[[keys.command]]
key = "prefix+shift+b"
type = "shell"
command = '"$HERDR_BIN_PATH" plugin pane open --plugin official.browser --entrypoint browser --placement split --direction right --focus'
description = "browser (right split)"

[worktrees]
directory = "~/repos/herdr-worktrees"

[experimental]
pane_history = true
# Required by official.browser — it renders Chromium into the pane via the
# Kitty graphics protocol; without this the browser pane simply won't draw.
kitty_graphics = true

[update]
channel = "preview"
manifest_check = true   # keep agent-detection manifests current across CC updates
```

**Verify** — this is a real check, not a formality, because an unknown key is *ignored
with a warning* rather than being a hard failure:

```bash
herdr config check
```

---

## Step 3 — Plugins

All four are pinned to the exact commits running here. Installing unpinned gets you
whatever is on the default branch today.

```bash
herdr plugin install iamhouser/herdr-claude-usage-multi --ref 21896aa75b7ac10029f490bc93d4e3fe2ae48240 -y
herdr plugin install ogulcancelik/herdr-browser        --ref be6888b71cf4eb5939ee79a746bd1a1c22ade046 -y
herdr plugin install smarzban/herdr-file-viewer        --ref 8a3efa14eb10f44d4b2c0b8b838b9d74e2aa1d86 -y
herdr plugin install qu8n/herdr-automatic-rename       --ref 31406e377d3c0b5b29ad3e4ff031bdcffe08d12d -y
```

`herdr plugin install` is also the **only update path** — there is no separate update
command, and it **replaces the whole managed directory**, destroying local patches.

### Per-plugin configuration

**`official.browser`** — `~/.config/herdr/plugins/config/official.browser/browser.json`:

```json
{"focusOnOpen": false}
```

**`herdr-file-viewer`** — `~/.config/herdr/plugins/config/herdr-file-viewer/config.toml`:

```toml
update_check = false
```

One switch disables **both** the daily update fetch and the vendor "spotlight" message.

> Caution: this plugin parses its config and falls back to defaults on any error, where
> `update_check` defaults to **true**. A malformed file therefore silently re-enables the
> fetch. Confirm the file actually parses (`python3 -c 'import tomllib,sys;
> tomllib.load(open(sys.argv[1],"rb"))' <path>`) rather than assuming it took.

**`herdr-automatic-rename`** — install it, but do **not** add its zshrc hook.

**Verify:**

```bash
herdr plugin list --json | jq -r '.result.plugins[] | "\(.plugin_id)\t\(.version)"'
```

---

## Step 4 — Patch the usage plugin

Two changes: a continuous gauge instead of `■□` segments, and feed publishing that makes
this plugin the Anthropic collector.

```bash
pr=$(herdr plugin list --json \
     | jq -r '.result.plugins[]|select(.plugin_id=="houser.claude-usage")|.plugin_root')
cd "$pr"
patch -p1 --dry-run < ~/repos/claude-skills/plugins/herdr/patches/houser.claude-usage-smooth-gauge.patch
patch -p1          < ~/repos/claude-skills/plugins/herdr/patches/houser.claude-usage-smooth-gauge.patch

# The daemon caches its code — an edit does nothing until restart.
herdr plugin action invoke stop  --plugin houser.claude-usage
herdr plugin action invoke start --plugin houser.claude-usage
```

**Verify** the feed file appears (may take a poll interval):

```bash
ls ~/.local/state/herdr-usage/
```

---

## Step 5 — The usage feed

Nothing to install: `install.sh` already put the collectors and panel in `~/bin`. The
panel discovers **every executable named `herdr-usage-collect-*`** on PATH, so adding a
provider later is dropping in one file.

| Provider | Collector | Needs |
|---|---|---|
| Anthropic | the patched plugin daemon | Claude Code logged in |
| Codex | `herdr-usage-collect-codex` | `codex` used at least once |
| Antigravity | `herdr-usage-collect-gemini` | `agy` installed and logged in |

**Verify end to end:**

```bash
herdr-usage-panel --once
```

Expect one row per provider. Reading the output correctly matters:

- **row absent** → that provider is not installed
- **`?`** → set up, but has not reported yet (legitimate and common on a fresh machine —
  Codex writes rate limits only once an API response carries them)
- **greyed with `(stale 2h)`** → reported once, now stale

Bind it with `prefix+shift+u`.

---

## Step 6 (optional, Hyprland only) — wheel-scroll agent cycling

herdr **cannot** bind a mouse wheel: it resolves every binding to a key code and returns
nothing otherwise. The compositor has to do it.

```
bindd = $mainMod SHIFT, mouse_down, Cycle agent next, exec, /home/komi/bin/herdr-agent-cycle next
bindd = $mainMod SHIFT, mouse_up,   Cycle agent prev, exec, /home/komi/bin/herdr-agent-cycle prev
```

**Use an absolute path.** Hyprland's `exec` does not have `~/bin` on PATH — that comes
from `.zshrc`, which is interactive-only — so a bare command name fails silently.

If it does nothing, a compositor bind swallows stderr, so distinguish "never ran" from
"ran and no-opped":

```bash
HERDR_AGENT_CYCLE_DEBUG=1   # logs to $XDG_RUNTIME_DIR
```

---

## Step 7 (optional) — build from source

Only needed to test unreleased features. The vendored `libghostty-vt` requires **zig
0.15.2 exactly** and rejects newer versions too, so pin a private toolchain rather than
touching the system one:

```bash
git clone https://github.com/herdrdev/herdr ~/repos/herdr    # branch is master, not main
cd ~/repos/herdr
ZIG=~/.local/share/zig/zig-x86_64-linux-0.15.2/zig cargo build --release
```

Launch it isolated with `herdr-dev`, which sets `HERDR_CONFIG_PATH` and `--session` so the
stable binary and your `default` session are never touched.

When capturing build output, **do not** pipe to `tail` and read the exit status — a
pipeline reports the *last* command's status, so a failed build reads as success. Redirect
to a log and check `$?`, or use `${PIPESTATUS[0]}`.

---

## Final verification checklist

```bash
herdr config check                                            # config parses
herdr plugin list --json | jq -r '.result.plugins[].plugin_id'  # 4 plugins
herdr-usage-panel --once                                      # bars render
systemctl --user is-active claude-skills-autosync.service     # active
```

In herdr: `prefix+?` should list the five plugin bindings with their descriptions.

---

## Things that will bite you

| Symptom | Cause |
|---|---|
| Plugin edit does nothing | Daemon caches code — `plugin action invoke stop` then `start` |
| Local patch vanished | `plugin install` replaces the whole managed dir; re-apply from `patches/` |
| `prefix+b` opens the sidebar | That is `toggle_sidebar`; the browser is `prefix+shift+b` |
| Browser pane draws nothing | `[experimental] kitty_graphics = true` missing, or terminal lacks the protocol |
| Compositor bind does nothing | `~/bin` not on `exec` PATH — use an absolute path |
| Script targets the wrong pane | `herdr pane current` returns the **caller's** pane; use the `focused` flag from a global `herdr pane list` |
| Split is the wrong size | `pane split --ratio` sizes the **original** pane — pass `1 - ratio` |
| Gauge looks segmented | `■`/`□` do not fill their cell; `█`/`░` do |
| Nesting refused | `allow_nested = true` goes under `[experimental]`, and is read from the config the **new** process loads |
| Build fails on zig | The gate requires 0.15.2 *exactly* and rejects newer — installing a newer zig will not help |

---

## Dead ends — do not repeat these

**Do not try to put a usage panel in the sidebar.** `expanded_sidebar_sections()` returns
exactly two rects (spaces, agents), the footer is hardcoded chrome, and plugins cannot
draw to the sidebar at all. A pane is the only surface available today.

**Do not use `cloudcode-pa.googleapis.com/v1internal:retrieveUserQuota` for Antigravity
usage.** It is real, returns HTTP 200, and is genuinely called by the `agy` binary — but it
reports buckets for `gemini-2.5-*` models that `agy` cannot run, on a tier the account is
ineligible for (`loadCodeAssist` lists it under `ineligibleTiers`). Every value sits at a
pristine 100%, so it renders a permanently-full bar that looks live and always says
"you're fine". `agy -p "/usage"` is the real source.

**Do not install `senna-lang/herdr-agent-usage`**, despite it implementing multi-provider
usage tracking. It ships a Chromium cookie decryptor for its OpenCode collector — a
capability wildly disproportionate to a status widget.

---

## Keeping the two machines in sync

The autosync watcher handles it: any change under `~/repos/claude-skills` is committed and
pushed, and pulled with `--rebase` before pushing.

What it does **not** cover, because it lives outside the repo:

- `~/.config/herdr/config.toml`
- `~/.config/herdr/plugins/config/**`
- the `houser.claude-usage` patch, once applied to the managed plugin dir

Those are reproduced by re-running the steps above. This document is the source of truth
for them; if you change the config on one machine, update this file rather than trying to
sync the config itself.
