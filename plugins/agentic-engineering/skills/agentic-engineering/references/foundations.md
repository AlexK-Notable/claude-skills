# Foundations: Context Engineering as the Discipline

Theory pillar T1. Status: **complete**. Sources verified 2026-06-12; corrected and re-audited 2026-08-08.

## T1.1 — Workflows vs agents, and the simplest-viable-design doctrine `[VENDOR-DOC]`

The foundational taxonomy (Anthropic, Dec 2024; still their working vocabulary — the Sep 2025 context-engineering post cites it):

- **Workflows**: systems where LLMs and tools are orchestrated through *predefined code paths*. You decide the control flow; the model fills in steps.
- **Agents**: systems where LLMs *dynamically direct their own processes and tool usage*. The model decides the control flow.

The doctrine that accompanies it: **start with the simplest viable design**. "For many applications, however, optimizing single LLM calls with retrieval and in-context examples is usually enough." The post reserves agents for open-ended problems: you can't predict how many steps a task will take, or hardcode a fixed path.

The operational adoption checklist quoted alongside that doctrine is not in the Dec 2024 post — it comes from Barry Zhang's AI Engineer Summit 2025 talk "How We Build Effective Agents" (New York; secondary write-ups mostly render it as four checks — one splits verifiability out as a fifth). Four checks before you commit to an agent: **complexity** (is the decision space genuinely ambiguous, or can you enumerate the tree?), **value** (does the task justify exploratory token spend plus the eval and monitoring autonomy demands?), **critical capabilities** (can the model do every essential step at acceptable accuracy, latency, and cost — one fatal bottleneck sinks the loop), and **cost of errors** (how expensive are mistakes, and how quickly are they discovered — when both are bad, constrain autonomy with read-only scopes or human checkpoints rather than trusting the loop).

Why this matters: moving rightward on the workflow→agent spectrum trades away predictability, bounded cost, and inspectability, in exchange for handling tasks you couldn't enumerate in advance.

Caveats: the definitions are *how*-based — third-party critics note this may not age well as harnesses blur the line (a "workflow" whose steps are themselves agentic loops is both). The canonical orchestrator-workers pattern is classified by the original taxonomy as a *workflow*, not an agent — even though Anthropic is explicit the subtasks are *not* pre-defined, but "determined by the orchestrator based on the specific input." What's predefined is the shape of the run — decompose → delegate → synthesize — with workers being individual LLM calls, not loops of their own. Fixed topology, dynamic content.

Sources: anthropic.com/engineering/building-effective-agents (Dec 2024; the older /research/ path redirects here); anthropic.com/engineering/effective-context-engineering-for-ai-agents (Sep 2025); Barry Zhang, "How We Build Effective Agents," AI Engineer Summit 2025 (talk).

## T1.2 — Context engineering as the successor discipline `[ATTRIBUTION]`

Two organizations that disagree about multi-agent architecture *converge* on this: context engineering — managing what enters a model's context window — is the core discipline of agent building.

- Cognition (Jun 2025): context engineering is "effectively the #1 job of engineers building AI agents." `[ATTRIBUTION]`
- Anthropic (Sep 2025): dedicated effective-context-engineering guidance, framing context as a finite resource to curate rather than a container to fill. `[VENDOR-DOC]`

The convergence matters more than either statement alone: it is the rare point of agreement across the central architectural debate of 2025–26 (see `multi-agent.md`). Where vendors disagree about *how many agents*, nobody disputes that *what's in the window* is the dominant quality lever. Read the evidence for what it is: both items are positions, not independent measurements — the convergence is in practitioners' judgement about where the leverage sits.

The historical arc: "prompt engineering" optimized a static artifact (the prompt) for a single call. Agents broke that frame — an agent's context is rebuilt every step from tool results, retrieved knowledge, conversation history, and orchestrator injections. The artifact being engineered is no longer a prompt; it is a *pipeline that produces contexts*. That shift is why context lifecycle — degradation, caching, compaction, memory, progressive disclosure — gets more attention here than prompt wording.

Sources: cognition.com/blog/dont-build-multi-agents (Jun 2025; the original cognition.ai domain now redirects to cognition.com); anthropic.com/engineering/effective-context-engineering-for-ai-agents (Sep 2025).

## T1.3 — The agent as a function of its context `[SYNTHESIS]`

The operating claim: **an agent's behavior is determined jointly by its model, its tools, and its context — and of the three, context is the one you rebuild every step.** The same model with the same tools produces expert or useless behavior depending on what its working environment contains: which facts are in-window, how they're positioned and formatted, what distractors share the window, how much of the window is occupied.

This is a framework claim, not a result from any one paper, but it is multiply supported. Three verified results make it concrete:

1. Performance on *identical tasks* degrades non-uniformly as input grows — the task didn't change, the context did (`context-degradation.md`, T2.1).
2. Distractor content sharing the window amplifies failure, with model-family-specific signatures (T2.5).
3. Multi-agent systems break down on coordination as much as on raw capability: MAST's inter-agent-misalignment category covers roughly a third of observed failures, spread across six modes — reasoning-action mismatch (13.2%, an agent acting against its own stated reasoning), task derailment (7.4%), failing to ask for clarification (6.8%), conversation reset (2.2%), ignored agent input (1.9%), and information withholding (0.85%) (`multi-agent.md`, T5.1).

   That headline third needs unpacking: the modes that literally mean "one agent never got what another knew" — withholding, ignored input, reset — sum to about 5%; the single largest mode is reasoning-action mismatch. And the largest MAST category overall is system design, at roughly 44%. Context handling is one major failure surface here, not the whole account.

Design consequence: when an agent underperforms, the first diagnostic question is not "is the prompt worded well?" or "is the model capable enough?" but **"what was actually in its window at the failure step, and what wasn't?"** Most production failures trace to context starvation (a needed fact never entered the window), context pollution (distractors or stale results crowded it), or context degradation (the fact was present but unfindable — see the lexical-matching mechanism in T2.2).
