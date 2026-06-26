#!/usr/bin/env python3
"""
AITestArena terminal-summary wrapper.

Purpose:
Run an operational command through the shared OpenClaw terminal-summary sender
so every important server operation leaves a compact email evidence trail.

This intentionally does not implement mail delivery itself. The runtime source
of truth remains:

    /root/openclaw/ops/mail_terminal_summary.py

That script executes the command, redacts/summarizes output, and sends the
terminal summary email.

Safe boundaries:
- no cron edits;
- no nginx edits;
- no bankroll/positions/settlement changes;
- no real-money or real-bet logic;
- no secrets printed by this wrapper.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

DEFAULT_MAIL_SUMMARY = Path("/root/openclaw/ops/mail_terminal_summary.py")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a command via /root/openclaw/ops/mail_terminal_summary.py."
    )
    parser.add_argument(
        "--topic",
        required=True,
        help='Short summary topic, e.g. "AITestArena | Training page | patch | SAFE".',
    )
    parser.add_argument(
        "--cmd",
        required=True,
        help="Shell command to execute and summarize.",
    )
    parser.add_argument(
        "--cwd",
        default=None,
        help="Optional working directory for the command.",
    )
    parser.add_argument(
        "--send-on",
        default="always",
        choices=("always", "failure", "success"),
        help="When the underlying summary sender should send mail. Default: always.",
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=200,
        help="Maximum summarized output lines. Default: 200.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=40,
        help="Command timeout in seconds. Default: 40.",
    )
    parser.add_argument(
        "--summary-script",
        default=str(DEFAULT_MAIL_SUMMARY),
        help=f"Path to mail_terminal_summary.py. Default: {DEFAULT_MAIL_SUMMARY}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary_script = Path(args.summary_script)

    if not summary_script.exists():
        print(
            f"ERROR: terminal summary sender not found: {summary_script}",
            file=sys.stderr,
        )
        print(
            "Expected runtime helper: /root/openclaw/ops/mail_terminal_summary.py",
            file=sys.stderr,
        )
        return 2

    command = [
        sys.executable,
        str(summary_script),
        "--topic",
        args.topic,
        "--cmd",
        args.cmd,
        "--send-on",
        args.send_on,
        "--max-lines",
        str(args.max_lines),
        "--timeout",
        str(args.timeout),
    ]

    if args.cwd:
        command.extend(["--cwd", args.cwd])

    completed = subprocess.run(command, check=False)
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
