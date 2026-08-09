# Multi-Agent Systems: Economics, Failure Modes, and the Central Dialectic

Theory pillars T4 + T5. Status: **complete**. Core claims adversarially verified 2026-06-12 (equal-budget evidence and protocol-landscape sections via same-day Opus probes; `[CORROBORATED*]` = single-verifier probe); corrections and re-audit applied 2026-08-08.

## T5.2 — The Anthropic–Cognition dialectic (read this first) `[MEDIUM]`

The defining 2025–26 debate, thesis → antithesis → synthesis:

**Thesis — Anthropic (Jun 2025):** orchestrator-workers is the canonical multi-agent architecture — a lead model decomposes a task across 3–5 parallel worker LLMs, each in an *isolated* context window. Their production research system (Opus 4 lead + Sonnet 4 workers) outperformed single-agent Opus 4 by **90.2%** on an internal breadth-first research eval. Caveats: internal vendor eval, undisclosed metric, ~15× chat-level tokens (the writeup credits much of the gain to that spend), and a limit — high-dependency, shared-context domains "are not a good fit for multi-agent systems today." Cite only for breadth-first, parallelizable tasks where extra token spend is acceptable — never as general superiority.

**Antithesis — Cognition, "Don't Build Multi-Agents" (Jun 2025) `[ATTRIBUTION]`:** multi-agent collaboration (as of mid-2025) produces fragile systems: decision-making disperses, context can't be shared thoroughly enough. Two design principles follow: (1) "Share context, and share full agent traces, not just individual messages" — contrasting with individual messages, not summarization per se; (2) "Actions carry implicit decisions, and conflicting decisions carry bad results". An influential position statement by one co-founder, time-bounded to 2025 — not an empirical finding. But its mechanism gets independent empirical support: MAST attributes 32.3% of multi-agent failures to inter-agent misalignment.

**Synthesis — 2026:** Cognition's own follow-up ("Multi-Agents: What's Actually Working") concedes multi-agent works **when writes stay single-threaded and the extra agents contribute intelligence rather than actions**. Its pattern: a manager-Devin scopes work, spawns child-Devins on clean contexts, monitors, resolves conflicts, and compiles results — the post's term is *map-reduce-and-manage*, not "Managed Devins." Combined with Anthropic's breadth-first framing, the consensus:

> **Parallelize reads, single-thread writes.** Fan out for gathering, exploring, reviewing, verifying — work where workers' outputs are *inputs to a synthesis* rather than mutations of shared state. Keep one context responsible for decisions and mutations. The failure zone is parallel workers making implicit, conflicting decisions about shared artifacts.

One point is undisputed across both camps: context engineering is the #1 job (see `foundations.md` T1.2). Don't let that agreement smuggle in either side's contested claims.

## T5.1 — MAST: the empirical failure taxonomy `[HIGH — peer-reviewed]`

MAST (UC Berkeley, NeurIPS 2025 Datasets & Benchmarks; 150 expert-annotated traces, κ=0.88, later expanded to 1,600+ traces across 7 frameworks) observes that multi-agent systems' **gains on popular benchmarks are often minimal**, taxonomizing **14 failure modes in 3 categories**:

