---
name: python-rich-cli
description: Building beautiful CLI tools with Python Rich library and Loguru integration
---

# Python Rich CLI Patterns

**Purpose:** Create professional, beautiful command-line interfaces using Rich library for terminal output, tables, progress bars, and logging.

**Use this skill when:**
- Building CLI tools that need formatted output
- Creating progress indicators for long-running tasks
- Displaying tables or structured data in terminal
- Adding rich formatting to Python applications
- Integrating with Loguru for enhanced logging

---

## Quick Start

### Basic Console Output

```python
from rich.console import Console

console = Console()

# Simple output
console.print("Hello, [bold magenta]World[/bold magenta]!")

# With styles
console.print("[bold red]Error:[/bold red] Something went wrong")
console.print("[green]✓[/green] Success!")

# Objects (automatic pretty printing)
console.print({"key": "value", "items": [1, 2, 3]})
```

---

## Common Patterns

### Pattern 1: CLI Tool with Rich Output

```python
#!/usr/bin/env python3
from rich.console import Console
from rich.table import Table
import sys

console = Console()

def main():
    console.print("[bold blue]My CLI Tool v1.0[/bold blue]")
    console.print()

    # Create table
    table = Table(title="Results")
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="magenta")

    table.add_row("Item 1", "[green]✓ Complete[/green]")
    table.add_row("Item 2", "[yellow]⚠ Warning[/yellow]")
    table.add_row("Item 3", "[red]✗ Failed[/red]")

    console.print(table)

if __name__ == "__main__":
    main()
```

### Pattern 2: Progress Bars

```python
from rich.progress import Progress
import time

with Progress() as progress:
    task = progress.add_task("[cyan]Processing...", total=100)

    while not progress.finished:
        progress.update(task, advance=1)
        time.sleep(0.02)
```

### Pattern 3: Rich + Loguru Integration

```python
from loguru import logger
from rich.console import Console
from rich.logging import RichHandler
import sys

console = Console()

# Configure loguru to use Rich
logger.remove()  # Remove default handler
logger.add(
    RichHandler(console=console, rich_tracebacks=True),
    format="{message}",
    level="INFO"
)

# Now logging looks beautiful
logger.info("Starting application")
logger.warning("This is a warning")
logger.error("Something went wrong")
```

### Pattern 4: Exception Handling with Rich Tracebacks

```python
from rich.console import Console
from rich.traceback import install

# Install rich traceback handler (globally)
install(show_locals=True)

console = Console()

def risky_function():
    # Rich will format exceptions beautifully
    result = 1 / 0
    return result

try:
    risky_function()
except Exception as e:
    console.print_exception()  # Beautiful exception display
```

---

## Key Components Reference

### Console

```python
from rich.console import Console

console = Console()

# Basic printing
console.print("text")
console.print("text", style="bold red")

# With markup
console.print("[bold]Bold[/bold] [red]Red[/red]")

# JSON/objects
console.print_json('{"key": "value"}')
console.print({"dict": "here"})

# Rules (horizontal lines)
console.rule("[bold red]Section Title")

# Input
name = console.input("What is your [bold blue]name[/bold blue]? ")
```

### Tables

```python
from rich.table import Table

table = Table(title="My Table")
table.add_column("Column 1", justify="right", style="cyan", no_wrap=True)
table.add_column("Column 2", style="magenta")

table.add_row("Row 1 Col 1", "Row 1 Col 2")
table.add_row("Row 2 Col 1", "Row 2 Col 2")

console.print(table)
```

### Progress Bars

```python
from rich.progress import Progress, SpinnerColumn, TextColumn

with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    *Progress.get_default_columns(),
) as progress:
    task1 = progress.add_task("[red]Downloading...", total=1000)
    task2 = progress.add_task("[green]Processing...", total=1000)

    while not progress.finished:
        progress.update(task1, advance=0.5)
        progress.update(task2, advance=0.3)
```

---

## Style Guide

### Colors

```python
# Basic colors
"[red]text[/red]"
"[green]text[/green]"
"[blue]text[/blue]"
"[yellow]text[/yellow]"
"[magenta]text[/magenta]"
"[cyan]text[/cyan]"

# Styles
"[bold]text[/bold]"
"[italic]text[/italic]"
"[underline]text[/underline]"

# Combined
"[bold red]text[/bold red]"
"[bold cyan on blue]text[/bold cyan on blue]"
```

### Status Indicators

```python
console.print("[green]✓[/green] Success")
console.print("[red]✗[/red] Failed")
console.print("[yellow]⚠[/yellow] Warning")
console.print("[blue]ℹ[/blue] Info")
console.print("[cyan]→[/cyan] Processing")
```

---

## Real-World Examples

### Example: MCP Server Status Display

```python
from rich.console import Console
from rich.table import Table
from pathlib import Path

console = Console()

def show_mcp_servers():
    table = Table(title="MCP Servers Status")
    table.add_column("Server", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Path", style="dim")

    servers = Path("~/repos/MCP").expanduser().iterdir()
    for server in servers:
        if server.is_dir():
            has_pyproject = (server / "pyproject.toml").exists()
            has_package_json = (server / "package.json").exists()

            status = "[green]✓ Ready[/green]" if has_pyproject or has_package_json else "[dim]— Empty[/dim]"
            table.add_row(server.name, status, str(server))

    console.print(table)

if __name__ == "__main__":
    show_mcp_servers()
```

### Example: File Processing with Progress

```python
from rich.progress import track
from pathlib import Path

def process_files(directory):
    files = list(Path(directory).rglob("*.py"))

    for file in track(files, description="Processing..."):
        # Process file
        process_file(file)
```

---

## Resource Files

📚 **For detailed guidance:**

- **resources/console-and-printing.md** - Complete console API reference
- **resources/tables-and-layouts.md** - Tables, columns, panels, and layouts
- **resources/progress-and-status.md** - Progress bars, spinners, live displays
- **resources/loguru-integration.md** - Combining Rich with Loguru logging
- **resources/styling-guide.md** - Colors, styles, themes, and markup

---

## Common Use Cases

**CLI Tools:**
- Use Tables for structured output
- Use Progress for long operations
- Use Console.print for general output
- Use Rich tracebacks for debugging

**Logging:**
- Integrate with Loguru for beautiful logs
- Use different styles for log levels
- Show tracebacks with Rich

**Data Display:**
- Tables for tabular data
- Tree for hierarchical data
- JSON for structured objects
- Syntax highlighting for code

---

## Quick Tips

✓ **Install Rich:** `pip install rich` or `uv pip install rich`
✓ **Install Loguru:** `pip install loguru` or `uv pip install loguru`
✓ **Test in terminal:** Rich needs real terminal for full features
✓ **Use console.print():** Better than print() for Rich features
✓ **Enable exceptions:** `install()` for beautiful tracebacks globally
✓ **Check terminal width:** `console.width` to adapt output

---

**When this skill activates:**
- Working with Python files using Rich library
- Keywords: "rich", "console", "cli", "terminal output", "progress bar"
- Patterns: `from rich import`, `Console()`, progress bars, tables

**Use explicitly for:**
- Creating new CLI tools
- Adding formatted output to Python scripts
- Implementing progress indicators
- Beautifying existing terminal output
