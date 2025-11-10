# Claude Code Skills Collection

Personal collection of Claude Code skills for portable skill management across machines.

## Repository Contents

### Skills (7 total)

1. **hierarchical-dev-orchestrator** - Multi-tier orchestration for complex software development tasks
2. **skill-developer** - Meta-skill for creating and managing Claude Code skills
3. **mcp-server-maintainer** - Installing, configuring, and troubleshooting MCP servers
4. **mcp-server-discovery** - Task-appropriate MCP server routing and recommendations
5. **python-rich-cli** - Building CLI tools with Python Rich library
6. **obsidian-plugin-dev** - Developing Obsidian plugins with TypeScript and React
7. **gtk-pygobject-dev** - Building desktop applications with GTK, PyGObject, and DBus

### Configuration

- **skill-rules.json** - Trigger patterns and activation rules for all skills

## Installation on New Machine

### Prerequisites

- Claude Code installed
- Git configured
- GitHub access (this is a private repo)

### Setup Steps

```bash
# 1. Clone this repository to Claude Code's skills directory
git clone git@github.com:AlexK-Notable/claude-skills.git ~/.claude/skills

# 2. Verify the skills are in place
ls ~/.claude/skills/

# 3. Restart Claude Code (if running)
# Skills will now be available globally
```

### Alternative: Manual Setup

If `~/.claude/skills` already exists with other content:

```bash
# 1. Clone to a temporary location
git clone git@github.com:AlexK-Notable/claude-skills.git ~/tmp-claude-skills

# 2. Copy skills to the correct location
cp -r ~/tmp-claude-skills/* ~/.claude/skills/

# 3. Clean up
rm -rf ~/tmp-claude-skills

# 4. Restart Claude Code
```

## Keeping Skills in Sync

### Push Changes from Current Machine

```bash
cd ~/.claude/skills

# Add new or modified skills
git add .

# Commit with descriptive message
git commit -m "Add new skill: example-skill"

# Push to remote
git push origin master
```

### Pull Changes on Another Machine

```bash
cd ~/.claude/skills

# Fetch latest changes
git pull origin master

# Restart Claude Code to reload skills
```

## How Skills Work

### Skill Activation

Skills automatically activate based on:
- **Keywords** in your prompts (e.g., "diagram", "mcp server", "obsidian plugin")
- **Intent patterns** (e.g., "(create|make).*diagram")
- **File paths** you're working with (e.g., `**/*.py` for Python files)
- **Content patterns** in files (e.g., `from gi.repository import Gtk`)

### Hooks System

The skills system uses two hooks in `~/.claude/hooks/`:
- **skill-activation-prompt.ts** - Suggests relevant skills before Claude responds (UserPromptSubmit hook)
- **error-handling-reminder.ts** - Gentle reminders for code quality (Stop hook)

## Skill Structure

Each skill follows this structure:

```
skill-name/
├── SKILL.md              # Main skill file (< 500 lines)
├── resources/            # Optional: Additional documentation
│   └── detailed-guide.md
└── references/           # Optional: Reference materials
    └── examples.md
```

**SKILL.md Format:**
```markdown
---
name: skill-name
description: Brief description with trigger keywords
---

# Skill Name

## Purpose
What this skill helps with

## When to Use
Specific scenarios

## Content
Actual guidance and examples
```

## Adding New Skills

### 1. Create Skill File

```bash
# Create skill directory
mkdir -p ~/.claude/skills/new-skill

# Create SKILL.md
nano ~/.claude/skills/new-skill/SKILL.md
```

### 2. Register in skill-rules.json

Add entry to `~/.claude/skills/skill-rules.json`:

```json
{
  "new-skill": {
    "type": "domain",
    "enforcement": "suggest",
    "priority": "high",
    "description": "Description with trigger keywords",
    "promptTriggers": {
      "keywords": ["keyword1", "keyword2"],
      "intentPatterns": ["(create|add).*?something"]
    }
  }
}
```

### 3. Test Activation

```bash
echo '{"prompt":"test prompt with keyword1"}' | \
  npx tsx ~/.claude/hooks/skill-activation-prompt.ts
```

### 4. Commit and Push

```bash
cd ~/.claude/skills
git add .
git commit -m "Add new skill: new-skill"
git push origin master
```

## Best Practices

### Skill Development

✅ Keep SKILL.md under 500 lines (Anthropic best practice)
✅ Use reference files for detailed content
✅ Include clear "When to Use" sections
✅ Add specific examples and code snippets
✅ Test trigger patterns thoroughly
✅ Document any special requirements

### Skill Management

✅ Commit skills after significant changes
✅ Use descriptive commit messages
✅ Pull before making changes on multiple machines
✅ Test skills after pulling updates
✅ Keep skill-rules.json synchronized

### Trigger Patterns

✅ Include all relevant keywords (lowercase)
✅ Use intent patterns for flexibility
✅ Test with actual user prompts
✅ Avoid false positives (too broad patterns)
✅ Balance between coverage and precision

## Troubleshooting

### Skill Not Activating

**Check trigger patterns:**
```bash
# Test specific prompt
echo '{"prompt":"your test prompt"}' | \
  npx tsx ~/.claude/hooks/skill-activation-prompt.ts
```

**Verify skill-rules.json syntax:**
```bash
jq . ~/.claude/skills/skill-rules.json
```

**Restart Claude Code:**
- Changes to skill-rules.json require restart
- Skill content (SKILL.md) does not require restart

### Git Conflicts

**If pulling causes conflicts:**
```bash
cd ~/.claude/skills

# Stash local changes
git stash

# Pull remote changes
git pull origin master

# Apply local changes
git stash pop

# Resolve conflicts manually
# Then commit
```

### Skills Directory Structure Changed

If hooks stop working after pulling:

1. Verify hooks still exist in `~/.claude/hooks/`
2. Check file permissions: `ls -la ~/.claude/hooks/*.ts`
3. Reinstall hooks if needed (from superpowers or skill-developer)

## Related Resources

- [Claude Code Documentation](https://docs.claude.com/claude-code)
- [Superpowers Skills](https://github.com/anthropics/superpowers) - Official skill collection
- [MCP Servers](https://github.com/modelcontextprotocol/servers) - Model Context Protocol servers

## Repository Information

- **Repository:** https://github.com/AlexK-Notable/claude-skills
- **Visibility:** Private
- **Purpose:** Personal skill collection for portable Claude Code workflows

## License

Private repository - All rights reserved.

---

**Created:** 2025-11-09
**Last Updated:** 2025-11-09
**Skills Count:** 7
**Total Lines:** 8,268
