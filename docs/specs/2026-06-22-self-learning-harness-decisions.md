# Self-Learning Harness — Open Decisions

*Companion to `2026-06-22-self-learning-harness.md`. That doc explains the design;
**this one is only the decisions still to make.** For each: the question in plain
terms, the real options, what each costs, and my lean. Working backlog:
z-note `TkNbWHrXQHyuyYMvyy_Ig`. Last updated 2026-07-11: C-group folded in
(v1-deterministic capture, znote `c7IdjdPQVEmZtFCZ3apY5`); confirm budget set ≤2/session.*

---

## How to read this

Each decision has a status:

- **LOCKED** — decided, don't re-open.
- **PENDING** — call made, waiting on a yes/flip.
- **LEAN** — recommendation, still genuinely open.
- **OPEN** — undecided, needs discussion.

And, where useful, **hinges on** (what must be settled first) and **blocks** (what
can't move until this is).

### Decide-first order

```
1.  B1 forks (§0)   ← LOCKED — schema frozen
2.  G  (scope)      ← LOCKED — skill-only v1 (conduct path → v2)
3.  F1              ← LOCKED — v1 boundary settled
4.  A1 + A3         ← the adapter + manifest (what makes it transposable)
5.  B3              ← LOCKED (hook injection)
6.  C1–C8           ← DECIDED — v1 deterministic capture (see §C)
7.  the rest (D1/D2/D3, A2)
```

### Dependency map

```
F1 (v1 scope) ───────────────── bounds everything below
   ▲
G (skill vs conduct scope) ──── RESOLVED: skill-only v1; conduct path → v2

B1 (schema) ──▶ B2 (storage) ──▶ B3 (consumption)
   └──────────▶ D2 (dedup) , D4 (precedence)

A1 (adapter) ◀──▶ A3 (manifest)      two halves of one interface
   └──▶ A2 (distribution) , A4 (language) , [home: TBD — maybe znote]

C1 / C2 (signals) ──▶ C3 (classify) ──▶ C4 (wiring) , C5 (worker)

D1 (promote gate) ──▶ E3 (Level-C graduation)
E1 / E2 (autonomy) ─── cross-cut capture + promotion
```

---

## ⚠ Blind review (2026-06-22) reopened these — design-level, beyond the manifest

A **blind** altitude-stratified review (znote `CR7l33av092VYHoN09qiu`; reviewers given no
knowledge of prior fixes) surfaced issues the leading re-review missed. Schema/manifest fixes
are tracked under A3. These four are **design decisions** that ripple beyond the TOML and need
resolving before A3 or the v1 build:

1. **Safety architecture (BLOCKING-class).** Advisory session-start injection is NOT a
   containment boundary. The capture→store→inject loop has a positive feedback path with no
   retraction edge, a directive-poisoning surface (untrusted transcript bytes → persisted
   injection), a single-verifier monoculture, and `["*"]` blast radius. → expands **E1/E2**:
   human gate before *first injection* (not just promotion); a retraction/quarantine signal;
   capture-source trust tiers (direct user correction ≫ tool/web bytes); injection-volume cap.
2. **Capability-probe, not label-detect.** `deploy_model`/`hook_registration` are install
   choices, not repo facts → the detect tier should probe a *capability* (writable + durable +
   isolated store) and fail loud at install if the store resolves inside a frozen cache.
   → reshapes **A1**.
3. **Degrade-to-disabled** for hosts with no durable isolated writable store (CI/ephemeral,
   immutable, multi-tenant) — a supported config, not an error. → **A1/F**.
4. **Retrieval/ranking is a missing first-class component.** Inject-every-session + a
   monotonic store + no index = hook latency + context pollution. Need top-K (recency ×
   confidence) + an index + a token budget. → new piece between **B3** (inject) and the store;
   interacts with **D3**.

**Status (2026-06-23):** #1 **DECIDED in full** — all four safety mitigations adopted (see
E2) plus a transparency inspector (see F2). #2–#4 **adopting** (leans were yes; flag if only
the safety four were meant).

**Re-review #2 refinements (2026-06-23, znote `YhcvfM3KPgiLPPp8U-7BS`)** — a second blind pass
sharpened the four into concrete obligations that gate A3-lock: (1) the probe must be **runtime
code** (resolve the runtime root, confirm the store backend is reachable *there*, write/read/
isolation-check, else disable — a static `deploy_model` mis-enables; the installed nsys cache
is a stale skills-less snapshot); (2) `source_trust` is a **heuristic prefilter, not a hard
boundary** (a flattened SessionEnd transcript can't tell typed corrections from pasted text) —
so **approve-before-first-use carries the real safety weight**; (3) quarantine needs **damping**
(a `contested`-topic terminal state + cooldown + cause attribution) or it oscillates/DoS-es and
fatigues the approver; (4) write a **retrieval contract** (mandate `confidence`/`timestamp`/
`topic` fields in both store backends) *before* freezing schemas; (5) `injection_cap` should be
**host-aware** (scale with `len(in_scope)`) and safety keys **monotonic** (host may only tighten).

**ALL FOLDED IN 2026-06-24:** #1 → A1 (runtime probe). #2 → E2.3 (the `self-learn teach`
explicit Tier-1 channel, znote `fSfJi7WzPeaDvvMzkVM2F`). #3 → E2.2 (quarantine damping). #4 → B4
(retrieval contract + `topic`/`last_used` fields). #5 → E2.4 (cap = per-session budget) + the
`[safety]` monotonic rule in `self-learn.defaults.toml`. The design reopenings are now closed.

