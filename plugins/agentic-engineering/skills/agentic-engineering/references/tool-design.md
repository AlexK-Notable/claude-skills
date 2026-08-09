# Tool Design and Agent Implementation Patterns

Practice pillar P3. Status: **complete**, verified 2026-06-12, corrections/re-audit applied 2026-08-08 — covers ACI design (P3.3), tool-catalog costs, CLI vs MCP vs code-execution surface choice, and orchestrator-worker implementation (P3.2), resolved via an Opus probe (2026-06-12).

## P3.3 — The agent-computer interface (ACI) `[HIGH — vendor-endorsed practice]`

Core verified principle (Anthropic Dec 2024, expanded Sep 2025 in "Writing effective tools for agents"): **agent-computer interfaces deserve as much design investment as human-computer interfaces.** A tool's definition is UI for a model. Evidence is vendor experience and anecdote, not controlled study — strongly endorsed practice, not quantified theory.

The verified elements, with rationale:

1. **Formats close to naturally occurring text.** Models train on prose, markdown, code, and shell output, not bespoke JSON micro-formats — closer-to-distribution I/O costs less capability to produce and parse.
2. **Example usage inside tool definitions.** Descriptions that show a sample call disambiguate argument semantics better than prose constraints alone.
3. **Poka-yoke (error-proofing) the arguments.** Design argument shapes so the easy thing is correct — e.g., after agents on SWE-bench mis-resolved relative file paths, requiring absolute paths eliminated the error class by schema change, not prompting.
4. **(Sep 2025 expansion)** Prototype → evaluate → iterate on tools with the agent in the loop; **namespace** related tools so selection is structurally guided; prefer a few **high-leverage** tools over exhaustive endpoint mirroring.

Two additions from current vendor docs `[VENDOR-DOC]`:

- **Prescriptive trigger conditions in descriptions.** State *when* to call the tool, not just what it does — `Call this when the user asks about current prices or recent events` narrows the model's decision more than a capability blurb. The lever for trigger *aggressiveness* sits in the system prompt, not the description: `"Use the tools to investigate before responding."` increases tool use; `"Use your judgment about whether to call a tool or respond directly."` keeps it conservative.
- **Error messages are steering.** A tool result of `"Error: location 'xyz' not found. Provide a valid city name."` (with `is_error: true`) lets the agent self-correct; an opaque stack trace or silent empty result produces flailing. Write error strings as instructions to the next attempt.

## Promoting actions to dedicated tools `[SYNTHESIS]`

*Our own framing, not vendor-published — no vendor doc states this rule, though each mechanism below is observable in shipped harnesses.*

A bash tool gives an agent maximal breadth but gives the *harness* only an opaque command string — promote to a dedicated tool when the harness needs an action-specific hook:

| Promote when you need | Why bash can't do it |
|---|---|
| **Gating** (approval before irreversible actions) | `send_email` is gateable; `bash -c "curl -X POST ..."` is not distinguishable from a read |
| **Invariants** (e.g. reject edit if file changed since read) | Bash can't enforce staleness checks |
| **Rendering** (custom UI, modal interactions) | Opaque strings render as text |
| **Scheduling** (parallel-safe vs serializing calls) | Harness can't tell parallel-safe `grep` from unsafe `git push` |

Rule of thumb: **start with bash for breadth; promote when you need to gate, render, audit, or parallelize.**

## P3.2 — Orchestrator-worker implementation `[VENDOR-DOC]`

The verified production shape (Anthropic research system): a lead agent decomposes the task and spawns **3–5 parallel subagents, each with an isolated context window**, then synthesizes their returns. Implementation guidance:

