---
name: hierarchical-dev-orchestrator
description: Multi-tier orchestration for complex software development tasks. Use when coding tasks risk getting stuck in narrow implementation patterns - debugging complex issues, architectural refactoring, building features across multiple files, performance optimization, or when Claude Code needs systems-level perspective. Haiku executes and scans, Sonnet analyzes patterns, Opus provides architectural guidance. Automatically escalates on test failures, circular dependencies, or scope expansion.
---

# Hierarchical Development Orchestrator

## Overview

Prevents implementation tunnel vision by distributing work across model tiers: Haiku scans code and runs tests, Sonnet analyzes patterns and plans changes, Opus makes architectural decisions. Automatic escalation on blockers keeps work moving.

## When to Use

**High-value scenarios:**
- Debugging issues touching 5+ files
- Refactoring that affects architecture
- Performance problems with unclear source
- Features requiring cross-cutting changes
- When stuck implementing same fix repeatedly

**Skip orchestration for:**
- Syntax fixes or small edits
- Single-file feature adds
- Following existing patterns exactly
- Clear implementation path already known

## Core Workflow

```
User: "Fix auth bug" or "Build feature X" or "Optimize performance"
  ↓
Haiku: Scan repo → identify relevant files → read selectively
  ↓
Sonnet: Analyze compressed info → generate hypotheses → plan approach
  ↓
Opus: (if needed) Evaluate architecture → make strategic decisions
  ↓
Sonnet: Design implementation → provide file-level plan
  ↓
Haiku: Execute changes → run tests → report
  ↓
[Pass] → Done
[Fail] → Compress + escalate
```

## Setup

Read these references in order before starting:
1. `references/model-capabilities-dev.md` - What each tier handles
2. `references/escalation-patterns-dev.md` - When/how to escalate
3. `references/codebase-analysis.md` - Token-efficient scanning

## Tier Responsibilities

### Haiku - Execution Layer
**Never analyze, just gather and execute:**
- Scan repo structure (`view` directories)
- Read specific files Sonnet requests
- Run tests after each change
- Search for patterns (`grep`)
- Make targeted edits (`str_replace`, `create_file`)
- Report findings compressed

**Token budget:** ~2-3k per scan cycle

### Sonnet - Analysis Layer
**Never scan files, just analyze:**
- Review Haiku's compressed findings
- Generate ranked bug hypotheses
- Design test strategies
- Plan multi-file changes
- Decide: handle locally or escalate to Opus
- Give specific directives to Haiku

**Token budget:** ~4-6k per analysis

### Opus - Architecture Layer
**Never touch files, just guide strategy:**
- Evaluate system design
- Make refactoring decisions
- Resolve pattern conflicts
- Break circular dependencies
- Decide: patch vs redesign
- Return strategic directives

**Token budget:** ~2-4k per decision

## Implementation Protocol

### Phase 1: Initial Assessment

**Haiku scans repository:**
```bash
view /path/to/repo              # Structure
view /path/to/main/src          # Key modules
view /path/to/tests             # Test organization
```

**Compresses to Sonnet:**
```
Repo: my-api
Structure: /src (15 files), /tests (12 files)
Tech: Python 3.11, Flask, SQLAlchemy, Redis, pytest
Entry: app.py, src/api/routes.py
Issue area: [based on user description]
```

**Sonnet requests specific files:**
"Read src/auth/validators.py and tests/test_auth.py focusing on token validation"

**Haiku reads selectively:**
```bash
view src/auth/validators.py --view_range [130, 180]
```

### Phase 2: Hypothesis Generation

**Sonnet receives compressed file info:**
```
File: auth/validators.py
Class: TokenValidator
Method issue: validate_refresh_token (line 142)
Error: KeyError 'refresh_scope'
Context: Access tokens work, refresh tokens fail
Dependencies: jwt, redis_client
```

**Sonnet generates hypotheses:**
1. Refresh tokens missing 'refresh_scope' field (80% likely)
2. Token format changed but validator didn't update (15%)
3. Redis caching stale token structure (5%)

**Sonnet plans verification:**
"Haiku: Add debug print to see token structure at line 141, then run test_refresh_token_validation"

### Phase 3: Execution + Testing

**Haiku makes change:**
```python
# Added at line 141
print(f"DEBUG token structure: {token.keys()}")
```

**Haiku runs test:**
```bash
pytest tests/test_auth.py::test_refresh_token_validation -v
```

**Haiku compresses result:**
```
Test: FAILED
Debug output: token structure: dict_keys(['scope', 'exp', 'user_id'])
Missing: 'refresh_scope' not in token
Error: Line 142 KeyError 'refresh_scope'
```

**Sonnet confirms hypothesis #1, plans fix**

### Phase 4: Escalation (If Needed)

