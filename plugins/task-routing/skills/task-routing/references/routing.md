# Task categories and model choice

Classify by the requested work product. Difficulty means reasoning or uncertainty; length means how much work and context must persist. A long mechanical task need not use the deepest model.

These are starting preferences from the user's September 2026 routing discussion and supplied benchmark report, not a verified universal ranking. Use the established family aliases or model IDs and supported effort below. Capacity can change the choice among suitable models.

| Category | Starting model family | Escalate when |
|---|---|---|
| Retrieve a fact from known documentation | Flash 3.8; Luna/Haiku for a narrow local lookup | Sources conflict or the answer requires reasoning beyond extraction |
| Discover and compare internet sources | Flash 3.8; affordable open research model when Flash is constrained (see [shortlist and evidence limits](openrouter.md)) | Evidence is difficult to locate, technical claims need experiments, or synthesis is hard |
| Brainstorm alternatives | Fable for substantial exploration; Sol/Sonnet for bounded ideas | Novel constraints interact and shallow alternatives are inadequate |
| Plan complex work | Fable or Astra, according to headroom and the nature of the reasoning | Cross-component dependencies, unfamiliar design, or consequential uncertainty |
| Orchestrate and track work | Either Claude Code or Codex; appropriate Fable/Opus or Astra/Sol tier | Dependencies and integration require sustained judgment; basic dispatch alone does not |
| Execute a bounded coding change | Terra/Sol or Sonnet; Luna/Haiku for truly mechanical edits | The change becomes novel, broad, or difficult to verify |
| Execute complex programming or reasoning | Astra for difficult abstract reasoning; Fable for sustained knowledge-heavy work | Give either a bounded deep task, rather than automatically fanning out frontier models |
| Review complicated code | Opus as the ordinary review preference | A deliberate Fable deep review or Astra second perspective has a specific purpose |
| Conduct deep research | Separate gathering from analysis; Astra/Fable for the difficult analysis | More retrieval alone will not resolve the central uncertainty |
| Communicate established findings | Sol or Sonnet; smaller model for a simple transformation | The writing still requires new synthesis or difficult reasoning |

Do not assert that code-writing benchmarks prove review skill, or that a composite score measures brainstorming. Model+harness+effort+tools is the relevant combination. Prefer observed success on similar work; when evidence is thin, say so and choose a bounded task that can be independently assessed.

## Resolve the actual model

Prefer an explicit family alias that the harness maintains as its current model. Establish the mapping once and rely on it during ordinary dispatch; do not inspect the catalog or prove the resolved version on every invocation. Keep task fit: the latest suitable family does not mean the most expensive frontier tier. Use a full release ID when a specific version is requested or no suitable family alias is supported.

| Harness | Normal selector | Established behavior |
|---|---|---|
| Claude Code subscription | `sonnet`, `opus`, `fable`, `haiku` | Native family aliases track the provider's recommended current version. Locally, `--model sonnet` launched Sonnet 5. Use the family alias instead of copying an older release ID. |
| Codex subscription | `gpt-6-astra`, `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna` | Current IDs from the native catalog. Bare `sol` was rejected by the ChatGPT-backed client; no equivalent evergreen family alias is established here. `gpt-5.6` is a version-family alias for Sol, not a promise to follow future generations. |
| agy, Gemini only | `gemini-3.8-flash-low`, `gemini-3.8-flash-medium`, `gemini-3.8-flash-high` | Bare `flash` was rejected and fell back to the saved model, both with and without `--effort`. Do not assume Claude-style alias resolution. Effort can be encoded in the model ID. |

These mappings were checked on 2026-09-08. Refresh the relevant row when a new model is introduced, a harness/provider changes, or a selection fails—not before every worker. Claude aliases can be redirected by provider-specific mappings or `ANTHROPIC_DEFAULT_*_MODEL` overrides; re-establish the mapping if those change. An unavailable requested model needs a surfaced conflict, not silent fallback to an older model.

For mapping updates, use `agy models` for Gemini IDs only; its Anthropic/OpenAI entries and quota are ineligible. Codex's native `/model` picker or app-server `model/list` supplies IDs and supported effort; `~/.codex/models_cache.json` is a cached hint. For Claude Code, use its documented aliases and native selector. For Hermes/OpenRouter, use the catalog and endpoint data in [OpenRouter](openrouter.md).

Sources: [Claude Code model aliases](https://code.claude.com/docs/en/model-config#model-aliases), [Codex model selection](https://learn.chatgpt.com/docs/models), [GPT-5.6 Sol alias](https://developers.openai.com/api/docs/models/gpt-5.6-sol), and local launch/response evidence in `/home/komi/notes/task-routing-iterations-2026-09-08/aliases/`. Codex 0.153.4 rejected `sol`; Claude Code 2.1.265 resolved `sonnet`; agy 1.1.27 rejected `flash`. These observations do not establish every possible alias in the other clients.

Do not print authentication files to discover models. Record what the harness actually launched, rather than treating its requested flags or a worker's self-description as proof.

## Capacity first, within task fit

Check required tools, context, modality, login, and native availability before comparing allowance. Compare the relevant short and long windows together. For example, 90% weekly remaining with an exhausted five-hour window cannot serve work now. Claude model-specific windows and separate Codex pools can be tighter than the service summary.

Percentages across differently sized subscriptions are not equivalent token quantities. Use them as headroom signals, retaining uncertainty when window sizes or pool applicability differ. A soon-to-reset allowance can break a close choice; do not invent a tokens-to-reset forecast. Keep enough capacity for the more demanding work that follows.

A deliberate exact-model request overrides ordinary value preferences when executable. An unavailable request needs a surfaced conflict, not automatic substitution. Always pass a model explicitly, especially when the orchestrator itself is Fable or Astra.

## Minimum dispatch record

A short Markdown entry suffices: task/group, category and difficulty, purpose, explicit alias or model ID/harness/effort, relevant usage observation time, reason for selection, worker/native-session handles, output path, and acceptance checks. Record a resolved model when observed without adding a routine probe. For paid work add the planned total allowance and observed cumulative spending. Reuse the record across retries/resume.

The original source is `~/notes/compass_artifact_wf-c25b09eb-c57a-5a8a-ae44-853ee564cde7_text_markdown.md`. Its benchmark numbers, release claims, and model labels require current primary-source verification before grounding a new empirical claim. The user's later capacity and bounded-paid-work preferences take precedence over that report's generic recommendations.