---

## 0. The three schema forks — LOCKED

### 0a. One time axis or two? → **LOCKED: mono-temporal**
`created_at` + `superseded_at`, one axis. A directive matters from when we capture
it until something supersedes it. No separate valid-time axis. Matches `ha-note`.

### 0b. Precedence — stored or derived? → **LOCKED: derived**
Resolve conflicts at read time by `confidence × recency × specificity`. No stored
precedence integer to rot. (This is also the answer to **D4**.)

### 0c. `fire_count` — wire it or reserve it? → **LOCKED: wire the cheap version in v1**

You want early performance signal, and it's achievable in v1 without instrumenting
interactive sessions, by splitting the concept:

- **`surfaced_count` / `last_surfaced`** *(v1)* — the injection hook (B3) already
  knows which directives it surfaced into a session, so it increments this for free.
  Measures **exposure**.
- **`recurrence_count`** *(v1)* — when a *new* correction comes in and dedup-matches
  an **already-promoted** directive (a D2 hit on a promoted record), that directive
  failed to prevent the behavior — increment this. Measures **ineffectiveness**.
- **`applied_count`** *(deferred)* — conscious "I followed directive X"
  self-report. This is the expensive part (needs the consuming session to
  introspect), so it waits.

**The early signal:** *high `surfaced_count` + non-zero `recurrence_count` = the
directive is in play but isn't working.* We get that read in v1 entirely from the
capture+dedup loop we're already building. A directive that works makes its own
correction stop recurring.

> Note on append-only: append-only governs **substance** (trigger, directive,
> evidence, status history — never rewritten). These counters are **derived
> mutable metadata** — a running tally, fine to update in place.

---

## G. Target scope — per-skill vs. a generic conduct path  ·  **LOCKED: skill-only v1**

> **RESOLVED 2026-06-22: skill-only v1.** The conduct path — global scope,
> `CLAUDE.md` target, all-session capture — is deferred **entirely to v2**. v1 learns
> only skill-scoped directives. Because the locked schema already keeps
> `scope ∈ {skill, global}`, v1 just never emits `global`, so adding the conduct path
> in v2 needs **no migration**. The concept below is preserved as the v2 design.

> You raised it: "per skill makes sense… unless we opt for a generic behavioral
> audit path as well, in which case the target wouldn't be a skill, it would be a
> CLAUDE.md."

This is real and changes the architecture in three places (all **v2**):

- **`scope` becomes first-class `{skill, global}`.** Some directives belong to a
  skill (`scope: home-assistant`); some are conduct rules that belong to no skill
  (`scope: global`) — the sudo rule is the canonical example.
- **Level C generalizes.** "Rewrite SKILL.md" becomes "rewrite the governing
  instruction file" — **SKILL.md** for skill scope, **CLAUDE.md** for global scope.
- **Storage:** per-skill stores for skill directives **+ one central store** for
  global/conduct directives. (Both sit behind the same `Store` interface — see B2.)

The thing that actually costs something: a generic conduct path means **capture
runs on sessions where no skill was active**, to catch conduct corrections (like
sudo) that happen during ordinary work. That widens C1/C2/C4's monitoring surface.
In v1 this is *cheaper than it sounds* because v1 has only correction-keyed capture
(a lexical gate at SessionEnd) — the expensive forensic layer is deferred either
way (F1).

**Outcome:** deferred to v2 (smallest v1 wins). The highest-damage mistakes are
conduct-level, so this is a strong v2 candidate — but v1 proves the loop on the
narrower, safer skill surface first.

---

## A. Portability — what makes it transposable

### A1. The adapter contract  ·  FIRMER — grounded in a two-repo assessment
> The minimum a host repo tells/gives the module so it can plug in.

Validated against two deliberately opposite repos — **claude-skills** (nested
`plugins/*/skills/*`, symlink deploy, manual settings.json, keyword activation,
detached `claude -p`, ha-note flat journal) vs **nsys-marketplace** (flat `skills/*`,
frozen-cache plugin install, declarative `hooks.json`, dispatcher activation,
in-session Task only, znote store). Full evidence: znote
`NElts4RW63EvMXjhQr0Ud` + the three assessments. They diverge on nearly every axis,
so the contract is a **three-tier** design:

