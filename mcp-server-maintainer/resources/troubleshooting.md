# MCP Server Troubleshooting Guide

Systematic approach to diagnosing and fixing MCP server issues.

---

## Troubleshooting Framework

Use this systematic approach for ANY MCP server issue:

```
1. Can the server run standalone? → Test manually
2. Is the config file correct? → Validate JSON
3. Are paths absolute? → Check all paths
4. Are dependencies installed? → Verify installation
5. Is the command in PATH? → Test with `which`
6. Check logs → Look for error messages
7. Test with minimal config → Isolate the issue
```

---

## Issue 1: Server Not Appearing in Claude

### Symptoms:
- Server not in the MCP servers list
- No errors shown
- Server recently added to config

### Diagnostic Steps:

**Step 1: Verify config file location**
```bash
# Claude Desktop (Mac):
ls -la ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Claude Desktop (Linux):
ls -la ~/.config/Claude/claude_desktop_config.json

# Claude Code (project):
ls -la ./.claude/settings.json

# Claude Code (global):
ls -la ~/.claude/settings.json
```

**Step 2: Validate JSON syntax**
```bash
# Use jq to check syntax:
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | jq .

# Common syntax errors:
# - Missing comma between server entries
# - Trailing comma after last entry
# - Unescaped backslashes in Windows paths
# - Missing quotes around keys/values
```

**Step 3: Check server configuration structure**
```json
{
  "mcpServers": {
    "server-name": {                    ← Server name (alphanumeric, hyphens OK)
      "command": "python",               ← Executable command
      "args": ["/path/to/server.py"],   ← Array of string arguments
      "env": {                           ← Optional environment variables
        "KEY": "value"
      }
    }
  }
}
```

**Step 4: Restart Claude**
```bash
# Claude Desktop: Quit and reopen application
# Claude Code: Exit session and restart

# NOT sufficient:
# - Switching conversations
# - Minimizing window
# - Reloading page
```

### Solutions:

✅ **Fix JSON syntax errors** - Use jq to validate
✅ **Use correct config file** - Different for Desktop vs Code
✅ **Restart application** - Configuration only loads on startup
✅ **Check server name** - No spaces, use hyphens or underscores

---

## Issue 2: "Command not found" Error

### Symptoms:
- Error message: "Command 'python' not found"
- Error message: "Command 'uv' not found"
- Error message: "Command 'node' not found"

### Diagnostic Steps:

**Step 1: Test if command exists**
```bash
which python   # Should show: /usr/bin/python3 or similar
which uv       # Should show: /home/user/.local/bin/uv
which node     # Should show: /usr/bin/node

# If "not found", the command isn't in PATH
```

**Step 2: Find the actual path**
```bash
# Python:
which python3
which python3.10
ls -la /usr/bin/python*

# uv:
ls -la ~/.local/bin/uv
ls -la ~/.cargo/bin/uv

# node:
which node
ls -la /usr/bin/node
ls -la ~/.nvm/versions/node/*/bin/node
```

**Step 3: Test with absolute path**
```bash
# Try running with full path:
/usr/bin/python3 /path/to/server.py
/home/komi/.local/bin/uv run server-name
/usr/bin/node /path/to/build/index.js
```

### Solutions:

✅ **Use absolute path to command**
```json
{
  "mcpServers": {
    "my-server": {
      "command": "/usr/bin/python3",  ← Full path instead of "python"
      "args": ["/home/komi/repos/MCP/my-server/server.py"]
    }
  }
}
```

✅ **Add to PATH** (system-wide solution)
```bash
# Add to ~/.zshrc or ~/.bashrc:
export PATH="$HOME/.local/bin:$PATH"

# Then restart terminal and Claude
```

---

## Issue 3: "Module not found" / Import Errors

### Symptoms:
- Python: "ModuleNotFoundError: No module named 'mcp'"
- Python: "ModuleNotFoundError: No module named 'fastmcp'"
- Node: "Cannot find module '@modelcontextprotocol/sdk'"

### Diagnostic Steps:

**Step 1: Check if dependencies are installed**
```bash
cd ~/repos/MCP/server-name

# Python:
pip list | grep mcp
# OR
uv pip list | grep mcp

# Node:
npm list | grep @modelcontextprotocol
# OR
ls -la node_modules/@modelcontextprotocol/
```

**Step 2: Verify installation method**
```bash
# Check for package definition:
ls -la pyproject.toml setup.py requirements.txt
ls -la package.json

# Check if installed in development mode:
pip show mcp
pip show fastmcp
```

**Step 3: Test import manually**
```bash
# Python:
python -c "import mcp; print(mcp.__version__)"
python -c "from fastmcp import FastMCP; print('OK')"

# Node:
node -e "require('@modelcontextprotocol/sdk')"
```

### Solutions:

