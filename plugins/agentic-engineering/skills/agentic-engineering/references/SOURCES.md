# Sources & Evidence Ledger

The bibliography behind this skill, plus the full provenance of how each claim was verified.

## How this skill was produced

The reference files were not hand-written from a reading list — they were synthesized from an
**adversarial deep-research pipeline** (Claude Code `Workflow` runs, 2026-06-12/13). Per claim:
**search** → **fetch + extract falsifiable claims** → **3-vote adversarial refutation panel** →
**synthesize with a confidence label**. Pass 1 (`wf_dcee7f5f-ff0`): 22 sources → 109 claims → 25
adversarially verified → **24 confirmed, 1 refuted**. Follow-up targeted batches added the
trust-calibration and instruction-following findings (`wf_59b6e5e3-c63`) and a set of
single-verifier corroboration probes.

Full provenance lives in two places:

- **Curated** — znote project **`agent-engineering-guide`** (25 atomic notes; each finding =
  Claim → Evidence → Caveats → Source). Query: `zk_list_notes mode=by_project project=agent-engineering-guide`,
  files at `~/repos/znotes/agent-engineering-guide/`.
- **Raw** — transcript + fetched-source archive at `~/notes/agentic-engineering-research/`
  (`transcripts.tar.xz`: the orchestrating session, 6 workflow runs, 227 subagent transcripts,
  and the downloaded source PDFs).

## Evidence labels

Same scale used throughout the reference files:

- `[HIGH]` — verified against primary sources, survived 3-vote refutation, ≥2 sources or peer review
- `[MEDIUM]` — verified but single-source, vendor-internal, or tested only on older/open models
- `[CORROBORATED*]` — confirmed by a single-verifier research probe (sources checked, no adversarial panel)
- `[VENDOR-DOC]` — official platform documentation (authoritative for mechanics, not effectiveness)
- `[ATTRIBUTION]` — accurately attributed position statement, not an empirical finding

## Primary sources

### Peer-reviewed & preprint research

| Source | Link | Backs | Confidence |
|---|---|---|---|
| **MAST** — multi-agent failure taxonomy (UC Berkeley, NeurIPS 2025 D&B) | arXiv:2503.13657 · <https://arxiv.org/abs/2503.13657> | `multi-agent.md` (T5.1) | `[HIGH]` peer-reviewed |
| **NoLiMa** — long-context fails via lexical-matching loss (Adobe, ICML 2025) | arXiv:2502.05167 · <https://arxiv.org/abs/2502.05167> · code <https://github.com/adobe-research/NoLiMa> | `context-degradation.md` (T2.2) | `[HIGH]` |
| **RULER** — claimed vs effective context gap (NVIDIA, COLM 2024) | arXiv:2404.06654 · <https://arxiv.org/abs/2404.06654> | `context-degradation.md` (T2.4) | `[HIGH]` historical |
| **Lost-in-the-middle, revised** — conditional on window occupancy (COLM 2025) | arXiv:2508.07479 · <https://arxiv.org/abs/2508.07479> | `context-degradation.md` (T2.3) | `[MEDIUM]` |
| **Chroma "Context Rot"** — non-uniform degradation across 18 frontier models | <https://research.trychroma.com/context-rot> | `context-degradation.md` (T2.1/T2.5) | `[HIGH]` (vendor, see caveat in note) |

### Vendor engineering documentation

| Source | Link | Backs | Confidence |
|---|---|---|---|
| Anthropic — **Building Effective Agents** | <https://www.anthropic.com/research/building-effective-agents> | `foundations.md` (T1.1), `tool-design.md` (P3.2/P3.3), `loops-and-stop-conditions.md` (P4.1) | `[VENDOR-DOC]` |
| Anthropic — **Writing Tools for Agents** | <https://www.anthropic.com/engineering/writing-tools-for-agents> | `tool-design.md` (P3.3) | `[VENDOR-DOC]` |
| Anthropic — **Multi-Agent Research System** | <https://www.anthropic.com/engineering/multi-agent-research-system> | `multi-agent.md` (T4.1, T5.2) | `[VENDOR-DOC]` |
| Anthropic — **Eval Awareness / BrowseComp** | <https://www.anthropic.com/engineering/eval-awareness-browsecomp> | `multi-agent.md` (T4.1) | `[VENDOR-DOC]` |
| Cognition — **Don't Build Multi-Agents** | <https://cognition.ai/blog/dont-build-multi-agents> | `multi-agent.md` (T5.2/T5.3) | `[ATTRIBUTION]` |

## Findings ledger

Every verified finding, grouped by the reference file it feeds. IDs are znote IDs in project
`agent-engineering-guide` (`zk_get_note <id>` for the full Claim/Evidence/Caveats).

