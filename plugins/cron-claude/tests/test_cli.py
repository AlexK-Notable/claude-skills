"""CLI orchestration: UNITS_DIR → tmp, control.* monkeypatched (no real systemd)."""
from typer.testing import CliRunner

import cron_claude.systemd.timers as timers
from cron_claude.cli import app

runner = CliRunner()


def _patch(monkeypatch, tmp_path):
    monkeypatch.setattr(timers, "UNITS_DIR", tmp_path)
    import cron_claude.cli as cli
    monkeypatch.setattr(cli.control, "validate_calendar", lambda spec: None)
    monkeypatch.setattr(cli.control, "daemon_reload", lambda: None)
    monkeypatch.setattr(cli.control, "enable_now", lambda t: None)
    monkeypatch.setattr(cli.control, "disable_now", lambda t: None)
    monkeypatch.setattr(cli.control, "stop", lambda s: None)
    monkeypatch.setattr(cli.control, "next_elapse", lambda t: None)
    monkeypatch.setattr(cli.control, "last_result", lambda s: ("success", 0))


def test_add_then_list(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    prompt = tmp_path / "job.txt"
    prompt.write_text("summarize")
    r = runner.invoke(
        app, ["schedule", "add", "demo", "--when", "Sun 03:07", "--prompt", str(prompt)]
    )
    assert r.exit_code == 0, r.output
    assert (tmp_path / "cron-claude-demo.timer").exists()
    r2 = runner.invoke(app, ["schedule", "list"])
    assert r2.exit_code == 0
    assert "demo" in r2.output


def test_add_duplicate_fails(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    prompt = tmp_path / "job.txt"
    prompt.write_text("x")
    args = ["schedule", "add", "dup", "--when", "daily", "--prompt", str(prompt)]
    first = runner.invoke(app, args)
    assert first.exit_code == 0, first.output
    r = runner.invoke(app, args)
    assert r.exit_code == 1
    assert "already exists" in r.output


def test_rm(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    prompt = tmp_path / "job.txt"
    prompt.write_text("x")
    runner.invoke(app, ["schedule", "add", "bye", "--when", "daily", "--prompt", str(prompt)])
    r = runner.invoke(app, ["schedule", "rm", "bye", "--force"])
    assert r.exit_code == 0
    assert not (tmp_path / "cron-claude-bye.timer").exists()


def test_rm_missing_fails(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    r = runner.invoke(app, ["schedule", "rm", "ghost", "--force"])
    assert r.exit_code == 1
    assert "not found" in r.output


def test_list_json(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    prompt = tmp_path / "job.txt"
    prompt.write_text("x")
    runner.invoke(app, ["schedule", "add", "j", "--when", "daily", "--prompt", str(prompt)])
    r = runner.invoke(app, ["schedule", "list", "--json"])
    assert r.exit_code == 0
    assert '"name": "j"' in r.output


def test_add_scaffold_creates_executable(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    prompt = tmp_path / "prompts" / "newjob"
    r = runner.invoke(
        app,
        ["schedule", "add", "nj", "--when", "daily", "--prompt", str(prompt), "--scaffold"],
    )
    assert r.exit_code == 0, r.output
    assert prompt.exists() and (prompt.stat().st_mode & 0o111)