- **Probe** (runtime capability, NOT a static label — refined 2026-06-23): the detect tier
  *measures*, it doesn't trust a parsed string. At startup it (1) resolves the runtime root
  (e.g. `${CLAUDE_PLUGIN_ROOT}` from env), (2) confirms the declared **store backend is
  reachable from that resolved root** (flat: the store's parent dir is writable; znote: the
  `znote-mcp` server is actually registered/reachable in the *loaded* plugin), (3)
  **write-probes + reads-back + isolation-checks** the store. Any failure → **degrade to
  disabled** (a supported config, surfaced via `--selftest`/the inspector — never a silent
  no-op). `deploy_model`/`hook_registration` are demoted to **hints** the probe verifies.
  *(Why: a static `deploy_model` mis-enables — the installed nsys cache is a stale skills-less
  snapshot whose runtime root has no skills and no `.mcp.json`.)*
- **Declare** (the A3 TOML manifest): policy + un-probe-able facts.
- **Shim** (≤5 optional functions): the un-declarable long tail —
  `resolve_skills()`, `store()`, `inject(text)`, `spawn_worker(prompt)`,
  `register_hooks()`. Transposability = this escape hatch.

**Assume (convergences → robust foundation):** SessionStart→stdout injection works in
*both* repos (the Level-B mechanism is universal; only its *registration* varies) ·
terse `name`+`description` frontmatter · append-only+supersede achievable in both
(flat journal natively / znote via git) · a writable store **outside** the code path
is mandatory · python+bash. **Parameterize (divergences):** skill_glob ·
command/agent presence · hook-registration idiom · worker spawn model · store
backend · path root · deploy model · enforcement strength.

### A3. The per-repo config manifest  ·  VALIDATED (2-repo proof) — lockable
> One small **TOML** file where a repo describes itself. Validated against two opposite
> repos (claude-skills + nsys); both fully declarative, no shim. Full proof + both
> concrete manifests in znote `c3zlB8p8WUWzA0YwBBAsj`. Refined field list:

- `[host]` `repo_root` (glob source) · `runtime_root` (hook-command base) · `deploy_model`
  (auto) · **`state_dir` (transient markers/locks — always `~/.cache`)** · `skill_glob` ·
  `commands_dir?` · `agents_dir?`
- `[skills]` `in_scope` (v1 skill-scope only) + per-skill `[skills.<name>]` `capture_checklist`
- `[store]` `backend` (flat|znote) · `append_only` · flat: `location` (in-repo|external —
  *deploy-derived*) · `path_template` · `format` · znote: `project` · `embeddings` · `mcp_server`
- `[capture]` `trigger_event` (SessionEnd) · `markers` · `worker` (**claude-p|sdk**) ·
  `worker_model` · `verifier_model` · (claude-p: `claude_bin`/`worker_tools`/`lock`)
- `[inject]` `event` (SessionStart) · `mode` (stdout|additionalContext|systemMessage) ·
  `hook_registration` (auto) · `auto_register` (claude-skills=false: never auto-edit settings.json)
- `[autonomy]` `visibility` · `promotion` · `enforcement` (v1=advisory; block/modify/verify=v2)

**Key results:** the `[inject]` line is byte-identical across both repos; injection reads
directive markdown from disk in *both* backends (no MCP at read time); `store.location`
being deploy-derived means symlink hosts get version-controlled+synced directives while
cache-copy hosts get machine-local ones.

**Status: SCHEMA FIXES APPLIED — awaiting a fresh blind re-review.** All 7 mechanical fixes
from the blind review are in (verified: all three TOMLs parse + the defaults/host merge
resolves to a complete config):
1. **worker discriminated union** — `[capture.claude_p]` / `[capture.sdk]` sub-tables mirror
   `[store.<backend>]`; the validator can now enforce required-per-variant.
2. **generalized capture vocabulary** — `skill_captures` names the glob wildcards;
   `path_template` tokens must be a subset; the `skill` capture is the per-skill key. v1 store
   is explicitly **skill-scoped** (command/agent/global directive homes = v2).
3. **symmetric znote addressing** — `partition_by` + `tag_template` mirror the flat
   `path_template`, so both store members answer "where does a skill's directive go."
4. **interpolation model split** — `${HOME}` loader-expands; `${CLAUDE_PLUGIN_ROOT}` / bare
   `$VAR` pass through literally; emitted hook snippets use the host's native style via
   `hook_cmd_root` (claude-skills `$HOME` bare, nsys `${CLAUDE_PLUGIN_ROOT}`). Loader-scope vs
   emitted-snippet-scope no longer conflated.
