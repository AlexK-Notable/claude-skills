# Tool Design and Agent Implementation Patterns

Practice pillar P3. Status: **complete** — ACI design (P3.3), tool-catalog costs, CLI vs MCP vs code-execution surface choice, and orchestrator-worker implementation (P3.2). The CLI/MCP/code-execution comparison was resolved by an Opus probe (2026-06-12).

## P3.3 — The agent-computer interface (ACI) `[HIGH — vendor-endorsed practice]`

Core verified principle (Anthropic Dec 2024, expanded Sep 2025 in "Writing effective tools for agents"; treated as accepted practice in community ADRs): **agent-computer interfaces deserve as much design investment as human-computer interfaces.** A tool's definition is UI for a model. Present this as strongly endorsed practice, not quantified theory — the evidence is vendor experience and anecdote, not controlled study.

The verified elements, with rationale:

1. **Formats close to naturally occurring text.** Models have spent training on prose, markdown, code, and shell output — not on bespoke JSON micro-formats. Tool inputs and outputs that resemble training-distribution text cost less capability to produce and parse correctly.
2. **Example usage inside tool definitions.** Descriptions that show a sample call disambiguate argument semantics better than prose constraints alone.
3. **Poka-yoke (error-proofing) the arguments.** Design argument shapes so the easy thing is the correct thing. Canonical case: requiring absolute file paths after observing agents repeatedly mis-resolving relative paths on SWE-bench — the schema change eliminated the error class rather than prompting against it.
4. **(Sep 2025 expansion)** Prototype → evaluate → iterate on tools with the agent in the loop; **namespace** related tools so selection is structurally guided; prefer a few **high-leverage** tools over exhaustive endpoint mirroring.

Two additions from current vendor docs `[VENDOR-DOC]`:

- **Prescriptive trigger conditions in descriptions.** State *when* to call the tool, not only what it does ("Call this when the user asks about current prices or recent events"). On recent frontier models, which reach for tools more conservatively, trigger conditions in the description measurably lift should-call rates.
- **Error messages are steering.** A tool result of `"Error: location 'xyz' not found. Provide a valid city name."` (with `is_error: true`) lets the agent self-correct; an opaque stack trace or silent empty result produces flailing. Write error strings as instructions to the next attempt.

## Promoting actions to dedicated tools `[VENDOR-DOC]`

A bash tool gives an agent maximal breadth but gives the *harness* only an opaque command string. Promote an action from bash to a dedicated tool when the harness needs an action-specific hook:

| Promote when you need | Why bash can't do it |
|---|---|
| **Gating** (approval before irreversible actions) | `send_email` is gateable; `bash -c "curl -X POST ..."` is not distinguishable from a read |
| **Invariants** (e.g. reject edit if file changed since read) | Bash can't enforce staleness checks |
| **Rendering** (custom UI, modal interactions) | Opaque strings render as text |
| **Scheduling** (parallel-safe vs serializing calls) | Harness can't tell parallel-safe `grep` from unsafe `git push` |

Rule of thumb: **start with bash for breadth; promote when you need to gate, render, audit, or parallelize.**

## P3.2 — Orchestrator-worker implementation `[HIGH + VENDOR-DOC]`

The verified production shape (Anthropic research system): a lead agent decomposes the task and spawns **3–5 parallel subagents, each with an isolated context window**, then synthesizes their returns. Implementation guidance derived from the verified findings and failure taxonomy:

