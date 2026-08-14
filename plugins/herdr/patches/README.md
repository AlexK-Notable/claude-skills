# Local patches to installed herdr plugins

herdr plugins are installed into `~/.config/herdr/plugins/github/<id>-<hash>/`, and
`herdr plugin install` (the only update path — there is no separate update command)
**replaces that whole directory**. Any local edit is lost on reinstall. These patches
are the record of what was changed and why, so a reinstall is recoverable.

Nothing here is applied automatically. Re-apply by hand after a deliberate reinstall.

| Patch | Plugin | Pinned upstream | What it changes |
|---|---|---|---|
| `houser.claude-usage-smooth-gauge.patch` | `houser.claude-usage` | `21896aa7` | Continuous gauge instead of `■□` segments **+** publishes a provider feed for the usage strip |

## Applying

```bash
pr=$(herdr plugin list --json \
     | jq -r '.result.plugins[]|select(.plugin_id=="houser.claude-usage")|.plugin_root')
cd "$pr" && patch -p1 --dry-run < ~/repos/claude-skills/plugins/herdr/patches/houser.claude-usage-smooth-gauge.patch
# then drop --dry-run
herdr plugin action invoke stop  --plugin houser.claude-usage
herdr plugin action invoke start --plugin houser.claude-usage   # daemon caches the old code
```

The restart matters: the plugin runs a long-lived Python daemon, so editing the file
changes nothing until it is stopped and started. Confirm with:

```bash
herdr workspace list | jq -r '.result.workspaces[0].tokens.cu'
```

## `houser.claude-usage-smooth-gauge.patch`

Upstream draws the sidebar gauge as `"■" * filled + "□" * rest` over `GAUGE_CELLS = 10`.
Those glyphs are small geometric shapes that do **not** fill their character cell, so the
bar reads as separated squares rather than a bar.

The patch swaps them for `█` (full block) and `░` (light shade), which both fill the cell
edge to edge and therefore render as one continuous bar.

It also adds `GAUGE_SUBCELL`, off by default:

- `False` — 10 steps, perfectly continuous. What "smooth bar" actually looks like.
- `True` — eighth-block glyphs (`▏▎▍▌▋▊▉█`) give 80 steps, so e.g. 3% and 7% stop
  rendering identically. **But** a partial block sits at the LEFT of its cell and leaves
  the remainder of that cell blank with no track behind it, opening a visible gap between
  the fill and the track. Verified by screenshot — precision at the cost of a broken-looking
  bar. Off unless sub-cell accuracy is worth that.

Only the sidebar gauge is affected. The detail popup (`prefix+u`) already used `█` plus a
`·` track and was never segmented.

### `publish_feed()` — the de-duplication half

herdr metadata has only `workspace` and `pane` scope; there is no account or global scope.
Plan usage is account-wide, so publishing it as a workspace token repeats the identical
number on **every** space row. That is a scope mismatch, not something plugin config can fix.

The patch adds `publish_feed()`, which writes the raw numbers to
`~/.local/state/herdr-usage/anthropic-<account>.json` (atomically, via `os.replace`, because
the panel may be mid-read). `bin/herdr-usage-panel` renders one bar per provider from that
directory, and the `$cu*` rows were removed from `[ui.sidebar.spaces]`.

This plugin deliberately stays the **only** Anthropic poller — nothing else should hold the
OAuth token or add rate-limit pressure. Adding Codex or Gemini means writing another
collector that emits the same JSON shape; the panel needs no change.