1. **Worker prompts are contracts.** Each dispatch needs a one-sentence objective, output format, IN/OUT scope boundaries, and context the worker can't discover itself. Workers fail along MAST category 2 (misalignment) when these stay implicit — the orchestrator knows things the worker doesn't.
2. **Choose the context-sharing point on the Cognition axis.** Full-trace maximizes alignment at token cost; summaries are cheaper and lossier. Riskier implicit worker decisions warrant sitting closer to full-trace; read-only breadth work suffices with packaged summaries.
3. **Workers return data, not narration.** A worker's output feeds a program or synthesis context, not a human. Structured returns (schemas where the harness supports them) eliminate a parse-failure class.
4. **Single-thread the writes.** Workers gather and propose; one context decides and mutates (see `multi-agent.md` synthesis). Two workers writing together must target different artifacts.
5. **Isolation is the point.** A subagent's clean window is how multi-agent systems beat one overstuffed context (see `context-degradation.md`) — protect it. Don't forward the orchestrator's full history into every worker "just in case"; package what the contract needs.
6. **Match model tier to subtask shape.** The lead/synthesis role concentrates judgment and belongs on the strongest model; mechanical sub-tasks tolerate cheaper tiers. (Production-validated in Anthropic's Opus-lead/Sonnet-workers split. `[MEDIUM]`)

## Composing many tool calls: programmatic tool calling `[VENDOR-DOC]`

When a task chains many tool calls or produces large intermediate results, each round trip through the model costs latency and floods context with data it'll never need again. Currently: the model writes a *script* invoking tools as sandboxed functions; intermediate results flow through code, and only the final output reaches the model's context. Token cost scales with the final output, not the intermediates — the API-level expression of a general principle: **route data through code, judgment through the model.**

## Tool-catalog costs and deferred loading `[CORROBORATED* — probe 2026-06-12]`

The tool-definition context tax now has independent numbers:

- **Large catalogs degrade selection, model-dependently.** LongFuncEval (arXiv:2505.10570, Apr 2025) — first benchmark to isolate catalog size (49→741 tools, 8K→120K tokens) — measured **7.6%–85.6%** accuracy degradation, excluding Mistral-large's 94% collapse. GPT-4o, the most robust model, dropped 10.6–13.8% (three BFCL subsets). Practitioner consensus: degradation onset **~50+ tools**, severe at 100+ — but frontier models tolerate big catalogs far better, so thresholds tuned on small models are obsolete.
- **Per-tool overhead: measure it, don't assume it.** Catalogs run roughly **500–1,000 tokens per tool**: Anthropic's five-server example is 58 tools for ~55K tokens (≈950 average), spanning ~600/tool (Sentry, Grafana) to ~1,900/tool (Slack). The widely repeated "~300 tokens per tool" figure is a category error: ~286–315 tokens is the *tool-use system prompt*, billed once per request regardless of tool count (Anthropic's tool-use pricing table, as of 2026-08-08). Totals scale fast: Anthropic saw **134K tokens before optimization**, and a static 400-tool server measures ~405K tokens before the first query (Speakeasy).
- **Deferred loading fixes both the cost and the accuracy loss.** Academic: on-demand, history-conditioned tool retrieval beat static loading by **23–104% success-rate improvement** (DTDR, arXiv:2512.17052). Vendor benchmarks (interested parties, but consistent): 85% token reduction on that same 58-tool catalog, usable context rising 122,800→191,300 tokens — a *different* metric from the savings percentage, don't merge; ~93% at 508 tools with accuracy maintained; Anthropic-internal tool-search evals report +8 to +25pp accuracy (Opus 4 49→74%, Opus 4.5 79.5→88.1%). Tool search *appends* discovered schemas, preserving the cache prefix (see `caching-and-knowledge-delivery.md`).
- **Past the vendor's catalog sizes, retrieval — not selection — becomes the binding constraint `[CORROBORATED*]`.** Two independent tests of Anthropic's Tool Search Tool, at an order-of-magnitude larger scale: Stacklok measured 48% retrieval accuracy (34% end-to-end selection) over 2,792 tools; Arcade measured 56% (regex) and 64% (BM25) over 4,027 tools across 25 tasks. If the right tool never surfaces in search results, no model quality recovers it — don't extrapolate the +8 to +25pp figures past the catalog sizes measured.

## Tool-surface choice: CLI vs MCP vs code-execution `[CORROBORATED* — probe 2026-06-12]`

**Token-efficient tool design is the actual win condition, not the transport label.** Demonstration cuts both ways: in one reproducible 120-run benchmark, a *well-designed* MCP server beat its own CLI twin by 23% on latency (the harness ran a security preflight on every bash call); in a single-run comparison over five GitHub tasks, the GitHub MCP server used **1.3×–80× more tokens than the `gh` CLI** at identical (100%) completion rates — worst case ~400K tokens through MCP against ~5K through the CLI. Same debate, opposite winners — design quality and task shape, not CLI-vs-MCP. Read the second result as n=1 — its own headline table is a single run, its 30-run paired-Wilcoxon protocol is unexecuted, and its blog and README figures disagree. Magnitudes are indicative, not error-barred.

**Choose a CLI (agent drives bash) when:** the verbs are common and training-familiar (git, grep, curl — the model one-shots them and adapts to variants), the tool surface is large but sparsely used (CLIs cost ~zero tokens until invoked — the measured 1.3–80× gap is mostly schema preloading `[MEDIUM]`), or the workflow benefits from composition (pipes/flags chain without per-step inference round-trips — argued by several senior practitioners, unmeasured). Willison has abandoned MCP entirely for coding agents on these grounds `[ATTRIBUTION]`. Ronacher, often cited alongside him, argues something narrower: collapse a server's thirty bespoke tools into one tool that accepts code, and leave MCP to what it's genuinely good at — session management and a built-in guiding prompt.

**Choose MCP / native tool definitions when:** you need typed, structured results (measured: 2 calls/7.7s vs the CLI's 8 calls/50.8s of parse-and-retry on a structured-retrieval task), permission gating and least-privilege boundaries (declared scopes beat gating arbitrary bash — though the *client* surface carries its own risk: CVE-2025-6514 is a CVSS 9.6 OS-command-injection RCE in the `mcp-remote` client proxy, triggered by connecting to an untrusted server, not a protocol flaw), no shell exists (browser/SaaS/remote contexts), the capability must be *discoverable* (obscure CLIs are invisible; MCP advertises), or the surface is small and well-designed (MCP's preload cost is trivial, its integration wins).

**Choose code-execution (agent writes scripts that call tools) when:** many tools but few needed per task, large intermediates that shouldn't traverse context, or multi-step control flow (loops/filters/branches) over tool calls. Evidence base: foundational CodeAct result (+up to 20% success, ~30% fewer actions vs JSON tool-calling — one 2024 paper's own benchmarks, widely re-cited but unreproduced `[MEDIUM]`); Anthropic's *measured* programmatic-tool-calling numbers (separate measurements, not one composite result): 37% fewer tokens on complex research tasks (43,588→27,297 average), GAIA accuracy 46.5→51.2%, and, per current docs, +11% average on BrowseComp and DeepSearchQA using 24% fewer input tokens `[VENDOR-DOC]`; and the famous "98.7% reduction" from code-execution-with-MCP — **real but example-specific** (one worked Drive→Salesforce flow, 150K→2K tokens), directionally corroborated by Cloudflare's independent Code Mode architecture, not a general benchmark. Hard gates: a secure sandbox is non-negotiable (vendor's own caveat), the model must be strong at codegen (CodeAct's gains concentrate in capable models), and counter-evidence exists that structured function calling beats freer, prompt-driven formats on reliability (AgentArch, arXiv:2509.10769: across 18 enterprise configurations, function-calling tends to outperform ReAct, and no model peaks under multi-agent ReAct — scope note: it contrasts ReAct prompting against native function calling, never code execution as a surface `[MEDIUM]`).

**The 2025–26 convergence** is a reconciliation, not a winner: keep MCP's structure and auth, but load definitions on demand (tool search / filesystem-based discovery) and route intermediates through code instead of context. Treat every dramatic token percentage here (98.7%, 99.9%, 81%) as a vendor self-measurement on an illustrative workflow — directionally corroborated across vendors, never benchmarked against each other.
