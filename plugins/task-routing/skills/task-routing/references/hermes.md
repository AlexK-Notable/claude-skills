# Hermes as the open-model harness

Use the existing Hermes installation and selected profile. Inspect `hermes --help`, `hermes chat --help`, and the relevant local config/source before changing settings. Preserve the user's rules, skills, web tools and Herdr state integration. A new skill does not require replacing their global Hermes configuration.

## Launch and resume

For a ready Herdr pane, launch interactively, then submit the assignment once through `herdr agent prompt`:

```text
herdr agent start WORKER --kind hermes --pane PANE_ID -- chat --provider openrouter --model EXACT_OPENROUTER_ID --reasoning low --yolo --accept-hooks --pass-session-id --max-turns 12 --run-budget 180
```

Use a supported reasoning setting, toolset and task-sized turn/time limits. Check paid allowance and effective provider configuration first. Do not add `--oneshot`, `--quiet` or a query-file to this interactive-then-prompt pattern.

For explicit headless execution:

```text
hermes chat --provider openrouter --model EXACT_OPENROUTER_ID --query-file /absolute/task/prompt.md --oneshot --yolo --accept-hooks --pass-session-id --max-turns 12 --run-budget 180
```

`--yolo` bypasses command permission prompts; `--accept-hooks` separately accepts configured hooks. `--run-budget` is **seconds**, not dollars. `--query-file` preserves arbitrary prompt text without shell expansion. Resume with `--resume EXACT_SESSION_ID`; avoid `latest` when several agents are running. Preserve the original task's cumulative spending record.

## Findings tested on this host

These observations concern Hermes v0.21.0, revision `2659c917`, tested September 2026. Recheck the affected behavior after an update.

- Main inference, session titles, compaction, and model-assisted web summaries can have separate model/provider settings. Inspect all of them before claiming an exact-model route or calculating cost.
- A named custom provider successfully directed the tested main/title/compaction paths to a loopback provider. An OpenRouter base-URL override alone still attempted direct OpenRouter access. Do not describe a URL override as complete proxy coverage.
- `agent.api_max_retries: 1` meant **one total attempt** in the tested version, despite UI wording suggesting retries. Check fallback lists and auxiliary retry settings separately.
- `--safe-mode` disables customizations, plugins and MCP; `--ignore-rules` drops rules and skills. Neither is an appropriate ordinary research profile when those integrations are needed.
- The launcher strips `PYTHONPATH`; setting it did not load a missing SDK. A tested isolated Firecrawl setup used SDK4.17.0, whose `v2.search/scrape` interface needed compatibility handling for Hermes's wrapper. Verify an actual tool call before spending model tokens on a task that depends on it. Do not silently replace the global environment.
- If projecting durable `state.db` through a symlink, let SQLite create an absent target. Pre-creating an empty target caused Hermes to quarantine/replace it, breaking the intended durable-session link. Ordinary native profile storage needs no such projection.

Web-tool credentials and costs are separate from inference. Check the selected profile actually has the intended search/fetch tools and credentials. Inject only needed credentials through the established secret mechanism; never put keys in prompts or reports. A local fake-provider test establishes wiring, not real model quality or live provider billing.

Sources: the installed CLI/source and durable probes at `/home/komi/repos/claude-skills-routing-build/docs/task-routing-build/hermes/`; [Hermes source](https://github.com/NousResearch/hermes-agent). The experimental routing runtime is unfinished and is not a prerequisite or promised spending control for this skill.
