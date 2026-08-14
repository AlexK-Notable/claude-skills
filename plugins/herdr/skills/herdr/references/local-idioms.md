# Herdr — local idioms (komi's layer)

Personal operating knowledge accumulated on top of the upstream skill. The upstream SKILL.md body covers driving herdr *from inside a pane*; this file covers everything else. Grow it as idioms accrete; keep entries terse and mechanism-level.

Seeded 2026-08-11 from a deep research pass (source-verified against herdr @ 3f752a72 / binary 0.8.0-preview.2026-08-04). Full reports live on the main machine at `~/repos/herdr-research/` (this-host path, not portable), alongside a docs mirror at `~/repos/herdr-docs/` and the clone at `~/repos/herdr`.

## Config & host setup

- **Notification delivery is `off` by default.** `[ui.toast] delivery = "terminal"` + `delay_seconds = 3` emits OSC 9, which the desktop notification daemon raises natively (swaync on Hyprland) and which survives SSH. `"system"` instead shells out to `notify-send` on the *client* machine — wrong for remote use.
- **`herdr config check` fail-opens.** It's a real validator (bad values → rc 1), but a bad value *silently downgrades to the default* at startup — read the checker's output, not just its exit code.
- **Keys that ship unbound and are worth binding:** `focus_agent = "prefix+alt+1..9"`, `next_agent`/`previous_agent`, `open_worktree`. `prefix+o` (`open_notification_target`) already jumps to whatever raised the last notification; with `agent_panel_sort = "priority"` that's the whole "which agent needs me" loop.

## Agent detection maintenance

- **Claude Code state (idle/working/blocked) is screen-scraped** via regex manifests (`website/agent-detection/*.toml` upstream), not hook-reported. `herdr integration install claude` only adds session identity for `claude --resume`.
- After a Claude Code upgrade, run `herdr server update-agent-manifests` (and keep `[update] manifest_check = true`).
- Debug misdetection with `herdr agent explain <target> --verbose` — shows the matched rule, manifest version, and idle-fallback reason.

## Automation surface

- **`agent prompt --wait` / `agent wait` block forever without `--timeout`** — always pass one. Gate on settled states; never treat `unknown` as success.
- **Global agent-state watcher:** subscribe to `pane.updated` over `$XDG_CONFIG_HOME/herdr/herdr.sock` and diff `agent_status` per pane. `pane.agent_status_changed` cannot do this — it *requires* a `pane_id`. Wire gotcha: subscribe with dot names, but pushed frames arrive snake_case (`"event":"pane_updated"`).
- **Sidebar metadata from Claude Code hooks:** `herdr pane report-metadata --token` (never `report-agent` — metadata must stay display-only). Tokens render as `$name` in `[ui.sidebar.agents] rows`. Limits: ≤32 token keys per pane, ≤32 distinct `--source` slots per pane *lifetime* (never freed) — use one stable source id.
- **Don't put `terminal_title_stripped` in a sidebar row:** the ◐/◑ spinner Claude Code uses isn't stripped, so the row flickers and re-renders every frame.
- **Worktree flow** (how the herdr maintainers run their own agents): `herdr worktree create --branch <b> --base origin/<default> --no-focus` → checkout + grouped workspace + a `worktree.created` event a plugin can bootstrap from. `workspace close` never touches the checkout; only `worktree remove` does, and it never deletes branches.

## Plugins (as hooks)

- Plugins are the **only** run-script-on-event mechanism — there is no `[hooks]` config section. A plugin = directory + `herdr-plugin.toml` naming argv commands (`[[events]]`, `[[actions]]`, `[[startup]]`, `[[panes]]`, `[[build]]`, `[[link_handlers]]`). The API is the herdr CLI itself via `$HERDR_BIN_PATH`, plus JSON over the socket.
- High-volume events (`pane.output_changed`, `pane.updated`, `layout.updated`, `workspace.metadata_updated`) are **deliberately unhookable from manifests** — an output-watcher needs its own socket subscriber, and `[[startup]]` won't supervise one (one-shot, not a daemon).
- Local development: `herdr plugin link <path>`; install is GitHub-shorthand-only (`herdr plugin install owner/repo[/subdir]`). Zero sandboxing by design — review before installing. Marketplace (herdr.dev/plugins) is an unreviewed auto-index of the `herdr-plugin` GitHub topic.
- Community plugins worth remembering: `herdr-spreader` (declarative YAML layouts with `wait_for` predicates), `cloudmanic/herdr-plus` (workspace/worktree launcher from TOML), `AltanS/collie` (remote control PWA).

