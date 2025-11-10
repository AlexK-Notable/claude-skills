---
name: mcp-server-maintainer
description: Installing, configuring, and troubleshooting MCP servers for Claude Desktop and Claude Code
---

# MCP Server Installer/Maintainer

**Purpose:** Systematically install, configure, debug, and maintain MCP (Model Context Protocol) servers across your development environment.

**Use this skill when:**
- Installing a new MCP server from a repository
- MCP server not appearing in Claude Desktop or Claude Code
- Server connection failures or crashes
- Updating or maintaining existing MCP servers
- Configuring servers for different Claude environments
- Debugging "Server not found" or "Connection refused" errors

---

## Quick Decision Tree

```
Is the server showing up?
├─ NO → Check Configuration (resources/configuration-*.md)
│   ├─ Correct config file? (Claude Desktop vs Claude Code)
│   ├─ Correct paths? (absolute paths required)
│   └─ Correct command? (node, python, uv, etc.)
│
└─ YES, but errors → Check Common Errors (resources/common-errors.md)
    ├─ Import errors → Python/Node dependencies
    ├─ Permission errors → File permissions/executable
    ├─ Connection errors → Stdio transport issues
    └─ Crashes on start → Check logs (resources/debugging.md)
```

---

## Critical Differences: Claude Desktop vs Claude Code

| Aspect | Claude Desktop | Claude Code |
|--------|---------------|-------------|
| **Config File** | `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac)<br>`%APPDATA%\Claude\claude_desktop_config.json` (Windows)<br>`~/.config/Claude/claude_desktop_config.json` (Linux) | `$CLAUDE_PROJECT_DIR/.claude/settings.json`<br>OR `~/.claude/settings.json` (global) |
| **Config Section** | `"mcpServers": {}` at root level | `"mcpServers": {}` at root level |
| **Scope** | Global (all conversations) | Project-specific OR global |
| **Path Requirements** | Absolute paths only | Can use `$CLAUDE_PROJECT_DIR` variable |
| **Reload** | Restart Claude Desktop app | Restart Claude Code session |

⚠️ **CRITICAL:** These are SEPARATE configurations. Installing for one does NOT install for the other!

---

## Installation Checklist

Before configuring ANY MCP server, verify:

```bash
# 1. Server exists and is in correct location
ls -la ~/repos/MCP/server-name/

# 2. Dependencies installed (choose appropriate command)
## Python servers:
cd ~/repos/MCP/server-name && python -m pip install -e .
# OR
cd ~/repos/MCP/server-name && uv pip install -e .

## Node.js servers:
cd ~/repos/MCP/server-name && npm install

## Go servers:
cd ~/repos/MCP/server-name && go build

# 3. Server can be executed manually
## Python:
python ~/repos/MCP/server-name/server.py
## OR
uv run ~/repos/MCP/server-name/server.py

## Node:
node ~/repos/MCP/server-name/build/index.js

# 4. Check for entry point scripts
ls -la ~/repos/MCP/server-name/bin/
ls -la ~/repos/MCP/server-name/src/

# 5. Verify it's an MCP server (look for MCP imports)
grep -r "from mcp" ~/repos/MCP/server-name/
grep -r "@modelcontextprotocol/sdk" ~/repos/MCP/server-name/
```

---

## Configuration Patterns

### Python MCP Server (uv)

**Claude Desktop:**
```json
{
  "mcpServers": {
    "server-name": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/server-directory",
        "run",
        "server-name"
      ]
    }
  }
}
```

**Claude Code (project-specific):**
```json
{
  "mcpServers": {
    "server-name": {
      "command": "uv",
      "args": [
        "--directory",
        "$CLAUDE_PROJECT_DIR/path/to/server",
        "run",
        "server-name"
      ]
    }
  }
}
```

### Python MCP Server (pip + python)

```json
{
  "mcpServers": {
    "server-name": {
      "command": "python",
      "args": [
        "/absolute/path/to/server/src/server.py"
      ],
      "env": {
        "PYTHONPATH": "/absolute/path/to/server/src"
      }
    }
  }
}
```

### Node.js MCP Server

```json
{
  "mcpServers": {
    "server-name": {
      "command": "node",
      "args": [
        "/absolute/path/to/server/build/index.js"
      ]
    }
  }
}
```

### Node.js MCP Server (with npx)

```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-name"
      ]
    }
  }
}
```

---

## Common Pitfalls

### 1. Relative Paths (DON'T USE)
```json
❌ WRONG:
"args": ["./server.py"]
"args": ["../MCP/server/server.py"]

