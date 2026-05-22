"""Bulk rename remaining "hermes" references to "kase" across the codebase.

Safe string replacements only -- no AST-level changes, no backward-compat
aliases.  Skips binary files, .git, __pycache__, node_modules, .venv.

Run:    python scripts/rename_hermes.py          # dry-run
        python scripts/rename_hermes.py --apply  # apply changes
"""

import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}
SKIP_EXT = {".pyc", ".pyo", ".so", ".dll", ".exe", ".bin", ".lock"}

REPLACEMENTS = [
    # ── file/dir/temp path strings ──────────────────────────────────
    (".kase_history", ".kase_history"),
    ("kase_conversation_", "kase_conversation_"),
    ("kase_voice", "kase_voice"),
    ("kase_rpc", "kase_rpc"),
    ("kase_sandbox_", "kase_sandbox_"),
    ("kase_terminal", "kase_terminal"),
    ("kase_task_id", "kase_task_id"),
    ("kase_tools.py", "kase_tools.py"),
    ("kase_dist_preview_", "kase_dist_preview_"),
    ("kase_dashboard_plugin_", "kase_dashboard_plugin_"),
    ("kase_plugins.", "kase_plugins."),
    ("kase_e2e_", "kase_e2e_"),
    ("kase_atyp_", "kase_atyp_"),
    ("kase_meet_src", "kase_meet_src"),
    ("kase_meet_sink", "kase_meet_sink"),
    ("kase_test", "kase_test"),
    ('"kase_"', '"kase_"'),
    ("'kase_'", "'kase_'"),
    # ── locale keys ─────────────────────────────────────────────────
    ("kase_cmd_not_found", "kase_cmd_not_found"),
    # ── OAuth / credential naming ───────────────────────────────────
    ("kase_pkce", "kase_pkce"),
    # ── internal function aliases ───────────────────────────────────
    ("_kase_now", "_kase_now"),
    ("_KASE_OAUTH_FILE", "_KASE_OAUTH_FILE"),
    ("_KASE_PROVIDER_ENV_BLOCKLIST", "_KASE_PROVIDER_ENV_BLOCKLIST"),
    ("_KASE_PROVIDER_CLS", "_KASE_PROVIDER_CLS"),
    # ── import aliases ──────────────────────────────────────────────
    ("as kase_version", "as kase_version"),
    ("as _kase_version", "as _kase_version"),
    ("_get_env_value", "_get_env_value"),
    # ── misc internal ───────────────────────────────────────────────
    ("_KASE_GATEWAY", "_KASE_GATEWAY"),
    ("__kaseDialogBridgeInstalled", "__kaseDialogBridgeInstalled"),
]

TEXT_EXT = {
    ".py", ".js", ".ts", ".tsx", ".jsx",
    ".yaml", ".yml", ".json", ".toml",
    ".cfg", ".ini", ".html", ".css", ".scss", ".md", ".txt",
}


def process_file(filepath: str, relpath: str, apply: bool) -> int:
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception:
        return 0

    original = content
    changes = []

    for old, new in REPLACEMENTS:
        # case-insensitive find, case-sensitive replace
        if old.lower() in content.lower():
            cnt = content.count(old)
            content = content.replace(old, new)
            if cnt > 0:
                changes.append((old, new, cnt))

    if changes:
        print(f"  {relpath}")
        for old, new, cnt in changes:
            print(f"    {cnt:>4}x  {old!r} -> {new!r}")
        if apply and content != original:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
        return len(changes)
    return 0


def main():
    parser = argparse.ArgumentParser(description="Bulk-rename hermes -> kase")
    parser.add_argument("--apply", action="store_true", help="Apply changes (default: dry-run)")
    args = parser.parse_args()

    total_files = 0
    total_changes = 0

    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        if any(sd in dirpath for sd in SKIP_DIRS):
            continue

        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in TEXT_EXT or ext in SKIP_EXT:
                continue
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, ROOT)
            n = process_file(fp, rel, args.apply)
            if n:
                total_files += 1
                total_changes += n

    print(f"\n{'Applied' if args.apply else 'Dry-run'} — {total_files} files, {total_changes} changes")
    if not args.apply:
        print("Re-run with --apply to commit changes.")


if __name__ == "__main__":
    main()
