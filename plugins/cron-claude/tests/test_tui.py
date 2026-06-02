"""TUI smoke: app mounts, populates the schedule table from list_units()."""
import pytest

import cron_claude.systemd.timers as timers
from cron_claude.systemd.timers import TimerSpec


@pytest.mark.asyncio
async def test_tui_lists_schedules(monkeypatch, tmp_path):
    monkeypatch.setattr(timers, "UNITS_DIR", tmp_path)
    timers.write_units(TimerSpec(
        name="demo", on_calendar="daily", exec_start="/bin/true",
        prompt_path="/bin/true", runner="script",
    ))
    from cron_claude.tui.app import CronClaudeApp
    app = CronClaudeApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        table = app.query_one("#schedules")
        assert table.row_count == 1
