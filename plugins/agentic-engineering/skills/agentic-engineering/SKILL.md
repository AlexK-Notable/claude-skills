---
name: agentic-engineering
description: Action-first playbooks over an evidence corpus, for prompt, context, agent, and loop engineering with frontier LLM agents (mid-2026). Routes by task: designing agent systems, deciding single vs multi-agent, writing dispatch prompts (subagent/worker prompts), designing tools for agents (tool catalogs, MCP vs CLI), building skills (SKILL.md descriptions, progressive disclosure), structuring context and caching (prompt caching, cache hit rate, memory files), setting stop conditions, verifying agent output when an agent says it is done, and why an agent system is failing. References carry the evidence — context degradation, multi-agent failure modes, attention and cache mechanics — under per-claim confidence labels.
---

# Agentic Engineering: Theory and Practice

A guide to engineering systems around frontier LLMs, split into **Theory** (why these systems behave the way they do) and **Practice** (patterns that work). Built from a June 2026 research pipeline — 3-vote adversarial refutation panels for `[HIGH]` and `[MEDIUM]` claims, single-verifier probes for `[CORROBORATED*]` ones — plus current vendor documentation. An independent nine-agent re-audit re-checked every claim against re-fetched primary sources on 2026-08-08; its corrections are applied here and logged in `references/SOURCES.md`. Read the per-claim labels rather than assuming a uniform standard across the corpus.

## The thesis

Three load-bearing ideas organize everything in this guide:

1. **Context is the product.** Prompt engineering matured into context engineering: the discipline of curating what enters a model's finite attention budget at each step. An agent is a function of its context — the working environment you construct matters as much as the task you assign.
2. **Capability degrades with context length, and not for the reason most people think.** Degradation is driven by attention's reliance on surface-level lexical matching, conditioned by window occupancy — not by position alone. Claimed context windows substantially overstate effective ones.
3. **Trust nothing an agent reports about its own work.** Verification must be structural (independent checks against actual output), not rhetorical (the agent saying it succeeded).

## Evidence labels

Every substantive claim in the reference files carries one of:

- `[HIGH]` — verified against primary sources; ≥2 independent sources or peer review, and (for labels assigned in the June 2026 pass) survived 3-vote adversarial refutation
- `[MEDIUM]` — verified but single-source, vendor-internal, or tested only on older/open-source models
- `[CORROBORATED*]` — independently corroborated by a single-verifier research probe (sources checked, but no adversarial panel); stronger than vendor-doc, weaker than HIGH
- `[VENDOR-DOC]` — current official platform documentation (authoritative for mechanics, not independently validated for effectiveness claims)
- `[ATTRIBUTION]` — accurately attributed position statement, not an empirical finding
- `[SYNTHESIS]` — this corpus's own framework or inference; no external source claims it. Judge it on the reasoning shown, and never cite it as though a vendor or paper said it
- `[ANECDOTAL]` — validated locally in practice but not corroborated by any external source; carried by `prompt-mechanics.md` P1.1–P1.3 (unlocked 2026-08-08) and by operator-rule notes in the playbooks
- `[PENDING]` — section awaiting a dedicated research pass; treat any content there as provisional. `[HELD BACK]` (withheld per source policy, not a gap) stays defined but is currently unused

**As-of convention:** figures quoted from live sources — pricing tables, TTLs, repo READMEs and version numbers, preprint figures that move between revisions — carry an `as of YYYY-MM-DD` date where they are used, and must be re-checked before anything depends on them. Treat an undated live-source figure as expired.

**Recency caveat (applies globally):** most empirical degradation work here tests 2023–mid-2025 model generations, so read magnitudes as snapshots and mechanisms as the durable content. The mid-2026 frontier is no longer unmeasured — ATLAS profiles 26 models on an 8K–1M grid and finds decay is capability-specific rather than one failure mode (`references/context-degradation.md`).

## Start here

| Task | Playbook (in `playbooks/`) | Evidence behind its steps |
|---|---|---|
| Workflow vs agent vs multi-agent | `designing-an-agent-system.md` | foundations T1.1/T1.3 · multi-agent P3.1/T4.1/T5.1/T5.2 |
| Writing a subagent / worker prompt | `writing-a-dispatch-prompt.md` | tool-design P3.2 · prompt-mechanics T3.1–T3.3/P1.1 · loops P4.1/P4.7 |
| Choosing or designing tools | `designing-a-tool-surface.md` | tool-design P3.3, catalog costs, surface choice · data-formats P2.3 · caching T6.2 |
| Authoring a skill or knowledge package | `building-a-skill.md` | caching T6.2/T6.3 · context-degradation T2.2 · loops P4.7 |
| Laying out context, caching, memory | `structuring-context.md` | caching T6.1/T6.3/T6.4 · context-degradation T2.2–T2.4 |
| Bounding a loop / verifying output | `closing-the-loop.md` | loops P4.1/P4.7 · multi-agent T5.1 |
| Doing any of this in Claude Code | `claude-code.md` | the rows above, mapped onto CC surfaces |
| *Diagnose:* agent underperforms | `designing-an-agent-system.md` Step 4 | foundations T1.3 (what was in the window?) · multi-agent T5.1 |
| *Diagnose:* cache hit rate zero, cost drift | `structuring-context.md` steps 2–3 | caching T6.1 |
| *Diagnose:* agent claims done, artifact wrong | `closing-the-loop.md` steps 2–4 | loops P4.7 |

## References — the evidence layer

All under `references/`, all **complete** except as noted:

- `foundations.md` — workflows vs agents; the context-first diagnostic
- `context-degradation.md` — context rot, lexical matching, occupancy, distractors
- `multi-agent.md` — economics, equal-budget evidence, MAST taxonomy, the Anthropic–Cognition dialectic
- `tool-design.md` — ACI, bash-vs-tool promotion, catalog costs, transport choice, orchestrator-worker
- `caching-and-knowledge-delivery.md` — cache mechanics and economics, progressive disclosure, memory, summarization
- `data-formats.md` — serialization by shape × model × direction
- `loops-and-stop-conditions.md` — stop conditions; trust calibration. **Mostly complete** — P4.5/P4.6 `[PENDING]`
- `prompt-mechanics.md` — serial position, instruction-following, structured output, local dispatch practice
- `SOURCES.md` — bibliography, per-claim evidence ledger, refuted claims

Never improvise content for `[PENDING]` sections from training data — those gaps exist because the available evidence was checked and found insufficient or refuted.