✅ **Install dependencies**
```bash
# Python with uv (recommended):
cd ~/repos/MCP/server-name
uv pip install -e .

# Python with pip:
cd ~/repos/MCP/server-name
pip install -e .
# OR
pip install -r requirements.txt

# Node:
cd ~/repos/MCP/server-name
npm install
```

✅ **Add PYTHONPATH if needed**
```json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["/home/komi/repos/MCP/my-server/src/server.py"],
      "env": {
        "PYTHONPATH": "/home/komi/repos/MCP/my-server/src"
      }
    }
  }
}
```

✅ **Use uv's isolated environment**
```json
{
  "mcpServers": {
    "my-server": {
      "command": "uv",
      "args": [
        "--directory",
        "/home/komi/repos/MCP/my-server",
        "run",
        "my-server"
      ]
    }
  }
}
```

---

## Issue 4: Server Crashes Immediately

### Symptoms:
- Server appears in list but doesn't respond
- Error in logs: "Server exited with code 1"
- Tools from server not available

### Diagnostic Steps:

**Step 1: Run server manually to see errors**
```bash
cd ~/repos/MCP/server-name

# Python with uv:
uv run server-name
# You should see initialization messages, NOT immediate crash

# Python directly:
python src/server_name/server.py

# Node:
node build/index.js
```

**Step 2: Check for common crash causes**
```bash
# Missing environment variables:
grep -r "os.environ" src/
grep -r "process.env" src/

# File not found errors:
# Look in server code for file operations

# Permission errors:
ls -la src/server_name/server.py
# Should be readable: rw-r--r--
```

**Step 3: Check entry point**
```bash
# Python - check pyproject.toml:
cat pyproject.toml | grep -A 10 "\[project.scripts\]"
# Should show: server-name = "module.path:main"

# Node - check package.json:
cat package.json | grep -A 5 '"bin"'
# Should show: "bin": { "server-name": "./build/index.js" }
```

### Solutions:

✅ **Fix entry point**
```bash
# If entry point is wrong in pyproject.toml:
# Find the actual main function:
grep -r "def main()" src/
# Update pyproject.toml accordingly

# If entry point is wrong in package.json:
# Find the actual build output:
ls -la build/ dist/
# Update package.json accordingly
```

✅ **Add required environment variables**
```json
{
  "mcpServers": {
    "my-server": {
      "command": "uv",
      "args": ["--directory", "/path/to/server", "run", "server-name"],
      "env": {
        "API_KEY": "your-key-here",
        "DEBUG": "false",
        "LOG_LEVEL": "info"
      }
    }
  }
}
```

✅ **Fix file permissions**
```bash
chmod +x src/server_name/server.py
chmod 644 src/server_name/*.py
```

---

## Issue 5: Works in Claude Desktop, Not in Claude Code (or vice versa)

### Symptoms:
- Server works perfectly in Claude Desktop
- Same server not available in Claude Code
- OR: Opposite situation

### Root Cause:
**They use DIFFERENT configuration files!**

### Solutions:

✅ **Configure for BOTH environments**

**Claude Desktop config** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "my-server": {
      "command": "uv",
      "args": [
        "--directory",
        "/home/komi/repos/MCP/my-server",
        "run",
        "my-server"
      ]
    }
  }
}
```

**Claude Code config** (`~/.claude/settings.json`):
```json
{
  "mcpServers": {
    "my-server": {
      "command": "uv",
      "args": [
        "--directory",
        "/home/komi/repos/MCP/my-server",
        "run",
        "my-server"
      ]
    }
  }
}
```

**Note:** Configuration is nearly identical, but in separate files!

---

## Issue 6: "Permission Denied" Errors

### Symptoms:
- Error: "Permission denied: '/path/to/server.py'"
- Server exists but can't execute

### Diagnostic Steps:

**Step 1: Check file permissions**
```bash
ls -la ~/repos/MCP/server-name/src/server.py
# Should show: -rw-r--r-- or -rwxr-xr-x

# NOT: ---------- (no read permission)
```

**Step 2: Check directory permissions**
```bash
ls -la ~/repos/MCP/server-name/
# Should show: drwxr-xr-x

# Directory needs execute permission to traverse
```

### Solutions:

✅ **Fix file permissions**
```bash
# Make executable:
chmod +x ~/repos/MCP/server-name/src/server.py

