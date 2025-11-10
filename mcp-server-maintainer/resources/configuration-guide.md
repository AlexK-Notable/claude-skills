# MCP Server Configuration Guide

Complete guide to configuring MCP servers for Claude Desktop and Claude Code.

---

## Configuration File Locations

### Claude Desktop

**Mac:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Linux:**
```
~/.config/Claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

### Claude Code

**Project-specific:**
```
$CLAUDE_PROJECT_DIR/.claude/settings.json
```

**Global:**
```
~/.claude/settings.json
```

---

## Basic Structure

Both Claude Desktop and Claude Code use the same `mcpServers` structure:

```json
{
  "mcpServers": {
    "server-name": {
      "command": "executable-name",
      "args": ["arg1", "arg2", "..."],
      "env": {
        "VARIABLE": "value"
      }
    },
    "another-server": {
      "command": "...",
      "args": [...]
    }
  }
}
```

**Key points:**
- `mcpServers` is an object at the root level
- Each server has a unique name (key)
- `command` is the executable to run
- `args` is an array of string arguments
- `env` is optional, for environment variables

---

## Configuration Templates

### Python Server with uv (RECOMMENDED)

```json
{
  "mcpServers": {
    "my-python-server": {
      "command": "uv",
      "args": [
        "--directory",
        "/home/komi/repos/MCP/my-python-server",
        "run",
        "my-python-server"
      ]
    }
  }
}
```

**Why uv is recommended:**
- Handles virtual environments automatically
- Fast and reliable
- No PYTHONPATH issues
- Isolated dependencies

---

### Python Server with pip

```json
{
  "mcpServers": {
    "my-python-server": {
      "command": "python",
      "args": [
        "/home/komi/repos/MCP/my-python-server/src/server.py"
      ],
      "env": {
        "PYTHONPATH": "/home/komi/repos/MCP/my-python-server/src"
      }
    }
  }
}
```

**When to use:**
- Server doesn't use pyproject.toml
- Simple single-file server
- You prefer pip over uv

---

### Node.js Server (built)

```json
{
  "mcpServers": {
    "my-node-server": {
      "command": "node",
      "args": [
        "/home/komi/repos/MCP/my-node-server/build/index.js"
      ]
    }
  }
}
```

**Prerequisites:**
- Server built: `npm run build` or `npx tsc`
- Dependencies installed: `npm install`

---

### Published npm Package

```json
{
  "mcpServers": {
    "published-server": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-name"
      ]
    }
  }
}
```

**Advantages:**
- No local installation needed
- Always uses latest version
- Easy to configure

---

### Go Server

```json
{
  "mcpServers": {
    "my-go-server": {
      "command": "/home/komi/repos/MCP/my-go-server/server",
      "args": []
    }
  }
}
```

**Prerequisites:**
- Server compiled: `go build -o server`

---

## Environment Variables

### When to Use env

```json
{
  "mcpServers": {
    "server-with-api": {
      "command": "python",
      "args": ["/path/to/server.py"],
      "env": {
        "API_KEY": "your-api-key-here",
        "DATABASE_URL": "postgresql://user:pass@localhost/db",
        "DEBUG": "false",
        "LOG_LEVEL": "info",
        "PYTHONPATH": "/path/to/server/src"
      }
    }
  }
}
```

**Common use cases:**
- API keys and secrets
- Database URLs
- Feature flags (DEBUG, VERBOSE, etc.)
- PYTHONPATH for Python imports
- NODE_ENV for Node.js

---

## Path Handling

### Absolute vs Relative Paths

```json
❌ WRONG - Relative paths:
{
  "command": "python",
  "args": ["./server.py"]
}
{
  "command": "python",
  "args": ["../MCP/server/server.py"]
}

