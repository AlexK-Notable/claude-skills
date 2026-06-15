# Multi-Agent Systems: Economics, Failure Modes, and the Central Dialectic

Theory pillars T4 + T5. Status: **complete**. Core claims adversarially verified 2026-06-12; equal-budget evidence and protocol-landscape sections verified by Opus probes same day (`[CORROBORATED*]` = single-verifier probe).

## T5.2 — The Anthropic–Cognition dialectic (read this first) `[HIGH]`

The defining architectural debate of 2025–26, best understood as thesis → antithesis → synthesis:

**Thesis — Anthropic (Jun 2025):** orchestrator-workers is the canonical multi-agent architecture — a lead model dynamically decomposes a task and delegates to 3–5 parallel worker LLMs, each with an *isolated* context window. Their production research system (Opus 4 lead + Sonnet 4 workers) outperformed single-agent Opus 4 by **90.2%** on an internal breadth-first research eval. Mandatory caveats: internal vendor eval with undisclosed metric; the system used ~15× chat-level tokens and the writeup itself attributes much of the gain to token spend; Anthropic explicitly limits the claim — high-dependency, shared-context domains "are not a good fit for multi-agent systems today." Cite as: *Anthropic's internal result for breadth-first, parallelizable tasks when extra token spend is acceptable* — never as general multi-agent superiority.

**Antithesis — Cognition, "Don't Build Multi-Agents" (Jun 2025) `[ATTRIBUTION]`:** multi-agent collaboration (as of mid-2025) produces fragile systems because decision-making disperses and context cannot be shared thoroughly enough. Two design principles follow: (1) **share full agent traces with subagents, not summarized messages**; (2) **avoid parallel agents acting on conflicting implicit decisions**. This is an influential position statement by one co-founder, time-bounded by its own author to 2025 — not an empirical finding. But its mechanism gets independent empirical support: MAST attributes 32.3% of multi-agent failures to inter-agent misalignment.

**Synthesis — 2026:** Cognition's own follow-up ("Multi-Agents: What's Actually Working"; the Managed Devins coordinator architecture) concedes multi-agent works **when writes stay single-threaded**. Combined with Anthropic's breadth-first framing, the operational consensus:

> **Parallelize reads, single-thread writes.** Fan out for gathering, exploring, reviewing, verifying — work where workers' outputs are *inputs to a synthesis* rather than mutations of shared state. Keep one context responsible for decisions and mutations. The failure zone is parallel workers making implicit, conflicting decisions about shared artifacts.

One convergence point is undisputed across both camps: context engineering is the #1 job (see `foundations.md` T1.2). Don't let agreement on that smuggle in either side's contested architectural claims.

## T5.1 — MAST: the empirical failure taxonomy `[HIGH — peer-reviewed]`

MAST (UC Berkeley, NeurIPS 2025 Datasets & Benchmarks; 150 expert-annotated traces, κ=0.88, later expanded to 1,600+ traces across 7 frameworks) starts from the observation that multi-agent systems' **gains on popular benchmarks are often minimal**, and taxonomizes exactly **14 failure modes in 3 categories**:

