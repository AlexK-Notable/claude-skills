---
name: testing-methodology
description: "Use when designing or trusting empirical checks: building a seeded corpus, test fixture, or sandbox for exercising a real system end to end; writing a guard test, invariant, or lint meant to catch a CLASS of defect; interpreting a failing or intermittent timing-sensitive result (browser tests, benchmarks, a suite that failed once) or manufacturing system load in a subagent; or verifying that a rebuilt/reinstalled GUI or graphics application actually works. Scaffolded by self-learn from routed lessons."
---

# testing-methodology

Scaffolded by self-learn (`route --dest new-skill`). Routed
lessons live in the managed section below; authored prose added
here survives every recompile (text outside the markers is
never touched).

<!-- self-learn:begin (do not hand-edit inside; managed by self-learn) -->
- **When about to trust a green suite as proof that a lock, flock, or timeout actually works:** A single-process suite cannot expose a broken lock -- no contention exists -- and tests that only check a timeout configuration parses never exercise its enforcement. Mutation-proven: replacing all three fcntl.flock calls with pass left 438 tests passing; removing timeout= from subprocess.run left 438 passing. Prove a safety property by deleting the mechanism (or adding a test double that genuinely contends or hangs past the limit) and confirming the suite goes red; if it stays green, the property is narrative, not tested (znote xGyrG5IdfqGDYNrtKHA3X, self-learn) *(lrn-0a76fae2)*
<!-- self-learn:end -->
