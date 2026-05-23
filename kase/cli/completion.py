"""Shell completion scripts for Kase CLI."""

from typing import List

from kase.cli.commands import COMMAND_REGISTRY

_SUBCOMMANDS = [
    ("web", "Launch Kase Web Panel"),
    ("setup", "Interactive setup wizard"),
    ("setup model", "Configure model provider"),
    ("setup msg", "Configure messaging platforms"),
    ("gateway", "Start messaging gateway"),
    ("completion", "Generate shell completion script"),
    ("version", "Show version"),
    ("help", "Show help"),
]


def print_bash_completion():
    cmds = " ".join(cmd for cmd, _ in _SUBCOMMANDS if " " not in cmd)
    print(f"""_kase_completions() {{
    local cur prev words cword
    _init_completion || return

    if [[ $cword -eq 1 ]]; then
        COMPREPLY=($(compgen -W "{cmds} --help --version -h -v" -- "$cur"))
        return
    fi

    if [[ $cword -eq 2 && "${{words[1]}}" == "setup" ]]; then
        COMPREPLY=($(compgen -W "model msg" -- "$cur"))
        return
    fi
}}
complete -F _kase_completions kase""")


def print_zsh_completion():
    lines = ["#compdef kase", "", "_kase() {", "  local -a subcommands"]
    for cmd, desc in _SUBCOMMANDS:
        lines.append(f'    "{cmd}:{desc}"')
    lines.append('  _arguments \\')
    lines.append('    "(-h --help)"{-h,--help}"[show help]" \\')
    lines.append('    "(-v --version)"{-v,--version}"[show version]" \\')
    lines.append('    "1: :->subcmd" \\')
    lines.append('    "*: :->args"')
    lines.append("  case $state in")
    lines.append("    subcmd)")
    lines.append('      _describe "subcommand" subcommands ;;')
    lines.append("    args)")
    lines.append("      case $words[1] in")
    lines.append('        setup) _describe "setup" \'("model:configure provider" "msg:configure messaging")\' ;;')
    lines.append("      esac ;;")
    lines.append("  esac")
    lines.append("}")
    lines.append("_kase \"$@\"")
    print("\n".join(lines))


def print_fish_completion():
    print("#!/usr/bin/env fish")
    print()
    for cmd, desc in _SUBCOMMANDS:
        parts = cmd.split()
        if len(parts) == 1:
            print(f"complete -c kase -f -a '{parts[0]}' -d '{desc}'")
        else:
            print(f"complete -c kase -f -n '__fish_seen_subcommand_from {parts[0]}' -a '{parts[1]}' -d '{desc}'")
    print("complete -c kase -f -a '--help' -d 'Show help'")
    print("complete -c kase -f -a '--version' -d 'Show version'")


def print_powershell_completion():
    cmds = "; ".join(f'"{{"command":"{cmd}","description":"{desc}"}}"' for cmd, desc in _SUBCOMMANDS)
    print(f"""$script:kaseCommands = @({cmds})

Register-ArgumentCompleter -Native -CommandName kase -ScriptBlock {{
    param($wordToComplete, $commandAst, $cursorPosition)
    $words = $commandAst.CommandElements | ForEach-Object {{ $_.Value }}
    $parent = $words | Select-Object -Skip 1 | Select-Object -First 1

    if ($parent -eq "setup") {{
        $script:kaseCommands | Where-Object {{
            $_.command -like "setup/*" -and $_.command -like "*$wordToComplete*"
        }} | ForEach-Object {{
            [System.Management.Automation.CompletionResult]::new(
                $_.command.Split("/")[-1], $_.command.Split("/")[-1],
                'ParameterValue', $_.description)
        }}
        return
    }}

    $script:kaseCommands | Where-Object {{
        -not $_.command.Contains("/") -and $_.command -like "$wordToComplete*"
    }} | ForEach-Object {{
        [System.Management.Automation.CompletionResult]::new(
            $_.command, $_.command,
            'ParameterValue', $_.description)
    }}
}}""")


def get_slash_command_names() -> List[str]:
    names = []
    for cmd in COMMAND_REGISTRY:
        names.append(f"/{cmd.name}")
        for alias in cmd.aliases:
            if not alias.startswith("-"):
                names.append(f"/{alias}")
    return sorted(names)
