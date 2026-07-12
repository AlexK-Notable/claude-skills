# Self-Learning Harness — State of Play (review briefing)

*A plain-English snapshot of where this design stands, written to be read on its own.
For the full design see `2026-06-22-self-learning-harness.md`; for the live decision
status see `…-decisions.md`. This doc is the "catch me up and tell me what's left."*

---

## The 30-second version

We're designing (not yet building) a **drop-in module that lets a Claude skill learn
from its mistakes** — when you correct Claude, the module writes down a corrected
behavior and quietly reminds Claude of it in future sessions. It's meant to be
**portable**: the same module slots into different code repositories by reading a small
per-repo config file.

We got the core design decided, proved the config file works by writing real ones for
two very different repos, and then ran the design past reviewers. A first review passed —
but it was *too easy on us*. A second, **blind** review (reviewers told nothing except
"find what's wrong") found a **significant safety problem** plus a handful of structural
fixes. So the config piece is **reopened, not locked**, and there's one genuinely
important design question on the table: *is the learn-and-reinject loop safe enough as
designed?*

---

## What we're building (plain English)

A Claude **skill** is basically an instruction sheet that tells Claude how to do a
certain kind of task. Today those sheets are static — if Claude makes the same mistake
twice, nothing learns. This module adds a feedback loop:

