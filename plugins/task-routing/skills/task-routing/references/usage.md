# One-call usage check

The existing standalone utility is `~/bin/agent-usage`:

```bash
agent-usage                 # JSON: Claude, Codex, agy, OpenRouter key and account
agent-usage --text          # readable summary
agent-usage --fresh         # bypass the five-minute cache
agent-usage --openrouter-env /absolute/profile/.env
```

Check `--help` before assuming extra options. The installed standalone version does not accept `--service` or `--json`. A partial result exits 1 while still returning healthy services; inspect the JSON rather than discarding it. No model turn is needed to retrieve usage.

Read each service's status, observation time, cached/stale markers, pools and windows. Null is unknown. A cached observation does not become new because it was read again. A reset timestamp crossed since observation makes the old percentage unsuitable for a new routing decision. Avoid repeated fresh requests after authentication errors or rate limiting.

Subscription headroom includes both short and long windows. Match the candidate to its actual pool: Claude's model-specific restrictions matter; Codex's separate pools are not interchangeable; agy may expose only some quota periods. Missing monthly data does not mean unlimited monthly use.

| OpenRouter scope | What it measures |
|---|---|
| Key (`/api/v1/key`) | Key usage totals and daily/weekly/monthly spending, key limit and remaining limit |
| Account (`/api/v1/credits`) | Account credits, total usage, and balance |

A null key limit means no configured key cap; account funds still bind. Account/key deltas can include other concurrent sessions and cannot establish one invocation's exact spend. Keep per-generation cost or trustworthy native session cost evidence for that attribution. Do not equate dollars with subscription percentage remaining.

The helper reads existing CLI logins and the selected Hermes profile's literal OpenRouter dotenv key, then the environment fallback. It does not resolve arbitrary vault commands or key pools. Never print credentials or copy them into worker prompts.

Sources: the installed `~/bin/agent-usage` implementation and its actual JSON; [OpenRouter current key](https://openrouter.ai/docs/api/api-reference/api-keys/get-current-key), [account credits](https://openrouter.ai/docs/api/api-reference/credits/get-credits).
