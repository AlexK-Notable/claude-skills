# Carry context through znote

Use the project that owns the work. For a substantial delegated task, keep a task hub with the goal, scope, acceptance criteria, current decisions, assignments and next action. Give each worker a linked assignment/report spoke. A small task can use one note; do not manufacture a hub and fan-out just to exercise the structure.

The orchestrator owns the shared hub and acceptance. Each worker owns its report. Record exact Herdr worker/workspace/pane handles, requested model selector/effort, resolved model/effort when observed, native session if available, and the timestamp of the latest observation. A note saying “working” is a timestamped observation, not proof of current process activity.

Before dispatch, project-scoped hybrid or semantic search can find relevant prior decisions and outcomes. Read the returned notes and follow their links. Search relevance is not proof of truth or recency; distinguish current decisions from historical plans. Give workers exact note IDs and the necessary excerpts or source paths so required context does not depend on repeating the search.

Write an ordinary assignment explaining why the task matters, what to produce, which inputs to read and what the worker owns. Keep long background in the linked notes. A reviewer should receive the report, controlling decisions and original sources explicitly, without needing the orchestrator's conversation history.

When a deliverable condenses accepted decisions, identify the conditions whose loss would change the reader's actions and ask the writer to preserve them explicitly. Keep trial-only execution limits separate from reusable policy. If a length limit conflicts with required coverage, surface that conflict instead of silently dropping conditions. Compare the delivered wording with the accepted decisions before accepting coverage. If a coverage report is useful, ask it to quote the delivered text beside its source; verify both the quotations and their meaning. A worker's “covered” verdict is not evidence that every condition survived.

When a worker has znote tools, it can read notes directly and update its own spoke. Fetch the current version and use `expected_version` for updates; re-read and reconcile conflicts. When tools are unavailable, supply identified note exports and have the worker write durable Markdown. The orchestrator imports the report into its spoke and records that fallback. Do not make MCP installation or configuration repair a prerequisite for the task.

At acceptance, inspect the files and independently retrieve any claimed note update before marking it delivered. Verify that the hub links to the reports, then update its leading status, accepted outcome and outstanding work. Preserve full reports separately from the orchestrator's corrections to their claims. Keep terminal transcripts and large evidence in durable files rather than copying them into every note.

Record what the handoff actually exercised: consuming exports does not demonstrate direct note retrieval, and a successful write to one's own spoke does not prove the whole handoff used MCP. Keep reusable findings with their evidence; do not turn every terminal event into a note.