**Sonnet discovers architectural issue:**
```
Problem: Token validation logic in 5 different files
Pattern: Each file checks different fields inconsistently
Attempted: Centralize in validators.py, breaks 3 other modules
Blocker: No single source of truth for token schema
```

**Escalates to Opus:**
```
Goal: Add refresh token support
Files involved: validators.py, tokens.py, session.py, middleware.py, utils.py
Pattern: Token validation scattered, no unified interface
Blocker: Centralizing breaks existing flows
Architectural issue: Missing abstraction layer
```

**Opus decides:**
```
STRATEGY: Create TokenValidator protocol
- Define interface: validate(token: dict) -> bool
- Implement AccessTokenValidator, RefreshTokenValidator separately
- Migrate scattered validation to protocol implementations
- 3-phase rollout to avoid breaking changes

RATIONALE: Current approach couples validation with business logic.
Future token types will hit same issue.

NEXT: Sonnet design protocol interface, Haiku implements incrementally
```

### Phase 5: Implementation + Verification

**Sonnet plans implementation:**
1. Create token_protocol.py with interface
2. Implement RefreshTokenValidator
3. Update validators.py to use protocol
4. Run full test suite
5. Migrate remaining files if tests pass

**Haiku executes each step:**
- Makes changes
- Runs tests after each
- Reports results compressed
- Escalates if new blockers

## Automatic Escalation Triggers

### Haiku → Sonnet
- Test fails after 2 fix attempts
- Error message unclear
- Multiple files need coordinated changes
- Found pattern inconsistency across files

### Sonnet → Opus
- Solution requires architectural change
- Circular dependency discovered
- Performance bottleneck is structural
- 3+ fix attempts in same area failed
- Pattern conflict across modules

## Manual Escalation

User can override:
- `@sonnet analyze` - Force Sonnet code review
- `@opus rethink` - Request architectural reevaluation
- `escalate` - Let current tier decide

## Context Compression Rules

**Haiku → Sonnet:**
- File paths + line numbers (not full contents)
- Function signatures (not implementations)
- Error messages (not full stack traces)
- Test results (pass/fail + key output)

**Sonnet → Opus:**
- Problem statement (1-2 sentences)
- Files involved (list with role of each)
- Approaches attempted (brief)
- Architectural concern (specific)
- Scope drift assessment

**Never pass up:**
- Complete file contents
- Full test output
- Entire stack traces
- Multiple reads of same file

## Test Integration

**Haiku runs tests automatically:**
```bash
# After each change
pytest tests/
npm test
cargo test
# Language-appropriate command
```

**On failure, compress:**
```
Test: test_name
Error: ErrorType: message
Location: file.py:142
Changed since last pass: file1.py, file2.py
```

**On pass:**
```
Tests: 45 passed (was 43 failed)
Duration: 2.3s (was 2.1s)
Coverage: 82% (was 80%)
```

## Cost Optimization

**Token waste patterns to avoid:**
- Opus reading files (use Haiku)
- Re-reading unchanged files (cache)
- Full test output (compress)
- Verbose stack traces (top + bottom only)

**Efficient patterns:**
- Haiku scans once, caches structure
- Sonnet requests targeted reads
- Opus receives 200-token summaries
- Reuse architectural decisions within session

**Typical costs:**
- Simple fix: $0.01-0.02 (mostly Haiku)
- Complex debug: $0.05-0.10 (Sonnet analysis)
- Architectural refactor: $0.20-0.40 (Opus guidance)

## Fail Loop Prevention

If stuck after 3 escalations in same area:

1. Sonnet flags: "Implementation loop detected"
2. Opus reviews: Architectural or implementation issue?
3. **If architectural:** Redesign approach entirely
4. **If implementation:** Try radically different approach

**Example loop:**
- Attempt 1: Fix in module A (fails)
- Attempt 2: Fix in module B (fails)
- Attempt 3: Add middleware (fails)
- **Opus: "This is session-layer concern, not auth-layer"**

## Integration with Claude Code

Assumes Claude Code environment:
- File system access via `view`, `str_replace`, `create_file`
- Bash execution for tests, git, tools
- Working directory = repository root
- Language-specific test runners available

**Haiku uses:**
- `view` for reading
- `str_replace` for edits
- `create_file` for new files
- `bash_tool` for tests/git
- `grep` for pattern search

## Success Metrics

Track in session:
- Files scanned vs files changed (efficiency)
- Escalations (should decrease over time)
- Test pass rate trend
- Token usage per tier
- Time to resolution

## References

- `references/model-capabilities-dev.md` - Detailed tier strengths, coding scenarios, token costs
- `references/escalation-patterns-dev.md` - Complete escalation logic, compression templates, fail loop detection
- `references/codebase-analysis.md` - Token-efficient scanning patterns, caching strategy, multi-file analysis
