"""cron-claude CLI — entry point.

Command groups:
- `schedule` — manage systemd user timer/service pairs (add, list, rm, show)
- `run`      — trigger a scheduled job once, out-of-band
- `logs`     — inspect a job's journal
- `tui`      — launch the interactive TUI (optional dep)
"""
from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from cron_claude import __version__

app = typer.Typer(
    name="cron-claude",
    help="Schedule and manage local claude -p invocations via systemd user timers.",
    no_args_is_help=True,
    add_completion=False,
)

schedule_app = typer.Typer(
    help="Manage scheduled claude -p jobs (systemd .timer/.service unit pairs).",
    no_args_is_help=True,
)
app.add_typer(schedule_app, name="schedule")

console = Console()
err_console = Console(stderr=True)


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"cron-claude {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            "-V",
            callback=_version_callback,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = None,
) -> None:
    """cron-claude — schedule local claude -p jobs via systemd user timers."""


# ---------- schedule subcommands ----------


@schedule_app.command("add")
def schedule_add(
    name: Annotated[str, typer.Argument(help="Schedule name (becomes the systemd unit basename).")],
    when: Annotated[
        str,
        typer.Option(
            "--when",
            "-w",
            help="Systemd OnCalendar spec, e.g. 'weekly', 'Sun 03:07', '*-*-* 09:00'.",
        ),
    ],
    prompt: Annotated[
        Path,
        typer.Option(
            "--prompt",
            "-p",
            help="Path to a prompt script under prompts/.",
            exists=False,  # validated by runner, not at CLI parse time
        ),
    ],
    description: Annotated[
        Optional[str],
        typer.Option("--description", "-d", help="Human-readable description."),
    ] = None,
) -> None:
    """Create a new scheduled job (writes a .service + .timer unit pair)."""
    raise NotImplementedError(
        "schedule add — compose a TimerSpec from runner+systemd modules, write units, daemon-reload, enable --now."
    )


@schedule_app.command("list")
def schedule_list(
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON instead of a table.")] = False,
) -> None:
    """List all cron-claude-managed schedules."""
    raise NotImplementedError(
        "schedule list — enumerate units in ~/.config/systemd/user matching the cron-claude marker."
    )


@schedule_app.command("rm")
def schedule_rm(
    name: Annotated[str, typer.Argument(help="Schedule name.")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation.")] = False,
) -> None:
    """Remove a scheduled job (disables, stops, and deletes both unit files)."""
    raise NotImplementedError(
        "schedule rm — disable + stop + unlink both unit files + daemon-reload."
    )


@schedule_app.command("show")
def schedule_show(
    name: Annotated[str, typer.Argument(help="Schedule name.")],
) -> None:
    """Show details for a single scheduled job."""
    raise NotImplementedError(
        "schedule show — render unit content + next firing + last result + recent runs."
    )


# ---------- top-level commands ----------


@app.command("run")
def run_now(
    name: Annotated[str, typer.Argument(help="Schedule name.")],
) -> None:
    """Trigger a scheduled job to run immediately, out of schedule."""
    raise NotImplementedError(
        "run — `systemctl --user start <unit>.service`, optionally follow journalctl until exit."
    )


@app.command("logs")
def logs(
    name: Annotated[str, typer.Argument(help="Schedule name.")],
    tail: Annotated[int, typer.Option("--tail", "-n", help="Show last N entries.")] = 50,
    follow: Annotated[bool, typer.Option("--follow", "-f", help="Tail-follow.")] = False,
) -> None:
    """View logs for a scheduled job's recent runs."""
    raise NotImplementedError(
        "logs — proxy to journalctl --user-unit <unit>.service with -n/-f flags."
    )


@app.command("tui")
def tui() -> None:
    """Launch the interactive TUI (requires `uv sync --extra tui`)."""
    try:
        from cron_claude.tui.app import CronClaudeApp
    except ImportError as exc:  # textual not installed
        err_console.print(
            "[red]TUI dependencies not installed.[/red] "
            "Install with: [bold]uv sync --extra tui[/bold]\n"
            f"  details: {exc}"
        )
        raise typer.Exit(code=1) from exc
    CronClaudeApp().run()


if __name__ == "__main__":
    app()
