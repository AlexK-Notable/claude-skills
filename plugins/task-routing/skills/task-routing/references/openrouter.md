# Open-weight choices through OpenRouter

Use paid work for small tasks with a concrete advantage, a deliberate paid-model request, or the preferred fallback for constrained Flash research. The rough maximum is USD5 for the entire invocation, not USD5 per request or retry. Do not automatically route long-horizon work to Kimi K3.

## Candidate shortlist

The research identified these exact OpenRouter IDs as leads; none completed a paid comparative quality trial during this skill build:

| Candidate | Task to consider | Evidence limit |
|---|---|---|
| `z-ai/glm-5.3-flash` | Bounded research, tool use, small coding tasks | Published weights/license and endpoints were inspected; local task quality still needs observation |
| `qwen/qwen3.8-flash` | Affordable Flash-like research/tool work | Published weights with a custom Qwen license; review terms for the intended use |
| `qwen/qwen3-coder-next` | Bounded coding tasks | Coding lead, not proof of research quality; endpoint reasoning support varies |

Refresh `/api/v1/models` and `/api/v1/models/{author}/{slug}/endpoints` before relying on availability, tools, context or prices. Check the actual weights repository and license. A model on OpenRouter is not necessarily open-weight, and `license: other` is not a license review. Prefer accepted similar work over leaderboard proxies. Use a small bounded first task when evidence is thin and an existing allowance covers it; no recurring experiment budget is implied.

## Pricing and endpoint selection

Use the endpoint's price, context, output limit and supported parameters. Cost for a successful task includes repeated tool turns, reasoning/output, auxiliary requests, retries and provider fees. Cheap input tokens alone do not establish best value.

Endpoint `pricing.prompt` and `pricing.completion` are USD per token. Provider request `max_price.prompt` and `max_price.completion` use **USD per million tokens**; `max_price.request` is USD per request. Do not confuse the units.

For an exact endpoint, set `provider.only` to its exact tag and `allow_fallbacks: false`. `order` alone is not exclusive pinning. `require_parameters: true` can reject endpoints that do not support the requested features. These routing fields must actually reach OpenRouter; writing them into a worker prompt does not configure the client.

Read key allowance and account balance through `agent-usage`. For attribution, retain returned generation IDs and per-generation usage/cost. Account balance changes can include concurrent activity. `/api/v1/generation?id=...` can provide later metadata for a known generation.

## Keep the money claim honest

A skill, `max_turns`, or Hermes's seconds-based `--run-budget` does not enforce a dollar cap. Before paid launch, establish how the selected setup bounds cumulative spending. Existing provider/key limits or a verified request gate may help; a shared key limit is not automatically a per-task limit. Do not create keys, change billing settings, or install a new runtime as an incidental part of routing.

If only estimates and observation are available, say so; choose a very small, conservatively priced task with room below the ceiling, and stop further requests as the allowance is approached. If the task cannot be kept within the authorized allowance with the available controls, choose a suitable subscription route or surface the specific limitation. Never claim a hard USD5 guarantee from estimated tokens.

After uncertain failure, retain the possible cost until positive evidence resolves it. Resuming or renaming the task does not reset its allowance. BYOK may have external-provider costs in addition to OpenRouter charges; a zero OpenRouter charge is not proof of zero total spend. Do not claim complete accounting for an unverified billing mode.

Sources: [provider selection](https://openrouter.ai/docs/guides/routing/provider-selection), [prompt caching](https://openrouter.ai/docs/guides/best-practices/prompt-caching), [generation metadata](https://openrouter.ai/docs/api/api-reference/generations/get-generation), and the current model/endpoint API responses. Prices and winning endpoints are deliberately not frozen into this skill.
