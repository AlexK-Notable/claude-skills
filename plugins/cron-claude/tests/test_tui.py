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


def _write_demo(tmp_path):
    timers.write_units(TimerSpec(
        name="demo", on_calendar="daily", exec_start="/bin/true",
        prompt_path="/bin/true", runner="script",
    ))


@pytest.mark.asyncio
async def test_tui_action_run_logs_result(monkeypatch, tmp_path):
    monkeypatch.setattr(timers, "UNITS_DIR", tmp_path)
    import cron_claude.systemd.control as control
    monkeypatch.setattr(control, "start", lambda s: None)
    monkeypatch.setattr(control, "last_result", lambda s: ("success", 0))
    _write_demo(tmp_path)
    from cron_claude.tui.app import CronClaudeApp
    app = CronClaudeApp()
    logged: list[str] = []
    async with app.run_test() as pilot:
        await pilot.pause()
        monkeypatch.setattr(app, "_log", logged.append)
        await pilot.press("r")
        await pilot.pause()
    assert any("ran demo" in m for m in logged)


@pytest.mark.asyncio
async def test_tui_remove_needs_confirmation(monkeypatch, tmp_path):
    # A single `x` must NOT remove (the CLI requires --force; the TUI requires
    # a second confirming keypress).
    monkeypatch.setattr(timers, "UNITS_DIR", tmp_path)
    import cron_claude.systemd.control as control
    for fn in ("disable_now", "stop", "daemon_reload"):
        monkeypatch.setattr(control, fn, lambda *a, **k: None)
    _write_demo(tmp_path)
    from cron_claude.tui.app import CronClaudeApp
    app = CronClaudeApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.query_one("#schedules").row_count == 1
        await pilot.press("x")
        await pilot.pause()
        assert app.query_one("#schedules").row_count == 1  # still there


@pytest.mark.asyncio
async def test_tui_other_action_cancels_pending_remove(monkeypatch, tmp_path):
    monkeypatch.setattr(timers, "UNITS_DIR", tmp_path)
    import cron_claude.systemd.control as control
    for fn in ("disable_now", "stop", "daemon_reload"):
        monkeypatch.setattr(control, fn, lambda *a, **k: None)
    monkeypatch.setattr(control, "journal_text", lambda *a, **k: "log")
    _write_demo(tmp_path)
    from cron_claude.tui.app import CronClaudeApp
    app = CronClaudeApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("x")  # arm
        await pilot.press("l")  # cancels
        await pilot.press("x")  # re-arms (does not remove)
        await pilot.pause()
        assert app.query_one("#schedules").row_count == 1


@pytest.mark.asyncio
async def test_tui_action_remove_drops_row_after_confirm(monkeypatch, tmp_path):
    monkeypatch.setattr(timers, "UNITS_DIR", tmp_path)
    import cron_claude.systemd.control as control
    for fn in ("disable_now", "stop", "daemon_reload"):
        monkeypatch.setattr(control, fn, lambda *a, **k: None)
    _write_demo(tmp_path)
    from cron_claude.tui.app import CronClaudeApp
    app = CronClaudeApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.query_one("#schedules").row_count == 1
        await pilot.press("x")
        await pilot.press("x")
        await pilot.pause()
        assert app.query_one("#schedules").row_count == 0


@pytest.mark.asyncio
async def test_tui_action_logs_writes_journal(monkeypatch, tmp_path):
    monkeypatch.setattr(timers, "UNITS_DIR", tmp_path)
    import cron_claude.systemd.control as control
    monkeypatch.setattr(control, "journal_text", lambda *a, **k: "JOURNAL-XYZ")
    _write_demo(tmp_path)
    from cron_claude.tui.app import CronClaudeApp
    app = CronClaudeApp()
    logged: list[str] = []
    async with app.run_test() as pilot:
        await pilot.pause()
        monkeypatch.setattr(app, "_log", logged.append)
        await pilot.press("l")
        await pilot.pause()
    assert any("JOURNAL-XYZ" in m for m in logged)
