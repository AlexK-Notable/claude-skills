"""cron-claude CLI — entry point."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from cron_claude import __version__
from cron_claude.errors import CronClaudeError, ScheduleExists, ScheduleNotFound
from cron_claude.runners import ScriptRunner, select_runner
from cron_claude.systemd import control, timers

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

_STARTER_TEMPLATE = """\
#!/usr/bin/env bash
# cron-claude prompt: {name}. Owns its own `claude -p` invocation + allowlist.
exec claude -p 'REPLACE ME: describe this scheduled job' --allowed-tools 'Bash(echo *)'
"""


def _fail(exc: CronClaudeError) -> typer.Exit:
    err_console.print(f"[red]error:[/red] {exc}")
    return typer.Exit(code=1)


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"cron-claude {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None,
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


@schedule_app.command("add")
def schedule_add(
    name: Annotated[str, typer.Argument(help="Schedule name (systemd unit basename).")],
    when: Annotated[
        str,
        typer.Option("--when", "-w", help="OnCalendar spec, e.g. 'Sun 03:07'."),
    ],
    prompt: Annotated[
        Path,
        typer.Option("--prompt", "-p", help="Prompt: an executable script, or a text file."),
    ],
    description: Annotated[
        str | None,
        typer.Option("--description", "-d"),
    ] = None,
    timeout: Annotated[
        int | None,
        typer.Option("--timeout", help="TimeoutStartSec (seconds)."),
    ] = None,
    allowed_tools: Annotated[
        list[str] | None,
        typer.Option("--allowed-tools", help="Text prompts only; repeatable."),
    ] = None,
    permission_mode: Annotated[
        str | None,
        typer.Option("--permission-mode", help="Text prompts only."),
    ] = None,
    dangerously_skip: Annotated[
        bool,
        typer.Option("--dangerously-skip-permissions", help="Text prompts only."),
    ] = False,
    randomized_delay: Annotated[
        int,
        typer.Option("--randomized-delay", help="RandomizedDelaySec."),
    ] = 0,
    scaffold: Annotated[
        bool,
        typer.Option(
            "--scaffold", "-s",
            help="If --prompt is missing, create an executable starter there.",
        ),
    ] = False,
) -> None:
    """Create a new scheduled job (writes a .service + .timer unit pair)."""
    try:
        if timers.unit_paths(name)[0].exists():
            raise ScheduleExists(
                f"schedule {name!r} already exists; "
                f"remove it first: cron-claude schedule rm {name}"
            )
        control.validate_calendar(when)
        prompt_path = prompt.expanduser()
        if not prompt_path.exists() and scaffold:
            prompt_path.parent.mkdir(parents=True, exist_ok=True)
            prompt_path.write_text(_STARTER_TEMPLATE.format(name=name))
            prompt_path.chmod(0o755)
            console.print(
                f"[yellow]scaffolded[/yellow] {prompt_path}"
                " — edit it before the first run"
            )
        runner = select_runner(
            prompt_path,
            allowed_tools=tuple(allowed_tools or ()),
            permission_mode=permission_mode,
            dangerously_skip=dangerously_skip,
        )
        runner.validate()
        is_script = isinstance(runner, ScriptRunner)
        if is_script and (allowed_tools or permission_mode or dangerously_skip):
            console.print(
                "[yellow]note:[/yellow] claude flags are ignored for an executable"
                " prompt (the script owns them)."
            )
        spec = timers.TimerSpec(
            name=name,
            on_calendar=when,
            exec_start=runner.to_exec_start(),
            prompt_path=str(prompt_path.resolve()),
            runner="script" if is_script else "claude",
            description=description,
            randomized_delay_sec=randomized_delay,
            timeout_sec=timeout,
        )
        timers.write_units(spec)
        control.daemon_reload()
        control.enable_now(timers.timer_unit(name))
    except CronClaudeError as exc:
        raise _fail(exc) from exc
    console.print(f"[green]✓[/green] scheduled [bold]{name}[/bold] → {timers.timer_unit(name)}")
    nxt = control.next_elapse(timers.timer_unit(name))
    if nxt is not None:
        console.print(f"  next run: {nxt:%Y-%m-%d %H:%M:%S %Z}")


@schedule_app.command("list")
def schedule_list(
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit JSON instead of a table."),
    ] = False,
) -> None:
    """List all cron-claude-managed schedules."""
    specs = list(timers.list_units())
    if json_output:
        payload = [
            {
                "name": s.name,
                "on_calendar": s.on_calendar,
                "runner": s.runner,
                "prompt": s.prompt_path,
                "description": s.description,
            }
            for s in specs
        ]
        console.print_json(json.dumps(payload))
        return
    if not specs:
        console.print("[dim]no schedules[/dim]")
        return
    table = Table("Name", "Schedule", "Next run", "Last result", "Description")
    for s in specs:
        nxt = control.next_elapse(timers.timer_unit(s.name))
        result, _ = control.last_result(timers.service_unit(s.name))
        table.add_row(
            s.name, s.on_calendar,
            f"{nxt:%Y-%m-%d %H:%M}" if nxt else "—",
            result, s.description or "",
        )
    console.print(table)


@schedule_app.command("rm")
def schedule_rm(
    name: Annotated[str, typer.Argument(help="Schedule name.")],
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Skip confirmation."),
    ] = False,
) -> None:
    """Remove a scheduled job (disables, stops, and deletes both unit files)."""
    try:
        if not timers.unit_paths(name)[0].exists():
            raise ScheduleNotFound(f"schedule {name!r} not found")
        if not force and not typer.confirm(f"Remove schedule {name!r}?"):
            raise typer.Abort()
        control.disable_now(timers.timer_unit(name))
        control.stop(timers.service_unit(name))
        timers.remove_units(name)
        control.daemon_reload()
    except CronClaudeError as exc:
        raise _fail(exc) from exc
    console.print(f"[green]✓[/green] removed [bold]{name}[/bold]")


@schedule_app.command("show")
def schedule_show(
    name: Annotated[str, typer.Argument(help="Schedule name.")],
) -> None:
    """Show details for a single scheduled job."""
    try:
        svc, tmr = timers.unit_paths(name)
        if not svc.exists() or not tmr.exists():
            raise ScheduleNotFound(f"schedule {name!r} not found")
    except CronClaudeError as exc:
        raise _fail(exc) from exc
    console.rule(f"{name}")
    console.print(tmr.read_text())
    console.print(svc.read_text())
    nxt = control.next_elapse(timers.timer_unit(name))
    result, status = control.last_result(timers.service_unit(name))
    console.print(f"next run: {nxt:%Y-%m-%d %H:%M:%S %Z}" if nxt else "next run: —")
    console.print(f"last result: {result} (exit {status})")
    console.rule("recent log")
    control.journal(timers.service_unit(name), tail=20)


@app.command("run")
def run_now(
    name: Annotated[str, typer.Argument(help="Schedule name.")],
) -> None:
    """Trigger a scheduled job to run immediately (blocks until it finishes)."""
    try:
        if not timers.unit_paths(name)[0].exists():
            raise ScheduleNotFound(f"schedule {name!r} not found")
        console.print(f"running [bold]{name}[/bold] …")
        control.start(timers.service_unit(name))  # oneshot: blocks until done
    except CronClaudeError as exc:
        raise _fail(exc) from exc
    result, status = control.last_result(timers.service_unit(name))
    console.print(f"[green]done[/green] — result: {result} (exit {status})")
    control.journal(timers.service_unit(name), tail=20)


@app.command("logs")
def logs(
    name: Annotated[str, typer.Argument(help="Schedule name.")],
    tail: Annotated[int, typer.Option("--tail", "-n", help="Show last N entries.")] = 50,
    follow: Annotated[bool, typer.Option("--follow", "-f", help="Tail-follow.")] = False,
) -> None:
    """View logs for a scheduled job's recent runs."""
    try:
        if not timers.unit_paths(name)[0].exists():
            raise ScheduleNotFound(f"schedule {name!r} not found")
    except CronClaudeError as exc:
        raise _fail(exc) from exc
    raise typer.Exit(control.journal(timers.service_unit(name), tail=tail, follow=follow))


@app.command("tui")
def tui() -> None:
    """Launch the interactive TUI (requires `uv sync --extra tui`)."""
    try:
        from cron_claude.tui.app import CronClaudeApp
    except ImportError as exc:
        err_console.print(
            "[red]TUI dependencies not installed.[/red] Install with: "
            "[bold]uv sync --extra tui[/bold]\n"
            f"  details: {exc}"
        )
        raise typer.Exit(code=1) from exc
    CronClaudeApp().run()


if __name__ == "__main__":
    app()
