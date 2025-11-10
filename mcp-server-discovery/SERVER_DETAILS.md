# MCP Server Detailed Specifications

## Visualization & Diagramming Servers

### mcp-mermaid
**Full Specification:**
- **Purpose:** Generate standard Mermaid diagrams (flowcharts, sequence, ER, class diagrams)
- **Output:** Diagram files (.png, .svg) saved to disk
- **Supported Diagrams:**
  - Flowcharts (TD, LR, BT, RL)
  - Sequence diagrams
  - ER diagrams
  - Class diagrams
  - State diagrams
  - Gantt charts
  - Pie charts
- **Tools:**
  - `generate_mermaid_diagram` - Single diagram generation
  - `generate_mermaid_diagrams_batch` - Multiple diagrams at once
- **Best for:** Technical documentation, process flows, database schemas
- **When to use:** Standard technical diagrams without UI, file output needed
- **Maturity:** Production-ready

### markmap
**Full Specification:**
- **Purpose:** Convert markdown hierarchies to interactive mind maps with export options
- **Output:** Multiple formats (PNG, JPG, SVG)
- **Features:**
  - Theme customization
  - Markdown-first approach (converts existing markdown)
  - Export flexibility
  - Interactive browser preview
- **Tools:** `markdown_to_mindmap`
- **Best for:** Documentation visualization, concept mapping with export needs
- **When to use:** Converting existing markdown docs, need multiple export formats
- **Maturity:** Beta/Active Development

### mindmap-mcp-server
**Full Specification:**
- **Purpose:** Simple, direct mind map generation from structured input
- **Output:** Interactive mind maps (HTML/web format)
- **Features:**
  - Simpler API than markmap
  - Direct generation (not markdown conversion)
  - Faster for basic visualizations
- **Tools:** `convert_markdown_to_mindmap`
- **Best for:** Quick hierarchical visualizations, straightforward mind mapping
- **When to use:** Simple mind maps without export requirements, speed over features
- **Maturity:** Beta/Active Development

### mindpilot-mcp
**Full Specification:**
- **Purpose:** 3D architecture visualization with web interface (specialized tool)
- **Output:** Interactive web interface with 3D support
- **Features:**
  - 3D visualization capabilities
  - Built-in web interface
  - Legacy code understanding
  - System modeling and architecture comprehension
  - Spatial understanding of complex systems
- **Tools:** `render_mermaid`, `open_ui`
- **Best for:** Legacy code understanding, complex system architecture, 3D visualizations
- **When to use:** Analyzing complex codebases, 3D architectural views, exploring legacy systems
- **NOT for:** General-purpose diagrams (use mcp-mermaid instead)
- **Maturity:** Production-ready (v0.5.0)

---

## Code Analysis Servers

### ai-distiller
**Full Specification:**
- **Purpose:** Extract essential code structure optimized for AI context
- **Supported Languages:** TypeScript, JavaScript, Python, Go, Java, C#, Rust, PHP, Ruby, Swift, Kotlin
- **Features:**
  - API signature extraction
  - Dependency analysis with `distill_with_dependencies`
  - Configurable visibility levels (public, protected, private)
  - Multiple output formats (text, markdown, JSON, XML)
- **Tools:**
  - `distill_file` - Single file analysis
  - `distill_directory` - Batch directory processing
  - `distill_with_dependencies` - Call dependency tracing
- **Best for:** Large codebases, API discovery, understanding code structure
- **When to use:** Need to understand code without full file contents, create docs from code
- **Maturity:** Production-ready

### godoc-mcp-server
**Full Specification:**
- **Purpose:** Go package documentation from pkg.go.dev
- **Features:**
  - Search Go packages by name/description
  - Get detailed package info (constants, types, functions, variables)
  - Access official pkg.go.dev documentation
  - Discover subpackages
- **Tools:**
  - `getPackageInfo` - Detailed package documentation
  - `searchPackages` - Find packages by query
- **Best for:** Go development, researching third-party libraries
- **When to use:** Looking up Go packages, researching Go libraries
- **Maturity:** Beta/Active Development

