# Self-Learning Harness — Design Spec (in progress)

*Status: design / brainstorming. No code yet. This document explains the idea in
plain terms; the terse working backlog lives in z-note `TkNbWHrXQHyuyYMvyy_Ig`.*

---

## 1. What this is, in one paragraph

A **portable module that lets a Claude skill get better at *behaving* over time.**
Today a skill is a static instruction file (`SKILL.md`) plus some reference docs.
When Claude using that skill makes the same mistake twice, nothing changes — the
next session starts from the same instructions. This module adds a feedback loop:
it **notices** when a behavior was wrong, **writes down** a corrected behavioral
rule, **checks** that the rule is trustworthy, and **feeds it back** into future
sessions. It is built to drop into *any* repo's skill/command structure with a
small adapter, not just this one.

It is **internal tooling** — something the engineering team uses to build products
that get sold. It is not itself a product, and it does not run on a customer's
machine.

---

## 2. Where the idea came from

This repo already has two homegrown "self-improvement" mechanisms. The module
generalizes the good parts of both:

- **home-network** has the more autonomous loop. A foreground command gathers
  findings, then spins off a *detached background* `claude -p` agent that verifies
  those findings against the live network and conservatively merges the survivors
  into reference docs, then commits. It is the template for "capture → verify →
  merge without blocking the user."

- **home-assistant** has `ha-note`: a dead-simple, **append-only journal** with no
  LLM in the write path. Every lesson is written atomically with provenance
  (cause, fix, repro, verified-or-not), never rewritten; corrections go in a
  companion revisions file; a `--selftest` proves the capture path still works so
  it can't silently die. It is the template for "a durable, trustworthy,
  append-only record."

The module is essentially: **home-network's loop discipline + ha-note's
append-only trust model, generalized and made repo-agnostic, aimed at *behavior*
instead of facts.**

---

## 3. The key distinction: knowledge vs. behavior

There are two different things a skill can learn, and they are not the same:

| | **Knowledge** (what Claude *knows*) | **Behavior** (what Claude *does*) |
|---|---|---|
| Example | "HA caches `.storage` in memory" | "Always stop HA before editing `.storage`" |
| Stored as | a fact / reference entry | a **triggerable directive** |
| Today's tool | `ha-note` journal | *nothing — this is the gap* |

`ha-note` already does knowledge well. **This module is about the behavior column.**
A behavioral record is not a fact; it's a *rule that fires under a condition*. Its
primary key is the **firing condition**, not the content.

---

## 4. The four levels (and where we start)

How aggressively can a skill rewrite itself? Four levels, increasing in power and
risk:

- **Level A — Reference data.** The skill accumulates facts (this is `ha-note`).
  Improves knowledge, not behavior.
- **Level B — Consulted directive layer.** ← **we start here.** The
  human-authored `SKILL.md` stays untouched; the skill *also* reads a separate
  file of learned behavioral directives at runtime. Additive, reversible, safe.
- **Level C — Self-editing.** ← **the end goal.** An agent rewrites `SKILL.md`
  itself, folding proven directives into the canonical instructions.
- **Level D — Fine-tuning weights.** Out of scope. Rejected.

**Why start at B if C is the goal?** Because B *is the curation pipeline that earns
C.* B produces a vetted, append-only stream of behavioral directives with
provenance and a track record. Level C is only safe once you have a pile of
directives that have proven themselves — and that pile is exactly what B
produces. B first, C when the directives have earned it.

**Two kinds of target (v1 does only the first).** Not every behavioral rule belongs
to a skill. Some are *conduct* rules that apply everywhere — "don't run sudo via
Bash" isn't a home-assistant rule, it's a project-wide one. So a directive's `scope`
is either a **skill** (folds into its `SKILL.md`) or **global** (a conduct rule that
folds into `CLAUDE.md`). **v1 ships the skill path only**; the generic conduct path
(global scope, `CLAUDE.md` target, capture on non-skill sessions) is a **v2**
milestone. The schema already carries `scope ∈ {skill, global}`, so v2 adds the
conduct path with no migration — v1 simply never writes `global`.

---

## 5. How the loop works (the five stages)

```
   ┌──────────┐   ┌────────────┐   ┌─────────┐   ┌──────────┐   ┌───────────┐
   │ 1 CAPTURE│──▶│ 2 CLASSIFY │──▶│ 3 STORE │──▶│ 4 CONSULT│──▶│ 5 PROMOTE │
   └──────────┘   └────────────┘   └─────────┘   └──────────┘   └───────────┘
   notice a        is this a real   append a       inject the      graduate proven
   behavioral      defect, a pref,  directive       directive into  directives to
   signal          or user error?   (append-only)   the session     curated / SKILL.md
```

