# MCP Server Common Errors Reference

Comprehensive catalog of error messages and their solutions.

---

## Python Errors

### Error: "ModuleNotFoundError: No module named 'mcp'"

**Full error:**
```
Traceback (most recent call last):
  File "/path/to/server.py", line 1, in <module>
    from mcp.server import Server
ModuleNotFoundError: No module named 'mcp'
```

**Cause:** MCP SDK not installed

**Solutions:**
```bash
# Option 1: Install with uv (recommended)
cd ~/repos/MCP/server-name
uv pip install mcp

# Option 2: Install with pip
pip install mcp

# Option 3: Install server package (includes mcp as dependency)
pip install -e .
```

**Verify fix:**
```bash
python -c "import mcp; print('MCP installed:', mcp.__version__)"
```

---

### Error: "ModuleNotFoundError: No module named 'fastmcp'"

**Cause:** FastMCP package not installed

**Solutions:**
```bash
# Install FastMCP:
pip install fastmcp
# OR
uv pip install fastmcp

# If server has pyproject.toml:
pip install -e .
```

---

### Error: "No module named 'server_name'"

**Full error:**
```
ModuleNotFoundError: No module named 'my_server'
```

**Cause:** Server package not installed in development mode

**Solutions:**
```bash
cd ~/repos/MCP/my-server

# Install in editable mode:
pip install -e .
# OR
uv pip install -e .

# This creates a link to the source code
# so Python can import the package
```

**Verify fix:**
```bash
python -c "import my_server; print('OK')"
```

---

### Error: "python: can't open file './server.py': [Errno 2] No such file or directory"

**Cause:** Using relative path in MCP configuration

**Solutions:**
```json
❌ WRONG:
{
  "command": "python",
  "args": ["./server.py"]
}

✅ CORRECT:
{
  "command": "python",
  "args": ["/home/komi/repos/MCP/my-server/src/server.py"]
}
```

---

### Error: "ImportError: attempted relative import with no known parent package"

**Full error:**
```
ImportError: attempted relative import with no known parent package
```

**Cause:** Running server as script instead of module

**Solutions:**
```bash
❌ WRONG:
python src/server.py

✅ CORRECT:
python -m server_name
# OR
pip install -e . && server-name
```

**In MCP config:**
```json
{
  "command": "python",
  "args": ["-m", "server_name"]
}
```

---

### Error: "[Errno 13] Permission denied: '/path/to/server.py'"

**Cause:** File not readable or executable

**Solutions:**
```bash
# Check permissions:
ls -la /path/to/server.py

# Make executable:
chmod +x /path/to/server.py

# OR ensure readable:
chmod 644 /path/to/server.py
```

---

## Node.js Errors

### Error: "Cannot find module '@modelcontextprotocol/sdk'"

**Full error:**
```
Error: Cannot find module '@modelcontextprotocol/sdk'
```

**Cause:** MCP SDK not installed

**Solutions:**
```bash
cd ~/repos/MCP/server-name

# Install dependencies:
npm install

# Or install SDK explicitly:
npm install @modelcontextprotocol/sdk
```

**Verify fix:**
```bash
npm list @modelcontextprotocol/sdk
```

---

### Error: "Cannot find module './build/index.js'"

**Cause:** TypeScript not compiled to JavaScript

**Solutions:**
```bash
cd ~/repos/MCP/server-name

# Build TypeScript:
npm run build
# OR
npx tsc

# Check build output:
ls -la build/ dist/
```

**In MCP config, use built file:**
```json
{
  "command": "node",
  "args": ["/home/komi/repos/MCP/server-name/build/index.js"]
}
```

---

### Error: "npm ERR! missing script: build"

**Cause:** No build script in package.json

**Solutions:**
```bash
# Check package.json for scripts:
cat package.json | jq .scripts

# If no build script, compile manually:
npx tsc

# OR check if it's pure JavaScript (no build needed):
ls -la src/*.js
# If JavaScript files exist, use them directly
```

---

## Command Errors

### Error: "zsh: command not found: uv"

**Cause:** uv not installed or not in PATH

