"""Job runners — produce ExecStart= commands for various job types.

Currently supports `claude -p` invocations (the original use case). The runner
protocol is deliberately minimal so other runner types (plain shell, python
scripts, pacman post-transaction hooks, etc.) can be added without touching
the systemd module.
"""
from cron_claude.runners.claude import ClaudeRunner

__all__ = ["ClaudeRunner"]
