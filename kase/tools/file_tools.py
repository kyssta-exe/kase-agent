"""File manipulation tools: read, write, patch, search."""

import json
import os
import re
from pathlib import Path
from kase.tools.registry import registry, tool_error, tool_result


def _resolve_path(path: str) -> str:
    return os.path.realpath(os.path.expanduser(path))


def read_file_tool(args: dict, **kwargs) -> str:
    path = args.get("path", "")
    offset = args.get("offset", 0)
    limit = args.get("limit", 2000)
    
    if not path:
        return tool_error("path is required")
    
    resolved = _resolve_path(path)
    if not os.path.exists(resolved):
        return tool_error(f"File not found: {path}")
    if os.path.isdir(resolved):
        return tool_error(f"Is a directory: {path}")
    
    from kase.agent.file_safety import get_read_block_error
    block = get_read_block_error(resolved)
    if block:
        return tool_error(block)
    
    try:
        with open(resolved, "r", encoding="utf-8", errors="replace") as f:
            if limit > 0:
                lines = []
                for i, line in enumerate(f):
                    if i < offset:
                        continue
                    if len(lines) >= limit:
                        break
                    lines.append(line.rstrip("\n"))
                content = "\n".join(lines)
            else:
                content = f.read()
        
        return tool_result(
            path=path,
            content=content,
            total_lines=limit if limit else 0,
        )
    except Exception as e:
        return tool_error(str(e))


def write_file_tool(args: dict, **kwargs) -> str:
    path = args.get("path", "")
    content = args.get("content", "")
    
    if not path:
        return tool_error("path is required")
    
    resolved = _resolve_path(path)
    
    from kase.agent.file_safety import is_write_denied
    if is_write_denied(resolved):
        return tool_error(f"Write denied: {path} is a protected path")
    
    try:
        os.makedirs(os.path.dirname(resolved), exist_ok=True)
        with open(resolved, "w", encoding="utf-8") as f:
            f.write(content)
        return tool_result(path=path, success=True, bytes_written=len(content.encode("utf-8")))
    except Exception as e:
        return tool_error(str(e))


def search_files_tool(args: dict, **kwargs) -> str:
    pattern = args.get("pattern", "")
    path = args.get("path", "")
    target = args.get("target", "files")
    
    if not pattern:
        return tool_error("pattern is required")
    
    search_path = _resolve_path(path) if path else os.getcwd()
    results = []
    
    try:
        if target == "content":
            for root, dirs, files in os.walk(search_path):
                for fname in files[:50]:
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                            for i, line in enumerate(f):
                                if pattern.lower() in line.lower():
                                    rel = os.path.relpath(fpath, search_path)
                                    results.append(f"{rel}:{i+1}: {line.rstrip()[:200]}")
                    except Exception:
                        pass
        else:
            for root, dirs, files in os.walk(search_path):
                for fname in files[:100]:
                    if pattern.lower() in fname.lower():
                        results.append(os.path.relpath(os.path.join(root, fname), search_path))
        
        return tool_result(results=results[:200], count=len(results))
    except Exception as e:
        return tool_error(str(e))


def patch_tool(args: dict, **kwargs) -> str:
    path = args.get("path", "")
    old_string = args.get("old_string", "")
    new_string = args.get("new_string", "")
    
    if not path or not old_string:
        return tool_error("path and old_string are required")
    
    resolved = _resolve_path(path)
    if not os.path.exists(resolved):
        return tool_error(f"File not found: {path}")
    
    try:
        content = Path(resolved).read_text(encoding="utf-8")
        if old_string not in content:
            return tool_error(f"old_string not found in {path}")
        
        count = content.count(old_string)
        new_content = content.replace(old_string, new_string, 1 if not args.get("replace_all") else -1)
        Path(resolved).write_text(new_content, encoding="utf-8")
        
        return tool_result(path=path, success=True, replacements=count)
    except Exception as e:
        return tool_error(str(e))


registry.register(
    name="read_file",
    toolset="file",
    schema={
        "description": "Read the contents of a file with optional offset/limit",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file"},
                "offset": {"type": "integer", "description": "Line number to start from"},
                "limit": {"type": "integer", "description": "Maximum number of lines to read"},
            },
            "required": ["path"],
        },
    },
    handler=read_file_tool,
    emoji="≡",
)

registry.register(
    name="write_file",
    toolset="file",
    schema={
        "description": "Write content to a file, creating directories as needed",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        },
    },
    handler=write_file_tool,
    emoji="✎",
)

registry.register(
    name="search_files",
    toolset="file",
    schema={
        "description": "Search for files or content within files",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Search pattern"},
                "path": {"type": "string", "description": "Directory to search"},
                "target": {"type": "string", "enum": ["files", "content"], "description": "Search file names or file contents"},
            },
            "required": ["pattern"],
        },
    },
    handler=search_files_tool,
    emoji="⌕",
)

registry.register(
    name="patch",
    toolset="file",
    schema={
        "description": "Replace text in a file using exact string matching",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file"},
                "old_string": {"type": "string", "description": "Text to replace"},
                "new_string": {"type": "string", "description": "Replacement text"},
                "replace_all": {"type": "boolean", "description": "Replace all occurrences"},
            },
            "required": ["path", "old_string", "new_string"],
        },
    },
    handler=patch_tool,
    emoji="◉",
)
