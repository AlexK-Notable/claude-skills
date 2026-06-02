"""Runner for `claude -p` headless invocations.

Renders an ExecStart= line that invokes claude with locked-down flags suitable
for cron/timer-driven execution. Defaults reflect the canonical safe-cron
template: --bare, --permission-mode dontAsk, --output-format json, --max-turns 5.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True, frozen=True)
class ClaudeRunner:
    """Renders ExecStart= for a `claude -p` invocation backed by a prompt script."""

    prompt_path: Path
    allowed_tools: tuple[str, ...] = field(default_factory=tuple)
    bare: bool = True
    permission_mode: str = "dontAsk"
    output_format: str = "json"
    max_turns: int | None = 5
    timeout_sec: int | None = 120

    def to_exec_start(self) -> str:
        """Render the ExecStart= value for the systemd .service unit."""
        raise NotImplementedError
