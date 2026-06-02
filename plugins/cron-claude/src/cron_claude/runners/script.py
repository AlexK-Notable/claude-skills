"""ScriptRunner — ExecStart for an executable prompt script.

The script owns its own `claude -p` invocation (allowed-tools, etc.), exactly
like the legacy prompts/ playground. ExecStart is simply the absolute path —
no systemd-quoting concerns.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from cron_claude.errors import CronClaudeError


@dataclass(slots=True, frozen=True)
class ScriptRunner:
    prompt_path: Path

    def validate(self) -> None:
        p = self.prompt_path
        if not p.is_file():
            raise CronClaudeError(f"prompt is not a file: {p}")
        if not os.access(p, os.X_OK):
            raise CronClaudeError(f"prompt is not executable: {p}")

    def to_exec_start(self) -> str:
        self.validate()
        return str(self.prompt_path.resolve())
