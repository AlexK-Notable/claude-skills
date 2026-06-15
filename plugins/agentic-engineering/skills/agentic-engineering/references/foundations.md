# Foundations: Context Engineering as the Discipline

Theory pillar T1. Status: **complete**. Sources verified 2026-06-12 (z-note hub: `agent-engineering-guide` project).

## T1.1 — Workflows vs agents, and the simplest-viable-design doctrine `[HIGH]`

The foundational taxonomy (Anthropic, Dec 2024; reaffirmed through 2025–26 in the context-engineering post, the multi-agent research system writeup, and conference restatements):

- **Workflows**: systems where LLMs and tools are orchestrated through *predefined code paths*. You decide the control flow; the model fills in steps.
- **Agents**: systems where LLMs *dynamically direct their own processes and tool usage*. The model decides the control flow.

The doctrine that accompanies it: **start with the simplest viable design**. "Optimizing single LLM calls with retrieval and in-context examples is usually enough." Adopt agentic systems only when the latency/cost trade-off is justified by the task: multi-step, hard to fully specify in advance, high value, viable for the model, and with recoverable errors.

Why this is the skeleton of the whole field: every subsequent pattern (orchestrator-workers, stop conditions, context isolation) is a response to what you give up when you move rightward on the workflow→agent spectrum — predictability, bounded cost, and inspectability — in exchange for handling tasks you couldn't enumerate in advance.

Caveats: the definitions are *how*-based (how the system is orchestrated), and third-party critics note how-based definitions may not age well as harnesses blur the line (a "workflow" whose steps are themselves agentic loops is both). Treat the taxonomy as a design vocabulary, not an ontology. Notably, the canonical orchestrator-workers pattern is classified by the original taxonomy as a *workflow*, not an agent — the orchestrating code path is predefined even though workers act autonomously within it.

Sources: anthropic.com/research/building-effective-agents (Dec 2024); anthropic.com/engineering/multi-agent-research-system (Jun 2025).

## T1.2 — Context engineering as the successor discipline `[HIGH attribution, convergent]`

Two organizations that disagree sharply about multi-agent architecture *converge* on this: context engineering — managing what enters a model's context window automatically and dynamically — is the core discipline of agent building.

- Cognition (Jun 2025): context engineering is "effectively the #1 job of engineers building AI agents." `[ATTRIBUTION]`
- Anthropic (Sep 2025): dedicated effective-context-engineering guidance, framing context as a finite resource to curate rather than a container to fill. `[VENDOR-DOC]`

The convergence matters more than either statement alone: it is the rare point of agreement across the central architectural debate of 2025–26 (see `multi-agent.md`). Where vendors disagree about *how many agents*, nobody disputes that *what's in the window* is the dominant quality lever.

The historical arc: "prompt engineering" optimized a static artifact (the prompt) for a single call. Agents broke that frame — an agent's context is rebuilt every step from tool results, retrieved knowledge, conversation history, and orchestrator injections. The artifact being engineered is no longer a prompt; it is a *pipeline that produces contexts*. That shift is why the rest of this guide spends more pages on context lifecycle (degradation, caching, compaction, memory, progressive disclosure) than on prompt wording.

## T1.3 — The agent as a function of its context `[MEDIUM — framework claim, multiply supported]`

The operating claim: **an agent's behavior is determined jointly by its model, its tools, and its context — and of the three, context is the one you rebuild every step.** The same model with the same tools produces expert or useless behavior depending on what its working environment contains: which facts are in-window, how they're positioned and formatted, what distractors share the window, how much of the window is occupied.

Three verified results make this concrete:

1. Performance on *identical tasks* degrades non-uniformly as input grows — the task didn't change, the context did (`context-degradation.md`, T2.1).
2. Distractor content sharing the window amplifies failure, with model-family-specific signatures (T2.5).
3. Multi-agent failure modes are dominated by context problems — inter-agent misalignment (context not shared thoroughly) accounts for roughly a third of failures in the MAST taxonomy (`multi-agent.md`, T5.1).

Design consequence: when an agent underperforms, the first diagnostic question is not "is the prompt worded well?" or "is the model capable enough?" but **"what was actually in its window at the failure step, and what wasn't?"** Most production failures trace to context starvation (a needed fact never entered the window), context pollution (distractors or stale results crowded it), or context degradation (the fact was present but unfindable — see the lexical-matching mechanism in T2.2).
