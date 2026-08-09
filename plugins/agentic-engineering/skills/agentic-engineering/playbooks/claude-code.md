# The Claude Code Harness

**Use when:** you are applying this corpus inside Claude Code specifically — authoring a skill or plugin, dispatching subagents, writing a workflow script, installing a hook, or editing CLAUDE.md and memory files.

The corpus is harness-agnostic. This file maps its principles onto the surfaces Claude Code gives you, and names which surface enforces what. Mechanics below were read off live artifacts on this machine; paths are given so you can re-check them.

## 1. `description:` is the gate — write it in trigger vocabulary

SKILL.md frontmatter carries two load-bearing fields, `name` and `description` (`../SKILL.md`; `plugins/testing-methodology/skills/testing-methodology/SKILL.md` for the scaffolded form). The description is the only part always resident in context; the body is read on demand. So it is not a summary — it is the lexical surface a caller's prompt has to collide with.

Write it as symptoms, error strings, tool names, and phrasings the caller already has in context. `../SKILL.md`'s own description enumerates *"deciding single vs multi-agent"*, *"writing dispatch prompts"*, *"why an agent system is failing"* — the shapes a request arrives in, not the topics the guide is organized by. Method and worked example: `./building-a-skill.md`.

Why: → ../references/context-degradation.md T2.2, ../references/caching-and-knowledge-delivery.md T6.2

## 2. `skill-rules.fragment.json` is the machine-readable half of the same gate

This plugin ships `plugins/agentic-engineering/skill-rules.fragment.json` — the worked example. `install.sh` merges every `plugins/*/skill-rules.fragment.json` via `jq -s 'add // {}'` into `~/.claude/skills/skill-rules.json` under `.skills`; the `UserPromptSubmit` hook `skill-activation-prompt.sh` matches each prompt against it.

The matcher is literally lexical, so author for it (verified in `hooks/skill-activation-prompt.ts`):

- The prompt is lowercased. Keywords **≥5 chars** match by plain substring; **<5 chars** require word boundaries (so `"bw"` won't fire on `bwrap`).
- `intentPatterns` are case-insensitive regexes — mirror how requests are *phrased*, not what they mean. The fragment's `"(single|multi)[\\s-]?agent"` catches "single agent", "multi-agent", and "multiagent" in one line.
- `fileTriggers` (`pathPatterns`, `contentPatterns`) fire on what the operator is touching — `**/.claude/agents/**`, `subagent_type` — routing by evidence rather than phrasing.

Keep the fragment's keywords and the description in the *same* vocabulary; two gates disagreeing on terminology pays the paraphrase penalty twice.

Why: → ../references/caching-and-knowledge-delivery.md T6.2

## 3. Every `Agent` dispatch is a P3.2 contract — and you set the model

The Agent tool spawns an isolated context window, and its final message is the deliverable — the report is not shown to the user, so the orchestrator must relay it. Each dispatch is therefore the orchestrator-worker contract: objective, output format, scope in/out, and the context the worker cannot discover. Use the block in `./writing-a-dispatch-prompt.md` rather than re-deriving it.

Harness-specific additions:

- **Pass `model:` explicitly on every dispatch.** It takes `sonnet | opus | haiku | fable`; omitted, it falls back to the agent definition's model or **inherits from the parent**. Silent inheritance is how a fan-out gets expensive without anyone choosing it. `[ANECDOTAL — operator's standing rule]`: Opus for reviewer/gate/judge roles, Sonnet for builder/mechanical roles; a deep-reasoning Fable unit asked for by name is the tool used correctly, not a violation.
- **One worker owns one file.** Parallelize reads, single-thread writes: fan out for search, audit, survey; converge to one context for the mutation.
- **Send independent dispatches in one message** so they run concurrently — that parallelism is why isolated windows beat one overstuffed one.

Why: → ../references/tool-design.md P3.2 (model tiering: item 6; single-threaded writes: ../references/multi-agent.md T5.2, "Synthesis — 2026")

## 4. Workflow scripts: `pipeline()` streams, `parallel()` gathers, barriers are a choice

A workflow file encodes the same synthesis in code. Verified against a real local script (`~/.claude/projects/-home-komi-repos-self-learn/.../workflows/scripts/deep-research-wf_5399f939-9a0.js`, run 2026-07-21 — this corpus's own research harness):

- `agent(prompt, { label, phase, schema })` returns the schema-shaped object, or `null` when the user skips it.
- `pipeline(items, stageFn, stageFn…)` runs stages **per item with no barrier** — item 1 reaches stage 2 while item 5 is still in stage 1.
- `parallel(arrayOfThunks)` gathers, and nests (3 verification votes fanned inside a fan-out over claims).

**Insert a barrier only when a stage needs *all* prior results.** The script marks both cases: none through search→dedup→fetch, then an explicit one before verification, because the claim pool must be complete before it can be ranked.

Two things worth copying. Budget counters *record* what they drop (`fetchSlots`, `budgetDropped`, `MAX_VERIFY_CLAIMS`) instead of truncating silently. And `null` — agent skipped or errored — stays distinct from a real negative verdict; per the script's own comment, infra failure must not read as "refuted". `[SYNTHESIS]` A gate that cannot tell "the check failed" from "the check never ran" reports success when it is blind.

Schema authoring: `reasoning` field first **and required** — `./writing-a-dispatch-prompt.md` §5.

Why: → ../references/multi-agent.md P3.1, ../references/loops-and-stop-conditions.md P4.1, ../references/prompt-mechanics.md T3.3

## 5. Hooks are the structural gate — pipe-test before trusting one

`PreToolUse` / `PostToolUse` hooks in `settings.json` are the harness's implementation of structural verification: a check that runs whether or not the model chose to check. That is what P4.7 says beats self-review, and what closes the knowledge-action gap on load-bearing steps.

**The danger is fail-open, and it is the default.** The official hookify plugin's `PreToolUse` wraps everything in `try/except` and ends `# ALWAYS exit 0 - never block operations due to hook errors` (`~/.claude/plugins/.../hookify/hooks/pretooluse.py:61`). Reasonable for an advisory hook; fatal for a gate — a broken gate passes everything and reads exactly like a clean run.

