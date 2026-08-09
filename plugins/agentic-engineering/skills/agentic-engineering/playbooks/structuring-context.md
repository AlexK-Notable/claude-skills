# Structuring Context for Cache Economics and Attention

**Use when:** laying out an agent's context window — what sits where, what stays cacheable, what moves to files, what gets cut when it fills.

## 1. Order the layout by stability, not by topic

Sort every byte by how often it changes. Anthropic-family render order is `tools → system → messages`:

1. **Frozen preamble** — system prompt + deterministic tool list; byte-identical every request.
2. **Per-session** — project facts, retrieved-once documents, the CLAUDE.md-style preload.
3. **Per-turn** — the appended transcript.
4. **Volatiles** — timestamps, UUIDs, request IDs, counters: tail position, or deleted.

Prefer deleting to relocating — a tail volatile still costs tokens every turn. [SYNTHESIS]

Two measurements, opposite directions: stable vs perturbed prefixes gave **71.3% cost reduction and ~39% TTFT improvement** over 1,300 requests; a production system recovered hit rate **7% → 84%** purely by moving volatile working memory into the tail. `[HIGH]`

Why: → ../references/caching-and-knowledge-delivery.md T6.1

## 2. Keep the transcript append-only, then audit for silent invalidators

Append; never rewrite. Editing the system prompt mid-session, swapping the tool array, or re-sorting history pays full price on the suffix. Filter tools with an `allowed_tools`-style parameter instead.

When hit rates are mysteriously zero, walk this list first:

- [ ] `now()` timestamps in the system prompt
- [ ] random IDs or session UUIDs early in content
- [ ] non-deterministic JSON — unsorted keys, set iteration
- [ ] per-user values interpolated into a shared prompt
- [ ] conditional system sections toggling by request
- [ ] per-user or per-request tool sets

Confirm empirically: if `cache_read_input_tokens` stays zero across requests you believe prefix-identical, diff the rendered bytes. `[VENDOR-DOC + community anti-pattern reports]`

Set payoff expectations correctly. Across caching strategies the *cost* spread is small — about **2–4 percentage points**, since the system prompt is cached under all of them — while the *latency* spread is large: naive full-context caching on GPT-4o **regressed TTFT ~8.8%**, while system-prompt-only and exclude-tool-results caching **improved TTFT 28–31%**. Sell prefix discipline as responsiveness, not dollars. `[CORROBORATED*]`

Why: → ../references/caching-and-knowledge-delivery.md T6.1

## 3. Pace the loop inside the TTL and clear the prefix floor

Provider economics differ; do not universalize one vendor's model. **As of 2026-08-08** — the fastest-drifting content in this guide; re-read the pricing pages before any cost model depends on it. `[VENDOR-DOC]`

| Provider | Read | Write | TTL |
|---|---|---|---|
| Anthropic | 0.1× | 1.25× (5-min) / 2× (1-hour) | 5 min default, 1 h opt |
| OpenAI GPT-5.6+ | ~0.1× | **1.25×** | 30 min (only value) |
| OpenAI pre-5.6 | ~0.1× | none | 5–10 min idle, 1 h max |
| Google (explicit) | ~0.1–0.25× | reduced + **hourly storage fee** | 60 min |

Break-even follows: Anthropic and GPT-5.6+ are now identical (1.25× write, ~0.1× read), so one hit beats two uncached sends of the prefix. Google's storage fee needs ~3–4 hits per 60-min window — an hourly scheduled agent can lose money on it. Realized across all three on an agentic benchmark: **41–80% cost reduction, 13–31% TTFT improvement**.

