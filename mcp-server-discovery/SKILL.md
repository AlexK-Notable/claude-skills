---
name: mcp-server-discovery
description: Discover and recommend task-appropriate MCP servers for code analysis, visualization, diagrams, mind maps, documentation, knowledge management, system operations, reasoning, academic research, and package security. Automatically suggests relevant servers based on task type including mcp-mermaid, ai-distiller, aira-http, context7, clear-thought, zettelkasten, desktop-commander, and more.
---

# MCP Server Discovery & Routing

## Purpose

Intelligent router that recommends task-appropriate MCP servers from 20+ available options, organized into 9 categories.

## When to Use

**Automatically activates for:** diagrams, code analysis, research papers, documentation, knowledge management, file processing, reasoning, npm packages.

**Reference Files:**
- [SERVER_DETAILS.md](SERVER_DETAILS.md) - Detailed server specifications and combinations

---

## Available MCP Servers by Category

### 1. Code Analysis & Understanding

**When to use:** Analyzing codebases, extracting API signatures, understanding code structure, Go language support

#### ai-distiller
Extract code structure → API signatures, dependencies. Supports 10+ languages.
- **Use when:** Large codebases, API discovery, understanding without full file reads

#### godoc-mcp-server
Go package docs from pkg.go.dev
- **Use when:** Researching Go libraries, looking up Go packages

#### mcp-gopls
Go LSP → navigation, diagnostics, completion
- **Use when:** Active Go editing, code navigation, refactoring

---

### 2. Visualization & Diagramming

**When to use:** Creating diagrams, flowcharts, mind maps, visualizing data or architecture

#### mcp-mermaid
Standard Mermaid diagrams (flowcharts, sequence, ER, class) → file output (.png, .svg)
- **Use when:** Technical docs, process flows, database schemas

#### markmap
Markdown → mind maps with PNG/JPG/SVG export + themes
- **Use when:** Converting existing markdown, need export formats, polished deliverables

#### mindmap-mcp-server
Direct mind map generation, no export formats
- **Use when:** Quick simple mind maps, speed over features

#### mindpilot-mcp
3D architecture visualization with web interface (NOT for general diagrams)
- **Use when:** Legacy code analysis, complex architecture exploration, need 3D spatial view

---

### 3. Documentation & References

**When to use:** Looking up library documentation, API references, code examples

#### context7
Up-to-date library documentation and API references
- **Use when:** Need current docs for frameworks, API usage

#### augments
Documentation and reference via HTTP
- **Use when:** Alternative documentation sources

---

### 4. Document Processing & Conversion

#### website-downloader
Download entire websites using wget
- **Use when:** Offline archives, documentation scraping

#### markitdown-http
Convert PDF/DOCX/HTML → markdown
- **Use when:** Extract text from various formats

---

### 5. Knowledge & Memory Management

#### in-memoria
Codebase intelligence, pattern recognition, file routing
- **Use when:** Project memory, predict coding approach

#### memcord
Memory slots for conversation context across sessions
- **Use when:** Preserve context, search past conversations

#### zettelkasten
Zettelkasten note-taking → atomic notes, bidirectional links
- **Use when:** Building permanent knowledge base, PKM

---

### 6. System Operations & Automation

#### desktop-commander
File ops, processes, search, data analysis
- **CRITICAL:** Use for ALL local file analysis (CSV, JSON). Analysis tool CANNOT access local files.

#### hyprland
Hyprland window manager control (Hyprland users only)
- **Use when:** Control windows/workspaces

---

### 7. Reasoning & Problem Solving

#### clear-thought
Chain of thought reasoning with verification
- **Use when:** Structured problem-solving, breaking down complex tasks

#### thoughtbox-http
Advanced frameworks, executable notebooks
- **Use when:** Advanced reasoning, literate programming

---

### 8. Academic Research

#### aira-http
SemanticScholar + arXiv search, citation networks, full paper downloads
- **Use when:** Literature review, finding papers, research citations

---

### 9. Package Security & Monitoring

#### npm-sentinel
NPM package analysis, vulnerabilities, comparisons
- **Use when:** Evaluating packages, security checks

---

## Task-to-Server Quick Reference

**I need to...**

### Create a Diagram
→ **mcp-mermaid** (standard technical diagrams: flowchart, sequence, ER, class diagrams)
→ **markmap** (markdown → mind map with PNG/JPG/SVG export + themes)
→ **mindmap-mcp-server** (simple mind maps, no export formats)
→ **mindpilot-mcp** (3D architecture visualization, legacy code analysis only)

