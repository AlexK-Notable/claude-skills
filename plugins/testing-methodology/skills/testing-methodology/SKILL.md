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
- **When about to write a guard test, invariant, or lint intended to catch a CLASS of defect - especially one replacing a hand-maintained enumeration that went stale:** assert on something the DEFECT must touch, never on something the correct code happens to have. A guard that counts the good thing is blind to omission. Measured instance: a guard counting call sites of an evidence-building helper stayed GREEN when a new route was added that resolved a record and redirected without ever calling it - the exact defect it claimed to cover - and pinned to the pre-fix count it would have stayed green through the entire defect window. The guard that worked counted HX-Redirect assignments: the thing the defect had to ADD. Then verify the guard the only way that works - reproduce the original defect and confirm it goes RED. A guard is itself a claim, and a claim derived by reading is a hypothesis. Prefer AST or structural matching over a text regex: a text match counts prose, and a false positive whose message says to update the count trains the bump-the-number reflex the guard exists to replace. *(lrn-fe16fceb)*
<!-- self-learn:end -->
