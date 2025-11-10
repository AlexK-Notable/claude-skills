# Model Capabilities for Software Development

## Opus 4.1 - Systems Architecture

**Core Strengths:**
- Cross-file dependency analysis and architectural patterns
- Identifying systemic issues vs isolated bugs
- Design pattern selection and trade-off evaluation
- Breaking circular dependencies and architectural debt
- Long-range refactoring strategy (affects 10+ files)
- API design and interface contracts
- Performance bottleneck identification at system level

**Coding Scenarios:**
- "This authentication flow touches 8 files and I don't know where the bug is"
- "Should we use microservices or modular monolith?"
- "Our caching strategy is causing race conditions"
- "We need to refactor this into testable components"
- "The code works but fails at scale"

**What Opus Sees:**
- Architectural anti-patterns (God objects, tight coupling)
- Missing abstraction layers
- Inconsistent patterns across codebase
- Performance implications of design choices
- Where implementation diverged from intended architecture

**Token Cost:** ~$15 per 1M input tokens

## Sonnet 4.5 - Implementation Design

**Core Strengths:**
- Converting architectural plans into file-level changes
- Algorithm selection and optimization
- Test strategy design
- Refactoring individual modules
- Library/framework integration patterns
- Error handling and edge case analysis
- Code review and bug hypothesis generation

**Coding Scenarios:**
- "Implement this feature according to the architecture"
- "These tests are failing and I don't know why"
- "How should I structure this module?"
- "Which library fits our requirements?"
- "This works for happy path but breaks on edge cases"

**What Sonnet Sees:**
- Implementation details within single files
- Test coverage gaps
- Error handling weaknesses
- Algorithm inefficiencies
- Missing validation logic

**Token Cost:** ~$3 per 1M input tokens

## Haiku 4.5 - Code Execution

**Core Strengths:**
- File scanning and information extraction
- Running tests and reporting results
- Making targeted code edits
- Quick syntax/lint fixes
- Following established patterns
- Iterative bug fixes within defined scope

**Coding Scenarios:**
- "Run the test suite"
- "Scan the repository structure"
- "Fix this linting error"
- "Apply this pattern to similar functions"
- "Check if X is defined anywhere"

**What Haiku Does:**
- Reads files efficiently (scans, doesn't analyze deeply)
- Executes tests, captures output
- Makes small, well-defined code changes
- Searches for patterns across files
- Reports findings to Sonnet

**Token Cost:** ~$1 per 1M input tokens

## Escalation Triggers - Code Edition

### Haiku → Sonnet
- Test failures after 2 fix attempts
- File contains unexpected structure
- Change requires understanding why (not just what)
- Multiple files need coordinated changes
- Error message unclear or contradictory

### Sonnet → Opus
- Solution requires architectural change
- Circular dependency discovered
- Performance issue is systemic, not local
- Pattern inconsistency across codebase
- 3+ modules need refactoring together
- Original architecture assumption broken

## Context Compression - Development

### Haiku → Sonnet (File Analysis)
```
File: path/to/file.py
Lines: 1-250 (of 800 total)
Key structures: Class Auth, function validate_token
Imports: jwt, bcrypt, datetime
Issue: Line 142 - token validation fails for refresh tokens
Attempted: Added expiry check, still failing
Error: KeyError: 'refresh_scope'
```

### Sonnet → Opus (Architectural)
```
Original goal: Add OAuth2 refresh token support
Files modified: auth.py, tokens.py, validators.py
Pattern: Added refresh_scope to Token model
Blocker: Token validation in 5 different places, inconsistent checks
Attempted: Centralized validation function, breaks legacy flows
Architecture issue: No single source of truth for token validation
Scope drift: Now touching session management, user model
```

## Cost Optimization - Development

**Token-heavy operations:**
- Opus analyzing large files directly (DON'T)
- Passing entire test output (compress)
- Re-reading same files (cache in Sonnet context)

**Efficient patterns:**
- Haiku scans, extracts key info → Sonnet
- Sonnet analyzes compressed structures → Opus
- Opus returns architectural directives → Sonnet → Haiku implements
- Cache architectural decisions for session

**When not to orchestrate:**
- Simple syntax fixes (Haiku only)
- Well-scoped feature adds (Sonnet + Haiku)
- Following established pattern (Haiku only)
- Only orchestrate when risk of getting stuck in narrow implementation is high