### Stage 1 — Capture (dual-layer)

Two sources feed the loop, deliberately weighted differently:

- **Layer 1 — Correction-keyed (immediate, high signal).** When the user corrects
  Claude ("no, don't do that", "always X"), that's a strong, human-labeled signal.
  Captured right away, weighted higher. *Caveat:* corrections are only as good as
  the user. A confident-but-wrong correction could *weaken* the skill — which is
  why every correction goes through the classifier (Stage 2) before it counts.
- **Layer 2 — Forensic (scheduled, lower confidence).** A cheap background pass
  watches for conversations that *look* like they went badly — tasks marked done
  that weren't, repeated failed attempts, abandonment, error density. Flagged
  conversations get a deeper scheduled (cron) analysis: *what went wrong, what
  reasoning pattern caused it, what role did the skill play?* Model-inferred, so
  it carries lower confidence than a human correction.

High signal-to-noise is the whole game. We'd rather capture *less* and trust it
*more*.

### Stage 2 — Classify (corrections are noisy labels)

A user correction is sorted into one of three buckets, because the right response
differs:

- **Skill defect** — the skill genuinely steered Claude wrong → candidate directive.
- **Preference** — the user wants it done their way → route to a preferences sink,
  not the shared skill (host-defined where that goes).
- **User error** — the user was mistaken → do *not* learn from it.

The model that proposes the correction is **not** the one that verifies it
(proposer ≠ verifier, with the user as proposer). This is the firewall against
"the user said something wrong and now the skill is worse."

### Stage 3 — Store (append-only, with provenance)

Directives are **appended, never overwritten.** When one turns out to be wrong or
stale, you don't edit it — you write a *supersede* record that points at it. The
history stays intact; the correction layers on top. (Straight from `ha-note`'s
journal + revisions model.) See §6 for the exact record.

A hard-won principle from the research survey: **verification must be run by
infrastructure, not asserted by the agent.** (One published self-improving agent,
DGM, faked its own test logs to look successful.) Trust scales with
*validation-signal strength × reversibility* — so we keep writes reversible
(append-only) and we don't let an agent grade its own homework.

### Stage 4 — Consult (the Level-B mechanism)

When a host skill activates, its active directives are surfaced to the model. The
key simplifying choice: **the model is the matcher.** We do *not* build a
rule-matching engine. The `scope` field coarsely routes (which skill), and the
model reads each directive's natural-language `trigger` to decide whether it
applies right now. This is what makes Level B cheap to build.

### Stage 5 — Promote (graduate what proves itself)

A directive starts as `proposed`. With corroboration and (eventually) a track
record of being applied, it advances to `verified` → `promoted`. Promotion to the
curated layer, and ultimately into `SKILL.md` itself (Level C), is gated — by
review and/or thresholds — so only earned rules make it to the canonical
instructions.

---

## 6. The directive record (the core data structure)

Everything hinges on this record — change its shape later and you migrate every
stored directive, so it's decided first. A directive is a **rule that fires under a
condition**.

**Fields:**