### Analyze Code
→ **ai-distiller** (any language, structure extraction)
→ **godoc-mcp-server** (Go packages)
→ **mcp-gopls** (Go language server)

### Find Documentation
→ **context7** (library docs, API references)
→ **godoc-mcp-server** (Go-specific)

### Search Research Papers
→ **aira-http** (academic papers, arxiv, citations)

### Take Notes / Build Knowledge Base
→ **zettelkasten** (atomic notes, linked thinking)
→ **memcord** (conversation memory slots)
→ **in-memoria** (project-specific memory)

### Process Documents
→ **markitdown-http** (PDF/DOCX to markdown)
→ **website-downloader** (download websites)

### File Operations / System Tasks
→ **desktop-commander** (file ops, processes, data analysis)
→ **hyprland** (window management, Hyprland only)

### Complex Problem-Solving
→ **clear-thought** (structured reasoning)
→ **thoughtbox-http** (advanced frameworks, notebooks)

### Check NPM Packages
→ **npm-sentinel** (security, versions, comparisons)

---

## Recommendations by Task Type

### "Create a flowchart of..."
✅ **Primary:** mcp-mermaid (standard flowcharts, sequence diagrams, ER diagrams)
🔧 **For complex architecture:** mindpilot-mcp (3D visualization, web interface, legacy code)

### "Analyze this codebase..."
✅ **Primary:** ai-distiller
🔧 **Go-specific:** godoc-mcp-server, mcp-gopls

### "Research papers about..."
✅ **Primary:** aira-http

### "Convert this PDF to markdown..."
✅ **Primary:** markitdown-http

### "Create a knowledge base for..."
✅ **Primary:** zettelkasten (structured notes)
🔧 **Alternative:** memcord (memory slots), in-memoria (project memory)

### "Analyze this CSV file..."
✅ **Primary:** desktop-commander
⚠️ **Do NOT use analysis tool** - it cannot access local files

### "Find documentation for [library]..."
✅ **Primary:** context7
🔧 **Go-specific:** godoc-mcp-server

### "Create a mind map of..."
✅ **With export needs:** markmap (PNG/JPG/SVG, themes, from existing markdown)
✅ **Simple/quick:** mindmap-mcp-server (direct generation, no export formats)

### "Break down this complex problem..."
✅ **Primary:** clear-thought
🔧 **Advanced:** thoughtbox-http

### "Check security of npm package..."
✅ **Primary:** npm-sentinel

---

## Server Choice Decision Criteria

### When to Choose Between Similar Servers

#### Visualization: mcp-mermaid vs mindpilot-mcp

**Choose mcp-mermaid when:**
- Creating standard technical diagrams (flowcharts, sequence, ER, class)
- Need file output (.png, .svg)
- Working with straightforward architecture
- Don't need interactive exploration

**Choose mindpilot-mcp when:**
- Analyzing complex legacy codebases
- Need 3D architectural visualization
- Want interactive web interface for exploration
- Dealing with large systems requiring spatial understanding

#### Mind Maps: markmap vs mindmap-mcp-server

**Choose markmap when:**
- Converting existing markdown documents to mind maps
- Need multiple export formats (PNG, JPG, SVG)
- Want theme customization
- Creating polished visualizations for presentations
- Starting with structured markdown content

**Choose mindmap-mcp-server when:**
- Need quick, simple mind maps
- Don't require export formats
- Prefer direct generation over markdown conversion
- Working with simple hierarchical data
- Speed matters more than features

#### Go Development: godoc-mcp-server vs mcp-gopls

**Choose godoc-mcp-server when:**
- Looking up Go package documentation
- Researching third-party Go libraries
- Need pkg.go.dev information
- Searching for Go packages by functionality

**Choose mcp-gopls when:**
- Editing Go code actively
- Need code navigation (go-to-definition, find-references)
- Running diagnostics and coverage analysis
- Getting code completion suggestions
- Working within a Go project

#### Knowledge Management: zettelkasten vs memcord vs in-memoria

**Choose zettelkasten when:**
- Building a permanent knowledge base
- Creating atomic, linked notes
- Long-term personal knowledge management (PKM)
- Need bidirectional links between concepts

**Choose memcord when:**
- Preserving conversation context across sessions
- Need memory "slots" for different topics
- Want to search across past conversations
- Temporary/medium-term memory needs

**Choose in-memoria when:**
- Project-specific memory and learning
- Codebase intelligence and pattern recognition
- Predicting coding approaches based on project history
- File routing and dependency analysis

---

## Best Practices

### 1. Use Multiple Servers Together