1. **Worker prompts are contracts.** Each dispatch needs: a one-sentence objective, the expected output format, explicit scope boundaries (what is IN and OUT), and the context the worker cannot discover itself. Workers fail along MAST category 2 (misalignment) when these are implicit — the orchestrator knows things the worker doesn't, and silence transmits nothing.
2. **Choose the context-sharing point on the Cognition axis deliberately.** Full-trace sharing maximizes alignment at token cost; summaries are cheaper and lossier. The riskier the implicit decisions a worker might make, the closer to full-trace you should sit. For read-only breadth work, packaged summaries usually suffice.
3. **Workers return data, not narration.** A worker's final output is consumed by a program or a synthesis context, not a human. Structured returns (schemas where the harness supports them) eliminate a parse-failure class.
4. **Single-thread the writes.** Workers gather and propose; one context decides and mutates (see `multi-agent.md` synthesis). If two workers must both write, they must not write to the same artifact.
5. **Isolation is the point.** A subagent's clean window is the mechanism by which multi-agent systems beat one overstuffed context (see `context-degradation.md`) — protect it. Don't forward the orchestrator's full history into every worker "just in case"; package what the contract needs.
6. **Match model tier to subtask shape**, with the caveat that the lead/synthesis role concentrates the judgment and belongs on the strongest model; mechanical sub-tasks tolerate cheaper tiers. (Production-validated in Anthropic's Opus-lead/Sonnet-workers split. `[MEDIUM]`)

## Composing many tool calls: programmatic tool calling `[VENDOR-DOC]`

When a task chains many tool calls or produces large intermediate results, each round trip through the model costs latency and floods context with data the model never needs again. Current platform support: the model writes a *script* that invokes tools as functions inside a sandbox; intermediate results flow through code, and only the final output returns to the model's context. Token cost scales with the final output, not the intermediates. This is the API-level expression of a general principle: **route data through code, judgment through the model.**

## Tool-catalog costs and deferred loading `[CORROBORATED* — probe 2026-06-12]`

The tool-definition context tax, previously a zero-evidence gap, now has independent numbers (single-verifier probe; below full panel verification):

- **Large catalogs degrade selection, model-dependently.** LongFuncEval (arXiv:2505.10570, Apr 2025) — the first benchmark isolating catalog size (49→741 tools, 8K→120K tokens of definitions) — measured accuracy degradation ranging **7.6% (GPT-4o, best case) to 85.6%** (smaller/older models). Practitioner consensus puts measurable degradation onset around **~50+ tools**, severe at 100+. The spread matters: frontier models tolerate big catalogs far better, so thresholds tuned on small models are obsolete.
- **Per-tool overhead:** rough industry consensus ~280–320 tokens per typical definition; published figures range 550–1,400 (methodology untraceable) and pathological cases exist (one 135-tool MCP server ≈ 125K tokens of definitions). Treat per-tool cost as something to *measure on your catalog*, not assume.
- **Deferred loading fixes both the cost and the accuracy loss.** Academic: on-demand, history-conditioned tool retrieval beat static loading by **23–104% success-rate improvement** (DTDR, arXiv:2512.17052). Vendor benchmarks (interested parties, but consistent): 85–95% token savings at 78 tools; ~93% at 508 tools with accuracy maintained; Anthropic-internal tool-search evals report +8 to +25pp accuracy. Mechanically, tool search *appends* discovered schemas, preserving the cache prefix (see `caching-and-knowledge-delivery.md`).

## Tool-surface choice: CLI vs MCP vs code-execution `[CORROBORATED* — probe 2026-06-12]`

The honest headline first: **token-efficient tool design is the actual win condition, not the transport label.** The cleanest demonstration cuts both ways — in one reproducible 120-run benchmark, a *well-designed* MCP server beat its own CLI twin by 23% on latency (the harness ran a security preflight on every bash call); in another rigorous benchmark (30 runs/task, paired statistics), the GitHub MCP server used **1.3×–80× more tokens than the `gh` CLI** for identical tasks at identical completion rates (worst case: ~5K vs ~400K tokens). Same debate, opposite winners — because the variable was design quality and task shape, not CLI-vs-MCP.

**Choose a CLI (agent drives bash) when:** the verbs are common and training-familiar (git, grep, curl — the model one-shots them and adapts to variants), the tool surface is large but sparsely used (CLIs cost ~zero tokens until invoked — the measured 1.3–80× gap is mostly schema preloading `[HIGH]`), or the workflow benefits from composition (pipes/flags chain without per-step inference round-trips — well-argued by multiple senior practitioners, unmeasured). Prominent practitioners have abandoned MCP entirely for coding agents on these grounds (Willison, Ronacher) `[ATTRIBUTION]`.

**Choose MCP / native tool definitions when:** you need typed, structured results (measured: 2 calls/7.7s vs the CLI's 8 calls/50.8s of parse-and-retry on a structured-retrieval task), permission gating and least-privilege boundaries (declared scopes beat gating arbitrary bash — though MCP is itself an attack surface; see CVE-2025-6514), no shell exists (browser/SaaS/remote contexts), the capability must be *discoverable* (obscure CLIs are invisible; MCP advertises), or the surface is small and well-designed (where MCP's preload cost is trivial and its integration wins).

**Choose code-execution (agent writes scripts that call tools) when:** many tools but few needed per task, large intermediates that shouldn't traverse context, or multi-step control flow (loops/filters/branches) over tool calls. Evidence base: foundational CodeAct result (+up to 20% success, ~30% fewer actions vs JSON tool-calling — one 2024 paper's own benchmarks, widely re-cited but not independently reproduced `[MEDIUM]`); Anthropic's *measured* programmatic-tool-calling numbers (37% token reduction with accuracy gains on GAIA) `[VENDOR-ONLY]`; and the famous "98.7% reduction" from code-execution-with-MCP — **real but example-specific** (one worked Drive→Salesforce flow, 150K→2K tokens), corroborated in *direction* by Cloudflare's independent convergent Code Mode architecture, not a general benchmark. Hard gates: a secure sandbox is non-negotiable (vendor's own caveat), the model must be strong at codegen (CodeAct's gains concentrate in capable models), and counter-evidence exists that structured function-calling beats freer agentic formats on reliability (AgentArch: higher loop-failure and hallucination rates in less-structured settings `[HIGH]`).

**The 2025–26 convergence** is a reconciliation, not a winner: keep MCP's structure and auth, but load definitions on demand (tool search / filesystem-based discovery) and route intermediates through code instead of context. Treat every dramatic token percentage in this space (98.7%, 99.9%, 81%) as a vendor self-measurement on an illustrative workflow — directionally corroborated across vendors, never benchmarked against each other.
