"""Kase CLI — main entry point and interactive REPL."""

import logging
import os
import shlex
import shutil
import signal
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter, FuzzyWordCompleter, merge_completers
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style as PTStyle
from prompt_toolkit.patch_stdout import patch_stdout

from kase import __version__
from kase.agent.core import AIAgent
from kase.agent.display import KawaiiSpinner, build_tool_preview
from kase.cli.banner import show_banner
from kase.cli.commands import COMMAND_REGISTRY, CommandDef
from kase.cli.config import load_config, save_config
from kase.cli.skin_engine import init_skin_from_config, get_active_skin
from kase.logging_setup import setup_logging
from kase.tools.registry import registry, discover_builtin_tools
from kase.utils import get_kase_home


logger = logging.getLogger(__name__)


class KaseCLI:
    """Kase interactive CLI."""

    def __init__(self):
        self._kase_home = get_kase_home()
        self._kase_home.mkdir(parents=True, exist_ok=True)
        
        setup_logging("kase-cli")
        self.config = load_config()
        self.skin = init_skin_from_config(self.config)
        
        self._setup_dotenv()
        discover_builtin_tools()
        
        self.agent: Optional[AIAgent] = None
        self._init_agent()
        
        self._history_file = self._kase_home / "history.txt"
        self._history_file.parent.mkdir(parents=True, exist_ok=True)

        from kase.cli.completion import get_slash_command_names
        self._slash_completer = FuzzyWordCompleter(
            get_slash_command_names(),
            sentence=True,
            match_middle=True,
        )
        self._session = PromptSession(
            history=FileHistory(str(self._history_file)),
            completer=self._slash_completer,
            complete_while_typing=True,
        )
        
        self._prompt_style = PTStyle.from_dict({
            "prompt": "ansiyellow",
            "command": "ansicyan",
        })
        
        self._running = True
        
        signal.signal(signal.SIGINT, self._handle_sigint)

    def _setup_dotenv(self):
        try:
            from dotenv import load_dotenv
            env_files = [
                self._kase_home / ".env",
                Path.cwd() / ".env",
            ]
            for env_file in env_files:
                if env_file.exists():
                    load_dotenv(env_file)
                    break
        except ImportError:
            pass

    def _init_agent(self):
        cfg = self.config
        self.agent = AIAgent(
            model=cfg.get("model", os.getenv("KASE_MODEL", "gpt-4o")),
            provider=cfg.get("provider", os.getenv("KASE_PROVIDER", "openai")),
            api_key=cfg.get("api_key", ""),
            base_url=cfg.get("base_url", ""),
            api_mode=cfg.get("api_mode", "chat_completions"),
            max_iterations=cfg.get("max_iterations", 90),
            enabled_toolsets=cfg.get("enabled_toolsets", ["kase-cli"]),
            disabled_toolsets=cfg.get("disabled_toolsets", []),
            quiet_mode=cfg.get("quiet_mode", False),
            platform="cli",
        )

    def _handle_sigint(self, sig, frame):
        if self.agent:
            self.agent.interrupt()
        print("\n[Interrupted]")
        self._running = False

    def run(self):
        show_banner()
        print(f"  Type /help for commands, or just start chatting!")
        print(f"  Model: {self.agent.model} | Provider: {self.agent.provider}")
        print()
        
        while self._running:
            try:
                user_input = self._get_input()
                if user_input is None:
                    continue
                
                if user_input.startswith("/"):
                    self._handle_command(user_input)
                elif user_input.strip():
                    self._handle_message(user_input)
                else:
                    continue
                    
            except (KeyboardInterrupt, EOFError):
                print()
                self._running = False
        
        print("Goodbye! ✦")

    def _get_input(self) -> Optional[str]:
        try:
            skin = get_active_skin()
            prompt_symbol = skin.branding.get("prompt_symbol", "✦ ") if skin else "✦ "
            mode_hint = ""
            if self.agent and hasattr(self.agent, "_model_router"):
                router = self.agent._model_router
                if router.is_multi_model() and router.active_task != "agentic":
                    mode_hint = f"[{router.active_task[:4]}] "
            full_prompt = f"{mode_hint}{prompt_symbol}"
            text = self._session.prompt(full_prompt)
            return text.strip()
        except (EOFError, KeyboardInterrupt):
            return None

    def _handle_command(self, text: str):
        parts = shlex.split(text)
        cmd = parts[0].lstrip("/").lower()
        args = parts[1:]
        
        command_map = {}
        for cmd_def in COMMAND_REGISTRY:
            command_map[cmd_def.name] = cmd_def
            for alias in cmd_def.aliases:
                command_map[alias] = cmd_def
        
        cmd_def = command_map.get(cmd)
        if cmd_def:
            handler_name = f"_cmd_{cmd_def.name}"
            handler = getattr(self, handler_name, None)
            if handler:
                handler(args, text)
            else:
                print(f"Command /{cmd_def.name} not implemented yet")
        else:
            print(f"Unknown command: /{cmd}. Type /help for commands.")

    def _handle_message(self, message: str):
        if not self.agent:
            self._init_agent()
        
        with patch_stdout():
            result = self.agent.run_conversation(message)
        
        final = result.get("final_response", "")
        if final:
            print(f"\n  {final}\n")
        
        usage = result.get("usage", {})
        api_calls = result.get("api_calls", 0)
        tool_calls = result.get("tool_calls", 0)
        
        if api_calls > 1 or tool_calls > 0:
            pts = usage.get("prompt_tokens", 0)
            cts = usage.get("completion_tokens", 0)
            print(f"  [{api_calls} call{'s' if api_calls != 1 else ''}, "
                  f"{tool_calls} tool{'s' if tool_calls != 1 else ''}, "
                  f"{pts + cts:,} tokens]")

    def _cmd_help(self, args: List[str], raw: str):
        from kase.cli.commands import COMMANDS_BY_CATEGORY
        
        print("\n  Kase Commands:")
        print(f"  {'─' * 50}")
        
        for category, cmds in COMMANDS_BY_CATEGORY.items():
            print(f"\n  {category}:")
            for cmd in cmds:
                aliases = f" ({', '.join('/' + a for a in cmd.aliases)})" if cmd.aliases else ""
                hint = f" {cmd.args_hint}" if cmd.args_hint else ""
                print(f"    /{cmd.name}{hint}{aliases}")
                print(f"      {cmd.description}")
        print()

    def _cmd_exit(self, args: List[str], raw: str):
        self._running = False

    def _cmd_clear(self, args: List[str], raw: str):
        os.system("cls" if os.name == "nt" else "clear")

    def _cmd_reset(self, args: List[str], raw: str):
        if self.agent:
            self.agent.reset_session()
        print("Session reset. Starting fresh.")

    def _cmd_web(self, args: List[str], raw: str):
        port = 8080
        bg = False
        for arg in args:
            if arg == "--bg" or arg == "-b":
                bg = True
            elif arg.isdigit():
                port = int(arg)
        from kase.web_panel.server import run_web_panel
        from kase.web_panel.analytics import AnalyticsTracker
        analytics = AnalyticsTracker()
        run_web_panel(host="127.0.0.1", port=port, agent=self.agent,
                      analytics=analytics, config=self.config, bg=bg)

    def _cmd_model(self, args: List[str], raw: str):
        if not args:
            print(f"Current model: {self.agent.model}")
            return
        self.agent.model = args[0]
        self.config["model"] = args[0]
        save_config(self.config)
        print(f"Model switched to: {args[0]}")

    def _cmd_provider(self, args: List[str], raw: str):
        if not args:
            print(f"Current provider: {self.agent.provider}")
            return
        
        from kase.providers import registry as provider_registry
        available = provider_registry.list_providers()
        
        if args[0] not in available:
            print(f"Unknown provider: {args[0]}")
            print(f"Available: {', '.join(available)}")
            return
        
        self.agent.provider = args[0]
        self.config["provider"] = args[0]
        self.agent._init_client()
        save_config(self.config)
        print(f"Provider switched to: {args[0]}")
        
        self.agent.reset_session()
        print("Session reset for new provider.")

    def _cmd_status(self, args: List[str], raw: str):
        status = self.agent.get_status() if self.agent else {}
        mm = status.get("multi_model", {})
        routes = mm.get("routes", {})
        print(f"\n  Session:  {status.get('session_id', 'N/A')[:16]}...")
        print(f"  Model:    {status.get('model', 'N/A')}")
        print(f"  Provider: {status.get('provider', 'N/A')}")
        print(f"  Mode:     {status.get('active_mode', 'agentic')} ({status.get('active_mode_model', 'N/A')})")
        if mm.get("multi_model"):
            for task, r in routes.items():
                print(f"    {task}: {r.get('provider','?')}/{r.get('model','?')}", end="")
                if r.get("has_fallbacks"):
                    print(" [+fallbacks]", end="")
                if r.get("cli_tools"):
                    print(f" [CLI: {', '.join(r['cli_tools'])}]", end="")
                print()
        print(f"  API Calls:{status.get('api_calls', 0)}")
        print(f"  Tool Calls: {status.get('tool_calls', 0)}")
        print(f"  Tokens:   {status.get('total_tokens', 0):,}")
        print(f"  Messages: {status.get('messages', 0)}")
        if hasattr(self.agent, "_long_term_memory") and self.agent._long_term_memory:
            stats = self.agent._long_term_memory.get_stats()
            print(f"  Memories: {stats.get('total_facts', 0)} stored")
        print()

    def _cmd_version(self, args: List[str], raw: str):
        print(f"Kase Agent v{__version__}")

    def _cmd_config(self, args: List[str], raw: str):
        import yaml
        if not args:
            print(yaml.dump(self.config, default_flow_style=False))
        elif len(args) == 2:
            self.config[args[0]] = yaml.safe_load(args[1])
            save_config(self.config)
            print(f"Config {args[0]} set.")

    def _cmd_skin(self, args: List[str], raw: str):
        if not args:
            print(f"Current skin: {get_active_skin().name if get_active_skin() else 'default'}")
            return
        from kase.cli.skin_engine import set_active_skin
        skin = set_active_skin(args[0])
        if skin:
            self.config.setdefault("display", {})["skin"] = args[0]
            save_config(self.config)
            print(f"Skin switched to: {args[0]}")
        else:
            print(f"Unknown skin: {args[0]}")

    def _cmd_export(self, args: List[str], raw: str):
        path = args[0] if args else f"kase_export_{int(time.time())}.json"
        if self.agent:
            import json
            Path(path).write_text(json.dumps({
                "session_id": self.agent.session_id,
                "model": self.agent.model,
                "messages": self.agent._messages[-100:],
                "usage": self.agent.usage,
            }, indent=2), encoding="utf-8")
            print(f"Exported to: {path}")

    def _cmd_tools(self, args: List[str], raw: str):
        tools = registry.get_all_tool_names()
        print(f"\n  Registered tools ({len(tools)}):")
        for tool in tools:
            print(f"    • {tool}")
        print()

    def _cmd_mode(self, args: List[str], raw: str):
        if not args:
            routes = self.agent._model_router.get_all_routes()
            print(f"\n  Active mode: {self.agent._model_router.active_task}")
            print(f"  Available modes:")
            for task, route in routes.items():
                fb = f" (fallbacks: {len(route.fallbacks)})" if route.fallbacks else ""
                cli = f" [CLI: {', '.join(t.name for t in (route.cli_tools or []))}]" if route.cli_tools else ""
                print(f"    {task}: {route.provider}/{route.model}{fb}{cli}")
            print()
            return
        from kase.agent.model_router import ALL_TASK_TYPES
        mode = args[0].lower()
        if mode not in ALL_TASK_TYPES:
            print(f"  Unknown mode: {mode}")
            print(f"  Available: {', '.join(ALL_TASK_TYPES)}")
            return
        if self.agent._switch_task_mode(mode):
            route = self.agent._model_router.get_route(mode)
            print(f"  Switched to {mode} mode: {route.provider}/{route.model}")
            self.config["multi_model"] = self.config.get("multi_model", {})
            self.config["multi_model"]["default_mode"] = mode
            save_config(self.config)
        else:
            print(f"  Failed to switch to {mode} mode")

    def _cmd_memory(self, args: List[str], raw: str):
        if hasattr(self.agent, "_long_term_memory") and self.agent._long_term_memory:
            ltm = self.agent._long_term_memory
            stats = ltm.get_stats()
            print(f"\n  Long-Term Memory:")
            print(f"    Facts stored: {stats.get('total_facts', 0)}")
            print(f"    Preferences: {stats.get('total_preferences', 0)}")
            print(f"    Knowledge items: {stats.get('total_knowledge', 0)}")
            if args and args[0] == "list":
                facts = ltm.get_all()
                for f in facts:
                    print(f"    • [{f.get('type','fact')}] {f.get('content','')[:100]}")
            print()
        else:
            print("  Memory: use the 'memory' tool to read/write from within a conversation.")

    def _cmd_btw(self, args: List[str], raw: str):
        if not args:
            print("  Usage: /btw <your question or direction>")
            return
        message = " ".join(args)
        print(f"  [Interjection noted]")
        result = self.agent.run_conversation(
            f"[Interjection from user during task: {message}]"
        )
        final = result.get("final_response", "")
        if final:
            print(f"\n  {final}\n")

    def _cmd_teach(self, args: List[str], raw: str):
        if len(args) < 2:
            print("  Usage: /teach <fact|preference|knowledge|project> <what to remember>")
            print("  Example: /teach fact I prefer Python for backend development")
            return
        mem_type = args[0].lower()
        valid_types = {"fact", "preference", "knowledge", "project", "user_info", "workflow"}
        if mem_type not in valid_types:
            mem_type = "fact"
            content = " ".join(args)
        else:
            content = " ".join(args[1:])
        if not content:
            print("  Nothing to teach!")
            return
        mem_id = self.agent.teach(content, mem_type)
        print(f"  ✓ Remembered! [{mem_type}] {content[:80]}...")
        if mem_id:
            print(f"    (id: {mem_id})")

    def _cmd_forget(self, args: List[str], raw: str):
        if not args:
            print("  Usage: /forget <content> | /forget --type <type> | /forget --all")
            return
        if args[0] == "--all":
            count = self.agent._long_term_memory.clear_all() if self.agent._long_term_memory else 0
            print(f"  Forgotten {count} memories.")
            return
        if args[0] == "--type" and len(args) > 1:
            count = self.agent.forget(memory_type=args[1])
            print(f"  Forgotten {count} memories of type '{args[1]}'.")
            return
        content = " ".join(args)
        count = self.agent.forget(content=content)
        print(f"  Forgotten {count} memories matching '{content[:60]}'.")

    def _cmd_learned(self, args: List[str], raw: str):
        mem_type = args[0] if args else None
        memories = self.agent.get_learned_memories(memory_type=mem_type)
        if not memories:
            print("  Nothing learned yet. Teach me with /teach!")
            return
        print(f"\n  What I've Learned ({len(memories)} items):")
        for m in memories:
            tags = m.get("tags", [])
            tag_str = f" [{', '.join(tags[:3])}]" if tags else ""
            print(f"    • [{m.get('memory_type', 'fact')}] {m.get('content', '')[:120]}{tag_str}")
        print()


