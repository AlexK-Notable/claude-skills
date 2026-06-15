# Context Degradation: Why Long Contexts Fail

Theory pillar T2. Status: **complete**. All claims adversarially verified 2026-06-12. **Global caveat:** empirical magnitudes below come from 2023–mid-2025 model generations; no study yet measures mid-2026 frontier models on 200K–1M windows. The *mechanisms* are the durable content.

## T2.1 — Context rot: degradation is real on frontier models, and non-uniform `[HIGH]`

Across 18 frontier and open-weight models (Claude Opus 4/Sonnet 4, GPT-4.1, o3, Gemini 2.5 Pro, Qwen3, ...), retrieval performance **degrades non-uniformly as input length grows, even on tasks the same models solve reliably at short lengths** (Chroma technical report, Jul 2025; replication code public).

Key properties of the degradation:

- It is not a cliff at the context limit — it accumulates well inside nominal capacity.
- It is task-difficulty-dependent: simple lexical-match retrieval survives long contexts far better than ambiguous or inference-requiring retrieval. This is why **vanilla needle-in-a-haystack scores systematically overstate robustness** for realistic queries.
- Source caveat: Chroma is a retrieval vendor with a commercial stake in the "context engineering > big windows" narrative; the report is not peer-reviewed and uses mostly synthetic tasks. Its similarity-dependence finding, however, is independently corroborated by peer-reviewed work (NoLiMa, below).

**Design consequence:** budget context as a depreciating asset. Tokens late in a large window buy less reliable attention than the same tokens in a small window. "It fits in context" is not the bar; "it will be *found* in context" is.

## T2.2 — The mechanism: lexical matching, not position `[HIGH — peer-reviewed]`

NoLiMa (Adobe Research, ICML 2025) isolates *why* long-context retrieval fails: **attention relies on surface-level literal matching. When lexical cues are absent — when the question and the stored fact share no overlapping wording — models fail to locate facts regardless of their position.**

Measured on 2024-generation models at only 32K tokens (far inside claimed 128K limits): GPT-4o drops 99.3% → 69.7% accuracy on non-literal-match retrieval; Llama 3.3 70B drops 97.3% → 42.7%. Ten of twelve tested models fell below 50% of their own short-context baselines (GPT-4o and Gemini 1.5 Pro were the two that stayed above). Effective context lengths implied: ~8K for GPT-4o, ~2K for Llama 3.3 70B — versus 128K claimed. The maintained repo has since added GPT-4.1, Gemini 2.5, Llama 4, and o3/o4-mini results showing the degradation pattern persists on newer models, with improved but not eliminated magnitudes.

**This finding restructures the folk model.** The popular story is positional ("things in the middle get lost"). The verified mechanism is associative: retrieval succeeds when the query's surface forms collide with the target's surface forms, and degrades with length because more text means more competing near-matches and weaker signal per token. Position effects exist (T2.3) but are second-order.

**Design consequences:**
1. When you control both the query and the stored content (memory files, notes, tool results you format), **engineer lexical overlap deliberately** — consistent terminology, IDs repeated verbatim, headers that echo the questions agents will ask.
2. Paraphrase-heavy contexts (summaries that rename things, synonyms for variety) actively damage retrievability.
3. NIAH-style "we tested our context window" claims tell you almost nothing about performance on real queries.

## T2.3 — Lost-in-the-middle, revised: conditional on window occupancy `[MEDIUM]`

The 2023/24 lost-in-the-middle finding (U-shaped accuracy by position: strong at start and end, weak in the middle) was substantially revised in 2025 (COLM 2025, arXiv:2508.07479): measured by input length **relative to each model's context window**, the U-shape is strongest when inputs occupy up to ~50% of the window. Beyond ~50% occupancy, primacy bias (the frontloading advantage) weakens while recency bias stays stable — the U-curve dissolves into a distance-based bias favoring information near the end. The paper attributes prior contradictory LiM replications to studies using absolute rather than relative input lengths; the ~50% threshold held across all six models tested.

**Why only MEDIUM:** single paper; open-source models only (Llama-3.x 70B, Mistral-Small-24B, Qwen-2.5-32B, Gemma-2-27B; 8K–128K windows); largely synthetic tasks. The authors excluded Claude/GPT for cost. **Transfer to Claude-family 200K–1M windows is an untested extrapolation — flag it whenever you apply this.**

**Design consequence:** "frontload the important content" is *conditional* advice. At low window occupancy (the common case for well-curated agent contexts) frontloading exploits intact primacy bias. At high occupancy, primacy decays — the end of the window becomes the only reliably privileged position, which is one reason recency-anchored patterns (instructions repeated near the end, freshest tool results last) survive in practice. If you operate near window capacity, do not assume your system-prompt-position content is being attended to.

## T2.4 — Claimed vs effective context (compressed history) `[HIGH, historical]`

RULER (NVIDIA, COLM 2024) established the claimed-vs-effective gap: nearly all of 17 evaluated models scored near-perfectly on vanilla NIAH yet showed large drops on harder tasks as length grew; though all claimed ≥32K contexts, only about half performed satisfactorily at 32K. The numbers are 2023–24-era and frontier models now partially saturate RULER (HELMET, ICLR 2025, also criticizes its synthetic tasks) — treat the specific statistic as historical. The durable lesson, corroborated by NoLiMa and Chroma on newer models: **"effective context length" is the operative concept, it is task-dependent, and it is always shorter than the spec sheet.**

## T2.5 — Distractors, and how models fail differently `[HIGH, family-rankings MEDIUM]`

Distractor content — plausible but wrong passages sharing the window with the target — **amplifies long-context failure non-uniformly** (Chroma, 2025). Two distinct failure signatures appeared across families on mid-2025 models: **Claude models showed the lowest hallucination rates under distractors, tending to abstain** ("I cannot find this") **while GPT models showed the highest, tending to confidently answer from the distractor.** The family ranking may not transfer to mid-2026 models; the structural point does:

1. Distractor sensitivity means context *pollution* is a distinct failure axis from context *length*. A short, polluted window can underperform a long, clean one. Curation (removing stale tool results, near-duplicate retrievals, superseded drafts) is not cosmetic.
2. Abstention and hallucination are different downstream risks requiring different harness responses: abstention-prone models need retry/escalation paths; hallucination-prone models need verification gates. Know which signature your model exhibits *under your workload* before designing the recovery path.
