"""Job runners — produce ExecStart= for a scheduled job.

select_runner() dispatches on the prompt: an executable prompt runs directly
(ScriptRunner); a non-executable text prompt is wrapped in `claude -p`
(ClaudeRunner). The protocol is deliberately minimal so other runner types
(plain shell, python, pacman hooks) can be added without touching systemd/.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol, runtime_checkable

from cron_claude.errors import CronClaudeError
from cron_claude.runners.claude import ClaudeRunner
from cron_claude.runners.script import ScriptRunner


@runtime_checkable
class Runner(Protocol):
    prompt_path: Path

    def validate(self) -> None: ...
    def to_exec_start(self) -> str: ...


def select_runner(
    prompt_path: Path,
    *,
    allowed_tools: tuple[str, ...] = (),
    bare: bool = True,
    output_format: str = "json",
    permission_mode: str | None = None,
    dangerously_skip: bool = False,
    timeout_sec: int | None = None,
) -> Runner:
    if not prompt_path.exists():
        raise CronClaudeError(f"prompt not found: {prompt_path}")
    if prompt_path.is_file() and os.access(prompt_path, os.X_OK):
        return ScriptRunner(prompt_path=prompt_path)
    return ClaudeRunner(
        prompt_path=prompt_path,
        allowed_tools=tuple(allowed_tools),
        bare=bare,
        output_format=output_format,
        permission_mode=permission_mode,
        dangerously_skip=dangerously_skip,
        timeout_sec=timeout_sec,
    )


__all__ = ["Runner", "ClaudeRunner", "ScriptRunner", "select_runner"]