def main():
    """Main entry point for the Kase CLI."""
    import sys
    args = sys.argv[1:]

    if "--version" in args or "-v" in args:
        print(f"Kase Agent v{__version__}")
        _print_version_info()
        return

    if not args or args[0] in ("-h", "--help", "help"):
        _print_help()
        return

    cmd = args[0]
    cmd_args = args[1:]

    if cmd in ("web", "webui", "server"):
        _cmd_web(cmd_args)
    elif cmd == "setup":
        _cmd_setup(cmd_args)
    elif cmd == "gateway":
        _cmd_gateway(cmd_args)
    elif cmd == "completion":
        _cmd_completion(cmd_args)
    elif cmd == "version":
        print(f"Kase Agent v{__version__}")
    elif cmd in ("-i", "--interactive", "cli"):
        cli = KaseCLI()
        cli.run()
    else:
        print(f"Unknown command: {cmd}")
        print(f"Run 'kase --help' for usage.")
        sys.exit(1)


def _print_version_info():
    import sys
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  Platform: {sys.platform}")


def _print_help():
    print("Usage: kase [command] [options]")
    print()
    print("Commands:")
    print("  kase                    Start interactive CLI")
    print("  kase web [port]         Launch Kase Web Panel  (default port: 8080)")
    print("  kase setup              Interactive setup wizard")
    print("  kase setup model        Configure model provider")
    print("  kase setup msg          Configure messaging platforms")
    print("  kase gateway            Start messaging gateway")
    print("  kase completion <shell> Generate shell completion script")
    print("  kase --version, -v      Show version")
    print("  kase --help, -h         Show this help")
    print()
    print("Completion:")
    print("  kase completion bash     > /etc/bash_completion.d/kase")
    print("  kase completion zsh      > /usr/local/share/zsh/site-functions/_kase")
    print("  kase completion fish     > ~/.config/fish/completions/kase.fish")
    print("  kase completion powershell > $PROFILE")
    print()
    print("Examples:")
    print("  kase web 9090           Web panel on port 9090")
    print("  kase web --host 0.0.0.0  Listen on all interfaces")
    print("  kase setup              Interactive first-run wizard")
    print("  kase setup model        Switch to a different model provider")


