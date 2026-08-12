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

## Licensing / versioning

- Apache-2.0 since 0.8.0 (relicensed from AGPL — older blog posts are stale on this).
- 0.8.0 cut idle multi-agent CPU ~10× (killed animated-spinner redraws); background agents are cheap now, weren't on 0.7.5.