5. **`history = native | layered`** moved into each store member (honest per-backend semantics).
6. **defaults layer** — module policy (markers, models, autonomy, **safety controls**, inject,
   schema_version) extracted to `self-learn.defaults.toml`; host manifests merge over it. Kills
   the ~50% duplication and gives the decided safety knobs one home.
7. **normalized `capture_checklist`** with the normalization rule stated (no false "verbatim").

**Blind re-review #2 done (znote `YhcvfM3KPgiLPPp8U-7BS`): code level PASSED** — all three
parse, every host fact verified accurate, capture_checklist a faithful normalization. Mid/high
found **spec gaps + design refinements, not wrong values.** Fixed this round: worker
discriminator (`claude-p`→`claude_p` so it matches its table), documented **merge semantics**
(deep-merge tables; replace scalars+lists), the discriminator-spelling + capture-token +
`history`-enum rules, `trigger_event`→`event`, `injection_cap` clarified per-session. **A3-lock
is now gated on DESIGN decisions, not TOML** (see the callout's re-review-#2 refinements): the
capability-probe must be runtime code (a static `deploy_model` mis-enables — the *installed*
nsys cache is a stale skills-less snapshot); `source_trust` is heuristic not a hard boundary
(a flattened transcript can't distinguish typed vs pasted) so the human gate does the real
work; quarantine needs damping; a retrieval contract must precede freezing store schemas;
`injection_cap` host-aware + safety keys monotonic. **2026-06-24: all five refinements are now
folded into the spec (A1 probe · E2.2 damping · E2.3 teach-channel · E2.4 cap+monotonic · B4
retrieval) — A3 is considered LOCKED** (an optional final blind pass could check the schema-field
additions). (Trail: `Fb7…` → `CR7l…` → `YhcvfM3…`.)

### A2. Distribution form + home  ·  LEAN
> How the module physically gets into a host repo — and where it ultimately lives.

- **Ruled out: pip/npm package** (your call).
- **In play:** git **subtree / vendoring** (precedent: this repo already
  subtrees merged skills) · **submodule** · **plugin**.
- **Home undecided — znote is a strong candidate.** If it becomes part of znote /
  nsys-marketplace, distribution = plugin *and* we inherit a DB + vector search for
  storage (see B2). The old "plugins freeze to a cache copy" objection only applies
  to *live-editing the library's own source* — a consumer wants a pinned copy, so
  plugin distribution is fine downstream. The dev-here / consume-elsewhere split
  mirrors this repo's own symlink-vs-marketplace model.

**Lean: defer the home choice; keep vendoring as the safe default and design so the
znote/plugin path stays open.** **Status: LEAN.**

### A4. Language  ·  LOCKED
Python core + bash hook shims. Matches `ha-note` (Python), `cron-claude`
(Python/uv), and the bash hooks. **LOCKED.**

---

## B. Directive schema (storage & consumption)

### B1. Fields  ·  LOCKED (spec §6, including the §0 forks)

Two **additive** fields decided with the C-group (2026-06-24; no migration, B1 stays locked):
- **`kind`** — `anti-pattern` · `surface-rule` · `reasoning-pattern`. Drives decay rate,
  injection priority, and Level-C promotion eligibility (see C8).
- **`reputation`** — the C8 outcome signal; derived mutable metadata (same append-only
  carve-out as the 0c counters).

### B2. Storage  ·  LEAN (direction set: swappable backend, flat-first)
> Where and how directives are physically stored.

**Set:** a **`Store` interface** with two planned implementations —

1. **Flat files** *(v1)* — each directive is **markdown + YAML frontmatter**
   (fields in frontmatter, `trigger`/`directive` prose in the body). Append-friendly,
   git-diffable, no DB dependency, matches `ha-note`.
2. **znote** *(planned second impl)* — because the flat-file form is already a
   note-with-frontmatter, "becoming a znote" is mostly relocation, and it buys
   **vector search** (→ cheap semantic dedup, D2) and a **database** layer for free.

**Layout:** per-skill stores for skill directives **+ a central store** for global/
conduct directives (G).

**Open sub-points:** exact frontmatter field names; whether the central + per-skill
stores share one directory tree. **Status: LEAN.**

### B3. Runtime consumption  ·  LOCKED: hook injection
> How an active skill's directives reach the model.

A **session-start hook** reads the active skill's directives (and, if G is enabled,
the global directives) and injects them. Keeps the learned layer physically
separate from authored `SKILL.md`/`CLAUDE.md` — the whole point of Level B
(additive, reversible). The same hook increments `surfaced_count` (0c). **LOCKED.**

### B4. Retrieval (consult-time)  ·  DECIDED (2026-06-23) — *contract* now, impl later
> Which directives the B3 hook injects when there are more than the `injection_cap` budget.

The store grows monotonically, so injection needs a **retriever**, not "inject everything."
Decided as a *contract* now (so the schema isn't frozen without it): the B3 hook ranks the
in-scope directives **top-K by recency × confidence** (× semantic relevance when available) and
injects only up to the E2.4 per-session budget. Required schema fields (additive to B1, all
forward-compatible): `confidence` (have), `created_at`/`last_used` timestamps, and **`topic`**
(also the quarantine key, B-shared with E2.2). Semantic ranking needs `store.embeddings`; with
embeddings off (znote default) the retriever degrades to **lexical/recency-only** top-K — an
accepted v1 limitation, not a silent one. **DECIDED (contract); the ranking impl is build-time.**

---

## C. Capture pipeline  ·  DECIDED (2026-06-24): **v1 deterministic · v2 statistical**

> **The strategic frame** (znote `c7IdjdPQVEmZtFCZ3apY5`, refining the 4-agent ideation
> synthesis `o4AsT5B15qcb92SCg8lCy`): v1's center of gravity is **deterministic** capture —
> explicit `teach` (E2.3/F2) + cold-start seeding (C6) + the in-the-moment confirm (C7).
> Silent SessionEnd inference (C1→C3) is the **fallback**, not the centerpiece; the
> statistical machinery (inferred corroboration at volume, forensic LLM analysis,
> shadow-holdouts) is **v2 / team-scale**. Three transcript-grounded reasons:
> 1. **Low base rate** — most real "corrections" are in-flight steering or one-off task
>    instructions, not durable skill-defects. Silent inference fights a bad base rate.
> 2. **Weak sensor** — the flattened SessionEnd transcript can't distinguish typed from
>    pasted text; it's the least trustworthy artifact in the system.
> 3. **Sparse volume** — a single-user, skill-scoped tool yields a handful of corrections a
>    month; corroboration-≥2 / frequency→confidence / dedup-at-volume never reach escape
>    velocity at that scale. They pay off at team scale.
>
> **Banked engineering facts** (transcript-verified constraints, not choices):
> `attributionSkill`/`attributionPlugin` sits on every assistant turn → **free scope
> assignment, no inference** · the **error→fix pair** (a tool `is_error` resolved by a later
> successful same-target call) is a zero-NLP structural signal · `interrupted` (Esc) is free
> and high-signal · **TodoWrite = 0** in this user's real sessions → completion signals must
> generalize to the task-tracker of record (`TaskUpdate` / znote tasks) or they no-op ·
> affect/frustration and re-asking are **not** reliably lexically detectable (structural
> proxies or an LLM only).

### C1. Cheap-gate markers  ·  DECIDED — fallback trigger, structural-first
> What cheaply flags a moment as "maybe worth learning," before spending a model.

**Structural spine + recall-tuned lexical, gated by co-occurrence.** The spine is the
banked facts above: error→fix pairs · `interrupted` · `attributionSkill` for scope. Lexical
adds explicit-correction labels ("correction", "to clarify" — near-zero false-positive) and
teaching imperatives ("always", "never", "from now on", "by default", "make sure to").
**Co-occurrence gate:** additive score, fire at ≥2 — one structural hit OR two lexical.
Runs as a **SessionEnd batch scan + a thin live breadcrumb hook** for ephemeral signals
(interrupt; user edits a file Claude just wrote). On a hit it **prefers the C7 one-tap
confirm**; only unconfirmed hits fall through to silent C3 inference. Exclusions: `teach`
invocations and compaction-summary lines (both contain Claude's own "always/never" text).
Calibrate against the downstream C3 accept rate (target band 20–50%). **DECIDED.**

### C2. Forensic gate signals  ·  DECIDED — v1 = cheap flag-and-store backlog ONLY
> What flags a whole conversation as "went badly, analyze later."

v1 is a **structural scorer, no LLM, no directives**: error-density as a *ratio* (good
sessions still had 4–5 errors) · **repeated-identical-failure clusters** (same tool + same
target failing ≥2× — the strongest signal) · task-completion via the task-tracker of record ·
abrupt/abandoned end. Hits append `forensic-flag` records to a **backlog queue**, nothing
else. **v2:** a cron LLM drains the queue, runs the 3-question diagnosis, and emits
**lowest-trust** `source: forensic` candidates through the same E2 gate — with source-aware
corroboration (forensic needs a non-forensic witness to exceed `low` confidence). **DECIDED.**

### C3. Correction classifier  ·  DECIDED — GATE-0 first; asymmetric error budget
> Buckets were settled (defect / preference / user-error); this decides the machinery.

- **GATE-0 — "is this even a directive?"** runs *before* the buckets. The dominant failure
  mode is "not a durable directive at all" (steering, one-offs); `is_directive = false` →
  drop, never reaches the expensive verifier.
- **Proposer ≠ verifier** — haiku-class proposes; the opus-class verifier **re-derives the
  bucket independently** (never shown the proposer's answer, to avoid anchoring).
- **Bucket-separation tests:** *skill-traceability* — a `defect` must point at the skill text
  that misled (or a silent omission) via a required non-null `skill_trace`, which also
  auto-resolves scope · *counterfactual-user* — "would a different competent user want the
  opposite?" → `preference` · *reversal/walk-back* — the user reverses later → `user-error`
  (cheap to see at SessionEnd).
- **Asymmetric error budget:** when torn, classify `preference` or reject — **never default
  to `defect`.**
- **Extraction rules:** `trigger` = the firing *condition*, not a restatement · the
  instruction carries the *why* · `topic` = coarse 2–4-word key · one directive per
  correction · extraction-failure is a first-class outcome.
- **Explicit paths skip the buckets entirely** — `teach` and C7-confirmed captures arrive
  pre-classified (`classification: n/a` for teach; the user's tap for C7), so this machinery
  serves only the silent fallback.
- **Approval queue as training data:** inspector rejects/quarantines feed back as few-shot
  context for the proposer/verifier — near-free, the data already exists. Calibrate from
  approval rates (free labels); **no auto-tuning in v1.** **DECIDED.**

### C4. Trigger wiring  ·  DECIDED
> Which hook events drive capture.

**SessionEnd is the spine** (full transcript for the C1 batch scan + C2 scorer), plus the
**thin live breadcrumb hook** (C1's ephemeral signals + the C7 confirm) and **mid-session
`teach`** (F2). Skill-active sessions only in v1 (G). Hook registration rides the A1/A3
adapter. **DECIDED.**

### C5. Worker harness  ·  DECIDED — host-declared (resolved by A3)
> What runs the background capture/analysis job.

Became a **per-host manifest choice**, not a module decision: `[capture].worker` is a
discriminated union — `claude_p` (home-net-capture's proven detached `setsid claude -p`;
claude-skills) or `sdk` (adapter-owned Agent SDK worker; nsys-marketplace). Both validated in
the two-repo proof. **DECIDED.**

### C6. Cold-start seeding  ·  DECIDED — front of the critical path
> Ship a populated store, not an empty loop.

Mine the **existing human-authored canon** at install: `ha-note` GOTCHAS journals and
SKILL.md gotcha sections (v1, skill-scoped); `CLAUDE.md` conduct rules (the sudo rule etc.)
become the **v2 conduct-path seed**. This fixes two problems at once: the loop is worthless
empty, and the C3 classifier + D2 dedup **can't be calibrated against an empty store** — the
seeds are the calibration set. Seeded records: `source: manual`, evidence pointing at the
source file; since they're normalized from already-human-authored canon they land `active`
(the canon *is* the prior approval). **DECIDED.**

### C7. In-the-moment confirm  ·  DECIDED — budget **≤2/session** (set 2026-07-11)
> Catch the lesson while it's happening, and get the classification for free.

When the live hook sees a **highest-confidence C1 marker**, surface one bounded "remember
this?" prompt; the user's one-tap answer (defect / preference / user-error / no) **collapses
C3's hard classification** for the confirmed path. **Interruption budget: at most 2 prompts
per session**, highest-confidence markers only; everything else stays silent and falls
through to the SessionEnd fallback. A confirmed capture is user-approved by construction —
the tap satisfies approve-before-first-use (E2.1), so it lands `active` with the confirm
recorded as provenance. Declining is free and leaves no directive. **DECIDED.**

### C8. Outcome / reputation signal  ·  DECIDED — design now, additive schema field
> The missing measurement: is injection actually helping?

A directive's **reputation** moves on session outcome: surfaced in a clean session → gain ·
a correction on its own `topic` → lose (the same edge E2.2 quarantine watches) · sustained
loss → retire. This gives **D1 a non-arbitrary promotion basis** ("paid for itself") and
**D3 a non-arbitrary decay basis**, closing the "tuning capture blind" gap.
**Learn-from-success is a confidence adjuster only** — a fail-only loop ratchets toward
timid. Stored as derived mutable metadata (same append-only carve-out as the 0c counters).
Paired schema addition: **`kind`** ∈ anti-pattern · surface-rule · reasoning-pattern — the
three rot on different clocks, so `kind` drives decay rate, injection priority, and
promotion eligibility (reasoning-patterns are the Level-C candidates). Both fields are
**additive to the locked B1 schema** (no migration). **DECIDED.**

---

## D. Promotion & lifecycle

### D1. Promotion gate  ·  OPEN
> How a directive graduates (proposed → verified → promoted → into the canon).

- **Manual review** *(lean for v1)* — a `--pending` queue a human promotes by hand
  (like `ha-note`).
- **Threshold** — auto-promote on corroboration crossing a bar.
- **Scored eval** — deferred (needs infra-run eval to avoid the "agent grades its
  own homework" trap).

**Lean: v1 = manual review, `corroboration_count` as the queue filter.** **OPEN.**

### D2. Corroboration & dedup  ·  OPEN  ·  *hinges on B1; eased by the znote backend*
> How we know two captures are the "same" rule, and how many sightings before it counts.

- **Dedup key** — semantic match on `trigger` within the same `scope` (not
  exact-string). **The znote backend (B2) gives this via vector search;** in the
  flat-file v1 it's a cheaper embedding/LLM match.
- **Corroboration count** — 1 sighting → consulted at low confidence; 2+ independent
  → higher confidence + promotion-eligible. Also feeds `recurrence_count` (0c) when
  the match is against an already-promoted directive.

**Status: OPEN.**

### D3. Decay / supersede / re-verify  ·  OPEN (mostly deferred)
> How stale directives retire or get rechecked.

**Lean:** time-based *decay flag* (mark stale, never auto-delete — append-only) +
optional *re-verify on access* for directives carrying a stored repro. Mostly
**deferred to v2** per F1. **Status: OPEN.**

### D4. Conflict resolution  ·  LOCKED (from 0b)
- **Directive vs. directive** → derived precedence (`confidence × recency ×
  specificity`).
- **Directive vs. canon** → the human-authored `SKILL.md`/`CLAUDE.md` wins *unless*
  a `promoted` directive explicitly supersedes it (which is itself the Level-C
  trigger). **LOCKED.**

---

## E. Autonomy & safety

### E1. The autonomy spectrum  ·  LEAN
> How loud/automatic, per skill.

Three dials: **trigger** × **execution** × **visibility**. **Lean: quietest
default** — instant append + a single transcript line; louder behavior is opt-in
per skill via the A3 manifest. **Status: LEAN.**

### E2. Human-gate placement + safety controls  ·  DECIDED (2026-06-23)
> Where a human must say yes, and the controls that keep the learn-loop safe.

Capture/append stays automatic (additive, reversible), but the blind review showed
*injection* is the real risk surface, so the gate moves earlier. **Decided controls:**
1. **Approve-before-first-use** — a captured directive sits `pending` and does NOT influence
   any session until a human approves it once (not just before promotion).
2. **Undo / quarantine signal — with damping** (refined 2026-06-23) — if a session where
   directive D was active ends in a correction about D's `topic` (a directive field, shared with
   B4 retrieval), D is auto-quarantined and re-queued. Damped so it can't oscillate or DoS:
   a **cooldown/corroboration debounce** (one stray correction doesn't instantly nuke a
   long-good directive), **cause attribution** (the triggering correction is recorded and shown
   in the inspector `pending` view), and a **`contested`-topic terminal state** (after N
   quarantine cycles on a topic, stop auto-proposing there and escalate to the human instead of
   looping).
3. **Source-trust tiers** (decided 2026-06-23; resolves re-review #2's "source-trust isn't a
   hard boundary" finding — znote `fSfJi7WzPeaDvvMzkVM2F`):
   - **T1 explicit** — the user runs `self-learn teach` (F2) to capture a directive on purpose:
     unambiguous provenance, and the **invocation *is* the approval**, so it lands `active`
     (skips `pending`; still echoed-back, quarantine-able, and removable). The hard boundary.
   - **T2 inferred** — auto-capture from an in-session correction at SessionEnd: heuristic (a
     flattened transcript can't prove typed-vs-pasted), so it stays gated behind
     proposer→verifier→approve-before-first-use.
   - **T3 tool / file / web-derived text** — inert.
4. **Injection-volume cap — a per-session total budget** (refined 2026-06-23) — a ceiling on
   directives injected per *session* (not multiplied per skill). The B4 retriever fills the
   budget top-K across all in-scope skills, so more skills → tighter competition, never a
   blow-up. (Resolves the "25 × 20 skills = 500" reading.)

**Monotonic safety keys** (refined 2026-06-23): `source_trust`, `approve_before_first_use`,
`quarantine_on_recurrence`, and `injection_cap` are **monotonic** — a host's manifest may
override them only in the *stricter* direction (narrow trust, force-on a gate, lower the cap).
The validator knows each key's polarity and rejects a loosening override; defaults set the
weakest *safe* value. (Plain "host wins" merge is not safe for safety floors.)

Then promotion is gated, and any Level-C `SKILL.md`/`CLAUDE.md` rewrite is diff-reviewed. The
capture/approve/reject/quarantine actions live in the **F2 inspector** — so the safety gate and
the transparency view are one tool. **Status: DECIDED.**

### E3. Level-C activation  ·  LEAN (defer to v2)
> What earns a directive a place in the canon, and is any of it in v1?

**Lean: defer to v2.** v1 produces and consults; folding into `SKILL.md`/`CLAUDE.md`
is the next milestone. Likely criteria: high confidence + corroboration + clean
`recurrence_count` + a reviewed diff. **Status: LEAN (deferred).**

---

## F. Scope & ops

### F1. The v1 boundary  ·  LOCKED
> What's actually in the first version.

- **In v1:** append-only **per-skill** journal + correction-keyed capture
  (skill-active sessions) + classifier + consulted per-skill directives (Level B) +
  `surfaced_count`/`recurrence_count` signals + `--selftest`.
- **Deferred to v2:** the entire **conduct path** (global scope, `CLAUDE.md` target,
  all-session capture), forensic-cron analysis, scored-eval promotion, Level-C
  automation, `applied_count`, cross-skill directive sharing.

**Status: LOCKED** (G resolved to skill-only).

### F2. Observability + capture — the `self-learn` tool  ·  DECIDED (2026-06-23)
> See what's influencing Claude now; capture on purpose; approve/quarantine; prove the path isn't dead.

A **portable CLI** (generalizing `ha-note --list`/`--pending`) so it works on *every* host;
where a host has a command system, also exposed as a `/self-learn` slash command (the
manifest's `commands_dir?` decides). Views:
- **`active`** (default) — directives injected into the *current* session's context, grouped
  by skill: trigger · instruction · confidence · status · `surfaced_count`/`recurrence_count`
  track record. ("What's whispering in Claude's ear right now.")
- **`pending`** — the approve-before-first-use queue (E2.1) + auto-quarantined items (E2.2);
  `approve`/`reject` act here. The transparency view IS the approval desk.
- **`all [--skill X]`** — the full store with statuses + provenance.
- **`teach "<rule>"`** — the explicit **Tier-1** capture channel (E2.3): the user states a
  directive on purpose; echoed back to confirm, then lands `active` (the invocation is the
  approval). Bare `teach` captures the lesson from the current session. Runs **mid-session**, so
  a lesson is locked the moment it happens — no wait for SessionEnd. (Optional `/teach` slash
  wrapper where the host has commands.)

Plus a generalized **`--selftest`** dead-path guard (from `ha-note`) so a broken capture path
fails loud. Note: in v1, "active but not yet in the skill" = *all* active directives (Level C
is v2); that framing sharpens once some graduate into `SKILL.md`. **Status: DECIDED — v1
must-have (the human gate needs a surface to approve from).**

---

## At-a-glance status

| # | Decision | Status |
|---|---|---|
| 0a | One vs. two time axes | **LOCKED** (mono-temporal) |
| 0b | Precedence stored vs. derived | **LOCKED** (derived) |
| 0c | `fire_count` | **LOCKED** (surfaced+recurrence in v1; applied deferred) |
| G | Skill vs. conduct scope | **LOCKED** (skill-only v1; conduct path → v2) |
| A1 | Adapter contract | **DECIDED** (probe/declare/shim — runtime capability-probe, degrade-to-disabled) |
| A2 | Distribution + home | LEAN (no package; vendor default; znote candidate) |
| A3 | Config manifest | **LOCKED** (code passed blind review; all 5 design refinements folded in) |
| A4 | Language | **LOCKED** (Python + bash) |
| B1 | Schema fields | **LOCKED** |
| B2 | Storage | LEAN (Store iface; flat→znote; per-skill + central) |
| B3 | Runtime consumption | **LOCKED** (hook injection) |
| B4 | Retrieval (consult-time) | **DECIDED** (contract: top-K recency×confidence within cap; +`topic`/`last_used`) |
| C1 | Cheap-gate markers | **DECIDED** (structural spine + co-occurrence lexical; fallback trigger) |
| C2 | Forensic signals | **DECIDED** (v1 = flag-and-store backlog only; LLM analysis → v2) |
| C3 | Classifier | **DECIDED** (GATE-0 · proposer≠verifier · skill-trace · asymmetric budget) |
| C4 | Trigger wiring | **DECIDED** (SessionEnd spine + live breadcrumb + mid-session teach) |
| C5 | Worker harness | **DECIDED** (host-declared: `[capture].worker` claude_p \| sdk) |
| C6 | Cold-start seeding | **DECIDED** (seed from canon at install; classifier calibration set) |
| C7 | In-the-moment confirm | **DECIDED** (≤2 prompts/session; tap = approval → `active`) |
| C8 | Outcome/reputation + `kind` | **DECIDED** (additive schema fields; feeds D1/D3) |
| D1 | Promotion gate | OPEN (lean manual v1) |
| D2 | Corroboration / dedup | OPEN (vector via znote later) |
| D3 | Decay / re-verify | OPEN (deferred) |
| D4 | Conflict resolution | **LOCKED** (from 0b) |
| E1 | Autonomy spectrum | LEAN (quietest default) |
| E2 | Human-gate + safety controls | **DECIDED** (approve-before-use · quarantine · source-tiers · cap) |
| E3 | Level-C activation | LEAN (deferred) |
| F1 | v1 boundary | **LOCKED** (skill-only) |
| F2 | Observability — `self-learn` inspector | **DECIDED** (active/pending/all + selftest) |
