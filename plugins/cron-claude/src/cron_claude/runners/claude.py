"""ClaudeRunner — ExecStart for a TEXT prompt wrapped in a `claude -p` call.

Flag spellings verified against `claude --help` (2026-06-02): there is no
--max-turns, and permission_mode defaults to None (rely on the --allowed-tools
allowlist, per the safe-cron model).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cron_claude.errors import CronClaudeError

VALID_MODES = ("acceptEdits", "auto", "bypassPermissions", "default", "dontAsk", "plan")
VALID_FORMATS = ("text", "json", "stream-json")

# Characters that would break out of the `/bin/bash -c '<inner>'` wrapper or its
# inner double-quoted tokens, or inject systemd directives (newlines).
_SHELL_UNSAFE = frozenset("\"'`$\\\n\r\0")


def _validate_shell_safe(label: str, value: str) -> None:
    bad = sorted({c for c in _SHELL_UNSAFE if c in value}, key=repr)
    if bad:
        raise CronClaudeError(
            f"{label} contains shell-unsafe character(s) "
            f"{', '.join(repr(c) for c in bad)}: {value!r}"
        )


@dataclass(slots=True, frozen=True)
class ClaudeRunner:
    prompt_path: Path
    allowed_tools: tuple[str, ...] = ()
    # bare=False by default: --bare makes claude ignore OAuth/keychain auth and
    # require ANTHROPIC_API_KEY, which is not set in the systemd user environment
    # on this machine (OAuth login). --bare stays available as an explicit opt-in.
    bare: bool = False
    output_format: str = "json"
    permission_mode: str | None = None
    dangerously_skip: bool = False

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
        # Every value interpolated into the bash -c wrapper must be free of shell
        # metacharacters. shlex.quote() can't help here — its single quotes would
        # terminate the outer `bash -c '...'` string. So validate, don't escape.
        _validate_shell_safe("prompt path", abs_prompt)
        for tool in self.allowed_tools:
            _validate_shell_safe("allowed-tools entry", tool)
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
        return f"/bin/bash -c '{inner}'"
