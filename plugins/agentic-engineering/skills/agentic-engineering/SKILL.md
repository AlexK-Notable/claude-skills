---
name: agentic-engineering
description: Evidence-based guide to prompt, context, agent, and loop engineering for frontier LLM agents (mid-2026). Use when designing agent systems, deciding single vs multi-agent, writing dispatch prompts, managing context windows, designing tools for agents, setting stop conditions, structuring caching, or evaluating why an agent system is failing. Covers theory (why context degrades, why multi-agent systems fail, attention mechanics) and practice (orchestrator-worker patterns, tool design, cache-aware prompt structure, progressive disclosure).
---

# Agentic Engineering: Theory and Practice

A guide to engineering systems around frontier LLMs, split into **Theory** (why these systems behave the way they do) and **Practice** (patterns that work). Built from adversarially verified research findings (every claim survived a 3-vote refutation panel unless marked otherwise) plus current vendor documentation.

## The thesis

Three load-bearing ideas organize everything in this guide:

1. **Context is the product.** Prompt engineering matured into context engineering: the discipline of curating what enters a model's finite attention budget at each step. An agent is a function of its context — the working environment you construct matters as much as the task you assign.
2. **Capability degrades with context length, and not for the reason most people think.** Degradation is driven by attention's reliance on surface-level lexical matching, conditioned by window occupancy — not by position alone. Claimed context windows substantially overstate effective ones.
3. **Trust nothing an agent reports about its own work.** Verification must be structural (independent checks against actual output), not rhetorical (the agent saying it succeeded).

## Evidence labels

Every substantive claim in the reference files carries one of:

- `[HIGH]` — verified against primary sources, survived 3-vote adversarial refutation, ≥2 independent sources or peer review
- `[MEDIUM]` — verified but single-source, vendor-internal, or tested only on older/open-source models
- `[CORROBORATED*]` — independently corroborated by a single-verifier research probe (sources checked, but no adversarial panel); stronger than vendor-doc, weaker than HIGH
- `[VENDOR-DOC]` — current official platform documentation (authoritative for mechanics, not independently validated for effectiveness claims)
- `[ATTRIBUTION]` — accurately attributed position statement, not an empirical finding
- `[PENDING]` — section awaiting a dedicated research pass; treat any content there as provisional

**Recency caveat (applies globally):** the strongest empirical degradation work tests 2023–mid-2025 model generations. Nothing here directly measures mid-2026 frontier models on 200K–1M windows. Mechanisms are the durable content; magnitudes are snapshots.

## Reading map

| File | Pillar | Status |
|------|--------|--------|
| `references/foundations.md` | Theory: the discipline, workflows vs agents, simplest-viable-design | **Complete** |
| `references/context-degradation.md` | Theory: context rot, lexical matching, lost-in-the-middle revised | **Complete** |
| `references/multi-agent.md` | Theory: economics, equal-budget evidence, MAST failure modes, the Anthropic–Cognition dialectic, A2A footnote | **Complete** |
| `references/tool-design.md` | Practice: ACI design, tool-catalog costs, CLI vs MCP vs code-execution, orchestrator-worker implementation | **Complete** |
| `references/caching-and-knowledge-delivery.md` | Theory+Practice: cache mechanics, progressive disclosure, JIT retrieval, memory architecture, summarization | **Complete** |
| `references/data-formats.md` | Practice: token-efficient serialization (shape × tier × direction) | **Complete** |
| `references/loops-and-stop-conditions.md` | Practice: stop conditions, budget pressure, trust calibration (flagship) | **Mostly complete** — HITL gates / self-correction (P4.5/P4.6) not yet researched |
| `references/prompt-mechanics.md` | Theory+Practice: serial position, instruction-following, structured output | **Complete** (researched); local dispatch patterns held back per source policy |
| `references/SOURCES.md` | Provenance: bibliography (with source URLs), per-claim evidence ledger, refuted claims | **Complete** |

## How to use this skill

For a **design decision** (single vs multi-agent, tool surface choice, context budget): read the relevant theory file first — the practice patterns assume its mental model. For a **failure diagnosis**: start with `multi-agent.md` (MAST categories) and `context-degradation.md` (length/distractor effects). For **building**: `tool-design.md` and `caching-and-knowledge-delivery.md` are self-contained. To **trace a claim** to its source, confidence label, or the underlying paper: `SOURCES.md` is the bibliography + evidence ledger.

Pending sections name the research pass that will fill them. Do not improvise content for pending sections from training data — the gaps exist because available evidence was checked and found insufficient or refuted.
