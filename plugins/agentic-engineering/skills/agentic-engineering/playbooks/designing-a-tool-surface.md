# Designing a Tool Surface

**Use when:** deciding what an agent can call — whether an action deserves a tool, in which transport, with what argument shapes, how big a catalog, and what results look like.

## Step 1 — Default to bash; promote only when the harness needs a hook

Bash gives the agent maximal breadth but gives the *harness* only an opaque command string. Promote an action out of bash when the harness needs an action-specific hook: `[SYNTHESIS]`

| Promote when you need | Why bash can't do it |
|---|---|
| **Gating** (approval before irreversible actions) | `send_email` is gateable; `bash -c "curl -X POST ..."` is indistinguishable from a read |
| **Invariants** (reject an edit if the file changed since read) | Bash can't enforce staleness checks |
| **Rendering** (custom UI, modal interaction) | Opaque strings render as text |
| **Scheduling** (parallel-safe vs serializing calls) | Harness can't tell parallel-safe `grep` from unsafe `git push` |

Rule of thumb: start with bash for breadth; promote when you need to gate, render, audit, or parallelize. No vendor doc states this rule; each mechanism above is observable in shipped harnesses.

Why: → ../references/tool-design.md "Promoting actions to dedicated tools" `[SYNTHESIS]`

## Step 2 — Choose the transport; the label is not the win condition

Headline first: **token-efficient tool design is the win condition, not the transport label** `[CORROBORATED*]`. The same debate produced opposite winners on design quality alone — a well-designed MCP server beat its own CLI twin by 23% on latency over 120 runs (the harness ran a security preflight on every bash call), while the GitHub MCP server burned **1.3×–80× more tokens than `gh`** at identical 100% completion (~400K vs ~5K worst case). Treat that second figure as **n=1**: a single run by the repo's own labeling, 30-run protocol unexecuted, blog and README disagreeing.

