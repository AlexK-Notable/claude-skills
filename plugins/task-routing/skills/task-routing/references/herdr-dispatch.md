# Dispatch through the existing Herdr CLI

Confirm the orchestrator's own Herdr context before controlling panes: `HERDR_ENV=1` and the caller's workspace/tab/pane IDs. Codex tool subprocesses can omit those variables even when its parent is inside Herdr. In that case, recover only the current user's own ancestor metadata and validate the caller with `herdr pane current --current`; do not infer the caller from the focused pane. If caller context cannot be established, report that prerequisite or use explicitly chosen headless execution.

Use installed `--help` for the relevant command. Do not probe a mutating command by omitting required-looking arguments: `workspace create` works with defaults. IDs are opaque; parse returned JSON.

## Task-group placement

The user's preference overrides ordinary sibling-pane defaults in the general Herdr skill:

- Create one workspace per task group, labelled `coding`, `review`, `research`, etc. Retain its returned ID in the orchestration notes; labels alone do not establish ownership.
- Use the workspace's root shell pane first. Split additional panes within its tab until four agents occupy it.
- Worker five starts a new tab in that same workspace; worker nine starts a third. Idle/blocked agents and pending starts still count toward four.
- Keep focus unchanged with `--no-focus`. Never close a shared group to stop one worker.

```bash
herdr workspace create --cwd /absolute/worktree --label research --no-focus
herdr pane split --pane RETURNED_PANE_ID --direction right --cwd /absolute/worktree --no-focus
herdr tab create --workspace RETURNED_WORKSPACE_ID --cwd /absolute/worktree --label research-2 --no-focus
```

Workspace creation returns `.result.workspace`, `.result.tab`, `.result.root_pane`; tab creation returns `.result.tab` and `.result.root_pane`; splitting returns `.result.pane`. Choose right/down from geometry rather than making an ever-narrower row. Before starting an agent, verify the pane's shell is ready with `herdr pane process-info --pane PANE_ID`. A just-created pane can still be initializing.

## Start with explicit native settings

Replace the uppercase placeholders with discovered IDs/effort; these are command patterns, not literal runnable assignments:

```text
herdr agent start WORKER --kind codex --pane PANE_ID -- --model EXACT_ID --config 'model_reasoning_effort="high"' --dangerously-bypass-approvals-and-sandbox
herdr agent start WORKER --kind claude --pane PANE_ID -- --model EXACT_ID --effort high --dangerously-skip-permissions
herdr agent start WORKER --kind agy --pane PANE_ID -- --model EXACT_ID --dangerously-skip-permissions
```

`agent start` has no `--no-focus` flag; focus preservation belongs to workspace/tab/pane creation. Herdr supplies the executable. Arguments after `--` are native arguments: do not repeat `codex`, `claude`, or `agy` there. agy effort can be encoded in its exact model ID (`gemini-3.8-flash-low` was observed locally); do not supply a contradictory effort. Hermes uses `chat` arguments as described in [Hermes](hermes.md).

Pass arbitrary prompt text as one subprocess argument, never shell-interpolate it. For example, after creating and starting `research-1`:

```python
from pathlib import Path
import subprocess
subprocess.run([
    "herdr", "agent", "prompt", "research-1",
    Path("/absolute/task/prompt.md").read_text(),
], check=True)
```

`agent start` waits for recognized readiness. `agent prompt` submits; `--wait --timeout 30000` can additionally wait for a settled state. A timeout does not prove submission failed. Continue with the same name:

```bash
herdr agent get research-1
herdr agent wait research-1 --timeout 30000
herdr agent read research-1 --source recent-unwrapped --lines 80
```

`idle` and `done` mean a settled turn; `blocked` requires inspection; `unknown` proves neither progress nor completion. Read the durable report and verify it. Terminal alternate-screen history can be incomplete even with a large `--lines` value.

For scoped interruption use `herdr agent send-keys WORKER ctrl+c` or the harness's supported stop key, then inspect the actual process/session. The key spelling is `ctrl+c`, not `ctrl-c`. Keep native session IDs for resume; see [recovery](recovery.md).

Sources: installed `herdr --help`/subcommand help; existing Herdr skill in this repository at `plugins/herdr/skills/herdr/SKILL.md`. These task-group and durable-report preferences supersede its ordinary sibling-pane and temporary-report defaults for this workflow.
