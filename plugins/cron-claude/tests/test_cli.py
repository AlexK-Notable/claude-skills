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
    monkeypatch.setattr(cli.control, "start", lambda s: None)
    monkeypatch.setattr(cli.control, "journal", lambda *a, **k: 0)
    monkeypatch.setattr(cli.control, "is_active", lambda u: False)


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


def test_add_rejects_traversal_name(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    prompt = tmp_path / "job.txt"
    prompt.write_text("x")
    r = runner.invoke(
        app, ["schedule", "add", "foo/../../evil", "--when", "daily", "--prompt", str(prompt)]
    )
    assert r.exit_code == 1
    assert "letters, digits" in r.output
    assert not list(tmp_path.glob("*evil*"))


def test_rm_rejects_traversal_name(monkeypatch, tmp_path):
    # rm 'x/../../victim' --force must not unlink anything outside UNITS_DIR.
    _patch(monkeypatch, tmp_path)
    victim = tmp_path / "cron-claude-victim.service"
    victim.write_text("[Service]\n")
    (tmp_path / "cron-claude-victim.timer").write_text("[Timer]\n")
    r = runner.invoke(app, ["schedule", "rm", "sub/../victim", "--force"])
    assert r.exit_code == 1
    assert "letters, digits" in r.output
    assert victim.exists()


def test_show_rejects_traversal_name(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    r = runner.invoke(app, ["schedule", "show", "foo/../../evil"])
    assert r.exit_code == 1
    assert "letters, digits" in r.output


def test_run_rejects_traversal_name(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    r = runner.invoke(app, ["run", "foo/../../evil"])
    assert r.exit_code == 1
    assert "letters, digits" in r.output


def test_logs_rejects_traversal_name(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    r = runner.invoke(app, ["logs", "foo/../../evil"])
    assert r.exit_code == 1
    assert "letters, digits" in r.output


def test_remove_schedule_operation_rejects_traversal(monkeypatch, tmp_path):
    # The TUI calls operations.remove_schedule directly — it must validate too.
    import pytest

    import cron_claude.systemd.control as control
    from cron_claude.errors import CronClaudeError
    from cron_claude.operations import remove_schedule
    _patch(monkeypatch, tmp_path)
    for fn in ("disable_now", "stop", "daemon_reload"):
        monkeypatch.setattr(control, fn, lambda *a, **k: None)
    with pytest.raises(CronClaudeError, match="letters, digits"):
        remove_schedule("sub/../victim")


def test_show(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    prompt = tmp_path / "job.txt"
    prompt.write_text("x")
    runner.invoke(app, ["schedule", "add", "sh", "--when", "daily", "--prompt", str(prompt)])
    r = runner.invoke(app, ["schedule", "show", "sh"])
    assert r.exit_code == 0, r.output
    assert "OnCalendar=daily" in r.output
    assert "timer: inactive" in r.output


def test_show_missing_fails(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    r = runner.invoke(app, ["schedule", "show", "ghost"])
    assert r.exit_code == 1
    assert "not found" in r.output


def test_run(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    prompt = tmp_path / "job.txt"
    prompt.write_text("x")
    runner.invoke(app, ["schedule", "add", "rn", "--when", "daily", "--prompt", str(prompt)])
    r = runner.invoke(app, ["run", "rn"])
    assert r.exit_code == 0, r.output
    assert "done" in r.output


def test_run_missing_fails(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    r = runner.invoke(app, ["run", "ghost"])
    assert r.exit_code == 1
    assert "not found" in r.output


def test_logs_proxies_journal(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    prompt = tmp_path / "job.txt"
    prompt.write_text("x")
    runner.invoke(app, ["schedule", "add", "lg", "--when", "daily", "--prompt", str(prompt)])
    r = runner.invoke(app, ["logs", "lg"])
    assert r.exit_code == 0


def test_logs_missing_fails(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    r = runner.invoke(app, ["logs", "ghost"])
    assert r.exit_code == 1
    assert "not found" in r.output


def test_add_default_is_no_bare(monkeypatch, tmp_path):
    # OAuth-friendly default: text prompts must NOT get --bare unless asked.
    _patch(monkeypatch, tmp_path)
    prompt = tmp_path / "job.txt"
    prompt.write_text("summarize")
    r = runner.invoke(
        app, ["schedule", "add", "oauth", "--when", "daily", "--prompt", str(prompt)]
    )
    assert r.exit_code == 0, r.output
    assert "--bare" not in (tmp_path / "cron-claude-oauth.service").read_text()


def test_add_bare_and_format_flags(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    prompt = tmp_path / "job.txt"
    prompt.write_text("summarize")
    r = runner.invoke(app, [
        "schedule", "add", "fmt", "--when", "daily", "--prompt", str(prompt),
        "--bare", "--output-format", "text",
    ])
    assert r.exit_code == 0, r.output
    svc = (tmp_path / "cron-claude-fmt.service").read_text()
    assert "--bare" in svc
    assert "--output-format text" in svc
