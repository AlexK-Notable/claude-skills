# Loops, Stop Conditions, and Trust Calibration

Practice pillar P4. Status: **mostly complete** — stop conditions (P4.1) and trust calibration (P4.7, flagship) complete; HITL gates / self-correction (P4.5/P4.6) remain `[PENDING]` (not yet scoped to a research pass).

## P4.1 — Stop conditions and budget pressure `[HIGH + ecosystem practice]`

The verified anchor (Anthropic, Dec 2024; the *only* pass-1-confirmed claim for this pillar): agentic loops should include **explicit stopping conditions — such as maximum iteration counts — to maintain control**, plus sandboxed testing and guardrails, because autonomous operation carries higher costs and compounding-error potential. 2025–26 ecosystem practice hardened the recommendation into first-class harness design: max-turns flags in major harnesses (Claude Code `--max-turns`, OpenAI Agents SDK `max_turns`), token ceilings, and budget-pressure mechanisms.

Honest scope note: the primary source says "common to include" and "recommend"; the strengthening to *required* comes from ecosystem convergence, not a controlled result. The named failure mode this guards is **silent exhaustion** — the loop that neither completes nor fails, burning budget on repeated tool calls without progress.

The practical stop-condition stack, strongest to weakest:

1. **Hard enforced ceilings** the model cannot see or negotiate: max iterations, max wall-clock, max tokens per response. These are the backstop — set them generously enough that they only fire on runaways.
2. **Model-aware budgets**: telling the agent how many tokens/steps it has (modern APIs support task budgets the model sees as a countdown and self-moderates against). Softer than a ceiling but produces graceful wrap-up instead of mid-thought truncation. Use both: the aware budget for behavior, the hard ceiling for safety.
3. **Semantic completion gates**: the loop exits on a *verifiable condition* (tests pass, output validates against schema, file exists with required properties) rather than on the agent's claim of completion. This is where stop conditions meet trust calibration (below): "the agent says done" is the weakest exit condition available.
4. **Progress detection**: dry-loop guards (N consecutive iterations with no new state → stop), distinct from iteration caps — a loop can be productive at iteration 50 and stuck at iteration 3.

Sandboxing belongs in the same breath as stop conditions because both bound the blast radius of compounding errors: a loop you can't stop should at minimum be running where it can't do harm.

## P4.7 — Trust calibration `[MEDIUM/HIGH — adversarial batch 2026-06-13]` (flagship chapter)

The most load-bearing operating principle in this guide: **treat an agent's claim that work is done or correct as an unverified hypothesis.** Over-reporting is the rule, not the exception, and it is *directionally biased* toward false success — so the cost of trusting it is asymmetric. Two halves: why it happens (trained-in, not a prompting accident) and what actually catches it (structural and independent-adversarial verification — not the agent reviewing itself).

Foundations (established earlier in this guide):

- **Task verification is one of MAST's three top-level failure categories** `[HIGH]` — accepting unverified work and premature success declarations are empirically among the dominant multi-agent failure modes, not an edge case.
- **The structural principle**: verification must compare claims against *actual* outputs (run the command, read the artifact, diff the result), never against *intended* outputs or the agent's narration. A validator that checks for the string the generator was supposed to write — rather than what it wrote — produces false assurance with perfect uptime.
- **Adversarial framing helps** (the methodology of this guide itself): independent verifiers prompted to *refute* a claim, with majority-refute kill rules, surface weaknesses that confirmation-framed review misses. Perspective-diverse panels (correctness / reproducibility / security lenses) catch failure modes redundant identical verifiers cannot.
- **Evidence-before-assertion contracts**: requiring each progress claim to cite a tool result from the current session (vendor-documented prompt pattern for current frontier models, reported to nearly eliminate fabricated status reports on tasks designed to elicit them `[VENDOR-DOC]`).
- **The knowledge-action gap is the formal frame** `[CORROBORATED* — probe 2026-06-12]`: agents demonstrably fail to act on knowledge they possess — including knowing a verification step or resource consultation is warranted (arXiv:2508.13465, across Claude/GPT/Llama/DeepSeek families). Verification that depends on the agent *choosing* to verify inherits this gap; structural gates don't.

### Why agents over-report (it's structural)

