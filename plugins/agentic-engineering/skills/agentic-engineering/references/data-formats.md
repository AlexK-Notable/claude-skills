# Token-Efficient Data Formats

Practice P2.3. Status: **complete** `[CORROBORATED* — Opus probe 2026-06-12]`. The question: when structured data must enter a model's window, which serialization minimizes tokens — and does compression cost comprehension?

## The three variables that decide it

Format choice is governed by **(a) data shape, (b) model tier, and (c) direction** (data going *into* the model vs the model *generating* the format). Generic "use format X" advice that ignores these is wrong somewhere.

## What the evidence shows

- **Compact formats deliver real savings on flat, uniform data** — 30–60% vs pretty-printed JSON is the independently measured cluster (TOON's own transparent benchmark: 39.9% fewer tokens than JSON at equal-or-better retrieval accuracy on capable models; CSV is another ~5–10% smaller than TOON). A locally-measured 60–70% reduction is plausible as a best case but is shape- and tokenizer-specific — present such numbers as "measured on my tokenizer and my data," never as universal. `[CORROBORATED*]`
- **Compact formats fall apart on nested/heterogeneous data.** The strongest independent academic result (21-model benchmark, arXiv:2603.03306): TOON wins on uniform arrays but is **>2× larger than JSON on nested invoice data** (null-padding and field declarations), and generation accuracy on hierarchical structures collapsed to 0% one-shot vs JSON's 18.6%. The paper also names a **"prompt tax"**: in-context format-explanation overhead can negate syntax savings except at large data volumes. `[HIGH]`
- **There is no free accuracy lunch on weak models.** The key contrarian datapoint (independent 11-format benchmark, GPT-4.1-nano on 1,000 records): the *most* token-efficient formats scored *worst* on accuracy (CSV 44.3%, pipe-delimited 41.1%) while token-expensive familiar formats scored best (Markdown key-value 60.7%, XML 56.0% — at ~2.7× CSV's tokens). Practitioners attribute this to training-distribution familiarity. Caveat: single weak model; the community flagged exactly that limitation. `[CORROBORATED*]`
- **Model tier collapses the difference.** Strong models score near-100% across formats, reducing format choice to a pure token-cost decision; weak models show large format-driven accuracy gaps (TOON's own benchmark shows the same split: 91–97% on strong models, 58–60% on haiku/fast-tier). Appears independently in both major sources. `[CORROBORATED*]`
- **Tokenizer caveat:** published savings are tokenizer-specific (most use OpenAI's o200k_base). Savings measured on one vocabulary don't transfer cleanly — re-measure on the target model's tokenizer via its token-counting API. `[MEDIUM]`
- **TOON itself** (github.com/toon-format/toon, v2.3 spec, multi-language SDKs): real and fast-growing, with an unusually honest self-benchmark (it discloses CSV beating it on flat data and its own weak-model accuracy dips). Independent academic assessment: "not in any way production-ready" for complex state trees — i.e., it's a tabular-input format, not a general JSON replacement. `[CORROBORATED*]`

## The selection rule

| Situation | Use | Why |
|---|---|---|
| Flat/uniform tabular → capable model | Compact tabular (TOON/CSV) | Real 30–60% savings, accuracy-neutral at this tier |
| Flat tabular → weak/cheap model | Markdown key-value, JSON | Terse formats measurably hurt weak-model accuracy |
| Nested / heterogeneous / optional fields | Minified JSON (or YAML) | Compact formats balloon (null-padding) and break |
| Model must *generate* the structure | JSON + constrained decoding / structured outputs | Compact-format generation is unreliable off-distribution |
| Accuracy dominates, tokens cheap | Familiar verbose (Markdown-KV, XML, JSON) | Training-distribution familiarity wins |
| Genuine tabular *querying* at scale | Don't put it in context — give the agent code/SQL | Contested practitioner consensus, but consistent with routing data through code (see `tool-design.md`) |

One connection to theory worth keeping in mind: compact formats strip the redundant scaffolding (repeated keys, punctuation) that — per the lexical-matching mechanism in `context-degradation.md` — sometimes *is* the retrieval signal. That's a plausible mechanism for why compression costs accuracy exactly where models are weakest, though it has not been directly tested.
