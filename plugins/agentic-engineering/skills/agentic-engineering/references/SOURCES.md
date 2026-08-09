# Sources & Evidence Ledger

The bibliography behind this skill, plus the full provenance of how each claim was verified.

Every arXiv ID cited anywhere in the eight reference files has a row here, grouped by the file that
cites it, with the evidence label it carries at that site. The reference files carry almost no URLs of
their own — a handful of Sources lines added in the 2026-08-08 correction pass are the exception — so
this file remains the primary link surface. Bibliographic metadata (title, first author, venue) was read off
the arXiv abstract pages on 2026-08-08; venues are recorded only where a source states one.

## How this skill was produced

The reference files were not hand-written from a reading list — they were synthesized from an
**adversarial deep-research pipeline** (Claude Code `Workflow` runs, 2026-06-12/13). Per claim:
**search** → **fetch + extract falsifiable claims** → **3-vote adversarial refutation panel** →
**synthesize with a confidence label**. Pass 1 (`wf_dcee7f5f-ff0`): 22 sources → 109 claims → 25
adversarially verified → **24 confirmed, 1 refuted**. Follow-up targeted batches added the
trust-calibration and instruction-following findings (`wf_59b6e5e3-c63`) and a set of
single-verifier corroboration probes.

**What that pipeline actually covered.** Only claims labelled `[HIGH]` or `[MEDIUM]` went through a
3-vote panel; `[CORROBORATED*]` claims were checked by a single verifier with no panel; `[VENDOR-DOC]`
and `[ATTRIBUTION]` items were checked for accurate transcription, not for truth. The corpus-level
phrasing this ledger used to carry — that every claim survived a 3-vote refutation panel — was
never true of the whole corpus, and is exactly the unverified success claim the trust-calibration
chapter warns about. Read the per-section labels; they were always the accurate account.

**2026-08-08 — independent re-audit.** Nine independent Opus agents (one per reference file plus this
ledger) re-verified every substantive claim against primary sources re-fetched from scratch, checked
each evidence label against the rubric below, and swept for supersession since the June stamp. No
fabricated citations were found: all arXiv IDs and vendor links resolve, and quoted *figures*
reproduced near-perfectly. What did not hold up was **compression**: roughly 85 corrections, clustered
as source misreadings and glosses that inverted their source (~20 critical, including two invented
quotations), systematic label inflation, undated staleness in pricing and live-repo figures, and six
or more relevant papers published *before* the June stamp that the original pass missed — one of which
falsified a stated caveat and one of which answered a declared open question. All corrections were
applied to the eight reference files on branch `corpus-audit` on 2026-08-08; this ledger was rebuilt
against the corrected files, not against the audit's snapshot of the old state. Full report:
`~/notes/agentic-engineering-research/audit-2026-08-08-fact-check.md`.

Full provenance lives in two places:

- **Curated** — znote project **`agent-engineering-guide`**: **25 notes — 23 atomic findings, plus the
  research hub and the refuted-claims ledger** (each finding = Claim → Evidence → Caveats → Source).
  Query: `zk_list_notes mode=by_project project=agent-engineering-guide`, files at
  `~/repos/znotes/agent-engineering-guide/`.
- **Raw** — transcript + fetched-source archive at `~/notes/agentic-engineering-research/`
  (`transcripts.tar.xz`: the orchestrating session, 6 workflow runs, 227 subagent transcripts,
  and the downloaded source PDFs), alongside the 2026-08-08 audit report.

## Evidence labels

Same scale used throughout the reference files:

- `[HIGH]` — verified against primary sources; ≥2 independent sources or peer review, and (for labels
  assigned in the June 2026 pass) survived a 3-vote refutation panel
- `[MEDIUM]` — verified but single-source, vendor-internal, preprint, or tested only on older/open models
- `[CORROBORATED*]` — confirmed by a single-verifier research probe (sources checked, no adversarial panel)
- `[VENDOR-DOC]` — official platform documentation (authoritative for mechanics, not effectiveness)
- `[ATTRIBUTION]` — accurately attributed position statement, not an empirical finding
- `[SYNTHESIS]` — corpus-original framework or inference; no external source claims it. Judge it on the
  reasoning shown, not on provenance, and never cite it as though a vendor or paper said it.
- `[ANECDOTAL]` — locally validated in practice but not externally corroborated. Defined here for use
  by later passes; no section carries it yet.

Two status markers are not confidence labels: `[PENDING]` (section awaiting a research pass — treat any
content as provisional) and `[HELD BACK]` (content deliberately withheld per source policy, not a gap).

**As-of convention.** Figures quoted from live sources — provider pricing tables and TTLs, repo READMEs
and version numbers, preprint numbers that move between revisions — carry an **as of YYYY-MM-DD** date at
the point of use and must be re-checked before anything depends on them. An undated live-source figure
is expired by default. The economics table in `caching-and-knowledge-delivery.md` is the
highest-drift content in the corpus; TOON's spec version moved twice in the two months between the June
probe and this audit.

## Bibliography

**Coverage as of 2026-08-08:** 53 unique arXiv IDs are cited across the eight reference files; all 53
have a row below. Ten further papers are cited by name without an ID in the prose (MAST, NoLiMa, RULER,
HELMET, LongMemEval, Levy et al., CodeAct, Let Me Speak Freely, the JetBrains masking paper, and Liu et
al.) and are given rows with their IDs restored — 63 arXiv rows in total, plus the named non-arXiv
sources. Where a source is cited in two files, it appears once, filed under its primary site, with both
citation sites listed.

### foundations.md

| Source | Link | Cited at | Label there |
|---|---|---|---|
| Anthropic — **Building Effective Agents** (Dec 2024) | <https://www.anthropic.com/engineering/building-effective-agents> (the `/research/` path 301s here) | T1.1; also `tool-design.md` P3.2/P3.3 and `loops-and-stop-conditions.md` P4.1 | `[VENDOR-DOC]` |
| Anthropic — **Effective context engineering for AI agents** (Sep 2025) | <https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents> | T1.1, T1.2; also `caching-and-knowledge-delivery.md` P2.1 (JIT guidance) | `[VENDOR-DOC]` |
| Barry Zhang — **How We Build Effective Agents**, AI Engineer Summit 2025 (talk, New York) | <https://www.youtube.com/watch?v=D7_ipDqhtwk> | T1.1 (the four-check adoption checklist — *not* in the Dec 2024 post) | `[VENDOR-DOC]` |
| Cognition — **Don't Build Multi-Agents** (Jun 2025) | <https://cognition.com/blog/dont-build-multi-agents> (cognition.ai 301s to cognition.com) | T1.2; primary treatment in `multi-agent.md` T5.2 | `[ATTRIBUTION]` |

T1.3 is a `[SYNTHESIS]` section: it argues from results sourced in `context-degradation.md` (T2.1, T2.5)
and `multi-agent.md` (T5.1/MAST) rather than from a source of its own.

### context-degradation.md

