"""Sandboxed code execution tool."""

import ast
import json
import sys
import traceback
from io import StringIO
from kase.tools.registry import registry, tool_error, tool_result


_ALLOWED_IMPORTS = {
    "json", "math", "random", "datetime", "collections", "itertools",
    "functools", "re", "string", "statistics", "typing", "enum",
    "dataclasses", "uuid", "os.path", "pathlib",
}


def execute_code_tool(args: dict, **kwargs) -> str:
    code = args.get("code", "")
    language = args.get("language", "python")
    
    if not code:
        return tool_error("code is required")
    
    if language != "python":
        return tool_error(f"Language '{language}' not supported yet")
    
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] not in _ALLOWED_IMPORTS and alias.name not in _ALLOWED_IMPORTS:
                    return tool_error(f"Import '{alias.name}' is not allowed")
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] not in _ALLOWED_IMPORTS and node.module not in _ALLOWED_IMPORTS:
                return tool_error(f"Import from '{node.module}' is not allowed")
    
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = StringIO()
    sys.stderr = StringIO()
    
    result = {"success": True, "stdout": "", "stderr": "", "error": None}
    
    safe_builtins = {
        "abs": abs, "all": all, "any": any, "bin": bin, "bool": bool,
        "chr": chr, "dict": dict, "dir": dir, "divmod": divmod,
        "enumerate": enumerate, "filter": filter, "float": float,
        "format": format, "frozenset": frozenset, "getattr": getattr,
        "hasattr": hasattr, "hash": hash, "hex": hex, "id": id,
        "int": int, "isinstance": isinstance, "issubclass": issubclass,
        "iter": iter, "len": len, "list": list, "map": map,
        "max": max, "min": min, "next": next, "object": object,
        "oct": oct, "ord": ord, "pow": pow, "print": print,
        "range": range, "repr": repr, "reversed": reversed,
        "round": round, "set": set, "slice": slice, "sorted": sorted,
        "str": str, "sum": sum, "tuple": tuple, "type": type,
        "zip": zip, "True": True, "False": False, "None": None,
    }
    try:
        exec_globals = {"__builtins__": safe_builtins}
        exec(code, exec_globals)
        result["stdout"] = sys.stdout.getvalue()[:50000]
        result["stderr"] = sys.stderr.getvalue()[:10000]
    except Exception as e:
        result["success"] = False
        result["error"] = f"{type(e).__name__}: {e}"
        result["traceback"] = traceback.format_exc()[:5000]
        result["stdout"] = sys.stdout.getvalue()[:50000]
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
    
    return tool_result(**result)


registry.register(
    name="execute_code",
    toolset="code_execution",
    schema={
        "description": "Execute Python code in a sandboxed environment",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python code to execute"},
                "language": {"type": "string", "enum": ["python"], "description": "Language"},
            },
            "required": ["code"],
        },
    },
    handler=execute_code_tool,
    emoji="▶",
)
