"""cron-claude exception hierarchy. The CLI catches CronClaudeError → exit 1."""
from __future__ import annotations


class CronClaudeError(Exception):
    """Base for all cron-claude errors."""


class ScheduleExists(CronClaudeError):
    """A schedule with this name already exists."""


class ScheduleNotFound(CronClaudeError):
    """No schedule with this name exists."""


class InvalidCalendar(CronClaudeError):
    """An OnCalendar spec was rejected by systemd-analyze."""


class SystemdError(CronClaudeError):
    """A systemctl/journalctl invocation failed."""

    def __init__(self, argv: list[str], stderr: str) -> None:
        self.argv = list(argv)
        self.stderr = stderr.strip()
        super().__init__(f"command failed: {' '.join(self.argv)}\n{self.stderr}")