### mcp-gopls
**Full Specification:**
- **Purpose:** Go Language Server Protocol integration
- **Features:**
  - Code navigation (go-to-definition, find-references)
  - Diagnostics and error checking
  - Hover information
  - Code completion
  - Test coverage analysis
- **Tools:**
  - `go_to_definition` - Jump to symbol definitions
  - `find_references` - Find all usages
  - `check_diagnostics` - Get errors/warnings
  - `analyze_coverage` - Test coverage stats
  - `get_completion` - Code suggestions
- **Best for:** Active Go development, code navigation, refactoring
- **When to use:** Editing Go files, need IDE-like features
- **Maturity:** Beta/Active Development

---

## Decision Criteria Reference

### Choosing Between Similar Servers

#### Visualization: mcp-mermaid vs mindpilot-mcp

| Criteria | mcp-mermaid | mindpilot-mcp |
|----------|-------------|---------------|
| Diagram Types | Flowchart, Sequence, ER, Class | 3D Architecture only |
| Output | File (.png, .svg) | Web interface |
| Best For | Standard technical diagrams | Complex legacy codebases |
| Interactive | No | Yes (3D + web UI) |
| Learning Curve | Low | Medium |
| Use Case | Documentation, process flows | Architectural exploration |

#### Mind Maps: markmap vs mindmap-mcp-server

| Criteria | markmap | mindmap-mcp-server |
|----------|---------|-------------------|
| Input | Existing markdown | Direct generation |
| Export | PNG, JPG, SVG | None |
| Themes | Yes | No |
| Speed | Medium | Fast |
| Polish | High (presentation-ready) | Basic |
| Use Case | Polished deliverables | Quick visualizations |

#### Go Tools: godoc-mcp-server vs mcp-gopls

| Criteria | godoc-mcp-server | mcp-gopls |
|----------|------------------|-----------|
| Purpose | Documentation lookup | Active development |
| Source | pkg.go.dev | Local project |
| Features | Search, package info | Navigation, diagnostics |
| Context | Any Go package | Current project only |
| Use Case | Research libraries | Edit code |

---

## Server Combinations for Complex Tasks

### Task: Create Architecture Documentation

**Workflow:**
1. **ai-distiller** → Extract code structure
   ```
   distill_directory(/project, include_methods=true, include_fields=true)
   ```
2. **mcp-mermaid** → Create diagrams
   ```
   generate_mermaid_diagrams_batch([
     {id: "architecture", mermaid: "graph TD..."},
     {id: "data-flow", mermaid: "sequenceDiagram..."}
   ])
   ```
3. **zettelkasten** → Document insights
   ```
   zk_create_note("Architecture Overview", content, type="permanent")
   ```

### Task: Research Paper Analysis

**Workflow:**
1. **aira-http** → Find papers
   ```
   paper-search-advanced(query, yearStart=2020, minCitations=50)
   ```
2. **aira-http** → Download full papers
   ```
   download-full-paper-arxiv(arxivId)
   ```
3. **clear-thought** → Synthesize findings
   ```
   clear_thought(operation="systematic_analysis", prompt="Analyze patterns...")
   ```
4. **memcord** → Save for future reference
   ```
   memcord_save_progress(summary)
   ```

### Task: Analyze Local Data Files

**Workflow:**
1. **desktop-commander** → Load and analyze
   ```
   start_process("python3 -i")
   interact_with_process(pid, "import pandas as pd")
   interact_with_process(pid, "df = pd.read_csv('/path/file.csv')")
   interact_with_process(pid, "print(df.describe())")
   ```
2. **mcp-mermaid** → Visualize findings
   ```
   generate_mermaid_diagram(diagram="graph LR...", title="Data Flow")
   ```
3. **zettelkasten** → Document insights
   ```
   zk_create_note("Data Analysis Results", findings)
   ```

---

**File Status:** Reference documentation (not loaded by default)
**Purpose:** Detailed specifications for mcp-server-discovery skill
**Usage:** Consult when needing deep technical details about specific servers