# Make readable:
chmod 644 ~/repos/MCP/server-name/src/*.py

# Fix directory permissions:
chmod 755 ~/repos/MCP/server-name/
```

✅ **Use Python/Node to execute** (doesn't require +x)
```json
{
  "command": "python",  ← Python interpreter executes script
  "args": ["/path/to/server.py"]  ← Doesn't need +x permission
}
```

---

## Issue 7: Server Shows Up But Tools Don't Work

### Symptoms:
- Server in MCP list
- No error messages
- Tools from server not available or don't respond

### Diagnostic Steps:

**Step 1: Check if server actually implements tools**
```bash
# Search for tool definitions:
grep -r "@mcp.tool" ~/repos/MCP/server-name/
grep -r "server.tool" ~/repos/MCP/server-name/
grep -r "listTools" ~/repos/MCP/server-name/
```

**Step 2: Test server communication**
```bash
# Try running and sending MCP protocol messages:
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python server.py

# Should get JSON-RPC response with tools list
```

**Step 3: Check logs for initialization errors**
```bash
# Claude Desktop logs:
tail -100 ~/Library/Logs/Claude/mcp-*.log | grep "my-server"
```

### Solutions:

✅ **Verify server implements MCP protocol correctly**
```python
# Server should have tool definitions:
from mcp.server import Server

server = Server("my-server")

@server.tool()
def my_tool(arg: str) -> str:
    return f"Result: {arg}"
```

✅ **Check for stdio communication issues**
```bash
# Server must:
# - Read from stdin (not keyboard input)
# - Write to stdout (not print debug messages)
# - Use stderr for debug/logs (not stdout)
```

---

## Issue 8: Relative Path Errors

### Symptoms:
- Error: "No such file or directory: './server.py'"
- Error: "Cannot find module '../build/index.js'"

### Root Cause:
**MCP configuration requires ABSOLUTE paths**

### Solutions:

✅ **Convert ALL paths to absolute**
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

✅ **Use $CLAUDE_PROJECT_DIR for Claude Code**
```json
{
  "command": "python",
  "args": ["$CLAUDE_PROJECT_DIR/mcp-servers/my-server/server.py"]
}
```

---

## Debugging Workflow Checklist

Use this checklist when troubleshooting ANY MCP server:

```
□ Server runs standalone (manual execution works)
□ Dependencies installed (pip/npm list shows packages)
□ Config file has correct JSON syntax (jq validation passes)
□ Using absolute paths (no ./ or ../)
□ Command in PATH or using absolute path
□ Configuration in correct file (Desktop vs Code)
□ Restarted Claude after config changes
□ Checked logs for error messages
□ Entry point correct (pyproject.toml or package.json)
□ Environment variables set if needed
□ File permissions correct (readable/executable)
□ Server implements MCP protocol correctly
```

---

## Quick Test: Minimal Working Config

Test with this minimal configuration first:

```json
{
  "mcpServers": {
    "test-echo": {
      "command": "python",
      "args": ["-m", "http.server", "0"]
    }
  }
}
```

If even this fails:
- Configuration file is wrong location
- JSON syntax error
- Claude not reading config at all
- Need to restart Claude

If this works but your server doesn't:
- Problem is with server-specific config
- Check server path, dependencies, entry point

---

## Common Error Messages Decoded

| Error Message | Meaning | Solution |
|---------------|---------|----------|
| "Command not found: python" | Python not in PATH | Use absolute path: /usr/bin/python3 |
| "ModuleNotFoundError: mcp" | Dependencies not installed | Run: pip install -e . |
| "No such file: ./server.py" | Relative path used | Use absolute path |
| "Permission denied" | File not executable | Run: chmod +x server.py |
| "Server exited with code 1" | Server crashed on start | Run manually to see error |
| "JSON parse error" | Invalid JSON syntax | Use jq to validate |
| "Cannot find module 'mcp'" | Node deps not installed | Run: npm install |
| "Connection refused" | Server not using stdio | Check server code |

---

## When All Else Fails

1. **Start from scratch:**
   ```bash
   # Remove server from config
   # Delete node_modules / .venv
   # Reinstall dependencies
   # Add server back with minimal config
   ```

2. **Compare with working example:**
   ```bash
   # Find a server that works
   # Compare configuration line by line
   # Look for differences in paths, commands, args
   ```

3. **Test with official MCP servers:**
   ```json
   {
     "mcpServers": {
       "memory": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-memory"]
       }
     }
   }
   ```
   If official servers work, issue is with your custom server.

4. **Check GitHub issues:**
   ```bash
   # Many MCP servers have known issues
   # Check the server's GitHub Issues tab
   # Look for similar error messages
   ```

---

## Prevention: Before Adding New Servers

**Checklist before adding to Claude config:**

```bash
□ Clone/download server to ~/repos/MCP/
□ Read the README for installation instructions
□ Install dependencies (pip install -e . OR npm install)
□ Test manual execution (python server.py OR node index.js)
□ Note the entry point (python -m package OR npx package)
□ Identify any required environment variables
□ Use absolute paths in configuration
□ Add to BOTH Claude Desktop AND Claude Code if needed
□ Restart Claude after adding
□ Verify server appears in MCP list
□ Test one tool to confirm it works
```

---

**Key Takeaway:** 90% of MCP server issues are:
1. Wrong paths (use absolute)
2. Missing dependencies (install first)
3. Wrong config file (Desktop vs Code are different)
4. Not restarted (config loads on startup only)

**Always start by testing the server manually outside of Claude!**