| Source | ID · link | Cited at | Label there |
|---|---|---|---|
| **ATLAS: All-round Testing of Long-context Abilities across Scales** — Huang et al. (18 authors); preprint | arXiv:2605.28079 · <https://arxiv.org/abs/2605.28079> | header (the mid-2026 frontier profile that retired the old no-study-measures-mid-2026-models caveat) | `[CORROBORATED*]` |
| **Chroma "Context Rot"** — non-uniform degradation across 18 models (vendor technical report, Jul 2025) | <https://www.trychroma.com/research/context-rot> (research.trychroma.com 301s here) | T2.1, T2.5; also `caching-and-knowledge-delivery.md` P2.1 | `[HIGH]` (T2.1) / `[HIGH, family-rankings MEDIUM]` (T2.5) |
| **NoLiMa: Long-Context Evaluation Beyond Literal Matching** — Modarressi et al. (LMU Munich + Adobe Research); ICML 2025 | arXiv:2502.05167 · <https://arxiv.org/abs/2502.05167> · code <https://github.com/adobe-research/NoLiMa> | T2.2 (mechanism 1), T2.5 (keyword-distractor ablation) | `[HIGH for measurements, MEDIUM for mechanism attribution]` |
| **Logit-Contribution Scoring Identifies Non-Literal Retrieval Heads** (LOCOS) — Gema et al.; preprint | arXiv:2607.01002 · <https://arxiv.org/abs/2607.01002> | T2.2 mechanism 1 (head-level localization) | `[CORROBORATED*]` |
| **Lost in the Middle at Birth: An Exact Theory of Transformer Position Bias** — Chowdhury (single author); preprint | arXiv:2603.10123 · <https://arxiv.org/abs/2603.10123> | T2.2 mechanism 2 (U-shape present at initialization) | `[MEDIUM]` |
| **Context Length Alone Hurts LLM Performance Despite Perfect Retrieval** — Du et al.; Findings of EMNLP 2025 | arXiv:2510.05381 · <https://arxiv.org/abs/2510.05381> | T2.2 mechanism 3 (13.9–85% degradation at held-constant retrieval) | section `[HIGH for measurements]` |
| **Same Task, More Tokens** — Levy, Jacoby, Goldberg; ACL 2024 | arXiv:2402.14848 · <https://arxiv.org/abs/2402.14848> | T2.2 mechanism 3 (0.92 → 0.68 by ~3,000 tokens); T2.5 (unrelated vs in-domain padding) | section labels |
| **Positional Biases Shift as Inputs Approach Context Window Limits** — Veseli, Chibane, Toneva, Koller (Saarland / MPI-SWS); COLM 2025 | arXiv:2508.07479 · <https://arxiv.org/abs/2508.07479> | T2.3 — revises the *finding* of Liu et al. (below); it is a different paper by a different group, not a revision of that paper | `[MEDIUM]` |
| **Lost in the Middle: How Language Models Use Long Contexts** — Liu et al.; TACL 2023 | arXiv:2307.03172 · <https://arxiv.org/abs/2307.03172> | origin of the U-shape result that T2.3 revises (referred to in prose as "The 2023/24 lost-in-the-middle finding") | historical |
| **RULER: What's the Real Context Size of Your Long-Context Language Models?** — Hsieh et al. (NVIDIA); COLM 2024 | arXiv:2404.06654 · <https://arxiv.org/abs/2404.06654> | T2.4 (claimed-vs-effective gap); T2.5 (multi-key distractor variants) | `[HIGH, historical]` |
| **HELMET: How to Evaluate Long-Context Language Models Effectively and Thoroughly** — Yen et al.; ICLR 2025 | arXiv:2410.02694 · <https://arxiv.org/abs/2410.02694> | T2.4 — sharpens RULER's *average score*, retains its harder distractor variants | `[HIGH, historical]` (section) |
| **Distractor-Aware Truncation** — Arjmandi (single author); preprint | arXiv:2608.03297 · <https://arxiv.org/abs/2608.03297> | T2.5 point 1 (naive middle-removal deletes the answer, not just context) | `[CORROBORATED*]` |
| **Not All Needles Are Found** (anti-hallucination prompt "safety tax") — Ebrahimzadeh & Salili; FAGEN Workshop @ ICML 2026 | arXiv:2601.02023 · <https://arxiv.org/abs/2601.02023> | T2.5 point 3 | `[CORROBORATED*]` |
| **Diagnosing and Mitigating Context Rot in Long-horizon Search** — Xia et al.; preprint | arXiv:2606.29718 · <https://arxiv.org/abs/2606.29718> | T2.5 point 4 (premature termination rises with context length) | `[CORROBORATED*]` |

### multi-agent.md

