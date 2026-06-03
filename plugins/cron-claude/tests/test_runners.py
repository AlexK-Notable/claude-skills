"""Runner selection + ExecStart rendering (flags verified vs `claude --help`)."""
from pathlib import Path

import pytest

from cron_claude.errors import CronClaudeError
from cron_claude.runners import select_runner
from cron_claude.runners.claude import ClaudeRunner
from cron_claude.runners.script import ScriptRunner


def _exe(p: Path) -> Path:
    p.write_text("#!/usr/bin/env bash\nexec claude -p 'hi'\n")
    p.chmod(0o755)
    return p


def test_select_executable_prompt_is_scriptrunner(tmp_path):
    runner = select_runner(_exe(tmp_path / "job"))
    assert isinstance(runner, ScriptRunner)


def test_select_text_prompt_is_clauderunner(tmp_path):
    p = tmp_path / "job.txt"
    p.write_text("summarize my inbox")
    assert isinstance(select_runner(p), ClaudeRunner)


def test_select_missing_prompt_raises(tmp_path):
    with pytest.raises(CronClaudeError):
        select_runner(tmp_path / "nope")


def test_scriptrunner_execstart_is_abs_path(tmp_path):
    p = _exe(tmp_path / "job")
    assert ScriptRunner(prompt_path=p).to_exec_start() == str(p.resolve())


def test_scriptrunner_rejects_non_executable(tmp_path):
    p = tmp_path / "job.txt"
    p.write_text("text")
    with pytest.raises(CronClaudeError):
        ScriptRunner(prompt_path=p).validate()


def test_clauderunner_renders_expected_command(tmp_path):
    p = tmp_path / "job.txt"
    p.write_text("do the thing")
    runner = ClaudeRunner(prompt_path=p, allowed_tools=("Bash(git *)", "Edit"))
    out = runner.to_exec_start()
    abs_p = str(p.resolve())
    assert out == (
        "/bin/bash -c "
        f"'claude -p \"$(cat \"{abs_p}\")\" --bare --output-format json "
        "--allowed-tools \"Bash(git *) Edit\"'"
    )


def test_clauderunner_optional_flags(tmp_path):
    p = tmp_path / "job.txt"
    p.write_text("x")
    runner = ClaudeRunner(
        prompt_path=p, bare=False, permission_mode="bypassPermissions", dangerously_skip=True
    )
    out = runner.to_exec_start()
    assert "--bare" not in out
    assert "--permission-mode bypassPermissions" in out
    assert "--dangerously-skip-permissions" in out


def test_clauderunner_rejects_bad_permission_mode(tmp_path):
    p = tmp_path / "job.txt"
    p.write_text("x")
    with pytest.raises(CronClaudeError):
        ClaudeRunner(prompt_path=p, permission_mode="dontAsk").validate()


def test_clauderunner_rejects_bad_output_format(tmp_path):
    p = tmp_path / "job.txt"
    p.write_text("x")
    with pytest.raises(CronClaudeError):
        ClaudeRunner(prompt_path=p, output_format="yaml").validate()


@pytest.mark.parametrize("badchar", ['"', "'", "$", "`"])
def test_clauderunner_rejects_shell_unsafe_path(tmp_path, badchar):
    p = tmp_path / f"bad{badchar}.txt"
    p.write_text("x")
    with pytest.raises(CronClaudeError, match="shell-unsafe"):
        ClaudeRunner(prompt_path=p).to_exec_start()


def test_clauderunner_rejects_shell_unsafe_tool(tmp_path):
    p = tmp_path / "ok.txt"
    p.write_text("x")
    runner = ClaudeRunner(prompt_path=p, allowed_tools=('"; touch /tmp/pwned; echo "',))
    with pytest.raises(CronClaudeError, match="shell-unsafe"):
        runner.to_exec_start()