**Solutions:**
```bash
# Check if uv is installed:
which uv

# If not found, install:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or use absolute path in config:
{
  "command": "/home/komi/.local/bin/uv",
  "args": ["--directory", "/path/to/server", "run", "server-name"]
}
```

---

### Error: "command not found: python"

**Cause:** python not in PATH

**Solutions:**
```bash
# Find python:
which python3
which python3.10
ls -la /usr/bin/python*

# Use absolute path in config:
{
  "command": "/usr/bin/python3",
  "args": ["/path/to/server.py"]
}
```

---

### Error: "command not found: node"

**Cause:** Node.js not installed or not in PATH

**Solutions:**
```bash
# Check if node exists:
which node

# If using nvm:
which node
# Will show: ~/.nvm/versions/node/v18.0.0/bin/node

# Use absolute path in config:
{
  "command": "/home/komi/.nvm/versions/node/v18.0.0/bin/node",
  "args": ["/path/to/server/build/index.js"]
}
```

---

## Configuration Errors

### Error: JSON parse error in config file

**Error message in Claude:**
```
Failed to load configuration
JSON parse error at line X
```

**Common causes:**
```json
// Missing comma:
{
  "server1": {...}   ← Missing comma here
  "server2": {...}
}

// Trailing comma:
{
  "server1": {...},
  "server2": {...},  ← Trailing comma not allowed
}

// Unescaped backslash (Windows):
"args": ["C:\Users\path"]  ← Wrong
"args": ["C:\\Users\\path"]  ← Correct

// Missing quotes:
{
  command: "python"  ← Wrong (no quotes on key)
  "command": "python"  ← Correct
}
```

**Solutions:**
```bash
# Validate JSON with jq:
cat config.json | jq .

# If error, jq will show exact line
# Fix the syntax error and validate again
```

---

### Error: Server not showing up after adding to config

**Cause:** Claude not restarted, or wrong config file

**Solutions:**
```bash
# 1. Verify correct config file:

# Claude Desktop (Mac):
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Claude Desktop (Linux):
cat ~/.config/Claude/claude_desktop_config.json

# Claude Code:
cat ~/.claude/settings.json
# OR
cat $CLAUDE_PROJECT_DIR/.claude/settings.json

# 2. Validate JSON:
cat config.json | jq .

# 3. FULLY restart Claude:
# - Claude Desktop: Quit app completely (not just close window)
# - Claude Code: Exit session and restart
```

---

## Runtime Errors

### Error: "Server exited with code 1"

**Cause:** Server crashed during startup

**Solutions:**
```bash
# Run server manually to see actual error:
cd ~/repos/MCP/server-name

# Python:
python src/server_name/server.py
# OR
uv run server-name

# Node:
node build/index.js

# Look for error messages like:
# - Missing environment variables
# - File not found
# - Import errors
# - Syntax errors

# Fix the error, then test again
```

---

### Error: "Connection refused"

**Cause:** Server not communicating via stdio properly

**MCP protocol requirements:**
- Server must read from stdin (standard input)
- Server must write to stdout (standard output)
- Server must NOT print debug messages to stdout

**Solutions:**
```python
# ❌ WRONG - Debug prints to stdout:
print("Debug: starting server")  # This breaks MCP protocol

# ✅ CORRECT - Debug to stderr:
import sys
print("Debug: starting server", file=sys.stderr)

# ✅ CORRECT - Use logging:
import logging
logging.basicConfig(level=logging.INFO)
logging.info("Starting server")  # Goes to stderr by default
```

---

### Error: "Timeout waiting for server response"

**Cause:** Server not responding to MCP protocol messages

**Diagnostic:**
```bash
# Test server manually with protocol message:
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python server.py

# Should get JSON-RPC response
# If nothing, server not reading stdin
# If crashes, check error messages
```

**Solutions:**
- Ensure server implements MCP protocol correctly
- Check server actually processes stdin/stdout
- Verify server initialization completes

---

## Environment Variable Errors

### Error: "KeyError: 'API_KEY'"

**Cause:** Required environment variable not set

**Solutions:**
```json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["/path/to/server.py"],
      "env": {
        "API_KEY": "your-api-key-here",
        "DATABASE_URL": "postgresql://...",
        "DEBUG": "false"
      }
    }
  }
}
```

