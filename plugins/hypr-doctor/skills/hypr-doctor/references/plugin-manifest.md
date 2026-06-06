# Plugin manifest reference

The manifest at [`../plugins.json`](../plugins.json) is the source of truth for
which Hyprland plugins `hypr-doctor` manages. Both the CLI (via `jq`) and
Claude (via Read) consume it directly.

## Schema

```jsonc
{
  "plugins": [
    {
      "name": "string",              // short id, used in `hypr-doctor plugin-rebuild <name>`
      "enabled": true|false,         // false → fully skipped (audit and rebuild both)
      "loaded_name": "…",            // name hyprctl reports in `plugin list` (e.g. "ExampleMesonPlugin"); used to verify a load actually took. Falls back to capitalized .name if omitted
      "disabled_reason": "…",        // shown by audit when enabled=false (optional)
      "repo_dir": "/abs/path",       // git clone location
      "branch": "…" | null,          // informational; not enforced by the script
      "remote_push_to": "…" | null,  // informational; the remote name where the fork lives
      "build_system": "meson|make|cargo|…",  // informational, free-form
      "build_cmd": "…",              // shell pipeline. Runs via `cd $repo_dir && eval $build_cmd`
      "so_path": "/abs/path.so",     // for mtime check vs Hyprland binary, and hyprctl load
      "loader_directive_file": "…",  // where the `hyprctl plugin load` line lives (informational)
      "loader_directive_pattern": "…",  // regex matching the load line (informational)
      "notes": "…"                   // free-form context for future Claude / future-you
    }
  ],
  "watched_venvs": ["/abs/project-dir", …],  // dirs containing a .venv whose interpreter health is checked
  "suppressions": {
    "pyqt_skew_ack": "<pyqt> vs <qt>"        // acknowledged skew pair; hook stays silent while it matches. Set via `hypr-doctor ack-skew`
  },
  "qt_python_bindings": { "watch": ["qt6-base", "python-pyqt6", …] },
  "stack_packages": {
    "compositor": [], "graphics": [], "wayland": [], "qt_python": [], …
  }
}
```

## `watched_venvs`

Project directories (absolute paths) that contain a `.venv`. The venv-health
check runs `<dir>/.venv/bin/python --version` for each; on failure it prints a
`rm -rf … && python -m venv … && pip install -e …` recipe. This catches venvs
orphaned when the system python is bumped (the old interpreter the venv
symlinks to is removed) or when the project tree moves. Omit or leave empty to
skip the check.

## `suppressions`

Acknowledged drift that should NOT nag in the SessionStart hook (it still
appears in full `audit`, marked acknowledged, and is not counted toward the
issue total). Currently one key:

- **`pyqt_skew_ack`** — a `"<pyqt_ver> vs <qt_ver>"` string. While the live
  pair matches, the hook is silent about the PyQt6↔Qt6 skew. It is
  self-expiring: any bump to either package changes the pair, so the ack stops
  matching and the warning revives (a worse skew is never masked). Set it to
  the current live pair with `hypr-doctor ack-skew` rather than hand-editing.

## Adding a new plugin

Three things must be true before you add it:

1. The plugin builds successfully on the current Hyprland version (verify
   manually once).
2. There's a stable `.so` output path you can mtime-check.
3. There's a single shell pipeline that does a clean rebuild from scratch
   (not just "run `make` if you're lucky"). This is what `hypr-doctor rebuild`
   will eval.

Then add an object to `plugins[]`:

```json
{
  "name": "myplugin",
  "enabled": true,
  "repo_dir": "/home/user/repos/myplugin",
  "branch": "main",
  "remote_push_to": null,
  "build_system": "meson",
  "build_cmd": "rm -rf build && meson setup build --buildtype=release && ninja -C build",
  "so_path": "/home/user/repos/myplugin/build/libmyplugin.so",
  "loader_directive_file": "/home/user/.config/hypr/hyprland.conf",
  "loader_directive_pattern": "hyprctl plugin load .*libmyplugin\\.so",
  "notes": "Whatever future-you needs to remember about this plugin."
}
```

Then add a corresponding `exec-once = hyprctl plugin load /home/user/repos/myplugin/build/libmyplugin.so` in the relevant hyprland.conf section
(or in `~/.config/hypr/config/autostart.conf`).

## Retiring a plugin (temporarily)

Set `enabled: false` and add a `disabled_reason`. This is the right move
when:

- The plugin is temporarily incompatible with the current Hyprland version
  (e.g., a plugin that's broken on the current release while waiting for an
  upstream PR).
- You've migrated to `hyprpm` for that plugin and no longer manage the
  build locally.
- You want to skip it for a while without deleting the entry.

Disabled plugins still appear in `hypr-doctor audit` output (with their
reason) so you don't forget about them.

## Retiring a plugin (permanently)

Delete the JSON object. Also remove the `hyprctl plugin load` line from
hyprland.conf (or wherever it lives) — the manifest is just a manifest, it
doesn't actually wire up the load itself.

## Editing the watched packages

The `stack_packages.*` groupings drive the "recent stack updates" section
of `audit`. If you start using a new Wayland portal, a new GPU userspace
driver, or anything else whose upgrades you want to be aware of, add the
package name to the most appropriate group.

The `qt_python_bindings.watch` array drives the Qt/PyQt skew check. If a
new Python binding for Qt enters the system, add it here.

## Common mistakes

- **`build_cmd` runs the wrong shell** — it's `eval`'d under bash, so use
  bash-compatible syntax. No fish-isms. Pipes and `&&` are fine.
- **Path uses `~/`** — the manifest fields aren't tilde-expanded by `jq`.
  Use absolute paths everywhere (`/home/user/…`).
- **`so_path` points to a debug build** — `hypr-doctor rebuild` always
  builds release. If `so_path` points to `build/debug/...` it'll get
  stale every release build. Match the path in `build_cmd`.
- **Forgetting the `exec-once` line** — the manifest manages the build,
  not the load. After adding an entry, also add the load directive.
