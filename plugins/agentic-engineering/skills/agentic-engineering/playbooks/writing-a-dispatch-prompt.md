# Writing a Dispatch Prompt

**Use when:** you are about to hand a subagent or worker a task and its prompt has to carry the whole handoff without you in the loop.

## 1. Fill the contract block before writing any prose

Paste this and fill every line. A blank line is the bug: the orchestrator knows things the worker does not, and silence transmits nothing.

```
OBJECTIVE (one sentence, one deliverable):
OUTPUT FORMAT:               (exact shape — headings, schema, field list)
CONSUMED BY:                 (synthesis context / program / gate — not a human reader)
IN SCOPE:                    (files, dirs, question boundary)
OUT OF SCOPE:                (what to leave alone; who owns it instead)
CONTEXT YOU CANNOT DISCOVER: (decisions already made, exact paths/IDs/names,
                              constraints from earlier turns, what was already tried)
DONE WHEN:                   (verifiable condition, not "when it looks finished")
```

Checks: the objective names one deliverable, not a theme. OUT OF SCOPE is non-empty. Every proper noun the worker needs appears verbatim. If a line is blank because *you* have not decided, decide now — the worker will decide it implicitly instead, and conflicting implicit decisions are the documented failure zone (inter-agent misalignment, 32.3% of multi-agent failures `[HIGH]`).

`DONE WHEN` extends the four documented contract elements with a verifiable exit condition, because "the worker says done" is the weakest exit available.

Why: → ../references/tool-design.md P3.2 (failure category: ../references/multi-agent.md T5.1; exit condition: ../references/loops-and-stop-conditions.md P4.1; prompt-level anatomy: ../references/prompt-mechanics.md P1.1 `[ANECDOTAL]`)

## 2. Spend the first 3–5 constraints on what actually matters

Constraint count does not degrade *compliance* — it degrades the *task*. In the measured sweep, constraint satisfaction stayed near ceiling (>94% average) while task success fell (~84% SustainScore), and most of the damage lands inside the first ~5 constraints `[MEDIUM — arXiv:2601.22047]`. So rank your constraints, keep the top three-to-five load-bearing ones, and delete the self-evident ones the worker's unconstrained output would already satisfy.

- **Format constraints count against the budget.** The sharpest measured conflict is not a semantic twin: −0.531 between a token-count requirement and respond-in-JSON `[HIGH]`. "Return JSON" plus "under 200 words" is a fight, not two instructions.
- **Don't stack opposed pairs** ("avoid X" alongside "use Y"): they degrade each other silently.
- **Grade the deliverable, not the checklist.** A worker that ticks every box while getting the answer wrong is the documented failure mode here, not a hypothetical.

Scope note: 5 is where the damage curve flattens in an eight-model keyword-constraint study, not a licensed ceiling on how many you may write.

Why: → ../references/prompt-mechanics.md T3.2

## 3. Write positive exemplars, not prohibitions

Naming a forbidden token tends to prime it — ~87.5% of "do not say X" violations were priming failures, and restating the prohibition can make it worse (ironic rebound) `[MEDIUM — single model, frontier transfer untested]`. It agrees with settled vendor guidance to show the desired output rather than enumerate bans.

| Replace | With |
|---|---|
| "Don't edit outside `src/`" | "Edit only files under `src/`; list anything else that needs changing" |
| "Don't be verbose" | "Return at most 10 bullets, one line each" |
| "Don't guess" | "Cite the `file:line` you read for each claim" |

Also dial back `CRITICAL: YOU MUST` framing — recent frontier models follow instructions more literally, so language written for older models now overtriggers; plain statements of when something applies work better `[VENDOR-DOC]`.

Why: → ../references/prompt-mechanics.md T3.2

## 4. Pick context depth by decision risk, not by what you have

Full trace or packaged summary: choose by how risky the worker's implicit decisions are. The riskier those decisions, the closer to full-trace you sit. Read-only breadth work (search, audit, survey) runs fine on packaged summaries.

Two guardrails. First, the "share full traces" principle contrasts full traces with passing along *individual messages* — it is not an argument against summarization as such `[ATTRIBUTION]`. Second, do not forward your entire history "just in case": the worker's clean window is the mechanism by which fanning out beats one overstuffed context. Package what the contract needs.

Why: → ../references/multi-agent.md T5.2 (implementation: ../references/tool-design.md P3.2)

## 5. Ask for data, not narration

The worker's output is consumed by a program or a synthesis context, so specify a return shape that parses. Structured returns eliminate a whole parse-failure class `[VENDOR-DOC]`.

If you constrain the return to a schema:

- **Put a free-text `reasoning` field first *and mark it required*.** Generation follows schema order, so answer-before-reasoning forces commitment before thought. On Anthropic, required properties are emitted before optional ones no matter where you declared them — an *optional* `reasoning` field placed first silently lands after the answer and buys nothing `[VENDOR-DOC]`. Nothing errors when this happens, which is why it survives review.
- **Add an explicit `error`/refusal field.** Constrained decoding cannot signal that the input was out of schema; it fills required fields with schema-valid garbage instead.

Why: → ../references/tool-design.md P3.2 and ../references/prompt-mechanics.md T3.3

## 6. Require evidence; keep the verdict on your side

Do not ask the worker to self-assess. Post-completion self-assessment is the weakest moment for calibration, not the strongest (AUROC 0.55 after the work vs 0.64 before; CIs overlap — read the cross-model consistency, not the deltas) `[MEDIUM]`, and over-reporting is directionally biased toward false success — overconfident on 62% of failing tasks against underconfident on 11% of passing ones `[MEDIUM]`. Instead: require each claim to cite a tool result from this session, ask for the command and its literal output, and run the pass/fail judgment in your own gate. Evidence-before-assertion is a filter, not a gate `[VENDOR-DOC]`.

Why: → ../references/loops-and-stop-conditions.md P4.7

## 7. Place it

- **Contract block at the top.** A fresh worker window sits at low occupancy, where primacy bias is intact — the condition frontloading depends on `[MEDIUM]`.
- **Restate only must-survive lines near the end, and only when the prompt is long or the window runs hot.** Repetition is not free: one 2×2 study measured a *negative* interaction (−27.4pp) from putting the same framing in both the system and user slots, and re-injecting a constraint the model already knows does not fix an enforcement-time drop.
- **Match vocabulary to the moment of need.** Lexical overlap with how the worker will encounter the requirement matters more than position; paraphrase-heavy context actively damages retrievability. Repeat IDs, paths, and symbol names verbatim instead of describing them.

Why: → ../references/prompt-mechanics.md T3.1 (the −27.4pp both-slots interaction: T3.2, placement paragraph) and ../references/context-degradation.md T2.2

## Pre-send checklist `[SYNTHESIS]`

- [ ] One sentence, one deliverable, one consumer named
- [ ] OUT OF SCOPE non-empty; every path/ID verbatim
- [ ] ≤5 load-bearing constraints, no format-vs-length conflict
- [ ] Zero prohibitions that could be exemplars
- [ ] Context depth justified by decision risk, not by convenience
- [ ] Return shape parses; `reasoning` first and required; refusal path exists
- [ ] Claims must cite tool output; you hold the verdict