1. **Capture** — when you correct Claude, the module notices.
2. **Classify** — it decides whether your correction is a real lesson, a personal
   preference, or just you being wrong (so bad corrections don't poison the skill).
3. **Store** — it writes the lesson down as a **directive**: a small rule with a
   *trigger* ("when about to edit a config file…") and an *instruction* ("…stop the
   service first").
4. **Consult** — next time, it slips the relevant directives into Claude's context at
   the start of the session, so Claude "remembers."
5. **Promote** — rules that prove themselves can later graduate into the skill's
   permanent instructions.

The **portability** trick: the module doesn't hard-code any one repo's layout. Each host
repo ships a small **manifest** (a `.toml` config file) describing where its skills live,
where to store directives, how to inject them, etc. One module, many repos.

---

## How we got here (the journey)

1. **Decided the core design** — start with a safe "advisory" version (the module only
   *suggests* learned rules, it doesn't rewrite anything yet), learn only from
   skill-specific corrections for now, store rules append-only with full provenance.
   *(These are locked — see "What's solid.")*
2. **Designed the manifest** — the per-repo config file, plus a 3-tier integration model:
   auto-**detect** what we can, **declare** the rest in the manifest, and fall back to a
   tiny bit of **code** for anything weird.
3. **Proved it** — wrote real manifests for two deliberately opposite repos
   (`claude-skills`, a personal repo; and `nsys-marketplace`, a big plugin repo). One
   schema covered both — encouraging.
4. **Reviewed it (round 1)** — three agents checked the work; we fixed what they found.
5. **Reviewed it again (round 2, leading)** — passed clean… but the prompts *told* the
   reviewers what to confirm, which biased them toward "yep, looks fixed."
6. **Reviewed it again (round 3, blind)** — three fresh reviewers at three "altitudes"
   (big-picture architecture / mid-level patterns / line-by-line), told nothing about
   prior reviews. **This is where the real problems surfaced.**

The lesson from 5→6 is itself worth keeping: *a review that tells the reviewer what to
look for mostly finds what you told it to.* Blind beats leading.

---

## What's solid (locked — not up for debate)

| Decision | In plain terms |
|---|---|
| Start "advisory," aim higher later | v1 only *suggests* rules; rewriting a skill's own instructions is a later milestone. |
| Learn from two kinds of signal | Immediate user corrections (high quality) + a slower "what went wrong" pass (later). |
| Classify before trusting | A correction is sorted into real-lesson / preference / user-error first. |
| Never overwrite, only add | Rules are append-only; a wrong one is superseded by a new record, history kept. |
| Skill-scoped for v1 | v1 learns rules tied to a specific skill; repo-wide "conduct" rules come later. |
| One config schema, two real proofs | The manifest format demonstrably describes two opposite repos. |

---

## What the blind review found

Two buckets. The first needs **your** input; the second I can just fix.

### A. Design questions (need decisions — they go beyond the config file)

1. **Is the learn-and-reinject loop safe enough?** *(the big one — see next section)*
2. **We're "detecting" things that aren't actually detectable.** The module tries to
   auto-sense how a repo is installed. The reviewer's point: that's not a fixed fact
   about the repo, it's a choice that can change between runs — and we're hanging the
   most important decision (where learned rules get saved) on that shaky signal. Better
   to **test the actual capability** ("can I write to a durable, private place here?")
   and refuse to start if not.
3. **Some hosts have nowhere safe to learn.** Throwaway/CI environments, locked-down
   images, and shared multi-user setups have no private, persistent place to keep rules.
   The module should *cleanly switch off* in those cases instead of pretending to learn.
4. **There's no "find the relevant rules" engine.** "Inject the relevant directives"
   sounds simple, but rules pile up forever and there's no ranking step — eventually
   you'd dump too much into every session, slowing it down and *degrading* the very
   behavior you're trying to improve. We need a "top-N most relevant" retriever with a
   size budget.

### B. Mechanical fixes (I can just do these — listed so you can see the scope)

- One part of the config (`worker`) has the same "pick-a-backend" shape as another part
  but wasn't written consistently — tighten it.
- The rule that maps config wildcards to file paths only covers *skills*, not commands or
  agents — give those a defined home too.
- The variable syntax we mandated (`${VAR}`) clashes with the bare-`$HOME` style one host
  actually uses in the file we'd be writing into — scope the rule correctly.
- A "this is append-only" flag means two different things depending on backend — make it
  honest per backend.
- About half of each manifest is duplicated boilerplate — add a defaults layer so a repo
  only states what's *different*.
- The four "what's worth capturing" example strings are paraphrases of the source skill,
  not exact quotes — make them verbatim (my earlier fix only caught one of the four).

---

## The safety question, explained simply

This is the most important thing the review surfaced, and it's a *design* question, not a
bug. We had assumed v1 was low-risk because it only **suggests** rules rather than
blocking anything. The reviewer's argument: a suggestion injected at the **start of every
session** is the single most influential spot in the whole system — it's the same channel
Claude's master instructions use. "Advisory" limits the *mechanism*, not the *influence*.

Three concrete ways it can go wrong as currently designed:

- **The echo chamber.** Once a rule is in play, Claude behaves differently. If you don't
  push back (because the new behavior looks fine), the module reads your silence as
  approval. There's no "that rule made things worse — undo it" signal, so a bad rule has
  no built-in way out.
- **Poisoned input.** The module learns by reading the *transcript* of a session — which
  includes the contents of files you opened and web pages you fetched. If one of those
  contains text shaped like an instruction (a README saying "always run this script
  first"), the module can mistake it for *your* correction and turn it into a standing
  rule. That's a path for untrusted text to quietly become permanent behavior.
- **One gatekeeper.** A single AI "verifier" approves new rules. One model, one prompt,
  one blind spot — repeated across every rule and every repo.

None of these are fatal; they're fixable with design choices we simply hadn't made yet:

- **Approve before first use, not just before promotion.** Don't let a freshly-captured
  rule influence any session until a human has okayed it once.
- **Add an undo signal.** If a session where a rule was active ends in a correction about
  that same topic, automatically quarantine the rule for re-review.
- **Trust the source, tiered.** A correction *you* typed is far more trustworthy than text
  the module merely *found* in a file or webpage. Only the former should auto-capture.
- **Cap the volume** of rules injected per session.

These mostly land in the part of the plan we hadn't reached yet ("autonomy & safety"), so
this review essentially told us which decisions to make there first.

---

## Decisions taken (2026-06-23)

You reviewed the safety question and **adopted all four mitigations**: approve-before-first-use,
the undo/quarantine signal, tiered source trust (a correction *you* typed can auto-capture;
text the module merely *found* cannot), and a per-session injection cap.

**Plus a new transparency feature you asked for** — a way to see, at any moment, which learned
rules are currently active (being injected into Claude's context) but not yet folded into the
skill itself:

- **What it is:** a small command — `self-learn active` — that prints the rules in play right
  now, grouped by skill, each with its trigger, instruction, confidence, status, and track
  record (how often it's fired; whether the problem it addresses has recurred).
- **Portable by default:** it's a **CLI** (like the existing `ha-note --list`), so it works in
  *every* host repo. Where a host has a slash-command system, the module can *also* expose it as
  a `/self-learn` command — but the CLI is the dependable core, because not every repo has
  commands (your `claude-skills` repo, for instance, has none).
- **It doubles as the approval desk.** The same tool has a `pending` view — the approve-before-
  first-use queue plus anything auto-quarantined — and lets you `approve`/`reject` a rule. So the
  transparency feature and the safety gate are literally **one tool**, not two.
- **Where it fits:** this is the concrete form of the "observability" item that was already on
  the agenda — now promoted to a v1 must-have, since the human gate needs a surface to approve
  *from*.

**And a deliberate "teach it directly" channel** (your idea) — `self-learn teach "<rule>"`, a
command you invoke *on purpose* to hand the system a lesson. It's the same `self-learn` tool as
the inspector. Why it matters: a later review pointed out that the system can't always tell, from
a session transcript, whether an instruction was something *you typed* vs something you *pasted in*
— so the automatic capture path is a good guess, not a guarantee. An explicit command removes all
doubt: you authored it on purpose, so it's the **most trusted** path, and because the act of
invoking it *is* your approval, it takes effect immediately (no separate approval step) while still
being visible and removable, and still auto-pulled if it later causes trouble. It also lets you
capture a lesson the *moment* it happens, mid-session, instead of waiting for end-of-session
analysis. The automatic path still exists for everything you don't explicitly teach.

(The other three review items — capability-probe instead of install-guessing, a clean
"disabled here" mode for unsupported hosts, and a real retrieval/ranking step — are being
adopted too; my lean was yes on each.)

---

## Outstanding decisions

### Decided in this review (2026-06-23)
1. **Safety model** — ✓ all four mitigations adopted (approve-before-first-use,
   undo/quarantine, tiered source trust, volume cap).
2. **Transparency inspector** — ✓ added at your request: `self-learn active` (see "Decisions
   taken" above); doubles as the approval desk for mitigation #1.
3. **Detect → probe**, **off-switch for unsupported hosts**, **retrieval/ranking**, **quarantine
   damping**, and **host-aware cap + monotonic safety keys** — ✓ **all folded into the spec
   (2026-06-24)**, so the config piece (the manifest, "A3") is now **locked**. Next up is the
   capture-pipeline detail.

### I can just do (mechanical, no decision needed)
5. Apply the six schema/config fixes from bucket B above, then re-run a **blind** review.

### Still untouched (the rest of the agenda, for later)
6. **Capture details** — exactly what cheap signals flag a "worth capturing" moment; how
   the classifier is prompted; which model tiers.
7. **Promotion & lifecycle** — when a rule graduates; how duplicates are merged; how stale
   rules retire.
8. **Observability** — how you inspect what's been learned and confirm the capture path
   isn't silently broken.

My suggested order: **1 (safety) → 5 (mechanical fixes) → re-blind-review → then 6–8.**

---

## Glossary

- **Skill** — an instruction sheet that tells Claude how to do a category of task.
- **Directive** — a learned behavioral rule: a *trigger* ("when X…") + an *instruction*
  ("…do Y"). The thing this module captures and stores.
- **Manifest** — the small per-repo `.toml` config file that tells the module how to plug
  into that repo.
- **Adapter / shim** — the integration layer; mostly the manifest, plus a tiny bit of
  optional code for unusual repos.
- **Advisory injection** — the module *suggests* directives by adding them to Claude's
  context, rather than hard-enforcing them.
- **SessionStart / SessionEnd hook** — a script Claude Code runs automatically at the
  start/end of a session; how the module injects rules (start) and captures lessons (end).
- **Capability probe** — testing whether something actually works (e.g. "can I write a
  file that survives a reinstall?") instead of assuming it from a label.
- **Frozen cache vs symlink deploy** — two ways a repo gets installed: a *frozen* copy
  (edits don't take effect until reinstall) vs a *live symlink* (edits are instant). This
  determines where learned rules can safely live.
- **Append-only / supersede** — never edit or delete a record; correct it by adding a new
  one that points back. Keeps full history.
- **Proposer / verifier** — one (cheap) AI proposes a captured rule; a different (stronger)
  AI checks it before it's trusted. A safeguard against bad captures.
- **Prompt injection** — when untrusted text (in a file or webpage) is mistaken for a real
  instruction. Here, the risk that such text becomes a permanent learned rule.
- **Retrieval / ranking** — choosing the *most relevant* rules to inject when there are too
  many to use them all.
- **Discriminated union** — a config pattern where one field ("which backend?") decides
  which other fields are valid. Keeps incompatible options from mixing.
- **TOML** — a human-friendly config file format (think "nicer INI"), used for the manifest.