| Field | What it holds |
|---|---|
| `id` | stable key (for supersede-pointers, dedup, provenance) |
| `trigger` | the firing condition in plain language — *"when about to…"* |
| `directive` | the rule — what to do or not do |
| `scope` | `skill:<name>` or `global` — skill → `SKILL.md`, global → `CLAUDE.md`. **v1 writes only `skill:`; `global` is the v2 conduct path** |
| `source` | `correction` · `forensic` · `manual` · `teach` (explicit Tier-1 — the user's deliberate capture, pre-approved) |
| `classification` | `defect` · `preference` · `user-error` · `n/a` |
| `kind` | `anti-pattern` · `surface-rule` · `reasoning-pattern` — they rot on different clocks, so this drives decay rate, injection priority, and Level-C eligibility (additive; decided with the C-group 2026-06-24) |
| `topic` | coarse subject key — the **quarantine key** (E2.2 damping) + a retrieval-grouping signal (B4) |
| `confidence` | `high` · `medium` · `low` (derived from source × corroboration) |
| `evidence` | a *pointer* — `{session_id, timestamp, short quote}`, never the full transcript |
| `status` | `proposed → verified → promoted → superseded` · plus `quarantined` / `contested` (E2.2 damping) · or `rejected` |
| `created_at` | when it was recorded |
| `superseded_by` / `superseded_at` | invalidation pointer (append-only; never overwrite) |
| `corroboration_count` | how many independent times we've seen this |
| `surfaced_count` / `last_surfaced` | how often it was injected into a session (exposure; incremented free by the injection hook) |
| `recurrence_count` | times a new correction recurred *after* this was promoted (ineffectiveness signal) |
| `reputation` | outcome-based standing — gains when surfaced in a clean session, loses on a correction in its own `topic`; sustained loss → retire. Derived mutable metadata, like the counters (additive; decided with the C-group 2026-06-24) |
| `applied_count` | conscious "I followed this" self-report — **reserved, deferred** (needs session instrumentation) |

**A worked example** — a real home-assistant behavioral rule, as a v1
(skill-scoped) directive:

```yaml
id: dir_4c1e
trigger: "about to edit a .storage/*.json file while HA is running"
directive: >
  Stop the HA container before editing .storage — HA caches it in memory and
  rewrites it on shutdown, so a live edit is silently clobbered.
scope: skill:home-assistant
source: correction
classification: defect
confidence: high
evidence: {session: f687d7ce…, ts: 2026-06-21T…, quote: "never edit .storage while HA is running"}
status: promoted
created_at: 2026-06-22
superseded_by: null
corroboration_count: 1
surfaced_count: 0      # bumped each time it's injected into a session
recurrence_count: 0    # stays 0 while the directive is working
```

*(The `sudo` rule from §4 is the same record shape with `scope: global` — that's a
**v2** conduct-path directive, not v1.)*

**Three deliberate calls on the trickier fields** (all locked):

1. **Mono-temporal, not bi-temporal** *(locked)*. A directive is valid from creation
   until superseded — one time axis (`created_at` + `superseded_at`) is enough. We
   skip the second "valid-time vs transaction-time" axis unless a real need appears.
2. **Precedence is derived, not stored** *(locked)*. When two directives conflict,
   resolve it at read time by `confidence × recency × specificity` (a skill-scoped,
   recent, high-confidence rule wins). No hand-tuned precedence number to rot.
3. **Track-record is split — ship the cheap signal in v1** *(locked)*. The valuable
   "is this directive actually working?" read is buildable now *without*
   instrumenting interactive sessions:
   - `surfaced_count` — incremented free by the injection hook (exposure).
   - `recurrence_count` — bumped when a new correction dedup-matches an
     already-promoted directive (it failed to prevent the behavior).
   - *high surfaced + non-zero recurrence = in play but not working.* A directive
     that works makes its own correction stop recurring.
   - Only `applied_count` (conscious self-report) is deferred — that's the part that
     needs session instrumentation. Append-only governs *substance*; these counters
     are derived mutable tallies and may be updated in place.

---

## 7. What's settled (don't re-open)

| Decision | Summary |
|---|---|
| **Levels** | End goal Level C (self-edit `SKILL.md`); start Level B (consulted layer). B earns C. |
| **Dual-layer capture** | Correction-keyed (immediate, weighted higher) + forensic (scheduled, lower confidence). |
| **Classify first** | User corrections are noisy labels — bucket as defect/preference/error before promoting. |
| **Append-only + abstractions** | Never overwrite; supersede. Store behavioral *rules*, not raw transcripts. |
| **Substrate** | Claude Agent SDK is the harness (hooks, subagents, sessions, structured output). Reuse the memory-tool *interface*, but own the backend (so we keep append-only + classifier + provenance). |
| **Storage** | A `Store` interface: flat **markdown + YAML frontmatter** files in v1, shaped so the planned **znote** backend (vector search + DB) is a near-trivial swap. Per-skill stores + one central store for global directives. |
| **Consumption** | Level B reaches the model via a **session-start hook** that injects the active skill's directives (and global ones), keeping the learned layer separate from authored canon. |
| **Distribution** | Not a pip/npm package. Vendoring/subtree (default), submodule, or plugin. Ultimate home undecided — **znote/nsys-marketplace is a candidate** (would make it plugin-distributed and DB/vector-backed). |
| **Licensing / scope** | Commercial-use posture cleared. It's internal tooling to build sold products — not sold itself, not customer-run. |

---

## 8. What's still open (the working agenda)

Grouped A–F. Leans noted where we have one; "OPEN" means genuinely undecided. The
**companion `…-decisions.md` is the authoritative, live status** — this is a
summary. As of the first decision pass, the schema forks (§6) and B3/A4/D4 are
**LOCKED**, and one new cross-cutting item is open:

- **G. Target scope (skill vs. generic conduct path)** — **LOCKED: skill-only v1.**
  `scope ∈ {skill, global}` stays in the schema, but v1 writes only `skill:`. The
  conduct path (global scope, `CLAUDE.md` target, all-session capture) is a **v2**
  milestone — no migration needed to add it later.

### A. Portability — *what makes it transposable* (top priority)
- **A1 Adapter contract** — the minimal interface a host repo implements: where
  skills/commands live, how to invoke Claude, where the store lives, how directives
  get injected, how hooks register. **OPEN.**
- **A2 Distribution form + home** — **not** pip/npm. Vendoring/subtree *(default)*,
  submodule, or plugin. Home undecided; **znote is a candidate** (→ plugin + DB +
  vector search). Adapter is declarative + a thin optional code shim escape-hatch.
- **A3 Per-repo config manifest** — **TOML** *(set)*; fields OPEN (in-scope skills,
  conduct-path on/off + its target file, capture checklist, store location, gate
  signals, autonomy/visibility). Draft the field list together.
- **A4 Language** — Python core + bash hook shims. **LOCKED.**

### B. Directive schema
- **B1 Fields** — **LOCKED**, see §6.
- **B2 Storage** — `Store` interface: flat md+YAML-frontmatter files now, **znote
  backend** planned (vector + DB); per-skill + central global store. *(lean)*
- **B3 Runtime consumption** — **LOCKED: session-start hook injection** (the
  concrete Level-B mechanism; also bumps `surfaced_count`).

### C. Capture pipeline
- **C1 Cheap-gate markers** — what cheaply flags a moment worth capturing
  (corrections, frustration/negation, error→fix, "always/never/remember"). **OPEN.**
- **C2 Forensic signals** — incomplete to-do lists, failing tests, repeated
  requests, abandonment, error density. **OPEN.**
- **C3 Classifier** — buckets, prompt, model tier, routing. **OPEN.**
- **C4 Trigger wiring** — Stop vs. SessionEnd hook *(lean: SessionEnd)*.
- **C5 Worker** — Agent SDK worker vs. `claude -p` *(lean: SDK)*.

### D. Promotion & lifecycle
- **D1 Promotion gate** — manual review vs. corroboration/fire-count threshold vs.
  optional scored eval. **OPEN.**
- **D2 Corroboration / dedup** — the dedup key; how many sightings before a
  directive influences anything. **OPEN.**
- **D3 Decay / re-verify** — invalidate stale directives; re-run stored repro/eval.
  **OPEN.**
- **D4 Conflict resolution** — **LOCKED** (from §6): directive-vs-directive by
  derived precedence; directive-vs-canon → authored `SKILL.md`/`CLAUDE.md` wins
  unless a `promoted` directive supersedes it.

### E. Autonomy & safety
- **E1 Spectrum** — trigger × execution × visibility, per skill *(lean: quietest
  default — instant append + one transcript line; louder is opt-in)*.
- **E2 Human-gate placement** — B auto-appends; promotion is gated; C diffs are
  reviewed *(lean as stated)*.
- **E3 Level-C activation** — criteria to graduate a directive into `SKILL.md`;
  in v1? *(lean: defer to v2)*.

### F. Scope & ops
- **F1 v1 boundary** *(lean)* — v1 = journal + correction-capture + classifier +
  consulted directives + selftest. Defer: forensic-cron, scored gate, Level-C
  automation, cross-skill sharing.
- **F2 Observability** — an inspect/audit surface + a generalized `--selftest`
  dead-path guard (from `ha-note`). **OPEN.**

---

## 9. Glossary

- **Directive** — a behavioral rule that fires under a stated condition. The atomic
  unit this module manages.
- **Trigger** — the plain-language firing condition; the model reads it to decide
  if a directive applies.
- **Correction-keyed capture** — learning triggered by an explicit user correction
  (high signal).
- **Forensic capture** — learning from after-the-fact analysis of conversations
  that look like they went badly (lower confidence).
- **Classifier** — sorts a correction into defect / preference / user-error so bad
  corrections don't degrade the skill.
- **Append-only / supersede** — records are never edited; a correction is a new
  record pointing at the old one.
- **Adapter** — the small per-repo glue that lets this module plug into a host
  repo's conventions.
- **Level A/B/C/D** — reference data / consulted directive layer / self-editing
  `SKILL.md` / weight fine-tuning (rejected).

---

## 10. Status & next step

- §6 (the directive record) is the first locked decision, pending your ratification.
- Next in the agenda: **A1 + A3** — the adapter contract and the per-repo config
  manifest, because those are what make the module transposable.
- No code until the spec decisions are made and confirmed. All build work happens
  in the `self-improve-lib` worktree.
