---
name: testing-methodology
description: "Use when: About to build a seeded corpus, test fixture, or sandbox for exercising a real system end to end. Scaffolded by self-learn from routed lessons; enrich the prose post-hoc (plugin-dev optional)."
---

# testing-methodology

Scaffolded by self-learn (`route --dest new-skill`). Routed
lessons live in the managed section below; authored prose added
here survives every recompile (text outside the markers is
never touched).

<!-- self-learn:begin (do not hand-edit inside; managed by self-learn) -->
- **When about to build a seeded corpus, test fixture, or sandbox for exercising a real system end to end:** vary the WORLD the operation lands in, not just the DATA it operates on — repo dirty/clean, destination present/absent, host registered/unregistered, prior state analysed/raw, remote configured/absent. A corpus that varies only record shapes against one fixed world leaves every refusal path unreachable and reports coverage that silently excludes them. Derive the world list from the product's own refusal predicates (grep the raise sites), make the states selectable and composable with the clean world as DEFAULT so the normal path stays normal, and apply them after seeding but BEFORE any snapshot, so a reset rewinds TO the world instead of out of it. Two traps once you do: world states can be gated behind record states (a dirty repo still could not reach the dirty-target refusal, because the verb raised NoProposalError first — every seeded record was unanalysed), and composing two worlds with 'git add -A' silently committed the other world's uncommitted edit, so the fixture came up clean while announcing it was dirty. Verify a world by reading the actual state, never the startup banner. *(lrn-4f89e33a)*
<!-- self-learn:end -->