## Installed automation (this host, 2026-08-11)

- **Config applied** (`~/.config/herdr/config.toml`, backup at `config.toml.bak-20260811`): toast `delivery = "terminal"` + `delay_seconds = 3`; sidebar rows rendering `$summary`/`$model` tokens; agent-nav keybindings; `[worktrees] directory`; `manifest_check = true`.
- **`herdr-agent-watch`** (this plugin's `bin/`, systemd user unit in `systemd/`): subscribes `pane.updated`, logs transitions to the journal, maintains `$XDG_RUNTIME_DIR/herdr-agent-watch.json` for consumers (future waybar module). Runs WITHOUT a notify hook — built-in toasts cover blocked/finished; `herdr-agent-alert` is the optional hook for custom cases.
- **`herdr-cc-meta`**: Claude Code `UserPromptSubmit` hook (registered async in `~/.claude/settings.json`) reporting the prompt as a `summary` token via `pane report-metadata`. Verified: tokens surface in `PaneInfo.tokens` (`herdr pane get <id> | jq .result.pane.tokens`).
- Herdr's own integration hook (`~/.claude/hooks/herdr-agent-state.sh`, SessionStart, managed by herdr) handles session identity — leave it alone; custom hooks live beside it.

### Installed plugins (2026-08-12)

`houser.claude-usage` (plan Session%/Week% gauges on space rows) · `official.browser` ·
`herdr-file-viewer` · `herdr-automatic-rename`. Per-plugin hardening: `focusOnOpen: false`,
`update_check = false`, and auto-rename installed without its zshrc hook. The usage plugin
needs a `[ui.sidebar.spaces] rows` block to render — it reports one of four severity token
variants (`$cu`, `$cu_warn`, `$cu_hot`, `$cu_out`) per space, and rows whose token is absent
are skipped, so unaffected spaces stay compact.

## Installing plugins — mechanics worth remembering

- **`herdr plugin install` pins to a commit** and prints a full preview (every action, event,
  pane, and build command) before it proceeds. Read the preview: it is the complete list of
  what the plugin can run. The pin means an upstream force-push cannot silently change what
  executes — updating requires a reinstall.
- Checkouts land in `~/.config/herdr/plugins/github/<id>-<hash>/`; config in
  `~/.config/herdr/plugins/config/<id>/`, exported to the plugin as `$HERDR_PLUGIN_CONFIG_DIR`.
  herdr creates the config dir **empty** — it never seeds defaults, so there is no example file
  to copy.
- **Find the config *filename* in the plugin's source, never guess it.** It varies
  (`browser.json` vs `config.toml`) and a file written under the wrong name is silently ignored.
  Grep for `HERDR_PLUGIN_CONFIG_DIR` to find the join.
- **Writing a config file is not evidence the setting took effect.** Plugins commonly parse
  with "malformed → fall back to defaults" (herdr-file-viewer: `Err(e) => (Config::default(),
  LoadOutcome::Malformed(..))`), so a typo silently restores the default you were trying to
  turn off. Parse the file yourself (`python3 -c 'import tomllib,...'` / `jq`) and confirm the
  key resolves to the value you intended — with a deliberately broken file to prove the check
  can fail.
- A plugin shipping `skills/<name>/SKILL.md` at the repo root is offering an agent-facing skill
  (herdr-browser and herdr-file-viewer both do). That is different from `.claude/skills/`, which
  auto-registers just from being cloned into an agent's view.

### Reaching a plugin after you install it

**Installing a plugin binds nothing.** herdr has no action-picker key and no command palette,
so a freshly installed plugin is reachable only via `herdr plugin action invoke <id> --plugin
<p>` or `herdr plugin pane open --plugin <p> --entrypoint <e>` from a shell. Budget a config
edit as part of every install:

- `[[keys.command]]` with `type = "plugin_action"` takes a **qualified** id
  (`<plugin_id>.<action_id>`, e.g. `herdr-file-viewer.open-file-viewer`).
- **`[[panes]]` entrypoints have no `plugin_action` equivalent** — bind them with
  `type = "shell"` running `"$HERDR_BIN_PATH" plugin pane open --plugin … --entrypoint …`.
- `description = "…"` replaces the generic `custom command` label in the `prefix+?` help panel.
- Check the key against the defaults before trusting a README: herdr-browser's README suggests
  `prefix+b`, which is already `toggle_sidebar`.
- `herdr plugin action list` enumerates everything invokable, qualified ids included.

**herdr-browser needs `[experimental] kitty_graphics = true`** — it paints Chromium into the
pane over the Kitty graphics protocol, and without the flag the pane simply doesn't draw. It
asks rather than setting it for you (unlike terminal-browser, which rewrites your config
silently). Also needs Bun and a Chrome/Chromium binary. Its link handler makes **Ctrl+click on a
`localhost` / `127.0.0.1` / `[::1]` URL** in any pane open that page in a browser pane — a plain
click stays terminal input.

**Reading a plugin pane's contents over the CLI usually returns empty** — TUI plugins paint on
the alternate screen, which never enters herdr's host scrollback. Verify such an action by its
exit status plus a `pane list` diff, not by `pane read`.

## Finding the UI-focused pane — `pane current` is a trap

**`herdr pane current` does NOT return the pane the user is looking at.** It resolves the
*caller's* inherited `HERDR_PANE_ID`, so a script running inside a pane always gets its own
pane back no matter what the UI shows, and a script launched from outside herdr (a systemd
unit, a compositor keybind) has no context at all. Verified live: with `w6:p1` genuinely
focused, `pane current` still reported the caller's `w4:p1`.

Use the `focused` flag from a **global** `pane list` instead — it takes no `--workspace` and
covers every workspace:

```bash
herdr pane list | jq -r '.result.panes[]|select(.focused)|.pane_id'
```

## herdr cannot bind a mouse wheel

`src/config/keybinds.rs` resolves every binding to a crossterm `KeyCode` and returns `None`
for anything unrecognised — there is no mouse/wheel/button token. herdr consumes the wheel
for scrollback, selection, and its scrollbars, but the wheel is not bindable to an action.

Wheel-driven actions therefore belong to the compositor. Hyprland binds `mouse_up`/`mouse_down`
and can `exec` a script that calls the herdr CLI — `bin/herdr-agent-cycle` does exactly this.
Two things make it safe rather than chaotic:

- **A compositor wheel bind is global.** Guard the script so it no-ops unless the focused
  window is the terminal hosting herdr — resolve that by walking each `herdr` process's
  ancestry until you hit a terminal emulator, never by hardcoding a pid (it changes every
  restart). Testing such a guard is confusing: any terminal you test from holds focus, so the
  guard correctly refuses and the script looks broken. Give it a documented env override.
- **Check the modifier is free.** `$mainMod + mouse_down/up` was already bound to Hyprland
  workspace cycling on this host, so agent cycling uses `$mainMod SHIFT`.

Confirm binds actually registered with `hyprctl -j binds` (filter on `.description`), and
run the same filter against a bogus string as a negative control.

**Use an ABSOLUTE path in a Hyprland `exec` bind.** Hyprland's exec environment does not
include `~/bin` — that is added by `.zshrc`, which only runs for interactive shells. A bare
command name resolves to nothing and fails **completely silently**: the bind fires, the shell
finds no such command, and no error surfaces anywhere. `~/.local/bin` *is* present, so a
script symlinked there works by luck; `~/bin` does not. Verify the real environment rather
than assuming:

```bash
hyprctl dispatch exec /path/to/probe    # probe writes $PATH + `command -v` results to a file
```

**A guarded script that no-ops looks exactly like a broken one**, and a compositor bind
swallows stderr. Give any guarded script a `*_DEBUG=1` env that logs its exit reason to
`$XDG_RUNTIME_DIR`, or the next "it doesn't work" report has no evidence attached.

## Patching an installed plugin

`herdr plugin install` replaces the entire managed directory, so local edits die on
reinstall — keep the diff in `plugins/herdr/patches/` (see its README) rather than only
in the live tree. There is no auto-update and installs are commit-pinned, so a patch
survives until *you* reinstall.

**A plugin running a daemon caches its code.** Editing the file changes nothing until the
daemon restarts: `herdr plugin action invoke stop --plugin <id>` then `start`. Verify
against the reported token, not the file.

## Account-wide values duplicate across the sidebar — by design

**Metadata has exactly two scopes: `workspace` and `pane`.** There is no account or global
scope. Anything account-wide (plan quota, a subscription meter) published as a workspace
token therefore repeats identically on every space row. No plugin setting fixes this; the
value has to leave the token system.

**The sidebar cannot host a dedicated region either.** `expanded_sidebar_sections()` returns
exactly two rects — spaces and agents. The 1-row footer inside the spaces area is hardcoded
chrome (`new` / `menu` buttons), and plugins cannot draw to the sidebar at all; they can only
report tokens into `[ui.sidebar.agents]` / `[ui.sidebar.spaces]` rows. So "a dedicated panel
below the agents list" is not expressible.

Two ways out:

- **A pane.** `bin/herdr-usage-panel` + `bin/herdr-usage-panel-open` render one bar per
  provider in a thin bottom strip, fed by JSON files in `~/.local/state/herdr-usage/`.
  Gotcha: **`pane split --ratio` sets the size of the ORIGINAL pane, not the new one** —
  `--ratio 0.16` yields a new pane taking ~84%. Invert it. `plugin pane open` has no size
  control at all (`--width`/`--height` are rejected unless placement is `popup`), which is
  why driving `pane split` directly beats a plugin `[[panes]]` entrypoint when size matters.
- **`[ui] tab_bar_right`** with `type = "command"` — a tmux-style status area that runs a
  command on an interval and renders its last line once, no workspace scoping. Fully
  implemented in `src/app/tab_bar_status.rs` but **unreleased**: 82 commits past
  `preview-2026-08-04-d78e3d3b5126`, which is the newest tag. Pair with the already-shipped
  `tab_bar_position = "bottom"` for a bottom-right status strip. Revisit when it tags.

**Sidebar bar-glyph gotcha, learned by screenshot.** `■`/`□` are small geometric shapes
that do not fill their character cell, so a bar built from them reads as separated squares.
`█` and `░` fill the cell edge to edge and render as one continuous bar. Eighth-block
glyphs (`▏▎▍▌▋▊▉█`) buy sub-cell precision — 80 steps instead of 10 — but a partial block
sits at the LEFT of its cell, leaving the rest of that cell blank with no track behind it,
which opens a visible gap between fill and track. A sidebar row is drawn in one fg colour,
so the fill and the track must be distinguished by glyph density, not colour.

## Plugin vetting — what to check before installing

Plugins are unsandboxed; pre-install review IS the security model. Lessons from vetting 15 repos (2026-08-11, full reports in `~/repos/herdr-research/vetting-*.md`):

- **Read `herdr-plugin.toml` first, then every executable it names.** `[[build]]` runs at install time — scrutinize hardest. `curl|bash` install steps mean the vendor can change the payload after you review it.
- **The dominant risk class is repo-supplied config, not malware.** Several plugins (herdr-plus, herdr-sessionizer) load executable configuration from *whatever repo you're sitting in* — `<repo>/.herdr-plus/quick-actions/*.toml`, `<repo>/.sessionizer/config.toml`. Sessionizer's runs automatically on workspace open with no trust prompt. Habit: keep untrusted clones outside any configured project root.
- **A plugin can ship Claude Code skills that the manifest never mentions.** Observed live: cloning a repo for review registered its `.claude/skills/*/SKILL.md` as an invocable skill in the reviewing session. Cloning a repo and pointing an agent at it is an instruction-loading event; read `AGENTS.md`/`CLAUDE.md`/`skills/` alongside the entrypoints, and delete review clones when done.
- **Check for silent config rewrites.** terminal-browser rewrites `~/.config/herdr/config.toml` (forcing `kitty_graphics = true`) inside a try/catch that swallows errors.
- **Focus discipline is easy to audit**: grep for `hyprctl`/`xdotool`/`wmctrl`/`swaymsg`, plus herdr's own `pane focus`/`agent focus`/`workspace switch` and splits missing `--no-focus`. Most plugins pass; `xdg-open` in an action is the sneaky one (raises a window).
- Prefer plugins that fetch prebuilts with a **pinned version + SHA-256 + source fallback** (herdr-file-viewer does this) over `latest`-tag unverified downloads.

## Licensing / versioning

- Apache-2.0 since 0.8.0 (relicensed from AGPL — older blog posts are stale on this).
- 0.8.0 cut idle multi-agent CPU ~10× (killed animated-spinner redraws); background agents are cheap now, weren't on 0.7.5.