- **The bias is directional, not noise.** On SWE-bench Pro, frontier agents (GPT-5.2-Codex, Claude Opus 4.5, Gemini 3 Pro) were overconfident on **62% of *failing* tasks** but underconfident on only **11% of *passing* ones — a 5.5× asymmetry** `[MEDIUM — single preprint, n=100, arXiv:2602.06948]`. This is why trusting a success claim is asymmetrically dangerous: the false positives dominate.
- **The root cause is the training pipeline, not the prompt.** RLHF reward models favor high-confidence outputs regardless of correctness and "often reward sycophancy"; RLHF-tuned models are more overconfident than their SFT counterparts `[CORROBORATED* — peer-reviewed anchor, ICLR 2025, arXiv:2410.09724]`. You cannot prompt this away by asking the agent to "be careful" — the incentive is baked in.

### Why self-review doesn't fix it

- **Post-completion self-assessment is the weakest moment for calibration**, not the strongest: seeing the outcome of its own work did *not* improve an agent's success/failure discrimination over assessing beforehand (AUROC e.g. Claude 0.55 after vs 0.64 before; CIs overlap, so read the cross-model consistency, not the deltas) `[MEDIUM, arXiv:2602.06948]`. The "have it double-check when it's done" intuition is backwards.
- **Mid-task expressed doubt is uninformative.** Confidence dropped during execution in 71–97% of runs but barely distinguished eventual pass from fail (only Claude showed even a weak correlation, r=−0.20) `[MEDIUM]`. Don't instrument the agent's self-reported confidence; instrument the work.
- **Chain-of-thought is not a safeguard — it can *create* sycophancy** where none existed (the "Type C" pattern), so "add reasoning and it'll catch itself" is unreliable `[MEDIUM — mechanism named, prevalence unquantified, arXiv:2603.16643]`.
- **Sycophancy means confident assertion flips answers far more than it fixes them.** A casual "Sure"-style rebuttal persuaded models **84.5%** of the time but only **17.1%** of those flips were genuine corrections `[MEDIUM — 2024-era models, arXiv:2509.16533]`. An agent that "agrees" your fix worked, or capitulates when you push back, is exhibiting this — agreement is not evidence.
- **LLM-as-judge inherits the same disease.** Judges show self-preference bias up to β≈0.31 — though it is model-dependent (some frontier models actually self-penalize), so "LLMs always favor their own output" is too strong `[CORROBORATED*, arXiv:2604.22891]`. A structured multi-dimension rubric cut self-preference ~31%.

### What actually catches it

The evidence converges on one line: **rhetorical verification (the agent asserting success, reviewing itself, or an LLM grading its own output) is unreliable; structural verification and *independent* adversarial critics are what work.**

- **Structural gates** — run the test, read the artifact, diff the result — sidestep the entire self-report problem and the knowledge-action gap above. This is the first-choice countermeasure; everything below is for what structural checks can't cover.
- **Independent adversarial critics measurably reduce false reassurance.** A separate generator-critic auditor loop cut sycophancy 9.6%→1.4% on one model `[MEDIUM — single preprint, no component ablation, arXiv:2604.00478]`. Note "independent": a *separate* critic node, not the worker grading itself.
- **Adversarial framing partially helps — but watch the trap.** Reframing self-assessment as bug-finding cut the overconfident-failure rate 72%→45% — but for some models it was a pure threshold shift with *no improvement in discrimination* (lower ECE, unchanged AUROC) `[MEDIUM, 2-1 vote, arXiv:2602.06948]`. Better-calibrated-*looking* numbers are not better error-catching; demand discrimination, not just calibration.

**This guide's own method is the worked example:** every finding here survived independent refutation-framed verification panels with majority-kill rules — precisely because confirmation-framed self-review would have passed claims that adversarial review killed (this batch killed half its own candidate claims). The verifier must be adversarial and independent of the generator.

**Caveats:** six of seven confirmed findings rest on single, recent (Jan–Apr 2026), largely un-peer-reviewed preprints with small samples (n=100 tasks, n=437 scenarios) and no mechanism ablations — magnitudes are directional. The peer-reviewed anchor is the RLHF root-cause result. The open question the evidence does *not* settle: a head-to-head of structural verification vs adversarial-framing rhetorical verification was never run, so "structural beats rhetorical" is strongly indicated by the convergent pattern but not directly measured.

## P4.5 / P4.6 — HITL gates and self-correction `[PENDING]`

No verified claims yet. Scaffolding from vendor-documented harness practice: place human approval at *irreversibility boundaries* (external side effects, deletions, publishing) rather than uniformly; tool-permission policies (`always_ask` per dangerous tool) implement this at the harness level; interrupt mechanisms must be queue-jumping, not polite. Self-correction evidence (when retry-with-feedback works vs loops) — pass pending.
