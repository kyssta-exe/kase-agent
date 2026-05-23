"""Web search and extraction tools."""

import json
import os
import re
import urllib.parse
from kase.tools.registry import registry, tool_error, tool_result


def _search_duckduckgo(query: str, num_results: int = 5) -> list:
    import urllib.request
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        
        results = []
        for m in re.finditer(r'<a[^>]+class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL):
            href = m.group(1)
            title = re.sub(r"<[^>]+>", "", m.group(2)).strip()
            if href and title:
                results.append({"title": title, "url": href})
                if len(results) >= num_results:
                    break
        return results
    except Exception as e:
        return [{"error": str(e)}]


def web_search_tool(args: dict, **kwargs) -> str:
    query = args.get("query", "")
    num_results = min(args.get("num_results", 5), 20)
    
    if not query:
        return tool_error("query is required")
    
    results = _search_duckduckgo(query, num_results)
    return tool_result(query=query, results=results, count=len(results))


def web_extract_tool(args: dict, **kwargs) -> str:
    url = args.get("url", "")
    if not url:
        return tool_error("url is required")
    
    import urllib.request
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8", errors="replace")[:50000]
        
        text = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL)
        text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()[:30000]
        
        return tool_result(url=url, content=text, length=len(text))
    except Exception as e:
        return tool_error(f"Failed to extract: {e}")


registry.register(
    name="web_search",
    toolset="web",
    schema={
        "description": "Search the web for information",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "num_results": {"type": "integer", "description": "Number of results (max 20)"},
            },
            "required": ["query"],
        },
    },
    handler=web_search_tool,
    emoji="◎",
)

registry.register(
    name="web_extract",
    toolset="web",
    schema={
        "description": "Extract readable text content from a URL",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to extract"},
            },
            "required": ["url"],
        },
    },
    handler=web_extract_tool,
    emoji="⇣",
)