✅ CORRECT:
"args": ["/home/komi/repos/MCP/server/server.py"]
```

### 2. Missing uv/python in PATH
```bash
# Test if command is available:
which uv
which python
which node

# If not found, use absolute path:
"command": "/home/komi/.local/bin/uv"
"command": "/usr/bin/python3"
```

### 3. Wrong Entry Point
```bash
# Find the correct entry point:
cat pyproject.toml | grep -A 5 "\[project.scripts\]"
cat package.json | grep -A 5 "bin"

# Common entry points:
# Python: src/server_name/__main__.py OR src/server_name/server.py
# Node: build/index.js OR dist/index.js OR src/index.ts
```

### 4. Environment Variables Not Set
```json
{
  "mcpServers": {
    "server-name": {
      "command": "...",
      "args": [...],
      "env": {
        "API_KEY": "your-key-here",
        "PYTHONPATH": "/path/to/server/src",
        "NODE_ENV": "production"
      }
    }
  }
}
```

---

## Debugging Workflow

### Step 1: Verify Server Runs Standalone
```bash
# Try to run the server manually:
cd ~/repos/MCP/server-name

# Python with uv:
uv run server-name

# Python directly:
python src/server_name/server.py

# Node.js:
node build/index.js

# Expected output:
# - Server starts without errors
# - Listens on stdio (reads from stdin, writes to stdout)
# - May show "MCP Server initialized" or similar
```

### Step 2: Check Configuration File

**For Claude Desktop:**
```bash
# Find config file:
## Mac:
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

## Linux:
cat ~/.config/Claude/claude_desktop_config.json

# Validate JSON syntax:
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | jq .
```

**For Claude Code:**
```bash
# Project-specific:
cat $CLAUDE_PROJECT_DIR/.claude/settings.json | jq .mcpServers

# Global:
cat ~/.claude/settings.json | jq .mcpServers
```

### Step 3: Check Logs

**Claude Desktop logs:**
```bash
# Mac:
tail -f ~/Library/Logs/Claude/mcp*.log

# Linux:
tail -f ~/.config/Claude/logs/mcp*.log
```

**Claude Code logs:**
```bash
# Check Claude Code debug output
# (shown in terminal where Claude Code is running)
```

### Step 4: Test with MCP Inspector
```bash
# Install MCP inspector (if available):
npx @modelcontextprotocol/inspector

# Point it at your server config
# This helps debug stdio communication issues
```

---

## Server Installation Patterns by Language

### Python Servers (uv method - RECOMMENDED)

```bash
# 1. Clone/navigate to server
cd ~/repos/MCP/
git clone https://github.com/username/mcp-server-name

# 2. Check for pyproject.toml
cd mcp-server-name
cat pyproject.toml

# 3. Install with uv (preferred)
uv pip install -e .

# 4. Find the entry point
cat pyproject.toml | grep -A 5 "\[project.scripts\]"
# Look for: server-name = "module.path:function"

# 5. Test execution
uv run server-name

# 6. Configure in Claude
# Use "command": "uv" with "args": ["--directory", "/full/path", "run", "server-name"]
```

### Python Servers (pip method)

```bash
# 1. Create/activate virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -e .
# OR
pip install -r requirements.txt

# 3. Find entry point (usually src/package_name/__main__.py)
python -m package_name
# OR
python src/package_name/server.py

# 4. Configure in Claude
# Use "command": "python" with "args": ["/full/path/to/server.py"]
```

### Node.js Servers

```bash
# 1. Navigate to server
cd ~/repos/MCP/mcp-server-name

# 2. Install dependencies
npm install

# 3. Build (if TypeScript)
npm run build
# OR
npx tsc

# 4. Find entry point
cat package.json | grep -A 5 "bin"
# OR look in build/index.js or dist/index.js

# 5. Test execution
node build/index.js

