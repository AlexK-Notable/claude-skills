"""ClaudeRunner — ExecStart for a TEXT prompt wrapped in a `claude -p` call.

Flag spellings verified against `claude --help` (2026-06-02): there is no
--max-turns, and permission_mode defaults to None (rely on the --allowed-tools
allowlist, per the safe-cron model).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from cron_claude.errors import CronClaudeError

VALID_MODES = ("acceptEdits", "auto", "bypassPermissions", "default", "plan")
VALID_FORMATS = ("text", "json", "stream-json")


@dataclass(slots=True, frozen=True)
class ClaudeRunner:
    prompt_path: Path
    allowed_tools: tuple[str, ...] = field(default_factory=tuple)
    bare: bool = True
    output_format: str = "json"
    permission_mode: str | None = None
    dangerously_skip: bool = False
    timeout_sec: int | None = 120

    def validate(self) -> None:
        if not self.prompt_path.is_file():
            raise CronClaudeError(f"prompt is not a file: {self.prompt_path}")
        if self.output_format not in VALID_FORMATS:
            raise CronClaudeError(
                f"invalid output format {self.output_format!r}; "
                f"choose one of {', '.join(VALID_FORMATS)}"
            )
        if self.permission_mode is not None and self.permission_mode not in VALID_MODES:
            raise CronClaudeError(
                f"invalid permission mode {self.permission_mode!r}; "
                f"choose one of {', '.join(VALID_MODES)}"
            )

    def to_exec_start(self) -> str:
        self.validate()
        abs_prompt = str(self.prompt_path.resolve())
        parts = ["claude", "-p", f'"$(cat "{abs_prompt}")"']
        if self.bare:
            parts.append("--bare")
        parts += ["--output-format", self.output_format]
        if self.allowed_tools:
            parts += ["--allowed-tools", f'"{" ".join(self.allowed_tools)}"']
        if self.permission_mode:
            parts += ["--permission-mode", self.permission_mode]
        if self.dangerously_skip:
            parts.append("--dangerously-skip-permissions")
        inner = " ".join(parts)
        if "'" in inner:
            raise CronClaudeError(
                "rendered command contains a single quote (prompt path or tool "
                "spec); unsupported in the bash -c wrapper"
            )
        return f"/bin/bash -c '{inner}'"
