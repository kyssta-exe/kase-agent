"""Test that kase setup runs without triggering agent init."""
import os
import sys

# Simulate main() dispatch for 'kase setup'
sys.argv = ["kase", "setup"]

from kase_cli._parser import build_top_level_parser

parser, subparsers, chat_parser = build_top_level_parser()
args = parser.parse_args(["setup"])

print(f"command: {args.command!r}")
print(f"has func: {hasattr(args, 'func')}")

# This is what main() calls:
from kase_cli.main import _prepare_agent_startup
_prepare_agent_startup(args)

print("_prepare_agent_startup OK")

# Now call the actual command
print("Calling cmd_setup...")
args.func(args)
print("cmd_setup returned (no crash)")
