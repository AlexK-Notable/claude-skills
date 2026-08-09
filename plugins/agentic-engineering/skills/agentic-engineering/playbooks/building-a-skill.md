# Building a Skill

**Use when:** authoring a skill, an `llms.txt`, a memory index, or any knowledge package where a short always-loaded blurb decides whether a larger body ever gets read.

## 1. Split the package into a gate and a body — and know which does which job

Write two artifacts with different jobs, not one document cut in half:

- **Gate** (the always-loaded description): its only job is to get the package into the candidate set for a given query.
- **Body** (`SKILL.md` and anything below it): its job is to be *selected* and then *acted on*.

Do not trade body quality for description polish. Description quality gates candidacy — 26.4% of community skills lack routing descriptions entirely and are effectively invisible (SkillReducer) — but **body content dominates final selection: hiding the body costs 37–44pp routing accuracy across dense and reranking baselines** (SkillRouter, arXiv:2603.22455; figure as of 2026-08-08, it has moved between revisions), far more than thinning descriptions costs. Better descriptions are worth real points (+11pp multi-step success, ~29% less degradation at 150+ tools, arXiv:2602.20426) — but a perfect index over mediocre bodies caps out fast. `[CORROBORATED*]`

Why: → ../references/caching-and-knowledge-delivery.md T6.2

## 2. Write the description in the querying agent's trigger vocabulary

The retrieval mechanism is lexical collision, not comprehension. Retrieval succeeds when the query's surface forms collide with the target's, and degrades as competing near-matches accumulate (NoLiMa; `[HIGH]` for the measurements, `[MEDIUM]` for the mechanism attribution). So when you control both the stored content and can anticipate the query — which is exactly the skill-authoring situation — **engineer the overlap deliberately**:

- Use consistent terminology; do not vary wording for style. Paraphrase-heavy text actively damages retrievability.
- Repeat identifiers verbatim (flag names, error strings, tool names, file names, product names).
- Write headers that echo the questions agents will actually ask, not the topics you organized by.

Concretely: enumerate the symptoms, error messages, and tool names a caller will have in context *before* they know your skill exists, and put those tokens in the description.

Why: → ../references/context-degradation.md T2.2

## 3. Make every body section change what the reader does next

**60%+ of skill body content measures as non-actionable** across a 55K-skill analysis, and the named mechanism is attention dilution (SkillReducer, arXiv:2603.29919) `[CORROBORATED*]`. Filler is not free: preloaded-but-unused text occupies window, raises occupancy (weakening primacy attention, T2.3 `[MEDIUM]` — whose ~50%-occupancy threshold was measured on open-weight models only, so transfer to 200K–1M windows is an untested extrapolation), and adds distractor surface (T2.5). Length alone also costs accuracy with retrieval held constant (13.9–85% degradation, arXiv:2510.05381) — so a perfectly curated long body still underperforms a short one `[HIGH]`.

Test each section against: *if the reader skipped this, what would they do differently?* No answer means cut it or demote it.

Why: → ../references/caching-and-knowledge-delivery.md T6.2

## 4. Push provenance, caveats, and evidence down a layer

Rationale, source lists, benchmark caveats, and confidence labels are real content — they just aren't what the reader needs *in the window while acting*. Move them into reference files the body points at, and structure those files for retrieval the same way memory files are structured: one fact per file with a summary line on top, verbatim IDs and consistent terminology over elegant paraphrase, an index file pointing at atomic notes.

Keep inline only the labels attached to load-bearing claims, so a reader can tell a measured figure from an inference without leaving the body.

Why: → ../references/caching-and-knowledge-delivery.md T6.3

## 5. Make load-bearing loads structural, not optional

A two-hop fetch the model must *choose* to make can be silently skipped. Read the evidence precisely, because this is where the corpus was corrected: the direct evidence is LOCA-bench-style insufficient exploration — context-pressured agents stop after partial retrieval without fetching the remainder (arXiv:2602.07962). The frequently-cited "knowledge-action gap" paper (arXiv:2508.13465) is an **adjacent-domain analogue**, measuring safety knowledge (>98% correct answers) against safe execution (<26%); it is suggestive of "knows the rule, doesn't apply it under pressure," not a measurement of skipped documentation fetches. **No published skip-rate for progressive disclosure exists.** `[MEDIUM]`

The design rule survives the weaker evidence, because it is the same rule structural verification runs on: anything that depends on the agent *choosing* to act inherits the gap; structural gates don't. So:

- If a load is load-bearing, make it **automatic** — harness or hook injection, not an instruction to go read something.
- Make it **loud when skipped** — fail or log visibly rather than degrading silently.
- Reserve model-initiated fetches for content that is genuinely optional.

Why: → ../references/loops-and-stop-conditions.md P4.7

## 6. Date every live fact at the point of use

Pricing, TTLs, repo counts, version numbers, and preprint figures that move between revisions carry an `as of YYYY-MM-DD` stamp *where they are used*, not in a header. An undated live-source figure is treated as expired. This is the corpus's own convention, and it is what lets a stale skill fail loudly instead of quietly.

Why: → ../SKILL.md "As-of convention"; ../references/caching-and-knowledge-delivery.md preamble

## 7. Worked example: the same skill, described twice `[SYNTHESIS]`

**Capability blurb (does not route):**

```yaml
description: A comprehensive guide to PostgreSQL performance optimization, covering
  best practices for indexing, query planning, and configuration tuning.
```

**Trigger vocabulary (routes):**

```yaml
description: Diagnose and fix slow PostgreSQL queries — reading EXPLAIN ANALYZE output,
  seq scan where an index scan was expected, table bloat, autovacuum falling behind,
  connection exhaustion (PgBouncer, "too many clients already"), work_mem and
  shared_buffers sizing. Use when a query got slow, a plan looks wrong, pg_stat_statements
  shows a regression, or after a deploy made "the database slow."
```

The caller's context says *"this query went from 40ms to 9s after Tuesday's deploy"* and carries tokens like `slow`, `query`, `EXPLAIN`, `deploy`, maybe `pg_stat_statements`. The second description collides with several of them; the first shares almost none — its distinctive words are `comprehensive`, `best practices`, `optimization`, which appear in the caller's context only if someone already typed them. Same skill, same body, different candidacy.

Why: → ../references/context-degradation.md T2.2

## Pre-ship checklist

1. Description contains the caller's symptom words, error strings, and tool names — verbatim.
2. Body has no section that fails "what would the reader do differently?"
3. Provenance and caveats live one layer down; only labels on load-bearing claims stay inline.
4. Every load the skill *depends on* is harness-enforced; every optional one is marked optional.
5. Every live figure carries an as-of date.
6. Terminology is consistent end to end — no synonyms introduced for variety.