**Example: Code documentation project**
1. **ai-distiller** → Extract code structure
2. **mcp-mermaid** → Create architecture diagrams
3. **zettelkasten** → Document insights as notes

**Example: Research paper analysis**
1. **aira-http** → Find relevant papers
2. **clear-thought** → Analyze and synthesize findings
3. **zettelkasten** → Store insights and connections

### 2. Choose Transport-Appropriate Servers

**HTTP servers** (persistent, good for repeated calls):
- augments, markitdown-http, thoughtbox-http, aira-http

**STDIO servers** (on-demand, fast startup):
- ai-distiller, mcp-mermaid, context7, clear-thought, desktop-commander

### 3. Task-Specific Optimizations

**For large codebases:**
- Start with **in-memoria** (`auto_learn_if_needed`)
- Then use **ai-distiller** for specific files

**For academic research:**
- Use **aira-http** advanced search with filters
- Download full papers with `download-full-paper-arxiv`

**For visualization:**
- **mcp-mermaid** for technical diagrams
- **markmap** for hierarchical/concept maps
- **mindpilot-mcp** when you need UI preview

**For local file analysis:**
- **ALWAYS use desktop-commander** (start_process + interact_with_process)
- **NEVER use analysis tool** - it cannot read local files

---

## Integration Examples

### Example 1: "Create architecture documentation"

**Recommended servers:**
1. **ai-distiller** → Extract code structure
   ```
   distill_directory with include_methods=true
   ```

2. **mcp-mermaid** → Create diagrams
   ```
   generate_mermaid_diagrams_batch for multiple views
   ```

3. **zettelkasten** → Document insights
   ```
   zk_create_note with links between concepts
   ```

### Example 2: "Analyze research on topic X"

**Recommended servers:**
1. **aira-http** → Find papers
   ```
   paper-search-advanced with year filters, citations
   ```

2. **clear-thought** → Synthesize findings
   ```
   clear_thought with systematic analysis
   ```

3. **memcord** → Save context
   ```
   memcord_save_progress for session continuity
   ```

### Example 3: "Process and visualize CSV data"

**Recommended servers:**
1. **desktop-commander** → Read and analyze
   ```
   start_process("python3 -i")
   interact_with_process(pid, "import pandas as pd")
   interact_with_process(pid, "df = pd.read_csv('/path/file.csv')")
   ```

2. **mcp-mermaid** → Visualize findings
   ```
   generate_mermaid_diagram for data flow/relationships
   ```

---

## Server Selection Decision Tree

```
START: What is your task?

├─ Code-related?
│  ├─ Analysis/Structure → ai-distiller
│  ├─ Go language → godoc-mcp-server, mcp-gopls
│  └─ Documentation → context7
│
├─ Visualization?
│  ├─ Technical diagrams → mcp-mermaid
│  ├─ Mind maps → markmap, mindmap-mcp-server
│  └─ With UI → mindpilot-mcp
│
├─ Research?
│  └─ Academic papers → aira-http
│
├─ Knowledge/Memory?
│  ├─ Structured notes → zettelkasten
│  ├─ Session memory → memcord
│  └─ Project memory → in-memoria
│
├─ Document processing?
│  ├─ Download website → website-downloader
│  └─ Convert to markdown → markitdown-http
│
├─ System operations?
│  ├─ File/process ops → desktop-commander
│  └─ Window management → hyprland
│
├─ Problem-solving?
│  ├─ Structured thinking → clear-thought
│  └─ Advanced reasoning → thoughtbox-http
│
└─ NPM packages?
   └─ Security/analysis → npm-sentinel
```

---

## Common Mistakes to Avoid

❌ **Using analysis tool for local files**
✅ **Use desktop-commander** with start_process/interact_with_process

❌ **Ignoring available specialized servers**
✅ **Check this skill first** to find the right tool

❌ **Using generic tools when specialized ones exist**
✅ **Use aira-http for papers**, not generic web search

❌ **Not combining servers for complex tasks**
✅ **Chain multiple servers** (analyze → visualize → document)

---

## Server Status & Reliability

**Production-Ready (use with confidence):**
- ai-distiller, context7, mcp-mermaid, clear-thought, desktop-commander, aira-http, npm-sentinel

**Beta (functional, minor issues possible):**
- godoc-mcp-server, mcp-gopls, markmap, mindmap-mcp-server, website-downloader, in-memoria

**Experimental (use with caution):**
- memcord, thoughtbox-http

---

**Skill Status:** ACTIVE ✅
**Servers Covered:** 20 servers across 9 categories
**Line Count:** < 500 (following Anthropic best practices)

**Next:** Invoke this skill at the start of any task to get server recommendations