| Source | ID · link | Cited at | Label there |
|---|---|---|---|
| **Why Do Multi-Agent LLM Systems Fail?** (MAST) — Cemri et al. (13 authors); NeurIPS 2025 Datasets & Benchmarks Track (spotlight) | arXiv:2503.13657 · <https://arxiv.org/abs/2503.13657> | T5.1; the 32.3% inter-agent-misalignment figure also anchors T5.2 and `foundations.md` T1.3 | `[HIGH — peer-reviewed]` |
| Anthropic — **Multi-Agent Research System** | <https://www.anthropic.com/engineering/multi-agent-research-system> | T5.2 (90.2% internal eval), T4.1 (4×/15× token economics) | `[MEDIUM]` / `[MEDIUM — vendor-internal]` |
| Cognition — **Don't Build Multi-Agents** (Jun 2025) | <https://cognition.com/blog/dont-build-multi-agents> | T5.2 antithesis | `[ATTRIBUTION]` |
| Cognition — **Multi-Agents: What's Actually Working** | <https://cognition.com/blog/multi-agents-working> | T5.2 synthesis (manager-Devin / child-Devins; *map-reduce-and-manage*) | `[ATTRIBUTION]` (section `[MEDIUM]`) |
| Anthropic — **Eval Awareness / BrowseComp** | <https://www.anthropic.com/engineering/eval-awareness-browsecomp> | T4.1 directional footnote (86.81 → 86.57 after scrubbing) | `[MEDIUM — vendor-internal]` |
| **Single-Agent LLMs Outperform Multi-Agent Systems on Multi-Hop Reasoning Under Equal Thinking Token Budgets** — Tran & Kiela; preprint | arXiv:2604.02460 · <https://arxiv.org/abs/2604.02460> | equal-budget evidence (primary; verified in-paper, not via probe) | `[HIGH]` |
| **Rethinking the Value of Multi-Agent Workflow: A Strong Single Agent Baseline** — Xu et al.; preprint | arXiv:2601.12307 · <https://arxiv.org/abs/2601.12307> | equal-budget replication 1 | `[CORROBORATED*]` |
| **The Illusion of Multi-Agent Advantage** — Jwalapuram et al.; preprint | arXiv:2606.13003 · <https://arxiv.org/abs/2606.13003> | equal-budget replication 2 (auto-generated vs expert-architected) | `[CORROBORATED*]` |
| **Towards a Science of Scaling Agent Systems** — Kim et al. (20 authors); preprint | arXiv:2512.08296 · <https://arxiv.org/abs/2512.08296> | equal-budget counter-nuance (+80.8% Finance Agent / centralized; −70.0% PlanCraft / independent — both in the abstract) | `[MEDIUM]` |
| **Multi-Agent Reasoning Improves Compute Efficiency: Pareto-Optimal Test-Time Scaling** — Wunderlich et al.; ACL 2026 Student Research Workshop (long paper) | arXiv:2605.01566 · <https://arxiv.org/abs/2605.01566> | equal-budget sign flip (+1.3 / +2.7pp on MMLU-Pro, BBH) | `[CORROBORATED*]` |
| Anthropic — **A harness for every task: dynamic workflows in Claude Code** (Jun 2, 2026) | <https://claude.com/blog/a-harness-for-every-task-dynamic-workflows-in-claude-code> | A2A footnote — the orchestrator-mediated verdict's cleanest illustration | `[CORROBORATED* — probe 2026-06-12]` (section) |
| Linux Foundation — **formation of the Agentic AI Foundation** (Dec 9, 2025) | <https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation> | A2A footnote (AAIF hosts MCP, goose, AGENTS.md; agentgateway added Jun 2026) | section |
| Linux Foundation — **Agent2Agent Protocol Project launch** (Jun 23, 2025) | <https://www.linuxfoundation.org/press/linux-foundation-launches-the-agent2agent-protocol-project-to-enable-secure-intelligent-communication-between-ai-agents> | A2A footnote — A2A is a *separate* LF project, never folded into AAIF | section |
| AAIF — **project proposals** (AAIF membership for A2A is an open proposal, #37) | <https://github.com/aaif/project-proposals> | A2A footnote | section |
| LangChain — **A2A server endpoint** (`/a2a/{assistant_id}`) | <https://docs.langchain.com/langsmith/server-a2a> | A2A footnote — the first-party SDK support that falsifies the claim that no major SDK ships A2A | section |

The decision framework (P3.1) is labelled `[HIGH/MEDIUM synthesis]`: it composes the equal-budget,
MAST and economics rows above into a rule none of them states.

### tool-design.md

| Source | ID · link | Cited at | Label there |
|---|---|---|---|
| Anthropic — **Building Effective Agents**; **Writing effective tools for agents** (Sep 2025) | <https://www.anthropic.com/engineering/writing-tools-for-agents> | P3.3 (ACI principles); P3.2 (orchestrator-worker shape) | `[HIGH — vendor-endorsed practice]` / `[VENDOR-DOC]` |
| Anthropic — **advanced tool use** (tool search, programmatic tool calling) | <https://www.anthropic.com/engineering/advanced-tool-use> · docs <https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool> | tool-catalog costs (134K-token catalogs, 85% reduction at 58 tools, +8–25pp evals); programmatic tool calling | `[CORROBORATED*]` / `[VENDOR-DOC]` |
| **LongFuncEval** — Kate et al.; preprint | arXiv:2505.10570 · <https://arxiv.org/abs/2505.10570> | tool-catalog costs (7.6–85.6% degradation excluding Mistral-large's 94% collapse; GPT-4o 10.6–13.8%) | `[CORROBORATED* — probe 2026-06-12]` |
| **Dynamic Tool Dependency Retrieval for Lightweight Function Calling** (DTDR) — Patel et al.; preprint | arXiv:2512.17052 · <https://arxiv.org/abs/2512.17052> | deferred loading (23–104% success-rate improvement); also `caching-and-knowledge-delivery.md` T6.2 | `[CORROBORATED*]` |
| Speakeasy — **dynamic toolsets / 100× token reduction** | <https://www.speakeasy.com/blog/how-we-reduced-token-usage-by-100x-dynamic-toolsets-v2/> | tool-catalog costs (400-tool static server ≈405K tokens of definitions) | `[CORROBORATED*]` (section) |
| Stacklok — **MCP Optimizer vs Anthropic's Tool Search Tool** | <https://stacklok.com/blog/stackloks-mcp-optimizer-vs-anthropics-tool-search-tool-a-head-to-head-comparison/> | large-catalog retrieval (48% retrieval / 34% end-to-end over 2,792 tools) | `[CORROBORATED*]` |
| Arcade — **Anthropic Tool Search test at 4,000 tools** | <https://www.arcade.dev/blog/anthropic-tool-search-4000-tools-test/> | large-catalog retrieval (56% regex / 64% BM25 over 4,027 tools, 25 tasks) | `[CORROBORATED*]` |
| Scalekit — **mcp-vs-cli-benchmark** repo | <https://github.com/scalekit-inc/mcp-vs-cli-benchmark> | surface choice (1.3×–80× token gap; read as n=1 — the README labels its headline table a single run and its 30-run Wilcoxon protocol is unexecuted) | `[MEDIUM]` |
| **AgentArch** — Bogavelli et al.; preprint | arXiv:2509.10769 · <https://arxiv.org/abs/2509.10769> | surface choice — function calling vs ReAct across 18 enterprise configurations; never tests code execution | `[MEDIUM]` |
| **Executable Code Actions Elicit Better LLM Agents** (CodeAct) — Wang et al.; ICML 2024 | arXiv:2402.01030 · <https://arxiv.org/abs/2402.01030> | code-execution surface (+up to 20% success, ~30% fewer actions; own benchmarks, not independently reproduced) | `[MEDIUM]` |
| **CVE-2025-6514** — OS command injection in the `mcp-remote` client proxy (CVSS 9.6) | <https://www.cve.org/CVERecord?id=CVE-2025-6514> | surface choice — client-surface risk, *not* a protocol flaw | `[VENDOR-DOC]`-adjacent (section `[CORROBORATED*]`) |

The **promote-to-a-dedicated-tool** table is `[SYNTHESIS]` — no vendor document states this rule; each
mechanism in it is observable in shipped harnesses, but the framing is corpus-original. Willison
(abandons MCP for coding agents) and Ronacher (keeps MCP behind a single code-accepting tool) are
carried as `[ATTRIBUTION]` with no URL captured in this ledger — see the flags below.

### caching-and-knowledge-delivery.md

| Source | ID · link | Cited at | Label there |
|---|---|---|---|
| **Auditing Prompt Caching in Language Model APIs** — Gu et al.; ICML 2025 | arXiv:2502.07776 · <https://arxiv.org/abs/2502.07776> | T6.1 — prefix caching detected by timing side-channel at Anthropic and OpenAI only (DeepSeek's per-user isolation hid the signal) | `[HIGH]` |
| OpenAI — **prompt caching guide** | <https://platform.openai.com/docs/guides/prompt-caching> | T6.1 (exact-prefix-match statement); economics table | `[VENDOR-DOC]` |
| googleapis/python-genai **#1880** — Gemini implicit-cache reliability defect (~42% hit rates, Dec 2025) | <https://github.com/googleapis/python-genai/issues/1880> | T6.1 | `[HIGH]` (section) |
| ankitbko — **KV-Cache Aware Prompt Engineering** (Azure OpenAI, 1,300-request experiment, Aug 2025) | <https://ankitbko.github.io/blog/2025/08/prompt-engineering-kv-cache/> | stability ordering (71.3% cost reduction, ~39% mean TTFT improvement) | `[HIGH]` |
| ProjectDiscovery — **How we cut LLM costs with prompt caching** | <https://projectdiscovery.io/blog/how-we-cut-llm-cost-with-prompt-caching> | stability ordering (cache hit rate 7% → 84% by relocating working memory to the tail) | `[HIGH]` |
| OpenAI Cookbook — **Prompt Caching 201** | <https://developers.openai.com/cookbook/examples/prompt_caching_201> | append-don't-edit (Codex is deliberately append-only; `allowed_tools` over mutating the tool array) | `[CORROBORATED*]` |
| **Don't Break the Cache** — Lumer et al.; preprint | arXiv:2601.06007 · <https://arxiv.org/abs/2601.06007> | append-don't-edit (cost differences 2–4pp; TTFT 28–31% for selective strategies); economics (41–80% cost reduction, 13–31% TTFT) | `[CORROBORATED*]` |
| anthropics/claude-code **#46829** — unannounced server-side TTL regression (1 h → 5 min, Mar 2026) | <https://github.com/anthropics/claude-code/issues/46829> | TTL coupling (~26% cost rise in the affected month) | `[CORROBORATED*]` |
| Provider pricing/caching pages — Anthropic, OpenAI, Google | vendor docs, read **as of 2026-08-08** | economics table (read/write multipliers, TTLs); minimum-cacheable-prefix floors | `[VENDOR-DOC]` **as-of dated**; floors `[VENDOR-DOC — floors as of 2026-08-08]` |
| **SkillFlow** — Li et al.; preprint | arXiv:2504.06188 · <https://arxiv.org/abs/2504.06188> | T6.2 — 9.2% → 16.4% Pass@1 from a 36K-skill corpus. The 9.2% arm is *no skills*; the paper never runs a load-everything arm | `[CORROBORATED* — cross-ecosystem]` |
| **SkillReducer** — Gao et al.; preprint | arXiv:2603.29919 · <https://arxiv.org/abs/2603.29919> | T6.2 — attention dilution; 60%+ of skill bodies non-actionable; 26.4% of community skills lack routing descriptions | `[CORROBORATED*]` |
| **SkillRouter: Skill Routing for LLM Agents at Scale** — Zheng et al.; preprint | arXiv:2603.22455 · <https://arxiv.org/abs/2603.22455> | T6.2 — hiding skill bodies costs 37–44pp routing accuracy (figure as of the current revision, 2026-08-08) | `[CORROBORATED*]` |
| **Learning to Rewrite Tool Descriptions for Reliable LLM-Agent Tool Use** — Guo et al.; preprint | arXiv:2602.20426 · <https://arxiv.org/abs/2602.20426> | T6.2 — +11pp multi-step success, ~29% less degradation at 150+ tools | `[CORROBORATED*]` |
| **LOCA-bench** — Zeng et al.; preprint | arXiv:2602.07962 · <https://arxiv.org/abs/2602.07962> | T6.2 — context-pressured agents stop after partial retrieval (closest direct evidence for the knowledge-action trade-off) | `[MEDIUM]` |
| **LM Agents May Fail to Act on Their Own Risk Knowledge** — Tang et al.; preprint | arXiv:2508.13465 · <https://arxiv.org/abs/2508.13465> | T6.2 — flagged explicitly as an *adjacent* domain (risk knowledge vs safe execution: >98% vs <26%), not a measurement of skipped fetches; also `loops-and-stop-conditions.md` P4.7 | `[MEDIUM]` here; `[CORROBORATED*]` in loops |
| **LongMemEval** — Wu et al.; ICLR 2025 | arXiv:2410.10813 · <https://arxiv.org/abs/2410.10813> | P2.1 (focused ~300-token vs full ~113K-token prompts, via Chroma); memory architecture (LongMemEval-M) | `[MEDIUM]` / `[HIGH but vendor-affiliated]` |
| **Beyond the Context Window** (fact-based memory vs long context) — Pollertlam & Kornsuwannawit; preprint | arXiv:2603.04814 · <https://arxiv.org/abs/2603.04814> | memory architecture — GPT-5-mini long-context beat Mem0 by ~35 points on LoCoMo | `[HIGH for the accuracy gap; contested benchmark]` |
| **Anatomy of Agentic Memory** — Jiang et al.; preprint | arXiv:2602.19320 · <https://arxiv.org/abs/2602.19320> | memory architecture — "Context Saturation Gap"; four structural types that *re-cut* rather than reject episodic/semantic | section `[HIGH/MEDIUM]` |
| **Hindsight is 20/20** (HINDSIGHT) — Latimer et al.; preprint | arXiv:2512.12818 · <https://arxiv.org/abs/2512.12818> | memory architecture — 83.6% vs 39.0% full-context on LongMemEval-M | `[HIGH but vendor-affiliated]` |
| **Memory in the LLM Era** (12-method benchmark) — Wu et al.; preprint, v3 as of 2026-08-08 | arXiv:2604.01707 · <https://arxiv.org/abs/2604.01707> | memory architecture — tree > graph; 9B → 27B backbone lifts multi-session >1.6× | `[HIGH]` |
| **Governing Evolving Memory in LLM Agents** (SSGM) — Lam et al.; preprint | arXiv:2603.11768 · <https://arxiv.org/abs/2603.11768> | memory architecture — pollution → drift → conflict; O(T) vs O(N) bounds; write gate *and* read gate, no dominance claim | `[MEDIUM — theoretical bounds]` |
| **The Complexity Trap: Simple Observation Masking…** (JetBrains) — Lindenbauer et al.; DL4C workshop @ NeurIPS 2025 (camera-ready), public repo | arXiv:2508.21433 · <https://arxiv.org/abs/2508.21433> | T6.4 — masking cuts cost 52% / +2.6% solve rate; hybrid ~11% cheaper; summarized trajectories run 13–15% longer | `[HIGH]` |
| **Chain of Summaries** — Brach et al.; preprint | arXiv:2511.15719 · <https://arxiv.org/abs/2511.15719> | T6.4 — query-aware summaries beat generic by 9.6% F1 and beat the source document (0.80 vs 0.76) | `[HIGH]` |
| **ReSum** — Wu et al.; preprint | arXiv:2509.13313 · <https://arxiv.org/abs/2509.13313> | T6.4 — +~4.5% over append-everything ReAct, ~8.2% with a tuned summarizer | `[HIGH]` |
| **Memory as Action** (MemAct) — Zhang et al.; preprint | arXiv:2510.12635 · <https://arxiv.org/abs/2510.12635> | T6.4 — 14B learned curator beats a summarization baseline ~9pp | `[HIGH]` |
| **The Illusion of Diminishing Returns** — Sinha et al.; ICLR 2026 | arXiv:2509.09677 · <https://arxiv.org/abs/2509.09677> | T6.4 — self-conditioning; not fixed by scale, largely avoided by reasoning models | `[HIGH]` |
| Anthropic — memory tool, context editing, compaction docs | platform docs, read **as of 2026-08-08** | T6.3 (the API now injects the memory protocol when the memory tool is present — hand-written "check your memory file first" triggers are obsolete); T6.4 preserve-verbatim / recall-first guidance, which is **Anthropic alone** — JetBrains takes no position | `[VENDOR-DOC — as of 2026-08-08]` / `[VENDOR-DOC]` |

Named in this file without a URL captured here: the Agent Skills standard and its cross-vendor
adoption, `llms.txt` (Jeremy Howard), Amazon Science's agentic-keyword-search result (AAAI 2026), the
Mem0 / Zep LoCoMo dispute posts (84 / 75.14 / 58.44), MemGPT–Letta and git-backed MemFS (Feb 2026).
The caches-are-model-scoped claim is explicitly `[SYNTHESIS]` in the file: an inference from how KV
prefixes are keyed, not a documented guarantee.

### data-formats.md

| Source | ID · link | Cited at | Label there |
|---|---|---|---|
| **Token-Oriented Object Notation vs JSON** — Matveev (single author); preprint | arXiv:2603.03306 · <https://arxiv.org/abs/2603.03306> | the 21-model benchmark: repair-loop tax (3626 vs 1723, an *invoice/TOON-aligned* case), prompt tax, deep-nesting case running the other way, 0% one-shot nested generation | `[CORROBORATED*]` |
| **Are LLMs Ready for TOON?** — Masciari et al.; preprint | arXiv:2601.12014 · <https://arxiv.org/abs/2601.12014> | model-identity-not-tier row — increased model capacity reduces the gap | `[CORROBORATED*]` |
| **Notation Matters: A Benchmark Study of Token-Optimized Formats in Agentic AI Systems** — Kutschka & Geiger; preprint (rev. Jun 2026, post-probe) | arXiv:2605.29676 · <https://arxiv.org/abs/2605.29676> | agentic-loop row — ~18% token reduction at ~9pp accuracy cost, cascading multi-turn parse failures, collapsed parallel tool calls | `[CORROBORATED*]` |
| improvingagents — **TOON benchmarks** | <https://www.improvingagents.com/blog/toon-benchmarks/> | nested-retrieval row (TOON 43.1% @ 45,436 tokens vs Markdown 54.3% @ 38,357, YAML 62.1%) | `[CORROBORATED*]` |
| **TOON** format repo — spec v4.1, figures **as of 2026-08-08** | <https://github.com/toon-format/toon> | headline 42.6% fewer tokens than JSON at 72.2% vs 71.4% retrieval accuracy, on four fast/cheap-tier models; flat-track CSV comparison | `[CORROBORATED*]` |

The 11-format benchmark (GPT-4.1-nano, 1,000 records) behind the Markdown-KV / Markdown-Table /
CSV / XML accuracy rows is cited in the file without a URL — see the flags below.

### loops-and-stop-conditions.md

| Source | ID · link | Cited at | Label there |
|---|---|---|---|
| Anthropic — **Building Effective Agents** (Dec 2024) | <https://www.anthropic.com/engineering/building-effective-agents> | P4.1 — the only pass-1-confirmed claim for this pillar; the source says "common to include" / "recommend", the strengthening to *required* is ecosystem convergence | `[HIGH + ecosystem practice]` |
| Harness flags — Claude Code `--max-turns`, OpenAI Agents SDK `max_turns` | vendor docs (both verified in the June pass) | P4.1 stop-condition stack | `[HIGH + ecosystem practice]` |
| Anthropic — hallucination-reduction guidance (cite-then-retract) | platform docs | P4.7 evidence-before-assertion — the doc explicitly disclaims elimination, so the contract is a filter, not a gate | `[VENDOR-DOC]` |
| **Agentic Uncertainty Reveals Agentic Overconfidence** — Kaddour et al.; preprint, n=100 | arXiv:2602.06948 · <https://arxiv.org/abs/2602.06948> | P4.7 — 62% overconfident on failing vs 11% underconfident on passing; post-hoc self-assessment; mid-task doubt (71% GPT / 97% Claude, a two-model spread); adversarial reframing 72% → 45% | `[MEDIUM]` (adversarial-reframing bullet `[MEDIUM, 2-1 vote]`) |
| **Confident and Wrong: Silent Semantic Failures in Coding Agents** — Mehta (single author); preprint | arXiv:2603.25764 · <https://arxiv.org/abs/2603.25764> | P4.7 — GPT-5 submits 100% / resolves 44%; silent semantic failure covers 68% of its failing runs | `[CORROBORATED*]` |
| **Taming Overconfidence in LLMs: Reward Calibration in RLHF** — Leng et al.; ICLR 2025 (poster) | arXiv:2410.09724 · <https://arxiv.org/abs/2410.09724> | P4.7 root cause — reward-model bias toward high-confidence scores; RLHF models more verbalized-overconfident than SFT | `[HIGH — peer-reviewed]` |
| **Towards Understanding Sycophancy in Language Models** — Sharma et al.; ICLR 2024 (poster) | arXiv:2310.13548 · <https://arxiv.org/abs/2310.13548> | P4.7 root cause — preference data favours agreement; preference models prefer convincing sycophancy over correctness a non-negligible fraction of the time | `[HIGH — peer-reviewed]` |
| **Good Arguments Against the People Pleasers** — Feng et al.; preprint | arXiv:2603.16643 · <https://arxiv.org/abs/2603.16643> | P4.7 — CoT reduces sycophancy on average, masks it, and creates it (Type C); Table 6 tabulates prevalence per model | `[MEDIUM]` |
| **Challenging the Evaluator: LLM Sycophancy Under User Rebuttal** — Kim & Khashabi; EMNLP 2025 Findings | arXiv:2509.16533 · <https://arxiv.org/abs/2509.16533> | P4.7 — 84.5% persuaded by casual rebuttal; 17.1pp is the *net* right-minus-wrong differential | `[MEDIUM — peer-reviewed, 2025-era small/mid-tier models only]` |
| **Quantifying and Mitigating Self-Preference Bias of LLM Judges** — Yang et al.; preprint | arXiv:2604.22891 · <https://arxiv.org/abs/2604.22891> | P4.7 — self-preference up to β≈0.31, model-dependent (some frontier models self-penalize); rubric cuts it ~31% | `[CORROBORATED*]` |
| **From Confident Closing to Silent Failure** — Advani (single author); FAGEN@ICML 2026 workshop paper | arXiv:2606.09863 · <https://arxiv.org/abs/2606.09863> | P4.7 — the head-to-head that closed this chapter's open question: no LLM judge >0.65 AUROC (0.54 on AppWorld) vs TF-IDF structural detectors at 0.83 / 0.95, ~3,300× lower latency | `[CORROBORATED*]` |
| **The Silicon Mirror** — Shah (single author); preprint, no component ablation | arXiv:2604.00478 · <https://arxiv.org/abs/2604.00478> | P4.7 — 9.6% → 1.4% sycophancy credited to the full three-component framework, not the critic loop alone; v1 headline was 12.0% on 50 scenarios | `[CORROBORATED*]` |
| **LM Agents May Fail to Act on Their Own Risk Knowledge** — Tang et al. | arXiv:2508.13465 (row under `caching-and-knowledge-delivery.md`) | P4.7 — the knowledge-action gap as formal frame | `[CORROBORATED* — probe 2026-06-12]` |
| MAST | arXiv:2503.13657 (row under `multi-agent.md`) | P4.7 foundations — task verification as one of three top-level failure categories | `[HIGH]` |

P4.5 / P4.6 (HITL gates, self-correction) are `[PENDING]`: no verified claims, scaffolding only from
vendor-documented harness practice. Not yet scoped to a research pass.

### prompt-mechanics.md

| Source | ID · link | Cited at | Label there |
|---|---|---|---|
| **Models Recall What They Violate** — Kruthof (single author); preprint | arXiv:2604.28031 · <https://arxiv.org/abs/2604.28031> | T3.2 — knows-but-violates 8–99% across seven models (no correlation test run: the does-not-track-tier reading is the corpus's own, filed by the paper as open); 74% of multi-turn drift first violates by turn 2 | `[MEDIUM]` |
| **On the Paradoxical Interference between Instruction-Following and Task Solving** — Qi et al.; preprint | arXiv:2601.22047 · <https://arxiv.org/abs/2601.22047> | T3.2 — compliance flat >94% while SustainScore falls to ~84%; damage front-loaded in the first ~5 constraints; the 8-model × 1–16-constraint sweep is a measurement design, not a recommended ceiling | `[HIGH]` |
| **IFScale** (How Many Instructions Can LLMs Follow at Once?) — Jaroslawicz et al.; preprint | arXiv:2507.11538 · <https://arxiv.org/abs/2507.11538> | T3.2 — curve taxonomy (threshold / linear / exponential by tier); cite the taxonomy, not the absolute scores | `[MEDIUM]` |
| Arize — **IFScale replication** (12 May 2026) | <https://arize.com/blog/llm-instruction-following-benchmark-2026/> | T3.2 — 2026 frontier models pinned at 100% at N=500; vocabulary widened 500 → 10,000 words to reinduce degradation; breaking point ~200–300 → ~2,000 constraints | `[CORROBORATED*]` |
| **MOSAIC** (Deconstructing Instruction-Following) — Purpura et al.; EACL 2026 | arXiv:2601.18554 · <https://arxiv.org/abs/2601.18554> | T3.2 — inter-constraint correlations: readability × keywords −0.28 to −0.34; avoid-X / use-X twins −0.32 to −0.44; sharpest is token-count × respond-in-JSON at −0.531 | `[HIGH]` |
| **Semantic Gravity Wells: Why Negative Constraints Backfire** — Rana (single author); preprint | arXiv:2601.08070 · <https://arxiv.org/abs/2601.08070> | T3.2 — ~87.5% of "do not say X" violations are priming failures; single model (Qwen-2.5-7B), frontier transfer untested | `[MEDIUM]` |
| **When Built-in Thinking Helps and Hurts** — Kumar (single author); preprint, post-stamp | arXiv:2606.09662 · <https://arxiv.org/abs/2606.09662> | T3.2 — thinking *redistributes* IF errors (−0.55 to −3.52pp aggregate, 10–20% of prompts flip): planning constraints improve, exact-form constraints worsen | `[CORROBORATED*]` |
| **The System Prompt Is the Attack Surface** — Litvak (single author); preprint | arXiv:2603.25056 · <https://arxiv.org/abs/2603.25056> | T3.2 placement — §4.2 2×2 factorial is the real source of the circulating +32.0 / +37.4pp figures; metric is phishing-detection recall, and the interaction term is −27.4 / −30.7pp | `[MEDIUM]` |
| **Let Me Speak Freely?** — Tam et al.; EMNLP 2024 Industry Track (<https://aclanthology.org/2024.emnlp-industry.91/>) | arXiv:2408.02442 · <https://arxiv.org/abs/2408.02442> | T3.3 — the 2024 alarm; tested no frontier reasoning models, used different prompts per condition | `[CORROBORATED*]` (section) |
| dottxt — **Say What You Mean** (rebuttal) | <https://blog.dottxt.ai/say-what-you-mean.html> (blog.dottxt.co 301s here) | T3.3 — same-prompt rerun: 0.77 vs 0.73 (JSON prompt), 0.68 vs 0.65 (NL prompt); the ~12-point gap is a cross-condition pairing error | `[CORROBORATED*, vendor-interested on both sides]` |
| **JSONSchemaBench** — Geng et al.; preprint (arXiv page lists no venue) | arXiv:2501.10868 · <https://arxiv.org/abs/2501.10868> | T3.3 — ~1–4 point accuracy gains; downstream experiments run on one model (Llama-3.1-8B-Instruct), and the paper makes no small-model claim | `[MEDIUM]` |
| **XGrammar** — Dong et al. (MLC/CMU); MLSys 2025 | arXiv:2411.15100 · <https://arxiv.org/abs/2411.15100> | T3.3 — constrained-decoding per-token overhead in the tens of microseconds; grammar-compilation as the one-time cost | `[HIGH]` (with vendor docs + SGLang corroborating) |
| Anthropic — structured outputs / strict tool schemas docs | platform docs | T3.3 — schema-valid JSON guarantee, ~24h schema-compilation cache, **required properties emit before optional ones regardless of declaration order** (so a `reasoning` field must be *required*, not merely first), grammar-state reset for thinking models, `stop_reason: "refusal"` escape | `[VENDOR-DOC]` |

T3.1 is `[MEDIUM]` and rests on `context-degradation.md` T2.3 (arXiv:2508.07479) plus the three-mechanism
framing in T2.2. P1.1–P1.3 are `[HELD BACK — source policy]`: locally validated dispatch patterns kept
out of the guide because no external corroboration was found — a deliberate hold, not a research gap.
The externally-supported subset lives in `tool-design.md` P3.2.

## Findings ledger

Every labelled section, grouped by the reference file it feeds, with the label the file currently
carries. IDs are znote IDs in project `agent-engineering-guide` (`zk_get_note <id>` for the full
Claim / Evidence / Caveats). Rows with no znote ID are sections that were synthesized, vendor-sourced,
or added after the June pass, and therefore have no finding note behind them.

| Finding / section | Label (as of 2026-08-08) | Source(s) | znote id |
|---|---|---|---|
| **foundations.md** | | | |
| T1.1 — Workflows vs agents + simplest-viable-design | `[VENDOR-DOC]` | Anthropic BEA + context-engineering post; Barry Zhang talk (the adoption checklist) | `PlnAKYB2HwbHP8K2Y0uWU` |
| T1.2 — Context engineering as the successor discipline | `[ATTRIBUTION]` (Cognition) + `[VENDOR-DOC]` (Anthropic) | cognition.com/blog/dont-build-multi-agents; anthropic.com effective-context-engineering | — |
| T1.3 — The agent as a function of its context | `[SYNTHESIS]` | corpus-original framing, argued from T2.1, T2.5, T5.1 | — |
| **context-degradation.md** | | | |
| Header — mid-2026 frontier profile (ATLAS) | `[CORROBORATED*]` | arXiv:2605.28079 | — |
| T2.1 — Context rot is real and non-uniform | `[HIGH]` | Chroma; NoLiMa | `vgmCOg-QYmYKfGofWyh2x` |
| T2.2 — Three mechanisms: lexical, positional, length | `[HIGH for measurements, MEDIUM for mechanism attribution]` | arXiv:2502.05167; 2607.01002; 2603.10123; 2510.05381; 2402.14848 | `YKTvnW-QV4v5rI4L-jsVT` |
| T2.3 — Lost-in-the-middle, revised (window occupancy) | `[MEDIUM]` | arXiv:2508.07479 (revises the *finding* of arXiv:2307.03172) | `Xcu8_aRsaCVVYG5p7xQOF` |
| T2.4 — Claimed vs effective context | `[HIGH, historical]` | RULER (2404.06654); HELMET (2410.02694) | `Suj40RsYngygRUOqNU64S` |
| T2.5 — Distractors and family-specific failure signatures | `[HIGH, family-rankings MEDIUM]` | Chroma; RULER multi-key; NoLiMa ablation; 2402.14848; 2608.03297; 2601.02023; 2606.29718 | — |
| **multi-agent.md** | | | |
| T5.2 — The Anthropic–Cognition dialectic | `[MEDIUM]` (Cognition items `[ATTRIBUTION]`) | Anthropic MARS; both Cognition posts | `hr_WQEP4noHYorvHtK87e` |
| T5.1 — MAST taxonomy of 14 failure modes | `[HIGH — peer-reviewed]` | arXiv:2503.13657 | `RdDAcSu453oiKhoLp_9pA` |
| T4.1 — Economics: multi-agent as token-spend scaling | `[MEDIUM — vendor-internal]` | Anthropic MARS; eval-awareness/BrowseComp | `1YMyUyd7tLDUJzMjeTM5I` |
| Equal-budget evidence | `[HIGH]` | arXiv:2604.02460 (verified in primary, not via probe) + replications 2601.12307, 2606.13003 | `mYS8aXuNJpVFj74rFCax8` |
| Equal-budget counter-nuance (Kim et al.) | `[MEDIUM]` | arXiv:2512.08296 | — |
| Equal-budget sign flip (Wunderlich et al.) | `[CORROBORATED*]` | arXiv:2605.01566 | — |
| P3.1 — The decision framework | `[HIGH/MEDIUM synthesis]` | composes the rows above | — |
| Footnote — agent-to-agent protocols | `[CORROBORATED* — probe 2026-06-12]` | LF press releases; AAIF proposals #37; LangChain server-a2a; Anthropic harness post | `y1fKbrMDjtYxcvx99j034` |
| **tool-design.md** | | | |
| P3.3 — The agent-computer interface | `[HIGH — vendor-endorsed practice]`; two additions `[VENDOR-DOC]` | Anthropic BEA + Writing Tools | `0hN0aQsob4wpMbUOK-c-6` |
| Promoting actions to dedicated tools | `[SYNTHESIS]` | corpus-original; no vendor source states the rule | — |
| P3.2 — Orchestrator-worker implementation | `[VENDOR-DOC]` (model-tier point `[MEDIUM]`) | Anthropic MARS + BEA; MAST categories | `4uDlH0UssGN1I6YxsZK3V` |
| Programmatic tool calling | `[VENDOR-DOC]` | Anthropic advanced tool use | — |
| Tool-catalog costs and deferred loading | `[CORROBORATED* — probe 2026-06-12]`; large-catalog retrieval bullet `[CORROBORATED*]` | arXiv:2505.10570; 2512.17052; Anthropic tool-search evals + pricing table (as of 2026-08-08); Speakeasy; Stacklok; Arcade | — |
| Tool-surface choice: CLI vs MCP vs code-execution | `[CORROBORATED* — probe 2026-06-12]` | Scalekit repo `[MEDIUM]`; Willison/Ronacher `[ATTRIBUTION]`; CodeAct `[MEDIUM]`; AgentArch `[MEDIUM]`; Anthropic PTC `[VENDOR-DOC]`; CVE-2025-6514 | `eRWpVwU_nQ2XhB1e9Tl4f` |
| **caching-and-knowledge-delivery.md** | | | |
| T6.1 — Cache mechanics: the prefix-match invariant | `[HIGH]` | arXiv:2502.07776; OpenAI docs; python-genai#1880 | `5xuPlMiSnsd9lLgMLwL6j` |
| — stability ordering | `[HIGH]` | ankitbko; ProjectDiscovery (two independent measurements) | — |
| — append, don't edit | `[CORROBORATED*]` | OpenAI Cookbook 201; arXiv:2601.06007 | — |
| — provider economics table | `[VENDOR-DOC]` **as of 2026-08-08** | Anthropic / OpenAI / Google pricing pages; arXiv:2601.06007 | — |
| — TTL coupling and the Mar 2026 regression | `[CORROBORATED*]` | claude-code#46829 | — |
| — silent invalidators / known subtleties | `[VENDOR-DOC + community anti-pattern reports]`; floors `[VENDOR-DOC — as of 2026-08-08]`; model-scoping `[SYNTHESIS]` | vendor docs | — |
| T6.2 — Progressive disclosure | `[CORROBORATED* — cross-ecosystem]`; index-vs-body `[CORROBORATED*]`; knowledge-action gap `[MEDIUM]` | arXiv:2504.06188; 2603.29919; 2603.22455; 2602.20426; 2512.17052; 2602.07962; 2508.13465 | `vs3qkoXqSAVbgtMQuIJ6e` |
| P2.1 — JIT retrieval vs preloading | `[MEDIUM/CORROBORATED* — probe 2026-06-12]` | Chroma on LongMemEval; Amazon Science AAAI 2026; Anthropic JIT guidance | `aYIWi1Ylbqe_0iZdjLUJy` |
| T6.3 — Memory surfaces | `[VENDOR-DOC + Opus probe 2026-06-13]`; memory-trigger obsolescence `[VENDOR-DOC — as of 2026-08-08]` | Anthropic memory/context-editing/compaction docs | — |
| — Memory architecture: pick by history length | `[HIGH/MEDIUM — Opus probe 2026-06-13]` (per-bullet: 2603.04814 `[HIGH for the accuracy gap; contested benchmark]`, 2512.12818 `[HIGH but vendor-affiliated]`, 2604.01707 `[HIGH]`, 2603.11768 `[MEDIUM — theoretical bounds]`, consolidation `[MEDIUM/aspirational]`, Letta/Mem0 `[CORROBORATED* / vendor-only on specific numbers]`) | arXiv:2603.04814; 2602.19320; 2512.12818; 2604.01707; 2603.11768; LoCoMo dispute posts | `lyYMAPQqBX_pAQW2xD2YO` |
| T6.4 — Summarization strategy and failure modes | `[HIGH/CORROBORATED* — Opus probe 2026-06-13]`; preserve-verbatim guidance `[VENDOR-DOC]` (Anthropic alone, not a two-vendor convergence) | arXiv:2508.21433; 2511.15719; 2509.13313; 2510.12635; 2509.09677; Anthropic compaction docs | `E22xkuYTWfqIu8h2-r3Gi` |
| **data-formats.md** | | | |
| Token-efficient formats: shape × model × direction | `[CORROBORATED* — Opus probe 2026-06-12; live-repo figures re-checked 2026-08-08]`; tokenizer caveat `[MEDIUM]` | arXiv:2603.03306; 2601.12014; 2605.29676; improvingagents; TOON repo (v4.1 as of 2026-08-08) | `f0iaOnJo10Lzd7bS1Atyj` |
| **loops-and-stop-conditions.md** | | | |
| P4.1 — Stop conditions and budget pressure | `[HIGH + ecosystem practice]` | Anthropic BEA; harness flags verified in both major SDKs | `DauD7ii04d2SsF9S_Cm3Y` |
| P4.7 — Trust calibration (flagship) | `[MEDIUM/HIGH — adversarial batch 2026-06-13]` | arXiv:2602.06948; 2603.25764; 2410.09724; 2310.13548; 2603.16643; 2509.16533; 2604.22891; 2606.09863; 2604.00478; 2508.13465; MAST | `_dmmMabxH2qLRZbLn9q8e` |
| P4.5 / P4.6 — HITL gates, self-correction | `[PENDING]` | none — vendor-practice scaffolding only | — |
| **prompt-mechanics.md** | | | |
| T3.1 — Serial position and frontloading | `[MEDIUM]` | via T2.2 / T2.3 | — |
| T3.2 — Instruction-following mechanics | `[HIGH/MEDIUM — adversarial batch 2026-06-13]` | arXiv:2604.28031; 2601.22047; 2507.11538 + Arize replication; 2601.18554; 2601.08070; 2606.09662; 2603.25056 | `u86WuFg3N_RNFeiRCEBQ4` |
| T3.3 / P1.5 — Structured output | `[CORROBORATED*/HIGH — Opus probe 2026-06-13]` | arXiv:2408.02442 + dottxt rebuttal; 2501.10868; Anthropic structured-output docs | `tjDOt1eWxtguMuOMXD6b4` |
| P1.1–P1.3 — Dispatch anatomy, purpose-first exploration, compaction anchors | `[HELD BACK — source policy]` | locally validated only; no external corroboration found | — |

## Refuted / do not use

The pipeline explicitly records what *failed* verification — don't reintroduce these from training
data. See the status ledger note `cu2e5XNmJgEY-j4KAx192` ("Research pass 1 refuted claims, gaps and
open questions") and the JIT-retrieval note (a prior preloading claim was refuted, then re-probed).
The research hub is `UUaeZVisQ0lUwBHKcH11O`.

**Retired by the 2026-08-08 re-audit** — these appeared in earlier revisions of this corpus and are
wrong; if you see them circulating, they may well have come from here:

- **Per-tool overhead of ~280–320 tokens, presented as industry consensus.** No. That range is the
  *tool-use system prompt*, billed once per request. Measured catalogs run ~500–1,000 tokens per tool.
- **A 135-tool server costing ≈125K tokens.** Unsourced after six search formulations. Use Anthropic's
  134K-before-optimization figure or Speakeasy's 400-tool ≈405K instead.
- **"85–95% savings at 78 tools".** A fake range: 85% at 58 tools is the saving; the 95% figure is
  context-window-preserved, a different metric.
- **A quotation mark around "I cannot find this"** as Chroma's abstention wording. Invented. Chroma's
  wording is about explicitly stating that no answer can be found.
- **A quotation attributing "often reward sycophancy" to arXiv:2410.09724.** The string does not appear
  in that paper. The surrounding clauses are verbatim-correct; that one was not.
- **"Ten of twelve models fell below 50%" (NoLiMa).** It is eleven of thirteen, per the abstract.
- **TOON described as ">2× larger than JSON on nested invoice data (null-padding…)".** A fourfold misreading:
  3626 vs 1723 is a repair-loop total on a TOON-*aligned* case, "null-padding" appears nowhere, and the
  paper's genuinely deep-nesting case runs the opposite way.
- **OpenAI as the provider with no cache-write premium.** Gone as of GPT-5.6 (1.25× write premium,
  30-minute TTL); the differentiator no longer exists.
- **Circulating Fable-orchestrator BrowseComp figures.** They trace to an X thread; no Anthropic post
  states them. Do not import.

## Flags for the next verification gate

Recorded here rather than silently fixed, because they sit outside this ledger's edit scope:

- **Sources named in the reference files with no URL captured anywhere in this ledger:** Willison and
  Ronacher (tool-design `[ATTRIBUTION]`); the 11-format benchmark behind data-formats' Markdown-KV /
  Markdown-Table / CSV / XML accuracy figures; Amazon Science's AAAI 2026 agentic-search result; the
  Mem0 / Zep LoCoMo dispute posts; Cloudflare's Code Mode; the Agent Skills marketplace adoption
  figures. Each is load-bearing somewhere and none can currently be traced from this file alone.
- **Single preprints still carrying `[HIGH]`** after the label pass: arXiv:2511.15719, 2509.13313,
  2510.12635, 2603.04814, 2512.12818, 2604.01707 (all in `caching-and-knowledge-delivery.md`) and
  arXiv:2601.22047 (`prompt-mechanics.md`). Per the rubric a single unreplicated preprint should not
  reach `[HIGH]`; several of these are also vendor-affiliated. Tier-2 residue, not yet resolved.
- **`loops-and-stop-conditions.md` still asserts** that every finding in the guide survived independent
  refutation-framed verification panels with majority-kill rules. That is true of the June `[HIGH]` /
  `[MEDIUM]` batches, not of `[CORROBORATED*]` sections, and the sentence reads as corpus-wide.
- **The archive README** at `~/notes/agentic-engineering-research/README.md` repeats the old
  arXiv:2508.07479-revises-Liu-et-al. misattribution corrected here.