def _cmd_web(args):
    from kase.web_panel.server import run_web_panel
    port = 8080
    host = "127.0.0.1"
    bg = False
    for i, a in enumerate(args):
        if a == "--host" and i + 1 < len(args):
            host = args[i + 1]
        elif a == "--bg":
            bg = True
        elif a.lstrip("-").isdigit():
            port = int(a)
    print(f"  {_PROMPT_INFO} Starting Kase Web Panel on http://{host}:{port}")
    run_web_panel(host=host, port=port, bg=bg)


def _cmd_setup(args):
    from kase.cli.setup import setup_all, setup_model, setup_msg
    if not args:
        setup_all()
    elif args[0] == "model":
        setup_model()
    elif args[0] == "msg":
        setup_msg()
    else:
        print(f"Unknown setup command: {args[0]}")
        print("Usage: kase setup [model|msg]")


def _cmd_gateway(args):
    from kase.gateway.run import run_gateway
    run_gateway()


def _cmd_completion(args):
    shell = args[0] if args else "bash"
    from kase.cli.completion import (
        print_bash_completion, print_zsh_completion,
        print_fish_completion, print_powershell_completion,
    )
    printers = {
        "bash": print_bash_completion,
        "zsh": print_zsh_completion,
        "fish": print_fish_completion,
        "powershell": print_powershell_completion,
    }
    printer = printers.get(shell)
    if not printer:
        print(f"Unknown shell: {shell}")
        print(f"Supported: {', '.join(printers.keys())}")
        return
    printer()
    if shell == "bash":
        print(f"\n# Install: kase completion bash > /etc/bash_completion.d/kase")
    elif shell == "zsh":
        print(f"\n# Install: kase completion zsh > /usr/local/share/zsh/site-functions/_kase")
    elif shell == "fish":
        print(f"\n# Install: kase completion fish > ~/.config/fish/completions/kase.fish")
    elif shell == "powershell":
        print(f"\n# Install: kase completion powershell > $PROFILE")


_PROMPT_INFO = "\033[94mi\033[0m"


if __name__ == "__main__":
    main()