- **Pace steps inside the TTL**, or accept the miss deliberately. Sleeping past TTL re-reads history at write price — a 12.5× per-token swing on Anthropic.
- **Monitor `cache_type_1h` vs `cache_type_5m` ratios** as a drift detector. An unannounced server-side TTL regression (1 h → 5 min, Mar 2026) silently raised one production user's costs **~26% that month**. TTL tier is infrastructure to observe, not assume. `[CORROBORATED*]`
- **Check the floor.** Minimum cacheable prefix is per-model — Anthropic 512 (Opus 5, Fable 5, Mythos 5) to 4,096 tokens (Opus 4.5/4.6, Haiku 4.5), OpenAI a strict 1,024 on GPT-5.6+, Gemini 2,048 on 2.5 and 4,096 on 3.x. **A prefix under the floor silently does not cache, with no error.**
- Max 4 breakpoints, each looking back ~20 content blocks — tool-heavy turns need intermediate markers. On fan-outs, send one request and await the first token before firing the rest; parallel identical requests miss.

Why: → ../references/caching-and-knowledge-delivery.md T6.1

## 4. Budget occupancy, not capacity

- **Size against effective context, not claimed.** It is task-dependent and always shorter than the spec sheet; NIAH-style window claims say little about real queries. `[HIGH, historical]`
- **Frontloading is occupancy-conditional.** Under ~50% occupancy primacy is intact and frontloading works. Past ~50%, primacy decays while recency holds, leaving the tail as the only reliably privileged position. Tested only on open-weight 8K–128K models — applying it to a 200K–1M Claude-family window is extrapolation; flag it. `[MEDIUM]`
- **Three stacked mechanisms**: lexical matching, position, and length itself. The third bounds what curation buys — holding retrieval constant, length alone still cost 13.9–85%. Curation reduces the length tax; it does not make length free. A short window is a design goal, not a fallback. `[HIGH]`
- Where you cannot shorten, have the model recite retrieved evidence before reasoning over it (up to +4%).

Why: → ../references/context-degradation.md T2.2, T2.3, T2.4

## 5. Externalize durable state into retrievable files

Write memory files for the attention mechanism that fetches them, not a human reader:

- one fact per file, summary line on top — beats sprawling documents
- identifiers repeated **verbatim**; consistent terminology over paraphrase, which actively damages retrievability
- an index file over atomic notes — progressive disclosure applied to memory

Do **not** hand-write a "check your memory directory first" trigger for the Anthropic memory tool: when the tool appears in a request's `tools`, the API adds the memory protocol to the system prompt itself. What is left for you to prompt is **scope** — bound what gets written to the topics you want persisted. Hand-roll memory over your own file tools and the trigger is yours again. `[VENDOR-DOC — as of 2026-08-08]`

Externalizing is a remedy for overflow, not an accuracy upgrade — it earns its keep on cross-session work.

Why: → ../references/caching-and-knowledge-delivery.md T6.3

## 6. Shrink in cascade order, cheapest first

1. **Mask or drop raw tool outputs.** Dominant token sink, safest to lose — agents rarely re-examine them. Observation masking alone cut cost 52% while *raising* solve rate 2.6% on SWE-bench Verified; the hybrid beat pure summarization on cost by ~11%. `[HIGH]`
2. **Slide a window** over old turns.
3. **Summarize last**, and make it query/task-aware, not generic.

Preserve verbatim: architectural decisions, unresolved bugs, exact constraints, identifiers. Discard raw and redundant tool outputs. Tune the compaction prompt for recall first, precision second `[VENDOR-DOC — one vendor's design advice]`.

**Compaction is lossy and unaudited.** Anything that must survive exactly — IDs, contracts, ratified decisions — goes to a file or a re-injected anchor, never to trust in a summary. Three failure modes: **stop-signal erasure** (summarized trajectories ran 13–15% longer), **self-conditioning** (summarizing context holding the model's own errors compounds them; not fixed by scaling, though reasoning models largely avoid it), and the **accuracy tax** (~35-point drop on LoCoMo for ~90% token reduction — the accuracy figure traces to a contested benchmark and the reduction figure is vendor-asserted `[MEDIUM]`). Verify a summary with atomic-claim faithfulness, not ROUGE overlap.

Why: → ../references/caching-and-knowledge-delivery.md T6.4

## Triage

Hit rate zero → step 2's list, then step 3's floor. Cost drift with no code change → step 3's TTL ratio. Facts missed in-window → steps 4–5. Early quitting → step 6's stop-signal erasure, before rewriting the stop condition. [SYNTHESIS]
