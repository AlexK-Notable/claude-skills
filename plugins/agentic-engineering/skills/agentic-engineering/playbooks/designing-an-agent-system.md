# Designing an Agent System

**Use when:** deciding whether a task needs a coded workflow, one agent, or many — and what shape the many take — before any prompt or tool is written.

## Step 0 — Write the task shape down

One line each. Every gate below reads from these answers, not from intuition. `[SYNTHESIS]`

- **Deliverable** — what artifact ends the run, and who consumes it (human, program, another context)?
- **Path** — can you enumerate the steps up front, or does step N depend on what step N−1 found?
- **Direction** — read-dominant (gather, explore, review, audit) or write-dominant (edits to shared state)?
- **Depth** — does each conclusion depend on the previous one (sequential depth-reasoning), or do sub-answers combine only at the end (breadth-first)?
- **Stakes** — value per successful run; cost of an error; how fast an error surfaces.

## Step 1 — Workflow, or agent?

| | Workflow | Agent |
|---|---|---|
| Control flow | predefined code paths; model fills in steps | model dynamically directs its own process and tool use |
| You get | predictability, bounded cost, inspectability | tasks you could not enumerate in advance |
| Fits | Path enumerable, Depth known | step count unpredictable, no hardcodable path |

Default to the **simplest viable design**: for many applications, optimizing single LLM calls with retrieval and in-context examples is enough. Moving rightward on the workflow→agent spectrum is a trade, not an upgrade. `[VENDOR-DOC]`

**Gate — all four Zhang adoption checks must pass before you commit to an agent:**

1. **Complexity** — is the decision space genuinely ambiguous, or can you enumerate the tree? Enumerable → workflow.
2. **Value** — does the task justify exploratory token spend *plus* the eval and monitoring that autonomy demands?
3. **Critical capabilities** — can the model do *every* essential step at acceptable accuracy, latency, and cost? One fatal bottleneck sinks the whole loop.
4. **Cost of errors** — how expensive, and how quickly discovered? Both bad → constrain autonomy (read-only scopes, human checkpoints) rather than trusting the loop.

Note before Step 2: orchestrator-workers is classified by the original taxonomy as a *workflow* — the subtasks are chosen dynamically by the orchestrator, but the run's shape (decompose → delegate → synthesize) is fixed. Fixed topology, dynamic content. Picking it is not picking "agent."

Why: → ../references/foundations.md T1.1

## Step 2 — Single agent, or many?

The burden of proof is always on adding agents. Go multi only when **all four** hold:

- [ ] Subtasks are **breadth-first, read-dominant, and genuinely parallelizable** — not tightly coupled edits to shared state, and not sequential depth-reasoning.
- [ ] Task value justifies roughly an order-of-magnitude token premium.
- [ ] Subtask outputs can be **verified or synthesized by a single downstream context** (MAST category-3 protection).
- [ ] Workers can be given **sufficient context** — full traces or careful packaging — to avoid implicit-decision divergence (category-2 protection).

Any box unchecked → single agent with a curated context, or a coded workflow.

**Price of entry:** agents run ~4× chat tokens, multi-agent ~15×; the vendor gates it explicitly on task value being high enough to pay for it. Read multi-agent first as a mechanism for scaling token spend past one window. `[MEDIUM — vendor-internal]`

**Discriminators are task shape and architecture quality, not agent count:**

| Signal | Read it as |
|---|---|
| Sequential depth-reasoning, text-only multi-hop | Expect a **single-agent edge**: at equal thinking-token budgets single agents are best or statistically tied at every budget but a degenerate 100-token one, with a Data Processing Inequality basis `[HIGH]` |
| Homogeneous workers (same base LLM, differing only by prompt, tools, graph position) | You are paying coordination overhead to simulate a multi-turn conversation a single agent already has — plus you lose KV-cache reuse `[CORROBORATED*]` |
| Architecture assembled automatically or by accretion | Auto-generated multi-agent systems underperform chain-of-thought with self-consistency at up to 10× cost; expert-architected ones win on both axes `[CORROBORATED*]` |
| No centralized coordination/verification | The −70.0% end of the observed +80.8%/−70.0% range is sequential planning under *independent* coordination, where nothing reconciles divergent world states `[MEDIUM]` |
| Breadth-first parallel research, extra spend acceptable | The 90.2% orchestrator-worker win lives here — internal vendor eval, undisclosed metric, ~15× tokens `[MEDIUM]` |

Before believing any multi-agent win, including your own pilot: **equalize budgets**. An unequal-budget comparison measures spend, not architecture.

Why: → ../references/multi-agent.md P3.1, T4.1 (equal-budget evidence), T5.2

## Step 3 — If multi: build the orchestrator-worker shape

1. **Parallelize reads, single-thread writes.** Fan out for gathering, exploring, reviewing, verifying — where worker output is *input to a synthesis*. One context decides and mutates. If two workers must both write, they must not write the same artifact.
2. **3–5 parallel workers, each with an isolated context window**, results synthesized by the lead. `[VENDOR-DOC]`
3. **Isolation is the point, so protect it.** A clean window is the mechanism by which multi-agent beats one overstuffed context; do not forward the orchestrator's full history "just in case" — package what the contract needs.
4. **Verify centrally and structurally.** Nothing enters the synthesis on a worker's say-so: run the test, read the artifact, diff the result. Agent self-report is directionally biased toward false success `[MEDIUM]`, and rhetorical judging loses to structural signal measured on the same traces `[CORROBORATED*]`. (Both: ../references/loops-and-stop-conditions.md P4.7)
5. **Workers return data, not narration** — structured returns kill a parse-failure class.
6. **Match model tier to subtask**; the lead/synthesis role concentrates judgment and belongs on the strongest model.
7. **Write the worker contracts** — objective, output format, IN/OUT scope, undiscoverable context: → ./writing-a-dispatch-prompt.md

Why: → ../references/tool-design.md P3.2

## Step 4 — Triage failures by MAST category *before* proposing fixes

| Category | Looks like | Fix in | Not fixed by |
|---|---|---|---|
| **1. System design** (~44%, the largest) | flawed specs, role/responsibility confusion, broken termination logic — baked in before any message is exchanged | specs, roles, topology, stop conditions | prompt wording |
| **2. Inter-agent misalignment** (32.3%) | divergent task understanding, withheld/distorted context, conflicting implicit decisions | sharing fuller context (full traces over lone messages), or removing parallelism over shared state | more workers |
| **3. Task verification** | unverified work accepted, premature success declarations, weak checking | structural gates on actual output | asking the agent to double-check itself — post-hoc self-assessment does not improve discrimination (../references/loops-and-stop-conditions.md P4.7) |

`[HIGH — peer-reviewed]` for the taxonomy. Classify first: a category-1 failure re-prompted as if it were category-2 just costs another run.

Why: → ../references/multi-agent.md T5.1, ../references/foundations.md T1.3
