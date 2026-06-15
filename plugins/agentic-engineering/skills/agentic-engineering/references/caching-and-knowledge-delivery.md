# Caching, Progressive Disclosure, and Memory Surfaces

Theory pillar T6 + Practice P2. Status: **complete**. Cache + progressive-disclosure + JIT upgraded 2026-06-12 by two verification probes; memory architectures (⑧) and summarization strategy (⑦) integrated 2026-06-13 from Opus probes. Label `[CORROBORATED*]` = independently corroborated via single-verifier probe — stronger than `[VENDOR-DOC]`, below full 3-vote panel `[HIGH]`.

## Why this chapter exists

The three topics share one underlying problem: **a model's window is finite and expensive, but the knowledge an agent might need is unbounded.** Caching makes the *stable* part of context cheap to re-send; progressive disclosure loads knowledge *on demand* instead of preemptively; memory surfaces move state *out* of the window entirely and let the agent fetch it back. They are three answers to "how do I give an agent access to more than fits in its attention budget" — and they interact, because all three change what bytes appear where in the prompt, which is exactly what caching is sensitive to.

## T6.1 — Cache mechanics: the prefix-match invariant `[CORROBORATED* — cross-provider]`

**Prompt caching is a prefix match. Any byte change anywhere in the prefix invalidates everything after it.** This is not Anthropic-specific: a peer-reviewed cross-provider audit (arXiv:2502.07776, Feb 2025) confirmed exact-prefix matching for Anthropic, OpenAI, and DeepSeek, and OpenAI's own docs require an "exact, repeated prefix match." The one architectural outlier is **Google Gemini**, whose reliable path is a *reference-object* model (pre-create a cache object, reference by ID) rather than in-band prefix marking; Gemini's implicit prefix caching had a documented reliability defect as of Dec 2025 (~42% hit rates on shared prefixes — googleapis/python-genai#1880).

For Anthropic-family APIs, render order is `tools → system → messages`; the cache key is the exact bytes up to each breakpoint.

### Design consequences (independently corroborated, with measurements)

- **Stability ordering.** Content must be physically ordered by how often it changes: frozen system prompt and deterministic tool list first; per-session content next; per-turn content last; per-request volatiles (timestamps, UUIDs) at the very end or eliminated. Best independent quantification: a 1,300-request controlled experiment on Azure OpenAI (ankitbko.github.io, Aug 2025) measured **71.3% per-request cost reduction and ~39% TTFT improvement** for stable vs perturbed prefixes. `[CORROBORATED*]`
- **Append, don't edit.** Multi-turn agent loops cache well because they only append. Anything that *rewrites* earlier context — editing the system prompt mid-session, swapping tool sets, re-sorting history — pays full price for the whole suffix. Independent support: OpenAI's Cookbook documents its Codex agent as deliberately append-only and recommends `allowed_tools` over mutating the tool array precisely to avoid invalidation; "Don't Break the Cache" (arXiv:2601.06007, Jan 2026) measured **5–15% savings without append-only discipline vs ~40% with it**; a production case study (ProjectDiscovery) recovered cache hit rates **from 7% to 84%** by relocating volatile working memory from the prefix to the tail. This is the deep tension with naive "curate your context freely" advice: curation that mutates the prefix has a real, measured price — which is why platform mechanisms (tool search *appends* discovered schemas; mid-conversation system messages *append* after history) are all shaped as appends. `[CORROBORATED*]`
- **Economics differ by provider — don't universalize Anthropic's model.** `[CORROBORATED*]`

  | Provider | Cache read | Cache write | TTL |
  |---|---|---|---|
  | Anthropic | ~0.1× input price | 1.25× (5-min) / 2× (1-hour) premium | 5 min default, 1 h option |
  | OpenAI | ~0.5× | **no premium** (standard input price) | 5–10 min; 24 h extended on newer models |
  | Google (explicit) | ~0.1–0.25× | reduced write + **hourly storage fee** | 60 min default |

  Break-even consequences: Anthropic/OpenAI prefix caching pays for itself in 1–2 reads; Google's storage-fee model needs ~3–4 hits per 60-min window — low-frequency loops (e.g. an hourly scheduled agent) may lose money on it. Community-measured realized savings in agentic workloads: **45–80% cost reduction, 13–31% TTFT improvement** (arXiv:2601.06007).
- **TTL couples to loop pacing.** An agent that sleeps past the TTL between steps re-reads its whole history cold (write-premium price instead of read price — a 12.5× per-token swing on Anthropic). Pace within the TTL or consciously accept the miss; don't linger just past it. **Live ops risk:** a documented, unannounced server-side TTL regression (1 h → 5 min, Mar 2026, claude-code#46829) silently raised one production user's costs 17% for a month. Monitor `cache_type_1h` vs `cache_type_5m` ratios in usage data as a drift detector — TTL tier is infrastructure you should observe, not assume. `[CORROBORATED*]`
- **Silent invalidators** (the audit list when hit rates are mysteriously zero): `now()`-style timestamps in the system prompt, random IDs early in content, non-deterministic JSON serialization (unsorted keys, set iteration), per-user interpolation into shared prompts, conditional system sections, per-user tool sets. Verify with usage fields: if `cache_read_input_tokens` stays zero across identical-prefix requests, diff the rendered bytes. `[VENDOR-DOC + community anti-pattern reports]`
- **Known subtleties** `[VENDOR-DOC]`: max 4 breakpoints per request; minimum cacheable prefix is model-dependent (≈1–4K tokens — shorter prefixes silently don't cache; OpenAI's floor is 1,024 tokens, Gemini's 2,048+); breakpoints look back at most ~20 content blocks (tool-call-heavy turns need intermediate markers); parallel identical requests all miss until the first response begins streaming (fan-outs: send one, await first token, then fire the rest); caches are model-scoped (switching models mid-session is a full miss — one more reason to run cheap sub-tasks in *subagents on the cheap model* rather than swapping the main loop's model).

**Theory takeaway:** caching is a *physical constraint that shapes architecture*. The cheapest context is the context you never change — so agent designs converge on an append-only transcript with stable preamble, and every context-management mechanism gets evaluated partly by whether it preserves the prefix. The convergence is now cross-provider: OpenAI's flagship agent harness independently arrived at the same append-only shape.

## T6.2 / P2 — Progressive disclosure: knowledge on demand `[CORROBORATED* — cross-ecosystem]`

The pattern: keep a small, always-loaded *index* in context, and load full content only when the task calls for it.

- **Skills are the canonical implementation** — a folder with a `SKILL.md`; only the short description sits in context by default; the model reads the full file (and deeper references) when relevant. This document is itself the pattern. No longer vendor-only: the Agent Skills standard (open-sourced Dec 2025) was adopted within days by OpenAI (Codex/ChatGPT), Google (Gemini CLI), GitHub Copilot, Cursor, and VS Code; third-party marketplaces indexed 400K+ skills within three months; and the parallel `llms.txt` pattern (Jeremy Howard, independently adopted by docs tooling) implements the same two-tier index-then-body shape for documentation.
- **It measurably works.** SkillFlow (UC Davis, arXiv:2504.06188): selective loading from a 36K-skill corpus raised Pass@1 **from 9.2% to 16.4% (+78% relative) versus loading everything** — preloading the full corpus actively hurt. SkillReducer (arXiv:2603.29919, 55K skills analyzed) names the mechanism "attention dilution" and found **60%+ of skill body content is non-actionable** — waste that progressive disclosure keeps out of the window. For tools specifically: on-demand retrieval beat static loading by **23–104% success-rate improvement** (DTDR, arXiv:2512.17052); see `tool-design.md` for the tool-catalog degradation numbers.
- **Why it works** (theory, connecting to `context-degradation.md`): preloaded-but-unused knowledge occupies window, raises occupancy (weakening primacy attention, T2.3), and adds distractor surface (T2.5). Progressive disclosure converts a standing context tax into a per-use cost.
- **The index layer is a gate; the body is the signal.** `[CORROBORATED*]` Important nuance from SkillRouter (arXiv:2603.22455): description quality gates whether a skill *enters the candidate set* (26.4% of community skills lack routing descriptions entirely and are effectively invisible — SkillReducer), but **body content dominates final selection** — removing bodies costs 31–44pp accuracy, far more than removing descriptions. Description-rewriting studies show +11pp multi-step success and ~29% less degradation at 150+ tools from better descriptions (arXiv:2602.20426). Practical rule: write descriptions with the trigger vocabulary the querying agent will actually use (lexical matching again — T2.2), *and* invest in body quality; a perfect index over mediocre bodies caps out fast.
- **The trade-off — the knowledge-action gap.** `[CORROBORATED*]` A two-hop fetch the model must *choose* to make can be silently skipped, and this is now empirically documented beyond our local observations: agents demonstrably fail to act on knowledge they possess about what to consult (arXiv:2508.13465, tested across Claude/GPT/Llama/DeepSeek — the "knowledge-action gap"); context-pressured agents stop after partial retrieval without fetching the remainder (LOCA-bench, arXiv:2602.07962); practitioner reports name corner-cutting near window limits explicitly. No published skip-*rate* yet. Mitigation: make on-demand loads structurally automatic (harness/hook-injected) where they're load-bearing, and loud when skipped.

## P2.1 — Just-in-time retrieval vs preloading `[MEDIUM/CORROBORATED* — probe 2026-06-12]`

(Deliberately modest section — the evidence is directional, not airtight, and our one prior candidate claim was killed in adversarial verification for misattributing a model detail.)

When an agent has tools to fetch information (file reads, grep, queries, search), **prefer lightweight references + on-demand fetching over preloading everything potentially relevant — as a default, not a law.** What the evidence actually supports:

- **Focused beats bloated** `[MEDIUM]`: across 18 models on LongMemEval, focused ~300-token prompts substantially outperform full ~113K-token prompts (Chroma, 2025; single-vendor but replicable). Claude-family models showed the largest focused-vs-full gap, driven by over-abstention under ambiguity. Caveat: this tests the *endpoint* (curated context wins), not the *mechanism* of how you arrive at it.
- **Tool-based fetching matches retrieval-preloading quality** `[CORROBORATED*]`: agentic keyword search reached >90% of vector-RAG performance with no vector store on general QA (Amazon Science, AAAI 2026); code-agent practitioners independently report embeddings "weren't the bottleneck" for code tasks — Claude Code dropped its early RAG implementation for agentic search (`[ATTRIBUTION]`, no published numbers; a vector-DB vendor dissents on token cost, so the latency/token trade is contested).
- **The vendor position is honest about its own evidence** `[VENDOR-DOC]`: Anthropic's just-in-time guidance (Sep 2025) is explicitly *unbenchmarked design advice*, flags that runtime exploration is slower than precomputed retrieval, and recommends **hybrids** — preload stable, reliably-needed context (the CLAUDE.md pattern); fetch dynamic content on demand.

What remains genuinely unknown: no neutral study isolates JIT fetching vs preloading with the final context held constant. Safe operating rule: **for agents with good search/read tools over dynamic content, just-in-time fetching is a reasonable default and rarely costs accuracy; preload only stable high-value context; go hybrid when latency matters or content is static.**

## T6.3 / P2 — Memory surfaces: state outside the window `[VENDOR-DOC + Opus probe 2026-06-13]`

Current vendor-supported lifecycle for long-running agents — three mechanisms with distinct scopes:

| Mechanism | Scope | What happens |
|---|---|---|
| **Context editing** | within session | Stale tool results / old thinking *pruned* (removed, not summarized); keeps transcript lean |
| **Compaction** | within session, near the limit | Earlier context *summarized* server-side into a compaction block carried forward |
| **Memory (files)** | across sessions | Agent reads/writes a persistent directory; survives restarts |

Design notes:

- **Memory is write-back, not write-once.** The useful patterns: scratchpads/notes maintained *while working* (externalizing intermediate state so the window holds only the active slice), and durable lesson/preference files consulted at session start. Vendor guidance for recent frontier models: file-based memory measurably helps long-horizon work *but models under-reach for it by default* — prompt the trigger ("check your memory file before tasks longer than a few turns; write new findings as you go"). Note this is the knowledge-action gap again, on the write path.
- **Retrievability rules apply to memory files** (T2.2): one fact per file with a summary line on top beats sprawling documents; verbatim IDs and consistent terminology beat elegant paraphrase; an index file pointing at atomic notes is progressive disclosure applied to memory.
- **Compaction is lossy and unaudited.** Anything that must survive verbatim (IDs, contracts, key decisions) belongs in a file or a re-injected anchor, not in trust that summarization preserves it.
- **Don't put secrets in memory or messages** — they persist in histories and summaries.

### Memory architecture: pick by history length, not by fashion `[HIGH/MEDIUM — Opus probe 2026-06-13]`

The decisive variable is whether the relevant history fits the context window:

- **If it fits the window, long-context beats an external memory layer on accuracy.** On LoCoMo, a GPT-5-mini long-context baseline beat the Mem0 memory pipeline by ~35 points (arXiv:2603.04814); memory's advantage at this scale is **cost, not accuracy** — it pays off past roughly 10 turns at 100K-token contexts (MEDIUM, single-source). LoCoMo (~20K tokens) is too short to even prove memory is necessary — the "Context Saturation Gap" (arXiv:2602.19320). `[HIGH for the accuracy gap; contested benchmark]`
- **When history genuinely exceeds the window, memory wins decisively.** On LongMemEval-M (>1M tokens) HINDSIGHT reached 83.6% with a 20B model vs a 39.0% full-context baseline (+44.6pp), gains concentrated in multi-session and temporal reasoning (arXiv:2512.12818) `[HIGH but vendor-affiliated]`. So external memory is a remedy for *overflow*, not a general accuracy upgrade — which refines the write-back guidance above: it earns its keep on long-horizon/cross-session work, not on tasks that fit the window.
- **Graph-structured memory does not measurably beat well-managed flat or hierarchical notes for recall.** In a 10-method benchmark a hierarchical tree beat the graph variant; the authors conclude *management strategy and information completeness matter more than representation type* (arXiv:2604.01707) `[HIGH]`. Graph extraction can lose information, and structured memory corrupts under weak models (~30% format errors on a 3B model). Reserve graphs for genuine multi-hop traversal needs.
- **The episodic/semantic/procedural split is the dominant vocabulary but contested as an engineering decomposition** — the strongest empirical taxonomy paper rejects it for four structural types (arXiv:2602.19320). The episodic→semantic *consolidation* pathway ("user corrected the date 3× → store the preference") is the agreed frontier and least-implemented piece `[MEDIUM/aspirational]`.
- **The MemGPT/Letta lineage** (OS-style paged, self-editing memory blocks) is active: 2025 added "sleep-time compute" (a second agent consolidates memory between turns) and git-backed MemFS. But Mem0 (drop-in layer) has wider adoption than Letta (full runtime) precisely because it doesn't require rewriting the agent stack `[CORROBORATED* / vendor-only on specific numbers]`.
- **Budget for the dominant failure class: pollution → drift → conflict, a compounding loop** (SSGM, arXiv:2603.11768). Unconstrained semantic drift grows ~O(T) with interaction length; periodic reconciliation bounds it to ~O(N). Mitigate with TTL/freshness decay, contradiction-checking at write time, and access-scoped retrieval; retrieval-stage tuning reportedly beats ingestion-stage tuning `[MEDIUM — theoretical bounds]`.

Benchmark caveat for all of the above: **LoCoMo scores are contested** (a Zep/Mem0 scoring dispute swung one claim from 84% to 58%) and the benchmark is short enough to under-test memory — prefer LongMemEval-M/V2 and always report cost alongside accuracy.

## T6.4 / P2.2 — Summarization strategy and its failure modes `[HIGH/CORROBORATED* — Opus probe 2026-06-13]`

When context must shrink, *how* you compress matters as much as whether you do. The evidence converges on a cascade and a set of guardrails.

**The cascade (cheapest-first):** mask or drop raw tool outputs → slide a window over old turns → invoke LLM summarization only as a last resort. On SWE-bench Verified, observation-masking *alone* cut cost 52% while raising solve rate 2.6%; the hybrid beat pure summarization on cost by ~11% (JetBrains, Dec 2025) `[HIGH — single vendor benchmark]`. Tool outputs are the dominant token sink and the safest thing to drop — agents rarely re-examine raw outputs.

**When you do summarize, make it query/task-aware, not generic.** Anticipating the downstream questions (Chain of Summaries) beat generic summaries by 9.6% F1 and even beat the *source document* (0.80 vs 0.76), at ~98% per-query token reduction (arXiv:2511.15719) `[HIGH]`. Recursive running-summaries (ReSum) add ~4.5% over append-everything ReAct, ~8.2% with a tuned summarizer (arXiv:2509.13313) `[HIGH]`. Agent-controlled curation beats fixed heuristics — a 14B learned curator beat a summarization baseline by ~9pp and outperformed a full-context 235B model at half the context (MemAct, arXiv:2510.12635) `[HIGH]`.

**Preserve verbatim** (two vendors independently agree): architectural decisions, unresolved bugs, exact constraints, and identifiers. **Discard:** redundant/raw tool outputs. Tune the compaction prompt for **recall first, precision second** (Anthropic + JetBrains) `[CORROBORATED*]`. Offload durable facts to external notes you can re-inject rather than paraphrasing them across rounds.

**Failure modes to guard against:**
- **Stop-signal erasure** — summaries smooth over the subtle cues that tell an agent to stop, so summarized trajectories ran 13–15% *longer* (JetBrains) `[HIGH]`.
- **Self-conditioning** — summarizing a context that contains the model's own earlier errors compounds them; this is additive to long-context decay and **not fixed by scaling model size**, but reasoning/thinking models largely avoid it (arXiv:2509.09677) `[HIGH]`. This is the mechanism behind "summary-of-a-summary" drift.
- **The accuracy tax** — condensation costs accuracy (full-context beat condensed memory by ~35 points on LoCoMo) in exchange for ~90% token/latency reduction. Budget the trade deliberately `[HIGH accuracy gap / vendor cost claim]`.

To check a summary kept the load-bearing content, use **atomic-claim faithfulness (FactScore-style)**, not ROUGE overlap `[HIGH metric / MEDIUM as proxy]`. Two honest gaps: no published per-round degradation *curve* for recursive summarization exists as of mid-2026 (mechanism attested, magnitude unquantified), and summarization hallucination rates are contested (0.7–1.5% grounded vs ~60% in one 2026 study) — don't cite a single rate.

## The composite picture

A well-engineered agent context, mid-2026: a frozen, cached preamble (system + tools); an append-only working transcript, pruned/compacted as it grows; knowledge held as a thin always-loaded index over on-demand bodies; durable state externalized to files engineered for lexical retrieval. Each piece exists because of a constraint documented elsewhere in this guide — prefix economics (here), attention mechanics (`context-degradation.md`), the finite-window thesis (`foundations.md`) — and the shape is now corroborated across providers and ecosystems, not just one vendor's docs.