1. **System design issues** — flawed specifications, role/responsibility confusion, broken termination logic. Failures baked in before any message is exchanged.
2. **Inter-agent misalignment** — agents diverging on task understanding, withholding or distorting context, conflicting implicit decisions (32.3% of failures; the empirical backbone of Cognition's position).
3. **Task verification** — accepting unverified work, premature success declarations, weak or absent checking.

Notes for correct use: "telephone game" is this guide's informal label, not MAST terminology — it maps onto inter-agent misalignment + task-verification modes. The taxonomy is explicitly non-exhaustive. And MAST does not contradict Anthropic's 90.2% result: minimal *average* gains across frameworks and a large win on one breadth-first internal eval at 15× token cost are compatible claims.

**Diagnostic use:** when a multi-agent system fails, classify the failure into one of the three categories *before* proposing fixes. Category-1 failures are fixed in specs and roles, not prompts. Category-2 failures are fixed by sharing more/better context (full traces, not summaries) or by removing parallelism over shared state. Category-3 failures are fixed by structural verification (see `loops-and-stop-conditions.md`).

## T4.1 — The economics: multi-agent as token-spend scaling `[MEDIUM — vendor-internal]`

Anthropic internal data (treat as one vendor's order-of-magnitude heuristics, single eval, unreplicated, no published methodology):

- Agents use **~4×** the tokens of chat interactions; multi-agent systems **~15×**.
- On BrowseComp, token usage alone explained **80% of performance variance**; tokens + tool calls + model choice explained 95%.
- Explicit economic gating: "multi-agent systems require tasks where the value of the task is high enough to pay for the increased performance."

The provocative reading (Anthropic's own): multi-agent architecture is primarily a mechanism for **scaling token spend past one context window's limits** — parallel windows as a way to convert money into coverage. Known confound: Anthropic's later eval-awareness work found multi-agent BrowseComp runs had ~3.7× more leaked solutions, which inflates the tokens→performance regression.

### The equal-budget evidence `[HIGH for the core paper; CORROBORATED* for the counter-nuance]`

Verified directly against the primary source (Tran & Kiela, arXiv:2604.02460, Apr 2026): under equal thinking-token budgets, the multi-agent advantage on **text-only multi-hop reasoning disappears** — single-agent systems match or modestly outperform multi-agent ones (~0.43 vs 0.39 averaged at 5K tokens, consistent across Qwen3, DeepSeek-R1-Distill, and Gemini 2.5 families), with an information-theoretic basis in the Data Processing Inequality (routing information through more agents cannot add information). **Precision matters here: this is shrink-to-parity, not reversal** — earlier drafts of this guide said "shrinks or reverses," which overstates the result. The authors explicitly scope out tools, vision, and breadth tasks.

The counter-nuance: budget-controlled studies that match total compute across *parallel* agents (Kim et al., "Towards a Science of Scaling Agent Systems," arXiv:2512.08296 — 260 configurations, 6 benchmarks) find performance effects ranging **+80% to −70%** depending on configuration: genuine matched-compute multi-agent advantage on **decomposable, parallelizable tasks** (independent retrieval across many sources), and degradation on **depth-sequential agentic tasks** where interaction depth produces divergent world states and cascading errors. (Exact percentages sourced via secondary synthesis of the paper — verify against its tables before quoting precisely.)

**The synthesis: task shape, not architecture, is the discriminator.** Equalize budgets before believing any multi-agent win. Expect parity or a slight single-agent edge on sequential depth-reasoning; expect real gains only where subtasks genuinely parallelize and the coordination structure matches the task's natural decomposition. This refines rather than overturns the economics above: much of the *headline* multi-agent advantage is unaccounted token spend, but not all of it.

## The decision framework (P3.1) `[HIGH/MEDIUM synthesis]`

Go multi-agent when **all** hold:
1. The task decomposes into subtasks that are **breadth-first, read-dominant, and genuinely parallelizable** (research, review, audit, exploration) — not tightly coupled edits to shared state, and not sequential depth-reasoning (where equal-budget evidence shows the advantage vanishes).
2. Task value justifies ~an-order-of-magnitude token premium (the 15× heuristic).
3. Subtask outputs can be **verified or synthesized** by a single downstream context (category-3 protection).
4. Workers can be given **sufficient context** — via full traces or careful packaging — to avoid implicit-decision divergence (category-2 protection).

Otherwise: a single agent with a well-curated context, or a coded workflow. Per the simplest-viable-design doctrine, the burden of proof is always on adding agents.

## Footnote: agent-to-agent protocols (P3.6, resolved as footnote) `[CORROBORATED* — probe 2026-06-12]`

A scope probe asked whether a "gold standard" for agent-to-agent communication exists as of mid-2026. Verdict: **no — teach orchestrator-mediated patterns; treat protocols as a watch item.** What's consolidated is *governance*, not runtime mechanism: the Linux Foundation's Agentic AI Foundation now hosts MCP, Google's A2A (v1.0, Apr 2026, 150+ announced supporters), and ACP together — but production multi-agent systems overwhelmingly use **in-process, orchestrator-mediated coordination** (subagents with isolated contexts, typed handoffs, supervisor graphs, shared state). The major agent SDKs (Claude Agent SDK, OpenAI Agents SDK, LangGraph) ship no A2A support and their vendors' architecture guidance doesn't mention network protocols at all; A2A's production-deployment evidence is vendor press-release material with documented O(n²) connection scaling and no built-in orchestration primitives. Reach for A2A only when **cross-vendor/cross-organization** interop is a hard requirement, and expect immaturity.