✅ CORRECT - Absolute paths:
{
  "command": "python",
  "args": ["/home/komi/repos/MCP/server/server.py"]
}
```

**Rule:** ALWAYS use absolute paths in `args`

---

### Using $CLAUDE_PROJECT_DIR (Claude Code only)

```json
{
  "mcpServers": {
    "project-server": {
      "command": "python",
      "args": [
        "$CLAUDE_PROJECT_DIR/mcp-servers/my-server/server.py"
      ]
    }
  }
}
```

**When to use:**
- Server is part of the project repository
- Want portability across machines
- Project-specific tools

**NOT available in Claude Desktop!**

---

## Multiple Servers Configuration

```json
{
  "mcpServers": {
    "python-server-1": {
      "command": "uv",
      "args": ["--directory", "/path/to/server1", "run", "server1"]
    },
    "python-server-2": {
      "command": "python",
      "args": ["/path/to/server2/server.py"]
    },
    "node-server": {
      "command": "node",
      "args": ["/path/to/server3/build/index.js"]
    },
    "npm-package": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    }
  }
}
```

**Important:**
- Each server needs unique name
- Comma after each server (except last)
- No trailing comma after last server

---

## Platform-Specific Paths

### macOS / Linux

```json
{
  "command": "python",
  "args": ["/home/user/repos/MCP/server/server.py"]
}
```

### Windows

```json
{
  "command": "python",
  "args": ["C:\\Users\\User\\repos\\MCP\\server\\server.py"]
}
```

**Note:** Backslashes must be escaped (`\\`) in JSON

---

## Validation

### Check JSON Syntax

```bash
# Mac:
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | jq .

# Linux:
cat ~/.config/Claude/claude_desktop_config.json | jq .

# Claude Code:
cat ~/.claude/settings.json | jq .
```

**If jq shows error:**
- Look for missing commas
- Check for trailing commas
- Verify quotes around all strings
- Check for unescaped backslashes

---

### Test Server Configuration

```bash
# Extract server command and args from config:
cat config.json | jq '.mcpServers["server-name"]'

# Then test manually:
uv --directory /path/to/server run server-name
# OR
python /path/to/server.py
# OR
node /path/to/build/index.js
```

---

## Configuration Workflow

### Adding a New Server

**Step 1: Install server**
```bash
cd ~/repos/MCP/new-server
pip install -e .  # OR: npm install
```

**Step 2: Test manual execution**
```bash
uv run new-server  # OR: python server.py  # OR: node build/index.js
```

**Step 3: Find entry point**
```bash
# Python:
cat pyproject.toml | grep -A 5 "\[project.scripts\]"

# Node:
cat package.json | grep -A 5 '"bin"'
```

**Step 4: Add to config file**
```json
{
  "mcpServers": {
    "new-server": {
      "command": "uv",
      "args": [
        "--directory",
        "/home/komi/repos/MCP/new-server",
        "run",
        "new-server"
      ]
    }
  }
}
```

**Step 5: Validate JSON**
```bash
cat config.json | jq .
```

**Step 6: Restart Claude**
- Claude Desktop: Quit and reopen
- Claude Code: Exit session and restart

**Step 7: Verify**
- Check server appears in MCP list
- Try using a tool from the server

---

## Troubleshooting Configuration

### Server Not Appearing

```
□ Config file in correct location?
□ JSON syntax valid? (use jq)
□ Claude restarted after changes?
□ Server name alphanumeric (no spaces)?
```

### Server Appears But Doesn't Work

```
□ Server runs manually?
□ Absolute paths used?
□ Dependencies installed?
□ Environment variables set?
□ Command in PATH or absolute?
```

---

## Configuration Examples by Project Type

### ~/repos/MCP/ Structure

Your MCP directory has 30+ servers. Here's how to configure them:

**Python FastMCP servers:**
```json
{
  "mcpServers": {
    "fastmcp-server": {
      "command": "uv",
      "args": [
        "--directory",
        "/home/komi/repos/MCP/fastmcp-server",
        "run",
        "fastmcp-server"
      ]
    }
  }
}
```

**Node.js TypeScript servers:**
```json
{
  "mcpServers": {
    "typescript-server": {
      "command": "node",
      "args": [
        "/home/komi/repos/MCP/typescript-server/build/index.js"
      ]
    }
  }
}
```

**Go servers:**
```json
{
  "mcpServers": {
    "go-server": {
      "command": "/home/komi/repos/MCP/go-server/server"
    }
  }
}
```

---

## Bulk Configuration Script

To configure all servers in `~/repos/MCP/`:

```bash
#!/bin/bash
# Generate MCP server configurations

echo '{'
echo '  "mcpServers": {'