| Choose | When |
|---|---|
| **CLI** (agent drives bash) | training-familiar verbs (git, grep, curl); large but sparsely-used surface — CLIs cost ~zero tokens until invoked, and the 1.3–80× gap is mostly schema preloading `[MEDIUM]`; composition pays (Willison has abandoned MCP for coding agents on these grounds `[ATTRIBUTION]`) |
| **MCP / native definitions** | typed structured results (2 calls/7.7s vs the CLI's 8 calls/50.8s of parse-and-retry); permission gating; no shell exists (browser/SaaS/remote); the capability must be *discoverable*; or the surface is small and well-designed |
| **Code execution** (agent scripts the tools) | many tools, few per task; large intermediates that shouldn't traverse context; multi-step control flow |

Gates on code execution: a secure sandbox is non-negotiable and the model must be strong at codegen — AgentArch found function-calling setups tend to outperform freer prompt-driven formats `[MEDIUM]` (scope: ReAct vs function calling, never code execution as a surface). Client risk is separate from the protocol: CVE-2025-6514, a CVSS 9.6 RCE in `mcp-remote`, fires on connecting to an untrusted server. The convergence is a reconciliation, not a winner: keep MCP's structure and auth, load definitions on demand, **route data through code and judgment through the model**; read dramatic percentages (98.7%, 99.9%, 81%) as vendor self-measurement on illustrative workflows.

Why: → ../references/tool-design.md "Tool-surface choice: CLI vs MCP vs code-execution" `[CORROBORATED*]`; "Composing many tool calls: programmatic tool calling" `[VENDOR-DOC]`

## Step 3 — Run the ACI checklist on every definition

A tool definition is UI for a model; give it the design investment a human interface would get `[HIGH — vendor-endorsed practice]`.

- [ ] **Naturally-occurring formats** — prose, markdown, code, shell output, not a bespoke JSON micro-format; training-distribution text costs less capability to parse correctly.
- [ ] **Example usage inside the definition** — a sample call disambiguates argument semantics better than prose constraints alone.
- [ ] **Poka-yoked arguments**, so the easy thing is the correct thing. Canonical case: requiring absolute file paths after agents kept mis-resolving relative ones on SWE-bench — eliminating the error class, not prompting against it.
- [ ] **Trigger conditions in the description** — say *when* to call it (`Call this when the user asks about current prices or recent events`), not only what it does `[VENDOR-DOC]`. Know where the lever sits: descriptions disambiguate *which* tool; the **system prompt** tunes *how eagerly* ("Use the tools to investigate before responding." raises tool use; "Use your judgment about whether to call a tool or respond directly." keeps it conservative). Never chase eagerness inside a description.
- [ ] **Error messages as steering** — `Error: location 'xyz' not found. Provide a valid city name.` with `is_error: true` lets the agent self-correct; stack traces and silent empties produce flailing `[VENDOR-DOC]`.
- [ ] **Namespace** related tools; prefer few high-leverage tools to endpoint mirroring; iterate with the agent in the loop.

Why: → ../references/tool-design.md P3.3

## Step 4 — Budget the catalog before you grow it

- **Measure per-tool cost; don't assume it.** Measured catalogs run **500–1,000 tokens per definition** (~600/tool Sentry, Grafana; ~1,900/tool Slack). The repeated "~300 tokens per tool" is a category error: ~286–315 tokens is the *tool-use system prompt*, billed once per request regardless of tool count (as of 2026-08-08).
- **Degradation onset ~50+ tools, severe at 100+** (practitioner consensus), and model-dependent: LongFuncEval (49→741 tools) measured **7.6%–85.6%**, a range explicitly excluding Mistral-large's 94% collapse; GPT-4o was most robust at 10.6–13.8%. Thresholds tuned on small models are obsolete.
- **Defer loading as the catalog grows.** On-demand, history-conditioned retrieval beat static loading by **23–104% success-rate improvement** (DTDR); vendor benchmarks report 85% token reduction on a 58-tool catalog and ~93% at 508 tools with accuracy maintained; internal evals report **+8 to +25pp**. Keep the metrics distinct — the usable-context rise (122,800 → 191,300 tokens) is a *different* measurement, not the far end of the savings range.
- **Don't extrapolate past tested catalog sizes.** At 2,792 tools: 48% retrieval, 34% end-to-end (Stacklok); at 4,027: 56% regex / 64% BM25 (Arcade). Past vendor scale the constraint moves from *selection* to *retrieval*: if the right tool never surfaces, model quality cannot recover it.

Why: → ../references/tool-design.md "Tool-catalog costs and deferred loading" `[CORROBORATED*]`

Two deferral mechanics: tool search **appends** discovered schemas, preserving the cache prefix; and a two-hop fetch the model must *choose* can be silently skipped — make load-bearing loads hook-injected and loud when skipped `[MEDIUM]`.

Why: → ../references/caching-and-knowledge-delivery.md T6.2

## Step 5 — Pick the serialization for tool *results*

Format is decided by **data shape × the specific model × direction** (data in vs model-generated) `[CORROBORATED*]`.

| Result shape / situation | Serialize as |
|---|---|
| **Multi-turn agentic tool-call loop** | **JSON** — compact formats buy up to 18% fewer tokens at ~9pp accuracy cost, parse failures cascade across turns, parallel tool-call output collapses for most models |
| Flat/uniform tabular → capable model | Compact tabular (TOON/CSV): ~15–65% savings by shape, accuracy-neutral *for single-turn retrieval only* |
| Flat tabular → weak/cheap model | Markdown-Table (Markdown-KV if accuracy is everything): terse *and* familiar — JSON-level accuracy at ~2.6× fewer tokens |
| Nested / heterogeneous / optional fields | Minified JSON (or YAML) — compact formats fail at generating nested shape, and minifying erases most of the gap |
| Model must *generate* the structure | JSON + constrained decoding / structured outputs |
| Genuine tabular *querying* at scale | Don't put it in context — give the agent code/SQL |

JSON is therefore the default for anything flowing through a tool loop; compact-format savings belong to data handed to the model once `[SYNTHESIS]`. Re-measure published savings on the target tokenizer first `[MEDIUM]`.

Why: → ../references/data-formats.md "The selection rule" (P2.3)

## Pre-ship checks `[SYNTHESIS]`

- [ ] Every promoted tool names the harness hook justifying it (Step 1); otherwise demote to bash.
- [ ] Catalog total **measured**, not estimated, checked against the ~50-tool onset — and if deferring, inside the sizes those retrieval numbers cover.
- [ ] Every definition passes Step 3; eagerness routed to the system prompt, not to descriptions.
- [ ] Result format per Step 5 — JSON unless a row says otherwise.