1. **System design issues** — flawed specifications, role/responsibility confusion, broken termination logic, baked in before any message is exchanged.
2. **Inter-agent misalignment** — agents diverging on task understanding, withholding or distorting context, conflicting implicit decisions (32.3% of failures; the empirical backbone of Cognition's position).
3. **Task verification** — accepting unverified work, premature success declarations, weak or absent checking.

Notes: "telephone game" is this guide's informal label, not MAST terminology — it maps onto inter-agent misalignment + task-verification modes. The taxonomy is non-exhaustive. MAST doesn't contradict Anthropic's 90.2% result: minimal *average* gains and one breadth-first win at 15× cost are compatible claims.

**Diagnostic use:** classify a failing system into one of the three categories *before* proposing fixes — category 1 in specs and roles, not prompts; category 2 via more/better context (full traces, not lone messages) or removing parallelism over shared state; category 3 via structural verification (see `loops-and-stop-conditions.md`).

## T4.1 — The economics: multi-agent as token-spend scaling `[MEDIUM — vendor-internal]`

Anthropic internal data (single, unreplicated eval — no published methodology):

- Agents use **~4×** the tokens of chat interactions; multi-agent systems **~15×**.
- On BrowseComp, token usage alone explained **80% of performance variance**; tokens + tool calls + model choice explained 95%.
- Economic gating: "multi-agent systems require tasks where the value of the task is high enough to pay for the increased performance."

The provocative reading (Anthropic's own): multi-agent architecture is primarily a mechanism for **scaling token spend past one context window's limits**. Directional footnote, not a correction: Anthropic's later eval-awareness work found multi-agent BrowseComp runs surfaced ~3.7× more leaked solutions, but scrubbing them moved the score just 86.81→86.57 (0.24pp) on a different model, a year later — hinting the tokens→performance regression is somewhat inflated, though too small to establish by how much.

### The equal-budget evidence `[HIGH]`

Verified directly against the primary source (Tran & Kiela, arXiv:2604.02460, Apr 2026): under equal thinking-token budgets, the multi-agent advantage on **text-only multi-hop reasoning does not merely vanish — it tips the other way**. Single-agent systems are the best performer, or statistically indistinguishable from the best, at every budget the paper tests but one (0.427 vs 0.386 averaged at 5K tokens, consistent across Qwen3, DeepSeek-R1-Distill, and Gemini 2.5 families), with an information-theoretic basis in the Data Processing Inequality (routing information through more agents cannot add information). The single exception is the 100-token budget, where the model emits no useful reasoning trace at all — a degenerate case, not a multi-agent regime. The paper names the conditions under which multi-agent becomes competitive again: that lowest budget, deliberate degradation of the single agent's effective context utilization, and simply spending more compute — which is the unequal-budget case the rest of this section is about. Scope-out is explicit: tools, vision, and safety constraints.

Two independent replications land on the same side and sharpen it:

- **arXiv:2601.12307** (Jan 2026), "Rethinking the Value of Multi-Agent Workflow: A Strong Single Agent Baseline" `[CORROBORATED*]` — across seven benchmarks spanning coding, mathematics, QA, domain reasoning, and real-world planning and tool use, a single agent in multi-turn conversation reaches the performance of *homogeneous* workflows, and even matches an automatically optimized heterogeneous one, with an efficiency advantage from KV-cache reuse. Homogeneity is the operative condition: same base LLM, differing only in prompt, tools, and position in the graph. If that describes your system, you are paying coordination overhead to simulate a conversation.
- **arXiv:2606.13003** (Jun 2026), "The Illusion of Multi-Agent Advantage" `[CORROBORATED*]` — *automatically generated* multi-agent systems consistently underperform chain-of-thought with self-consistency at up to 10× the cost, including on interactive multi-step workflows. But *expert-architected* systems beat the auto-generated ones on both raw performance and cost-efficiency, even on a synthetic dataset built to favor decomposition. Architecture quality is a second discriminator alongside task shape: the paper attributes the auto-generated failures to architectural bloat — superficial complexity that never converts to functional utility.

The counter-nuance `[MEDIUM]`: budget-controlled studies that match total compute across *parallel* agents (Kim et al., "Towards a Science of Scaling Agent Systems," arXiv:2512.08296 — 260 configurations, 6 benchmarks, 5 architectures, 3 model families) find performance effects relative to a single-agent baseline ranging **+80.8% to −70.0%** depending on configuration. Both endpoints are in the paper's own abstract, and both are as much about topology as about task: +80.8% is decomposable financial reasoning (Finance Agent) under **centralized** coordination; −70.0% is sequential planning (PlanCraft) under **independent** coordination, where nothing reconciles divergent world states and errors cascade. The paper's generalizations follow the same line — architectures without centralized verification propagate errors more than those with it, tool-heavy tasks incur multi-agent overhead, and coordination yields diminishing returns once the single-agent baseline is already strong.

And a genuine sign flip in the other direction `[CORROBORATED*]`: Wunderlich et al. (arXiv:2605.01566, May 2026) hold the compute budget equal on MMLU-Pro and BBH and find multi-agent debate and mixture-of-agents *beat* self-consistency by 1.3 and 2.7 percentage points respectively, with multi-agent gains persisting after self-consistency saturates, particularly on harder items. Different task family, opposite sign — which is the point.

**The synthesis: task shape and architecture quality, not agent count, are the discriminators.** Equalize budgets before believing any multi-agent win. Expect a slight single-agent edge on sequential depth-reasoning, and expect real gains only where subtasks genuinely parallelize, the coordination structure matches the task's natural decomposition, and something centralized verifies the pieces. The sign disagreement across task families (multi-hop reasoning vs aggregation-style reasoning vs decomposable retrieval) is not noise to be averaged away — it is the finding. This refines rather than overturns the economics above: much of the *headline* multi-agent advantage is unaccounted token spend, but not all of it.

## The decision framework (P3.1) `[SYNTHESIS]`

Synthesizes HIGH-grade evidence (MAST, the equal-budget studies) with MEDIUM-grade evidence (token-spend economics, the Anthropic–Cognition dialectic). Go multi-agent when **all** hold:
1. The task decomposes into subtasks that are **breadth-first, read-dominant, and genuinely parallelizable** (research, review, audit, exploration) — not tightly coupled edits to shared state, and not sequential depth-reasoning (where equal-budget evidence shows a slight single-agent edge).
2. Task value justifies ~an-order-of-magnitude token premium (the 15× heuristic).
3. Subtask outputs can be **verified or synthesized** by a single downstream context (category-3 protection).
4. Workers can be given **sufficient context** — via full traces or careful packaging — to avoid implicit-decision divergence (category-2 protection).

Otherwise: a single agent with a well-curated context, or a coded workflow. Per the simplest-viable-design doctrine, the burden of proof is on adding agents.

## Footnote: agent-to-agent protocols (P3.6, resolved as footnote) `[CORROBORATED* — probe 2026-06-12]`

Does a "gold standard" for agent-to-agent communication exist as of mid-2026? **No — teach orchestrator-mediated patterns; treat protocols as a watch item.** What's consolidated is *governance*, not runtime mechanism — split into two houses, not one. The Linux Foundation's Agentic AI Foundation (formed Dec 9, 2025) hosts **MCP, goose, AGENTS.md, and agentgateway** (the last added Jun 2026). Google's A2A is a **separate** Linux Foundation project, donated in Jun 2025, never folded into AAIF — an open proposal, not settled. ACP is no longer a distinct protocol: IBM's implementation merged into A2A in Aug 2025. A2A is real and shipping (v1.0; 150+ organizations by Apr 2026), but production systems overwhelmingly use **in-process, orchestrator-mediated coordination** (subagents with isolated contexts, typed handoffs, supervisor graphs, shared state). Anthropic's "A harness for every task" (claude.com/blog, Jun 2, 2026) shows this: its orchestration primitive is a JavaScript workflow file spawning subagents, each with its own context, model, and worktree — no network protocol involved.

LangGraph ships a **first-party A2A server endpoint** (`/a2a/{assistant_id}` on its Agent Server, mapping A2A's `contextId` onto its own `thread_id`), so a LangGraph agent can be *reached* over A2A. The Claude Agent SDK and OpenAI Agents SDK ship none, and none of the three vendors' architecture guidance runs on network protocols. A2A's production-deployment evidence remains largely vendor press-release material, with documented O(n²) connection scaling and no built-in orchestration primitives. Reach for A2A only when **cross-vendor/cross-organization** interop is a hard requirement, and expect immaturity.
