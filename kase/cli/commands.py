"""Central command registry for Kase CLI."""

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class CommandDef:
    name: str
    description: str
    category: str
    aliases: Tuple[str, ...] = ()
    args_hint: str = ""
    cli_only: bool = False
    gateway_only: bool = False


COMMAND_REGISTRY: List[CommandDef] = [
    CommandDef("help", "Show this help message", "Info", aliases=("h", "?")),
    CommandDef("exit", "Exit Kase", "Exit", aliases=("quit", "q", "bye")),
    CommandDef("clear", "Clear the screen", "Session", aliases=("cls",)),
    CommandDef("reset", "Start a new conversation", "Session", aliases=("new", "fresh")),
    CommandDef("model", "Switch the active model", "Configuration", aliases=("m",), args_hint="<model>"),
    CommandDef("provider", "Switch provider", "Configuration", aliases=("p",), args_hint="<provider>"),
    CommandDef("mode", "Switch task mode (agentic/reasoning/coding/summary/image_gen)", "Configuration", aliases=(), args_hint="<mode>"),
    CommandDef("btw", "Ask a question or give direction during a task", "Session", aliases=("bytheway", "ps")),
    CommandDef("teach", "Teach Kase something to remember forever", "Memory", aliases=("learn", "remember"), args_hint="<fact|preference|knowledge> <text>"),
    CommandDef("forget", "Delete learned memories", "Memory", aliases=("forgive", "unlearn"), args_hint="[content|--type <type>|--all]"),
    CommandDef("learned", "Show what Kase has learned", "Memory", aliases=("memories", "whatiknow"), args_hint="[type]"),
    CommandDef("tools", "Configure toolsets", "Tools & Skills", aliases=("tool",)),
    CommandDef("skills", "Manage skills", "Tools & Skills", aliases=("skill",), args_hint="<action> [name]"),
    CommandDef("memory", "View or manage memory", "Tools & Skills", aliases=("mem",)),
    CommandDef("status", "Show session info", "Info", aliases=("stats",)),
    CommandDef("cron", "Manage cron jobs", "Tools & Skills", aliases=(), args_hint="<action>"),
    CommandDef("kanban", "Kanban board management", "Tools & Skills", aliases=(), args_hint="<action>"),
    CommandDef("skin", "Change the CLI theme", "Configuration", aliases=(), args_hint="<name>"),
    CommandDef("web", "Launch Kase Web Panel", "Configuration", aliases=("webui", "server"), args_hint="[port] [--bg]"),
    CommandDef("config", "View or edit config", "Configuration", aliases=("cfg",), args_hint="[key] [value]"),
    CommandDef("export", "Export conversation", "Session", aliases=(), args_hint="[file]"),
    CommandDef("undo", "Undo last tool call", "Session", aliases=("u",)),
    CommandDef("retry", "Retry the last step", "Session", aliases=("r",)),
    CommandDef("save", "Save conversation to file", "Session", aliases=(), args_hint="<file>"),
    CommandDef("version", "Show Kase version", "Info", aliases=("v", "--version")),
]

COMMANDS_BY_CATEGORY: dict = {}
for cmd in COMMAND_REGISTRY:
    COMMANDS_BY_CATEGORY.setdefault(cmd.category, []).append(cmd)