first=true
for dir in ~/repos/MCP/*/; do
  server_name=$(basename "$dir")

  # Skip if not a directory
  [ ! -d "$dir" ] && continue

  # Add comma if not first
  [ "$first" = false ] && echo ','
  first=false

  # Python servers with pyproject.toml
  if [ -f "$dir/pyproject.toml" ]; then
    echo "    \"$server_name\": {"
    echo "      \"command\": \"uv\","
    echo "      \"args\": ["
    echo "        \"--directory\","
    echo "        \"$dir\","
    echo "        \"run\","
    echo "        \"$server_name\""
    echo "      ]"
    echo -n "    }"

  # Node.js servers with package.json
  elif [ -f "$dir/package.json" ]; then
    echo "    \"$server_name\": {"
    echo "      \"command\": \"node\","
    echo "      \"args\": ["
    echo "        \"$dir/build/index.js\""
    echo "      ]"
    echo -n "    }"

  # Go servers with go.mod
  elif [ -f "$dir/go.mod" ]; then
    echo "    \"$server_name\": {"
    echo "      \"command\": \"$dir/server\""
    echo -n "    }"
  fi
done

echo ''
echo '  }'
echo '}'
```

**Usage:**
```bash
chmod +x generate-mcp-config.sh
./generate-mcp-config.sh > mcp_servers_draft.json

# Review and edit as needed
# Then copy to appropriate config file
```

---

## Global vs Project-Specific (Claude Code)

### Global Configuration (~/.claude/settings.json)

**Use for:**
- Servers you use across all projects
- Utility servers (memory, filesystem, etc.)
- Development tools

**Example:**
```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem",
                "/home/komi"]
    }
  }
}
```

### Project-Specific (.claude/settings.json)

**Use for:**
- Project-specific tools
- Servers in project repository
- Context-dependent servers

**Example:**
```json
{
  "mcpServers": {
    "project-api": {
      "command": "python",
      "args": ["$CLAUDE_PROJECT_DIR/tools/api_server.py"],
      "env": {
        "PROJECT_ROOT": "$CLAUDE_PROJECT_DIR"
      }
    }
  }
}
```

---

## Configuration Best Practices

### 1. Use Absolute Paths
```json
✅ "/home/komi/repos/MCP/server/server.py"
❌ "./server.py"
❌ "../MCP/server/server.py"
```

### 2. Test Before Configuring
```bash
# Always test manually first:
python /full/path/to/server.py
# OR
uv run server-name
# OR
node /full/path/to/build/index.js
```

### 3. Use uv for Python Servers
```json
{
  "command": "uv",  ← Better than "python"
  "args": ["--directory", "/path", "run", "server-name"]
}
```

### 4. Document Environment Variables
```json
{
  "env": {
    "API_KEY": "get-from-1password",  ← Document where to get values
    "DATABASE_URL": "see-production-config"
  }
}
```

### 5. Keep Configs Organized
```json
{
  "mcpServers": {
    // Python servers
    "python-server-1": {...},
    "python-server-2": {...},

    // Node.js servers
    "node-server-1": {...},

    // Published packages
    "memory": {...}
  }
}
```

---

## Common Configuration Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Relative paths | Won't work | Use absolute paths |
| Trailing comma | JSON invalid | Remove last comma |
| Spaces in names | Parsing issues | Use hyphens/underscores |
| Wrong config file | Server won't appear | Check Desktop vs Code |
| Not restarting | Changes not loaded | Fully restart Claude |
| Missing env vars | Server crashes | Add to `"env"` section |
| Command not in PATH | Command not found | Use absolute path |

---

## Template Collection

### Minimal Working Server
```json
{
  "mcpServers": {
    "test": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    }
  }
}
```

### Complex Server with Everything
```json
{
  "mcpServers": {
    "complex-server": {
      "command": "uv",
      "args": [
        "--directory",
        "/home/komi/repos/MCP/complex-server",
        "run",
        "complex-server"
      ],
      "env": {
        "API_KEY": "your-key",
        "DATABASE_URL": "postgresql://...",
        "DEBUG": "false",
        "LOG_LEVEL": "info",
        "CUSTOM_VAR": "value"
      }
    }
  }
}
```

---

**Key Takeaway:** Configuration is simple once you understand:
1. Use absolute paths
2. Test server manually first
3. Validate JSON syntax
4. Restart Claude after changes
5. Configure in correct file (Desktop vs Code)

**Most configuration issues come from:**
- Using relative paths
- Not restarting Claude
- Wrong config file
- JSON syntax errors
