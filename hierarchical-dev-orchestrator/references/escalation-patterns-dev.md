# Escalation Patterns for Development

## Flow Architecture

```
User Request
    ↓
Haiku: Repository scan + initial file read
    ↓
Sonnet: Code analysis + hypothesis generation
    ↓
Opus: Architectural assessment + strategy
    ↓
Sonnet: Detailed implementation plan
    ↓
Haiku: Execute changes + run tests
    ↓
[Success] → Done
[Failure] → Escalate with compressed context
```

## Haiku Operations

**Primary responsibilities:**
- Scan directory structure (`view /path/to/repo`)
- Read specific files identified by Sonnet
- Run test commands (`bash pytest`, `npm test`, etc.)
- Make targeted edits (`str_replace`)
- Search for patterns across files
- Execute linting/formatting

**When Haiku escalates to Sonnet:**
1. Test failures after fix attempt
2. File structure doesn't match expected pattern
3. Multiple files reference same problematic pattern
4. Error requires understanding "why" not just "what"
5. Change needs coordination across files

**Haiku compression format:**
```
Action: [what was attempted]
Files: [list of touched files]
Test output: [last 10 lines of failure]
Error context: [line numbers + surrounding code]
Observation: [what Haiku noticed]
```

## Sonnet Operations

**Primary responsibilities:**
- Analyze Haiku's compressed findings
- Generate bug hypotheses (rank by likelihood)
- Design test strategies
- Plan multi-file refactors
- Review code patterns
- Identify missing edge cases

**When Sonnet escalates to Opus:**
1. Solution requires changing architecture
2. Multiple modules have inconsistent patterns
3. Circular dependencies block clean solution
4. Performance issue is structural
5. Original design assumption incorrect
6. 3+ fix attempts in same area failed

**Sonnet compression format:**
```
Goal: [feature/fix objective]
Current state: [what works, what doesn't]
Hypotheses tested: [approaches tried + results]
Blocker: [technical issue with context]
Architectural concern: [why this needs Opus]
Files involved: [list with brief role of each]
Scope change: [how problem grew from original]
```

## Opus Operations

**Primary responsibilities:**
- Evaluate system architecture
- Make strategic refactoring decisions
- Design new abstractions
- Break circular dependencies
- Resolve design pattern conflicts
- Assess trade-offs (performance vs maintainability)

**Opus decides between:**

### Minor Adjustment (20% effort)
Add branch to existing plan without changing strategy.

**Triggers:**
- New edge case discovered
- Need additional helper function
- Missing validation check
- Minor interface extension

**Output:** Targeted directive to Sonnet

### Major Refactor (80% effort)
Restructure approach from architectural level.

**Triggers:**
- Core design assumption wrong
- Implementation creates new architectural debt
- Pattern inconsistency across codebase discovered
- Scope grew beyond original architecture
- Circular dependency requires redesign

**Output:** New architectural plan, old approach archived

## Test-Driven Escalation

### Haiku runs tests after each change
```bash
# Haiku executes
pytest tests/ -v --tb=short

# On failure, compress output:
FAILED tests/test_auth.py::test_refresh_token
KeyError: 'refresh_scope'

→ Escalate to Sonnet with:
- Test name
- Error type + message
- Last 5 lines of traceback
- Changed files since last success
```

### Sonnet analyzes test failure
- Review test expectations
- Check implementation against test
- Generate fix hypotheses
- Identify if test or code is wrong

If hypothesis unclear or touches architecture → Escalate to Opus

## Automatic vs Manual Escalation

**Automatic triggers:**
- Test fails 2x after Haiku fixes
- Same error in 3+ files (pattern issue)
- Stack trace crosses 5+ modules
- Linter reveals architectural smell

**Manual commands:**
- `@sonnet analyze` - Force Sonnet code review
- `@opus rethink` - Request architectural reevaluation
- `escalate` - Let current tier decide

## Code Context Compression Rules

**Don't pass to higher tiers:**
- Full file contents (pass structure + problem area)
- Complete test output (last 10 lines + summary)
- Full dependency trees (just the problematic path)
- Entire stack traces (top + bottom + suspicious middle)

**Do pass to higher tiers:**
- File paths + line numbers
- Key function signatures
- Error messages
- What was attempted
- Compressed observations

**Example - BAD (500 tokens):**
```
[entire 200-line file]
[entire 50-line test output]
```

**Example - GOOD (50 tokens):**
```
File: auth.py, Class TokenValidator
Issue: Line 142, method validate_refresh()
Error: KeyError 'refresh_scope'
Context: Token dict has 'scope' but not 'refresh_scope'
Attempted: Added refresh_scope to Token model, still fails
```

## Repository Analysis Pattern

**Phase 1: Haiku scans**
```bash
view /path/to/repo           # Get structure
view /path/to/main/files     # Identify key modules
```

Haiku output to Sonnet:
```
Structure:
- src/
  - auth/ (4 files, 800 lines)
  - api/ (12 files, 2400 lines)
  - models/ (6 files, 600 lines)
- tests/ (coverage: 78%)
Entry points: main.py, api/routes.py
Dependencies: flask, sqlalchemy, jwt, redis
```

**Phase 2: Sonnet requests specific files**
Sonnet tells Haiku: "Read src/auth/validators.py and src/models/token.py"

**Phase 3: Sonnet analyzes**
Finds pattern: Token validation scattered across 5 files

**Phase 4: Sonnet decides**
- If fixable within current structure → plan changes for Haiku
- If architectural issue → compress to Opus

## Fail Loop Detection

If same area escalates 3+ times:
1. Sonnet flags to Opus: "Stuck in implementation loop"
2. Opus reviews: Is this architectural or implementation?
3. If architectural: Redesign approach
4. If implementation: Sonnet tries radically different approach

**Example:**
- Attempt 1: Fix token validation in auth.py
- Attempt 2: Centralize validation in validators.py
- Attempt 3: Add validation middleware
- **All fail → Opus: "Token validation needs to be at the session layer, not auth layer"**

## Performance Escalation

Haiku notices:
```
Tests pass but run time increased from 2s to 45s
```

→ Sonnet profiles: N+1 query problem

→ If fixable with query optimization: Sonnet handles
→ If requires caching layer: Escalate to Opus

## Integration with Claude Code

Skill assumes Claude Code environment:
- File system access via `view`, `str_replace`, `create_file`
- Bash for test execution, git operations
- Working directory is repository root
- Can run language-specific commands (pytest, npm test, cargo test)

Haiku should:
- Always run tests after changes
- Use git status to track modifications
- Report changed files in escalations