| Finding | Confidence | Source(s) | znote id |
|---|---|---|---|
| **foundations.md** | | | |
| Simplest-viable-design + workflows-vs-agents taxonomy | `[HIGH]` | Anthropic BEA | `PlnAKYB2HwbHP8K2Y0uWU` |
| **context-degradation.md** | | | |
| Context rot established on mid-2025 frontier models | `[HIGH]` | Chroma, NoLiMa | `vgmCOg-QYmYKfGofWyh2x` |
| NoLiMa lexical-matching mechanism | `[HIGH]` | arXiv:2502.05167 | `YKTvnW-QV4v5rI4L-jsVT` |
| Lost-in-the-middle conditional on window occupancy | `[MEDIUM]` | arXiv:2508.07479 | `Xcu8_aRsaCVVYG5p7xQOF` |
| Claimed context window overstates effective context | `[HIGH]` historical | RULER, NoLiMa, Chroma | `Suj40RsYngygRUOqNU64S` |
| **multi-agent.md** | | | |
| MAST taxonomy of 14 failure modes | `[HIGH]` | arXiv:2503.13657 | `RdDAcSu453oiKhoLp_9pA` |
| Cognition contrarian position | `[HIGH]` attribution | Cognition | `hr_WQEP4noHYorvHtK87e` |
| Multi-agent token economics 4x/15x + variance | `[MEDIUM]` | Anthropic MARS, BrowseComp | `1YMyUyd7tLDUJzMjeTM5I` |
| Orchestrator-workers + 90.2% internal eval | `[HIGH]` caveated | Anthropic BEA, MARS | `4uDlH0UssGN1I6YxsZK3V` |
| Equal-budget multi-agent advantage shrinks to parity | `[CORROBORATED*]` | probe (single-verifier) | `mYS8aXuNJpVFj74rFCax8` |
| No agent-to-agent protocol gold standard mid-2026 | `[CORROBORATED*]` | probe (single-verifier) | `y1fKbrMDjtYxcvx99j034` |
| **tool-design.md** | | | |
| ACIs deserve HCI-level design investment | `[HIGH]` | Anthropic BEA, Writing Tools | `0hN0aQsob4wpMbUOK-c-6` |
| Tool surface: CLI vs MCP vs code-execution | `[CORROBORATED*]` | probe (single-verifier) | `eRWpVwU_nQ2XhB1e9Tl4f` |
| **caching-and-knowledge-delivery.md** | | | |
| Cache mechanics (cross-provider) | `[CORROBORATED*]` | probe (single-verifier) | `5xuPlMiSnsd9lLgMLwL6j` |
| Progressive disclosure (cross-ecosystem) | `[CORROBORATED*]` | probe (single-verifier) | `vs3qkoXqSAVbgtMQuIJ6e` |
| JIT retrieval vs preloading (prior claim refuted, re-probed) | `[CORROBORATED*]` | probe (single-verifier) | `aYIWi1Ylbqe_0iZdjLUJy` |
| Memory architecture: pick by history length | `[MEDIUM]`/`[CORROBORATED*]` | probe (single-verifier) | `lyYMAPQqBX_pAQW2xD2YO` |
| Summarization strategy cascade + failure modes | `[CORROBORATED*]` | probe (single-verifier) | `E22xkuYTWfqIu8h2-r3Gi` |
| **data-formats.md** | | | |
| Token-efficient formats: shape × tier × direction | `[CORROBORATED*]` | probe (single-verifier) | `f0iaOnJo10Lzd7bS1Atyj` |
| **loops-and-stop-conditions.md** | | | |
| Agentic loops need explicit stop conditions | `[HIGH]` | Anthropic BEA | `DauD7ii04d2SsF9S_Cm3Y` |
| Trust calibration: why agents over-report, what catches it | `[MEDIUM]` (3-vote batch) | targeted batch | `_dmmMabxH2qLRZbLn9q8e` |
| **prompt-mechanics.md** | | | |
| Instruction-following drop is enforcement, not memory | `[HIGH]` (3-vote batch) | targeted batch | `u86WuFg3N_RNFeiRCEBQ4` |
| Structured-output costs + reasoning-field-first fix | `[CORROBORATED*]` | probe (single-verifier) | `tjDOt1eWxtguMuOMXD6b4` |

## Refuted / do not use

The pipeline explicitly records what *failed* verification — don't reintroduce these from training
data. See the status ledger note `cu2e5XNmJgEY-j4KAx192` ("Research pass 1 refuted claims, gaps and
open questions") and the JIT-retrieval note (a prior preloading claim was refuted, then re-probed).
The research hub is `UUaeZVisQ0lUwBHKcH11O`.
