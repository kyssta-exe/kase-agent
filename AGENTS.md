# Kase Agent - Development Guide

Kase is a next-generation AI agent developed by Kyssta. It is designed to be
smarter, faster, and more optimized than any other agent framework.

## Project Structure

```
kase-agent/
├── kase/
│   ├── __init__.py          # Package metadata
│   ├── __main__.py          # `python -m kase` entry point
│   ├── utils.py             # Shared utilities
│   ├── logging_setup.py     # Logging configuration
│   ├── toolsets.py          # Toolset definitions
│   ├── agent/               # Agent internals
│   │   ├── core.py          # AIAgent class (main orchestrator)
│   │   ├── display.py       # CLI presentation
│   │   ├── system_prompt.py # Prompt assembly
│   │   ├── redact.py        # Secret redaction
│   │   ├── file_safety.py   # Write/read safety rules
│   │   ├── error_classifier.py  # API error taxonomy
│   │   ├── context_engine.py    # Context engine ABC
│   │   ├── context_compressor.py # Context compression
│   │   ├── memory_manager.py    # Memory orchestration
│   │   ├── credential_pool.py   # Credential management
│   │   ├── model_metadata.py    # Model context mapping
│   │   ├── message_sanitization.py  # Message cleaning
│   │   ├── think_scrubber.py    # Reasoning tag removal
│   │   ├── iteration_budget.py  # Turn budget
│   │   ├── tool_dispatch_helpers.py  # Tool call dispatching
│   │   ├── tool_executor.py     # Sequential/concurrent execution
│   │   ├── tool_guardrails.py   # Tool loop detection
│   │   ├── auxiliary_client.py  # Side-task LLM calls
│   │   └── curator.py           # Skill archiving
│   ├── tools/               # Tool implementations
│   │   ├── registry.py      # Central tool registry
│   │   ├── file_tools.py    # read_file, write_file, etc.
│   │   ├── terminal_tool.py # terminal, process
│   │   ├── web_tools.py     # web_search, web_extract
│   │   ├── browser_tool.py  # browser automation
│   │   ├── delegate_tool.py # subagent spawning
│   │   ├── code_execution_tool.py # sandboxed code
│   │   ├── memory_tool.py   # persistent memory
│   │   ├── vision_tools.py  # image analysis
│   │   ├── todo_tool.py     # task tracking
│   │   ├── skills_tool.py   # skill management
│   │   ├── cronjob_tools.py # scheduled jobs
│   │   ├── kanban_tools.py  # multi-agent board
│   │   ├── message_tool.py  # cross-platform messages
│   │   ├── approval.py      # command safety
│   │   ├── image_gen_tools.py   # image generation
│   │   ├── tts_tools.py     # text-to-speech
│   │   ├── session_search_tool.py  # conversation search
│   │   ├── clarify_tool.py  # ambiguity resolution
│   │   └── browser_tool.py  # browser interaction
│   ├── cli/                 # CLI subsystem
│   │   ├── main.py          # Interactive REPL
│   │   ├── config.py        # YAML config management
│   │   ├── commands.py      # Command registry
│   │   ├── skin_engine.py   # Theming system
│   │   └── banner.py        # Startup banner
│   ├── providers/           # LLM provider profiles
│   │   ├── base.py          # ProviderProfile ABC
│   │   ├── openai_provider.py
│   │   ├── anthropic_provider.py
│   │   ├── gemini_provider.py
│   │   ├── bedrock_provider.py
│   │   ├── deepseek_provider.py
│   │   ├── openrouter_provider.py
│   │   ├── groq_provider.py
│   │   ├── grok_provider.py
│   │   ├── perplexity_provider.py
│   │   ├── together_provider.py
│   │   ├── fireworks_provider.py
│   │   ├── cohere_provider.py
│   │   ├── huggingface_provider.py
│   │   ├── replicate_provider.py
│   │   ├── mistral_provider.py
│   │   ├── azure_provider.py
│   │   ├── vertex_provider.py
│   │   ├── sambanova_provider.py
│   │   ├── cerebras_provider.py
│   │   ├── anyscale_provider.py
│   │   ├── octoai_provider.py
│   │   ├── deepinfra_provider.py
│   │   ├── lepton_provider.py
│   │   ├── stability_provider.py
│   │   ├── nvidia_provider.py
│   │   ├── xai_provider.py
│   │   ├── ai21_provider.py
│   │   ├── novita_provider.py
│   │   ├── minimax_provider.py
│   │   ├── alibaba_provider.py
│   │   └── kilocode_provider.py
│   ├── gateway/             # Multi-platform messaging
│   │   ├── run.py           # Gateway runner
│   │   ├── config.py        # Gateway config
│   │   ├── session.py       # Session management
│   │   ├── stream_consumer.py   # Stream bridging
│   │   └── platforms/       # Platform adapters
│   ├── transports/          # Transport layer
│   │   └── base.py          # Transport dataclasses
│   ├── plugins/             # Plugin system
│   │   └── manager.py       # Plugin discovery/loading
│   ├── skills/              # Skill system
│   │   └── manager.py       # Skill discovery/loading
│   ├── kanban/              # Multi-agent coordination
│   │   └── board.py         # SQLite kanban board
│   ├── cron/                # Job scheduling
│   │   └── scheduler.py     # Cron scheduler
│   └── acp/                 # Editor integration
│       └── server.py        # ACP JSON-RPC server
├── setup.py                 # Package setup
├── pyproject.toml            # Project config
└── AGENTS.md                # This file
```

## Architecture

### AIAgent Class

The `AIAgent` class in `kase/agent/core.py` is the main orchestrator:

```python
agent = AIAgent(
    model="gpt-4o",
    provider="openai",
    platform="cli",
    enabled_toolsets=["kase-cli"],
)
response = agent.chat("Hello!")
```

### Providers (31 total)

Kase supports 31 LLM providers through provider profiles, all registered
automatically at import time. Each profile defines models, base URLs, env keys,
and availability checks. To switch providers:

```python
agent = AIAgent(model="claude-3-5-sonnet", provider="anthropic")
```

### Agent Loop

1. User message → sanitize → system prompt → LLM call
2. If tool calls → dispatch → append results → continue loop
3. If text response → return to user

### Tool Registry

Tools auto-register via `registry.register()` at module import time.
Discovery via string search detects top-level `registry.register()` calls.

### Toolset Definitions

Toolsets are defined in `kase/toolsets.py` as named groups of tools.
`kase-cli` enables all core tools. Other toolsets like `kanban`, `browser`,
`terminal` provide focused subsets.

### Security

- File safety: write-denied paths (.ssh, .env, /etc/), read-blocked credential stores
- Secret redaction: 18+ regex patterns for API keys, tokens, passwords
- Command safety: hardline/dangerous pattern detection for terminal commands
- Tool guardrails: repeat-call detection, failure thresholds
- Code sandbox: restricted builtins, AST-level import whitelist

Skills provide specialized instructions and workflows for specific tasks.
Use the skill tool to load a skill when a task matches its description.
