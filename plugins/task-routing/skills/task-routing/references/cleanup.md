# Finish and clean up Herdr resources

Record the workspace/tab/pane IDs returned when this task creates them, together with worker names and native session IDs. Labels and current focus do not establish ownership. By default, clean up those resources when the task completes or is cancelled; honor a request to retain them for inspection or continuation.

Save accepted or partial reports outside terminal scrollback, verify claimed note writes, and record the outcome before closing terminals. Keep resumable native session IDs even when their panes are removed. Closing a terminal does not delete its worktree or durable reports; worktree deletion is a separate decision.

## Stop the worker

Use the harness's supported interrupt/exit action on the exact owned worker. For example:

```bash
herdr agent send-keys WORKER esc
herdr agent send-keys WORKER ctrl+c
herdr pane process-info --pane PANE_ID
```

These are actions to select after inspecting the session, not a sequence to send blindly. `esc` may stop the current turn without exiting the agent. A harness may require a second `ctrl+c` after displaying an exit prompt. Use its native exit command when appropriate. Verify that the foreground has returned to the shell; a sent key or Herdr `done` state is not proof of process exit. The installed Herdr agent command group has no `agent kill` subcommand.

## Close owned layout

The installed CLI accepts explicit IDs:

```bash
herdr pane close PANE_ID
herdr tab close TAB_ID
herdr workspace close WORKSPACE_ID
```

Choose the narrowest appropriate action. A pane close can terminate a foreground process; use it as the fallback for an owned worker that will not exit after a bounded graceful attempt. A tab/workspace close affects its contained panes, so inspect their current occupants first and close the container only if every affected resource belongs to this task and no work needs to continue. If another task shares it, close only this task's owned panes. Never close the caller's own pane/workspace while it is still coordinating or delivering its result; its parent can close it after collecting that result.

When the whole task-created group is finished, close its workspace directly instead of issuing redundant closes for every descendant. If individual closes remove the last pane or tab, re-list before further cleanup rather than assuming the parent still exists. Do not kill the Herdr server, use broad process-name kills, or sweep old similarly named groups.

## Verify cleanup

Inspect `herdr api snapshot` or explicit workspace/tab/pane lists before and after closure. Confirm the exact owned IDs are absent from a successful live response; an error or empty response is not proof of removal. Check that the user's original focus and peer resources are preserved. Pane removal does not establish that a separately detached job stopped: if the task launched one, verify that specific recorded process independently.

Update the task hub with which resources were closed, which were deliberately retained and any unfinished cleanup. Keep the notes and files needed to understand or resume the work.
