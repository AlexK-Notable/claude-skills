# Observe, recover, and accept

Keep the worker's Herdr name/pane, native session ID, assignment and durable report path together. For paid work, preserve the same cumulative allowance across retries and resume.

| Observation | Action |
|---|---|
| Prompt/read/wait timeout | Inspect the same agent; a timeout does not prove the prompt was not delivered |
| Login, tool, or approval block | Read the actual prompt/error and resolve the specific prerequisite within existing authorization |
| Idle/done but absent or incorrect output | Inspect the artifact and request a scoped correction from the existing worker |
| Pane or launcher disappears | Check the recorded native session/process before assuming work stopped or relaunching |
| Subscription limit reached | Preserve partial output and reroute by the original task category and capacity rules |
| Paid allowance reached or cost uncertain | Stop new paid calls, retain partial work and possible charges, and report what remains |
| Quality failure | One targeted correction where useful, or a deliberate stronger model after closing the old execution |

Interrupt only the owned worker. `herdr agent send-keys NAME ctrl+c` is a scoped input, not proof the native process exited. Read its state and `herdr pane process-info --pane PANE_ID`. Never kill the Herdr server or delete a shared workspace for cancellation.

Once reports or partial results are saved, follow [cleanup](cleanup.md) to close the task-created layout. Keep the caller alive until it has delivered its result, and leave peer resources alone.

Resume by recorded exact session: Claude `--resume ID`, agy `--conversation ID`, Hermes `chat --resume ID`; Codex uses its `resume` subcommand (inspect installed help for interactive versus `exec resume`). If native resume is unavailable, hand off the saved artifacts explicitly. Do not duplicate work whose execution is still uncertain.

For headless commands, Claude stream-json requires `--verbose`; Codex `exec --json -` accepts the prompt on stdin; the tested agy CLI instead required a single `--print=TEXT` argument. Supply arbitrary text via a subprocess argument array, never unsafe shell interpolation. Headless children should not inherit Herdr pane metadata that would make their hooks report state into the parent's pane.

## Acceptance

Inspect the actual output against the assignment. For code, run the relevant behavioral check and preserve others' edits. For research, check consequential claims against sources and run locally testable checks where feasible. For planning/review, check that the deliverable addresses the stated constraints and dependencies. A source's claim, model confidence, empty command output, and exit0 are not independent proof.

Record the model/harness/effort, task type, outcome, verification, useful limitations and actual cost if known. This is lightweight evidence for subsequent routing, not a mandatory database or certification workflow. Keep full reports in a durable project directory or notes; terminal scrollback is not the sole result store.
