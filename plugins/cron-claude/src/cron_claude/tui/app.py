"""Textual app: browse schedules, view logs, run/remove — over the systemd module."""
from __future__ import annotations

from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.widgets import DataTable, Footer, Header, RichLog

from cron_claude import operations
from cron_claude.systemd import control, timers


class CronClaudeApp(App):
    """List cron-claude schedules; r=run, x=remove (press twice), l=logs, q=quit."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("r", "run", "Run"),
        Binding("x", "remove", "Remove"),
        Binding("l", "logs", "Logs"),
        Binding("q", "quit", "Quit"),
    ]

    # Two-keypress confirm state for `x` (the CLI equivalent requires --force;
    # zero-confirmation removal from a single keypress is too destructive).
    _pending_remove: str | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        table = DataTable(id="schedules", cursor_type="row")
        table.add_columns("Name", "Schedule", "Runner", "Description")
        yield table
        yield RichLog(id="log", markup=True, highlight=True)
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_table()

    def refresh_table(self) -> None:
        table = self.query_one("#schedules", DataTable)
        table.clear()
        for s in timers.list_units():
            table.add_row(s.name, s.on_calendar, s.runner, s.description or "", key=s.name)

    def _selected(self) -> str | None:
        table = self.query_one("#schedules", DataTable)
        if table.row_count == 0:
            return None
        return table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value

    def _log(self, msg: str) -> None:
        self.query_one("#log", RichLog).write(msg)

    def action_run(self) -> None:
        self._pending_remove = None  # any other action cancels a pending removal
        name = self._selected()
        if not name:
            return
        try:
            control.start(timers.service_unit(name))
            result, status = control.last_result(timers.service_unit(name))
            self._log(f"[green]ran {name}[/green] — {result} (exit {status})")
        except Exception as exc:  # surface, don't crash the TUI
            self._log(f"[red]run failed:[/red] {exc}")

    def action_remove(self) -> None:
        name = self._selected()
        if not name:
            return
        if self._pending_remove != name:
            self._pending_remove = name
            self._log(
                f"[yellow]press x again to remove {name!r}[/yellow] "
                "(any other action cancels)"
            )
            return
        self._pending_remove = None
        try:
            operations.remove_schedule(name)
            self._log(f"[yellow]removed {name}[/yellow]")
            self.refresh_table()
        except Exception as exc:
            self._log(f"[red]remove failed:[/red] {exc}")

    def action_logs(self) -> None:
        self._pending_remove = None  # any other action cancels a pending removal
        name = self._selected()
        if not name:
            return
        unit = timers.service_unit(name)
        self._log(f"[dim]$ journalctl --user-unit {unit} -n 20[/dim]")
        self._log(control.journal_text(unit, tail=20))
