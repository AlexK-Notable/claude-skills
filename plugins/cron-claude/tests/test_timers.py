"""write_units → list_units round-trip + unit file content."""
import pytest

import cron_claude.systemd.timers as t
from cron_claude.errors import CronClaudeError
from cron_claude.systemd.timers import TimerSpec


def _spec(name="demo"):
    return TimerSpec(
        name=name,
        on_calendar="Sun 03:07",
        exec_start="/abs/prompt",
        prompt_path="/abs/prompt",
        runner="script",
        description="weekly demo",
        randomized_delay_sec=300,
        timeout_sec=120,
    )


def test_write_units_creates_pair_with_marker(tmp_path, monkeypatch):
    monkeypatch.setattr(t, "UNITS_DIR", tmp_path)
    svc, tmr = t.write_units(_spec())
    assert svc.exists() and tmr.exists()
    assert svc.name == "cron-claude-demo.service"
    assert tmr.name == "cron-claude-demo.timer"
    svc_text = svc.read_text()
    assert "X-CronClaude-Managed=1" in svc_text
    assert "Type=oneshot" in svc_text
    assert "ExecStart=/abs/prompt" in svc_text
    assert "TimeoutStartSec=120" in svc_text
    tmr_text = tmr.read_text()
    assert "OnCalendar=Sun 03:07" in tmr_text
    assert "RandomizedDelaySec=300" in tmr_text
    assert "WantedBy=timers.target" in tmr_text


def test_list_units_roundtrips(tmp_path, monkeypatch):
    monkeypatch.setattr(t, "UNITS_DIR", tmp_path)
    t.write_units(_spec("alpha"))
    t.write_units(_spec("beta"))
    got = {s.name: s for s in t.list_units()}
    assert set(got) == {"alpha", "beta"}
    a = got["alpha"]
    assert a.on_calendar == "Sun 03:07"
    assert a.exec_start == "/abs/prompt"
    assert a.runner == "script"
    assert a.prompt_path == "/abs/prompt"
    assert a.randomized_delay_sec == 300
    assert a.timeout_sec == 120


def test_remove_units(tmp_path, monkeypatch):
    monkeypatch.setattr(t, "UNITS_DIR", tmp_path)
    svc, tmr = t.write_units(_spec("gone"))
    t.remove_units("gone")
    assert not svc.exists() and not tmr.exists()


def test_list_ignores_foreign_units(tmp_path, monkeypatch):
    monkeypatch.setattr(t, "UNITS_DIR", tmp_path)
    (tmp_path / "cron-claude-x.timer").write_text("[Timer]\nOnCalendar=daily\n")
    (tmp_path / "cron-claude-x.service").write_text("[Service]\nExecStart=/bin/true\n")  # no marker
    assert list(t.list_units()) == []


def test_service_has_onfailure_and_template_is_written(tmp_path, monkeypatch):
    monkeypatch.setattr(t, "UNITS_DIR", tmp_path)
    svc, _ = t.write_units(_spec())
    assert "OnFailure=cron-claude-notify-fail@%n.service" in svc.read_text()
    template = tmp_path / "cron-claude-notify-fail@.service"
    assert template.exists()
    text = template.read_text()
    assert "notify-send" in text
    assert "%i" in text  # instance = failed unit name


def test_write_notify_template_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr(t, "UNITS_DIR", tmp_path)
    p1 = t.write_notify_template()
    first = p1.read_text()
    p2 = t.write_notify_template()
    assert p1 == p2 and p2.read_text() == first


def test_remove_units_keeps_shared_notify_template(tmp_path, monkeypatch):
    # The template is shared by ALL schedules — removing one must not drop it.
    monkeypatch.setattr(t, "UNITS_DIR", tmp_path)
    t.write_units(_spec("a"))
    t.write_units(_spec("b"))
    t.remove_units("a")
    assert (tmp_path / "cron-claude-notify-fail@.service").exists()


def test_percent_escaped_in_rendered_units_and_roundtrips(tmp_path, monkeypatch):
    # Unescaped % would be eaten/expanded by systemd specifier expansion.
    monkeypatch.setattr(t, "UNITS_DIR", tmp_path)
    spec = TimerSpec(
        name="pct",
        on_calendar="daily",
        exec_start="/bin/echo 100% done",
        prompt_path="/bin/echo",
        runner="script",
        description="50% description",
    )
    svc, tmr = t.write_units(spec)
    svc_text = svc.read_text()
    assert "ExecStart=/bin/echo 100%% done" in svc_text
    assert "Description=50%% description" in svc_text
    assert "Description=50%% description" in tmr.read_text()
    # Our own specifiers must survive escaping of user values.
    assert "Environment=PATH=%h/.local/bin" in svc_text
    assert "OnFailure=cron-claude-notify-fail@%n.service" in svc_text
    # Parsing back must un-escape (round-trip).
    got = {s.name: s for s in t.list_units()}["pct"]
    assert got.exec_start == "/bin/echo 100% done"
    assert got.description == "50% description"


def test_validate_name_rejects_traversal():
    with pytest.raises(CronClaudeError, match="letters, digits"):
        t.validate_name("foo/../../evil")
    t.validate_name("ok-name_2")  # no raise


def test_write_units_rejects_newline_in_description(tmp_path, monkeypatch):
    monkeypatch.setattr(t, "UNITS_DIR", tmp_path)
    spec = TimerSpec(
        name="x", on_calendar="daily", exec_start="/bin/true",
        prompt_path="/bin/true", runner="script",
        description="ok\n[Service]\nExecStartPre=/bin/touch /tmp/pwned",
    )
    with pytest.raises(CronClaudeError):
        t.write_units(spec)