**Finding required variables:**
```bash
# Search server code for environment variables:
grep -r "os.environ" src/
grep -r "process.env" src/

# Check README for required variables:
grep -i "environment" README.md
grep -i "API" README.md
```

---

## Path Errors

### Error: "FileNotFoundError: [Errno 2] No such file or directory"

**Cause:** Server trying to access file with relative path

**Solutions:**
```python
# ❌ WRONG - Relative path:
with open("./data/config.json") as f:
    ...

# ✅ CORRECT - Absolute path:
import os
config_path = os.path.join(os.path.dirname(__file__), "data", "config.json")
with open(config_path) as f:
    ...

# ✅ CORRECT - Use PYTHONPATH:
{
  "env": {
    "PYTHONPATH": "/home/komi/repos/MCP/server-name/src"
  }
}
```

---

## Package Manager Errors

### Error: "error: externally-managed-environment"

**Full error:**
```
error: externally-managed-environment

× This environment is externally managed
```

**Cause:** Trying to use pip in system Python (Linux)

**Solutions:**
```bash
# Option 1: Use uv (recommended):
uv pip install mcp

# Option 2: Use virtual environment:
python -m venv venv
source venv/bin/activate
pip install mcp

# Option 3: Use --break-system-packages (NOT recommended):
pip install --break-system-packages mcp
```

---

### Error: "npm ERR! code ENOENT"

**Cause:** npm dependencies not installed

**Solutions:**
```bash
cd ~/repos/MCP/server-name

# Install dependencies:
npm install

# If package-lock.json exists:
npm ci  # Clean install
```

---

## Specific MCP Server Errors

### FastMCP Servers

**Error: "AttributeError: 'FastMCP' object has no attribute 'tool'"**

**Cause:** Old FastMCP API or wrong decorator

**Solutions:**
```python
# ✅ Correct FastMCP usage:
from fastmcp import FastMCP

mcp = FastMCP("server-name")

@mcp.tool()
def my_tool(arg: str) -> str:
    return f"Result: {arg}"

if __name__ == "__main__":
    mcp.run()
```

---

### MCP SDK Servers

**Error: "Server did not return proper initialization response"**

**Cause:** Server not implementing initialization correctly

**Solutions:**
```python
# Ensure server responds to initialize:
from mcp.server import Server

server = Server("my-server")

@server.initialize()
async def initialize():
    # Initialization logic
    return {"capabilities": {...}}
```

---

## Debugging Checklist by Error Type

**"Command not found" errors:**
```
□ Check command exists: which <command>
□ Use absolute path in config
□ Verify command is in PATH
```

**"Module not found" errors:**
```
□ Dependencies installed: pip list / npm list
□ Installed in editable mode: pip install -e .
□ PYTHONPATH set if needed
```

**"Permission denied" errors:**
```
□ File is readable: ls -la file.py
□ File is executable if script: chmod +x file.py
□ Directory has execute permission
```

**"Server crashed" errors:**
```
□ Run manually to see error
□ Check for missing env variables
□ Check entry point is correct
□ Check dependencies installed
```

**"Connection refused" errors:**
```
□ Server uses stdin/stdout correctly
□ No debug prints to stdout
□ Server implements MCP protocol
```

---

## Quick Reference: Error to Solution

| If you see... | It means... | Quick fix... |
|---------------|-------------|--------------|
| "command not found" | Command not in PATH | Use absolute path |
| "ModuleNotFoundError" | Dependencies missing | Run pip/npm install |
| "No such file" | Relative path used | Use absolute path |
| "Permission denied" | File not executable | chmod +x file |
| "exited with code 1" | Server crashed | Run manually to see why |
| "Connection refused" | Stdio issue | Check stdout usage |
| JSON parse error | Config syntax wrong | Use jq to validate |
| "KeyError" | Missing env variable | Add to "env" in config |

---

**Remember:** Most errors can be diagnosed by running the server manually outside of Claude!

```bash
# Always test standalone first:
cd ~/repos/MCP/server-name
python src/server.py  # OR: uv run server-name  # OR: node build/index.js

# If this fails, fix it first before adding to Claude
# If this works, problem is in Claude configuration
```
