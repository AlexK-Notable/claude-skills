"""Errors form a single catchable hierarchy; SystemdError carries argv+stderr."""
import pytest

from cron_claude.errors import (
    CronClaudeError,
    InvalidCalendar,
    ScheduleExists,
    ScheduleNotFound,
    SystemdError,
)


@pytest.mark.parametrize("exc", [ScheduleExists, ScheduleNotFound, InvalidCalendar, SystemdError])
def test_all_subclass_base(exc):
    assert issubclass(exc, CronClaudeError)


def test_systemd_error_carries_argv_and_stderr():
    err = SystemdError(["systemctl", "--user", "start", "x"], "  boom\n")
    assert err.argv == ["systemctl", "--user", "start", "x"]
    assert err.stderr == "boom"
    assert "boom" in str(err)
    assert "systemctl --user start x" in str(err)