# 6. Configure in Claude
# Use "command": "node" with "args": ["/full/path/to/build/index.js"]
```

### Published npm Packages

```bash
# No installation needed! Use npx:
# Configure in Claude:
{
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-name"]
}
```

---

## Troubleshooting Quick Reference

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| Server not in list | Config file error | Check JSON syntax, restart app |
| "Command not found" | Wrong command path | Use absolute path: `which uv` |
| "Module not found" | Dependencies not installed | Run `pip install -e .` or `npm install` |
| "Permission denied" | Not executable | `chmod +x server.py` |
| Server crashes immediately | Wrong entry point | Check pyproject.toml or package.json |
| "Connection refused" | Stdio transport issue | Server must read stdin/write stdout |
| Works in Desktop, not Code | Separate configs | Configure in BOTH places |
| Import errors | PYTHONPATH not set | Add `"env": {"PYTHONPATH": "/path"}` |

---

## Resource Files (Detailed Guides)

📚 **For detailed guidance, see:**

- **resources/installation-patterns.md** - Step-by-step installation for each language/package manager
- **resources/claude-desktop-config.md** - Complete guide to configuring Claude Desktop
- **resources/claude-code-config.md** - Complete guide to configuring Claude Code
- **resources/troubleshooting.md** - Systematic debugging approach for connection issues
- **resources/common-errors.md** - Comprehensive error catalog with solutions
- **resources/testing-validation.md** - How to test servers before configuring Claude

---

## Your MCP Server Repository Pattern

Based on your `~/repos/MCP/` directory structure:

```bash
# You have 30+ MCP servers in ~/repos/MCP/
# To systematically install and maintain them:

# 1. Create a maintenance script:
cat > ~/repos/MCP/install-all.sh << 'EOF'
#!/bin/bash
for server in ~/repos/MCP/*/; do
  echo "Installing $(basename $server)..."
  if [ -f "$server/pyproject.toml" ]; then
    cd "$server" && uv pip install -e . || pip install -e .
  elif [ -f "$server/package.json" ]; then
    cd "$server" && npm install
  elif [ -f "$server/go.mod" ]; then
    cd "$server" && go build
  fi
done
EOF
chmod +x ~/repos/MCP/install-all.sh

# 2. Run it:
~/repos/MCP/install-all.sh

# 3. Test each server individually:
for server in ~/repos/MCP/*/; do
  echo "Testing $(basename $server)..."
  # Try to run it (will fail if not an MCP server, that's OK)
  # Python:
  (cd "$server" && timeout 2s uv run $(basename $server) 2>&1 | head -5)
  # Node:
  (cd "$server" && timeout 2s node build/index.js 2>&1 | head -5)
done
```

---

## When This Skill Activates

**Prompt triggers:**
- "install mcp server"
- "mcp not working"
- "server not found"
- "configure mcp"
- "mcp connection error"

**File triggers:**
- Working in `~/repos/MCP/**/*`
- Editing `claude_desktop_config.json`
- Editing `.claude/settings.json` mcpServers section

**Use explicitly when:**
- Adding a new MCP server from GitHub
- Updating an existing MCP server
- Troubleshooting why a server isn't appearing
- Moving servers between machines

---

## Next Steps After Installation

1. **Verify in Claude:**
   - Restart Claude Desktop or Claude Code
   - Check that server appears in available tools
   - Try using a tool from the server

2. **Document configuration:**
   - Keep track of what servers you've installed
   - Note any custom environment variables needed
   - Document any special setup steps

3. **Update regularly:**
   - MCP servers are actively developed
   - Pull latest changes: `cd ~/repos/MCP/server && git pull`
   - Reinstall: `uv pip install -e .` or `npm install`

---

## Common Success Patterns

**Pattern: Python server with uv (RECOMMENDED)**
```json
{
  "mcpServers": {
    "my-server": {
      "command": "uv",
      "args": ["--directory", "/home/komi/repos/MCP/my-server", "run", "my-server"]
    }
  }
}
```

**Pattern: Node.js built server**
```json
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["/home/komi/repos/MCP/my-server/build/index.js"]
    }
  }
}
```

**Pattern: Published npm package**
```json
{
  "mcpServers": {
    "official-server": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-name"]
    }
  }
}
```

---

## Red Flags (Common Mistakes)

🚩 **Using relative paths** - Always use absolute paths
🚩 **Forgetting to install dependencies** - Run `pip install -e .` or `npm install`
🚩 **Wrong Python/Node in PATH** - Test with `which python`, `which node`
🚩 **Configuring only Claude Desktop OR Code** - They're separate!
🚩 **Not restarting after config changes** - Always restart!
🚩 **Copying configs from different OS** - Paths differ (Mac, Linux, Windows)
🚩 **Missing environment variables** - Check if server needs API keys

---

**Remember:** MCP servers communicate via stdio (standard input/output). They should:
- Read JSON-RPC messages from stdin
- Write JSON-RPC responses to stdout
- NOT print debug messages to stdout (use stderr or logs)

If a server isn't working, it's usually: wrong path, missing dependencies, or incorrect entry point.

📋 **Start with the troubleshooting checklist in resources/troubleshooting.md**
