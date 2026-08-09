# Closing the Loop

**Use when:** bounding an autonomous agent loop and deciding what is allowed to count as "done."

---

## Step 1 — Build the stop-condition stack, all four layers

Each layer catches what the others miss; shipping only one is the common defect.

1. **Hard enforced ceilings the model cannot see or negotiate.** Max iterations, max wall-clock, max tokens per response, enforced by the harness (`--max-turns`, `max_turns`, token ceilings). The backstop: set it generously enough that it fires only on runaways, never as routine flow control.
2. **Model-aware budgets.** Tell the agent its step/token allowance so it self-moderates against a visible countdown. Softer than a ceiling, but it buys graceful wrap-up instead of mid-thought truncation. Ship **both**: the aware budget shapes behavior, the hard ceiling guarantees safety.
3. **Semantic completion gates.** Exit on a *verifiable condition* — tests pass, output validates against schema, the file exists with the required properties — not on the agent's report. "The agent says done" is the weakest exit condition available to you.
4. **Progress detection.** A dry-loop guard: N consecutive iterations producing no new state → stop. This is *not* the iteration cap. A loop can be productive at iteration 50 and stuck at iteration 3; only the dry-loop guard distinguishes them.

Configure the sandbox in the same commit. Ceilings and sandboxing bound the same thing — the blast radius of compounding errors — and a loop you cannot stop should at minimum run where it cannot do harm. The named failure this whole stack guards is **silent exhaustion**: the loop that neither completes nor fails, burning budget on repeated tool calls without progress. Honest scope: the primary source *recommends* stop conditions; the hardening to "required" is ecosystem convergence, not a controlled result.
`Why: → ../references/loops-and-stop-conditions.md P4.1`

## Step 2 — Treat the success claim as an unverified hypothesis, and act on the asymmetry

Write the loop so that no downstream step consumes a completion claim as fact.

- **Assume false-success, not noise.** On SWE-bench Pro, frontier agents were overconfident on **62% of failing tasks** but underconfident on only **11% of passing** ones — a **5.5× asymmetry** toward false success `[MEDIUM — single preprint, n=100, arXiv:2602.06948]`. Trusting the claim is asymmetrically expensive; the errors you inherit are almost all in one direction.
- **Do not add a self-review step after completion.** Seeing the outcome of its own work did not improve an agent's success/failure discrimination over assessing beforehand (AUROC e.g. Claude 0.55 after vs 0.64 before; CIs overlap, so read the cross-model consistency, not the deltas). "Have it double-check when it's done" is backwards `[MEDIUM]`.
- **Do not instrument expressed confidence.** Mid-task confidence dropped in 71% of GPT and 97% of Claude runs while barely distinguishing eventual pass from fail (only Claude showed even r=−0.20). Instrument the work, not the narration `[MEDIUM]`.
- **Do not try to prompt it away.** Reward models used for PPO are biased toward high-confidence scores regardless of response quality, and RLHF-tuned models express more overconfidence than their SFT counterparts `[HIGH — peer-reviewed, ICLR 2025]`. The incentive is trained in.

`Why: → ../references/loops-and-stop-conditions.md P4.7`

## Step 3 — Spend your verification budget structurally first

Order your gates by what the evidence says actually catches false success.

1. **Structural gates — run the test, read the artifact, diff the result.** First choice, always. They sidestep both the self-report problem and the knowledge-action gap (agents fail to act on knowledge they possess, including knowing a verification step is warranted). Verification must compare claims against *actual* outputs, never against intended outputs or the agent's narration.
2. **Do not substitute an LLM judge for a structural check.** Measured head-to-head on ~11.8K shared trajectories: no judge configuration out of 5 judges × 5 prompt strategies exceeded **0.65 AUROC** on tau2-bench (0.54 on AppWorld), while cheap TF-IDF trace detectors hit **0.83** and **0.95** — recovering **4–8× more false successes at the same flag rate** and ~3,300× lower latency. The judges keyed on surface completion proxies: confident closing language and action-sequence volume `[CORROBORATED* — workshop paper, FAGEN@ICML 2026, arXiv:2606.09863]`. Scope kept honest: two benchmarks, and the structural arm there is text-derived triage rather than the run-the-test state verification recommended above.
3. **For what structure cannot cover, use independent adversarial critics with majority-kill.** Independent means a *separate* critic node, not the worker grading itself — a generator-critic framework with an auditor veto cut sycophancy 9.6%→1.4% on one model `[CORROBORATED* — single-author preprint, no component ablation]`. Watch the trap: adversarial reframing cut the overconfident-failure rate 72%→45%, but for some models this was a pure threshold shift with **no improvement in discrimination**. Demand better AUROC, not better-looking calibration.
4. **Add evidence-before-assertion contracts as a filter, not a gate.** Requiring each claim to cite a tool result from the current session (cite-then-retract) significantly reduces hallucination but does not eliminate it, per the vendor's own doc `[VENDOR-DOC]`. Never make it the last line of defense.

`Why: → ../references/loops-and-stop-conditions.md P4.7`

## Step 4 — Make every gate emit per-item verdicts `[SYNTHESIS]`

A gate that returns a bare `PASS` is indistinguishable from a gate that ran zero checks — both print success, so a misconfigured or crashed gate reads as a clean run. That is fail-open, the most dangerous shape a check can take.

Require of every gate:

- **A per-item verdict line** — one row per criterion, each with the criterion, the command or artifact inspected, and pass/fail. An overall verdict with no item list is rejected as unreadable, not accepted as passing.
- **An item count**, compared against the expected count. A gate that checked 3 of 9 criteria is a failed gate, not a partial pass.
- **A positive control** — one check known to fail, asserted to fail. If it passes, the harness is not observing the target and every other verdict in the report is void.
- **Unpiped exit status.** Read the gate's own pass/fail line or capture status directly; a status read downstream of a pipe reports the wrong process.

`Why: → ../references/multi-agent.md T5.1`

## Quick reference — failure smell → mechanism

| Smell | Catch it with |
|---|---|
| Loop runs forever, no completion, no error | Hard ceiling (layer 1) + dry-loop guard (layer 4) |
| Output truncated mid-thought at the cap | Model-aware budget (layer 2) alongside the ceiling |
| Loop still spinning at iteration 3, cap is 50 | Dry-loop guard — iteration caps cannot see this |
| Agent declares done, artifact is wrong | Semantic completion gate (layer 3) + structural gate |
| Confident summary, plausible patch, tests fail | Structural gate — run the test; the claim is the symptom |
| Judge approves work a human immediately rejects | Replace judge with structural signal; judges cap near 0.65 AUROC |
| Reviewer agrees with whatever the worker asserted | Independent critic node, majority-kill, refutation framing |
| Gate reports PASS, defects ship anyway | Per-item verdicts + item count + positive control |
| Calibration numbers improved, escapes did not | Measure discrimination (AUROC), not calibration (ECE) |
| Cited evidence present, claim still wrong | Treat citation contracts as a filter; add a structural check |
