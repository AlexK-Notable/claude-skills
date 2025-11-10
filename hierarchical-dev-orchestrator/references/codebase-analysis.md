# Codebase Analysis Workflow

## Purpose
Efficient repository scanning that extracts key info without wasting tokens on full file reads.

## Haiku's Scanning Protocol

### Step 1: Repository Structure
```bash
view /path/to/repo
```

Extract:
- Directory organization
- File counts per directory
- Key configuration files (package.json, requirements.txt, etc.)
- Test directory location

**Output format:**
```
Repo: project-name
Structure:
  /src: 12 files (main code)
  /tests: 8 files (pytest)
  /config: 3 files
  /docs: README, API.md
Tech: Python 3.11, Flask, SQLAlchemy, Redis
Entry: app.py
```

### Step 2: Identify Critical Files

Based on user's request, scan relevant directories:
```bash
view /path/to/relevant/dir
```

Prioritize:
- Files mentioned in error traces
- Entry points (main, app, index)
- Common modules (auth, database, api)
- Test files related to failing tests

### Step 3: Targeted File Reads

Read ONLY what Sonnet needs:
```bash
view /path/to/file.py --view_range [start_line, end_line]
```

For each file, extract:
- Imports (what it depends on)
- Class/function signatures (not implementations)
- Docstrings (what it's supposed to do)
- Problem area (specific lines if known)

**Good compression:**
```
File: auth/validators.py (250 lines)
Classes: TokenValidator, SessionValidator
Key methods:
  - validate_access_token(token: str) -> bool
  - validate_refresh_token(token: str) -> bool (ISSUE HERE)
  - _check_expiry(token: dict) -> bool
Imports: jwt, datetime, redis_client
Issue location: Lines 140-155
```

**Bad (don't do this):**
```
[paste entire 250 lines]
```

### Step 4: Test Execution

Run relevant tests:
```bash
pytest tests/test_auth.py -v --tb=short
# or
npm test auth
# or
cargo test auth
```

Capture:
- Which tests passed/failed
- Error messages (not full traces)
- Changed behavior (if comparing to previous run)

**Output format:**
```
Tests run: 12
Passed: 10
Failed: 2
  - test_refresh_token_validation: KeyError 'refresh_scope'
  - test_refresh_token_expiry: AssertionError expected True, got False
Duration: 0.8s (was 0.6s before changes)
```

## Sonnet's Analysis Protocol

Receives Haiku's compressed findings and:

1. **Identifies patterns** across files
2. **Generates hypotheses** ranked by likelihood
3. **Plans verification steps** for Haiku to execute
4. **Decides if architectural** (escalate to Opus) or implementation (handle it)

**Sonnet should NOT:**
- Ask Haiku to re-read files already scanned
- Request full file dumps
- Analyze code Haiku already compressed well

**Sonnet SHOULD:**
- Request specific additional files if needed
- Ask Haiku to search for patterns: "Check if 'refresh_scope' appears in any other files"
- Design targeted tests: "Add a test that prints the token dict structure"

## Opus Analysis Protocol

Receives Sonnet's compressed analysis:

**Opus should NOT:**
- Request file reads (token waste)
- Micromanage implementation
- Re-analyze what Sonnet already covered

**Opus SHOULD:**
- Evaluate architectural patterns
- Make strategic decisions about approach
- Identify missing abstractions
- Decide between refactor vs patch
- Set clear directives for Sonnet

**Example Opus output:**
```
ARCHITECTURAL DECISION:
Token validation is scattered across 5 files because there's no single
TokenValidator interface. This is causing the refresh_scope inconsistency.

STRATEGY:
1. Create unified TokenValidator protocol
2. Implement for AccessToken and RefreshToken separately
3. Migrate existing validators to use protocol
4. Deprecate scattered validation functions

RATIONALE:
Current approach mixes concerns (validation + business logic).
Future token types (API keys, OAuth) will hit same issue.

NEXT: Sonnet design the protocol interface, Haiku implements.
```

## Caching Strategy

**Within a session:**
- Haiku caches file structures in memory
- Sonnet caches architectural understanding
- Opus decisions persist until scope changes

**Don't re-read:**
- Files already scanned (unless changed)
- Test output (unless re-run)
- Dependency info (unless deps changed)

**Do update:**
- After Haiku makes changes
- After test results change
- When user provides new info

## Efficient Multi-File Analysis

**Scenario:** Bug affects 5 files

**Inefficient approach:**
1. Read all 5 files completely (1000+ lines)
2. Pass all to Sonnet
3. Sonnet overwhelmed

**Efficient approach:**
1. Haiku reads file 1, extracts key info (50 tokens)
2. Passes to Sonnet
3. Sonnet: "Check file 2 for similar pattern"
4. Haiku reads file 2, confirms pattern (30 tokens)
5. Sonnet: "Likely pattern issue, escalate to Opus"
6. Opus receives compressed summary (80 tokens total)

## Search Pattern Optimization

When looking for where something is defined/used:

**Inefficient:**
```bash
# Read every file looking for pattern
view file1.py
view file2.py
view file3.py
...
```

**Efficient:**
```bash
# Use grep to locate first
grep -r "refresh_scope" src/

# Then read only relevant files
view src/auth/validators.py --view_range [140, 160]
```

## Token Budget Awareness

**Rough token costs:**
- Small file scan (< 100 lines): ~300 tokens
- Large file scan (500+ lines): ~1500 tokens
- Test output: ~200-500 tokens
- Directory structure: ~100 tokens

**Escalation costs:**
- Haiku → Sonnet: ~100 tokens (compressed)
- Sonnet → Opus: ~200 tokens (compressed)

**Goal:** Keep total context under 10k tokens per tier
- Haiku: Scans 20+ files efficiently
- Sonnet: Analyzes compressed info from those files
- Opus: Receives 200-500 token summary of entire investigation

## When to Expand Context

**Narrow context (default):**
- Single bug in known file
- Feature add to one module
- Test failure in isolated test

**Expanded context:**
- Cross-cutting concerns (auth, logging)
- Architectural issues
- Performance problems
- Pattern inconsistencies

Haiku signals: "This pattern appears in 5 files" → Sonnet expands investigation