Measured, not inferred. `~/.claude/hooks/no-sudo.sh` reads `$CLAUDE_TOOL_NAME` / `$CLAUDE_TOOL_INPUT_COMMAND`. Given those env vars with `sudo ls`, it returns **rc=2** and `{"decision":"block",…}`. Given the stdin-JSON shape hookify reads (`{"tool_name":"Bash","tool_input":{"command":"sudo ls"}}`), it returns **rc=0** and allows it. Same logic, same command, opposite outcome — and nothing in the source says which contract you are on.

So **pipe a known-bad input through the hook and confirm it blocks**, capturing the status unpiped (a pipe replaces it). A gate you have only read is a hypothesis.

Why: → ../references/loops-and-stop-conditions.md P4.7 (structural gates), P4.1 (semantic completion gates)

## 6. Memory surfaces obey the retrievability rules

CLAUDE.md, managed sections, and memory files are read *cold*, by an agent that has not yet decided the entry is relevant — so T6.3's rules apply verbatim.

- **Trigger-shaped entries.** Lesson entries in `~/.claude/CLAUDE.md` open `**When about to X:** do Y` — the condition first, in the vocabulary of the moment it applies. An entry titled by topic is retrievable only by someone already hunting that topic.
- **Verbatim identifiers.** Paths, commit hashes, lesson IDs (`lrn-ea833a5b`), env var names — never paraphrased.
- **Index over atomic files.** `memory/MEMORY.md` is a pointer list to one-topic files: progressive disclosure applied to memory.
- **Managed sections are machine-owned.** `testing-methodology/SKILL.md` fences routed lessons in `<!-- self-learn:begin … end -->`; prose outside survives recompile, hand-edits inside are discarded. `[ANECDOTAL]`
- `[SYNTHESIS]` Budget these surfaces — they are the standing context tax every session pays. When one outgrows its budget, evict or demote to a reference file; appending is not free, and length alone costs accuracy.

Why: → ../references/caching-and-knowledge-delivery.md T6.3, ../references/context-degradation.md T2.2

## Cross-reference: principle → CC surface

| Corpus principle | Anchor | Claude Code surface |
|---|---|---|
| Progressive disclosure | T6.2 | `description:` gate over on-demand body/references |
| Lexical matching decides retrieval | T2.2 | `description:`, fragment `keywords`/`intentPatterns` |
| Worker prompts are contracts | P3.2 | `Agent` prompt; `agent()` in a workflow |
| Match model tier to subtask | P3.2 §6 | `model:` — set it, never inherit |
| Isolated windows beat one big one | P3.2 §5 | Subagent context; `isolation: "worktree"` |
| Single-thread the writes | multi-agent synthesis | One worker per file; converge before mutating |
| Parallelize only genuine breadth | P3.1 | `parallel()`; barrier only when a stage needs all |
| Structured returns kill parse failures | T3.3 / P1.5 | `schema:` on `agent()`; `reasoning` first + required |
| Explicit stop conditions | P4.1 | `--max-turns`; counters that log what they drop |
| Structural, not rhetorical, verification | P4.7 | `PreToolUse`/`PostToolUse` hooks |
| State outside the window | T6.3 | CLAUDE.md, managed sections, `memory/` files |
| Compaction is lossy | T6.4 | Compact instructions pinning verbatim identifiers |
