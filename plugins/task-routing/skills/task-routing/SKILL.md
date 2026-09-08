---
name: task-routing
description: Classify delegated work, choose an explicit model using subscription headroom and task value, and coordinate workers through Herdr, including bounded OpenRouter work with Hermes. Use from either Claude Code or Codex when choosing or dispatching agents.
---

# Task routing

Help the orchestrator choose **who should do this task, why, and how to launch them**. Claude Code and Codex can both orchestrate. Use the existing `herdr`, native agent CLIs, and `~/bin/agent-usage`; this skill does not require a routing daemon or a new task schema.

## Choose the route

**Harness boundary: agy is Gemini-only. Never launch Anthropic or OpenAI models through agy, even if its catalog lists them or their quota pool has more headroom. Use Claude Code for Anthropic subscription models and Codex for OpenAI subscription models. Apply this boundary before comparing capacity.**

1. Classify the work and difficulty using [task categories](references/routing.md). Separate cheap source gathering from difficult analysis when that makes a useful handoff. Delegate bounded, independently useful work; do not manufacture a fan-out for a simple request.
2. Read current allowance and spending in one call: `agent-usage`. Use `agent-usage --fresh` when its observations are stale. Interpret the windows and model pools using [usage](references/usage.md).
3. Among models capable of the task, prefer the subscription service with more usable headroom. Then choose the model that delivers the required quality with the least cost and allowance consumption. If subscriptions are fresh, choose the best appropriate model for the category; spare capacity does not justify Astra or Fable for routine documentation retrieval.
4. For small paid tasks, prefer an open-weight model with a demonstrated task advantage. **When Flash 3.8 research allowance is constrained, a suitable affordable open research model is the preferred next option before moving that routine research to other subscription models.** If none fits, use a suitable subscription route.
5. Pass an explicit model selector and effort on every launch. Prefer a supported family alias that tracks the latest generation, such as Claude Code's `sonnet`, `opus` or `fable`; use the [known model IDs](references/routing.md#resolve-the-actual-model) where that alias behavior is unavailable. Rely on established mappings during normal dispatch, without repeating catalog or version checks. Honor deliberate model requests and surface unavailable selections; never silently inherit or substitute a model.

The initial model families and their evidence limits are in [task categories](references/routing.md). Establish a mapping when adding a route; revisit it after a relevant harness/provider change, a model update or a selection error. Old release names in reports are not default launch recommendations.

## Dispatch

Use [Herdr dispatch](references/herdr-dispatch.md): one workspace per task group (`coding`, `review`, `research`, etc.), up to four agents per tab, overflow tabs in the same workspace, and preserve the user's focus. Keep group and worker handles in the task's durable notes. For coding, assign disjoint ownership and an appropriate worktree.

Native permission bypass is the user's authorized default. Use each harness's actual flag; honor an explicit restrictive exception. Headless versus interactive execution is a separate choice.

Give the worker a concrete deliverable, inputs, ownership, acceptance criteria, and durable report path. Adapt the [prompt template](assets/worker-prompt.md); no generated manifest is required. Ask the worker to preserve evidence and distinguish sourced claims, locally verified observations, and inference.

Resolve startup prompts before submitting work. Established model aliases do not need a separate version-verification step on each launch. Inspect native model selection when a warning, rejected selector or other evidence suggests a mismatch; follow [startup and recovery](references/herdr-dispatch.md#verify-before-submitting-work) rather than accepting a fallback silently.

Use [znote handoffs](references/znote-handoff.md) to carry project decisions, assignments and accepted results between workers. Keep prompts conversational: explain the purpose, point to the relevant notes and files, and state the outcome and boundaries. The template is a checklist, not a required prompt format.

For OpenRouter, read [paid model selection](references/openrouter.md) and [Hermes](references/hermes.md). Keep paid work small, with approximately **USD5 maximum for the whole invocation, including auxiliary calls, retries and resume**. Do not use long-horizon Kimi work as the ordinary fallback. Check what spending controls actually exist; a turn limit or time limit is not a dollar cap.

## Observe and finish

Observe the same worker after a timeout; do not submit the task twice. An idle agent or successful process exit means the turn stopped, not that the work passed. Inspect its durable output and independently check the task's acceptance criteria. Use [recovery](references/recovery.md) for interruption, missing output, or exhausted allowance.

After saving results, [clean up the task's Herdr resources](references/cleanup.md): stop owned workers and close their task-created panes, tabs and workspaces unless the user asked to retain them. Record ownership at creation and verify removal; preserve reports, native session IDs, peer resources and the caller's pane.

Keep the route explanation brief: category/difficulty, harness + explicit alias/model + effort, relevant allowance, why it fits, and paid allowance if applicable. Record meaningful results for future selections; small local trials and published benchmarks inform judgment without becoming universal eligibility gates.
