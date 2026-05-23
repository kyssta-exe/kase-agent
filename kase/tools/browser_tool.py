"""Browser automation tools via Playwright."""

import json
import logging
import os
import threading
from kase.tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)

_browser_context = threading.local()
_playwright_instance = [None]
_playwright_lock = threading.Lock()


def _get_browser():
    """Get or launch a persistent browser instance."""
    if getattr(_browser_context, "page", None) and getattr(_browser_context, "browser", None):
        try:
            _browser_context.page.title()
            return _browser_context.browser, _browser_context.page
        except Exception:
            pass

    try:
        from playwright.sync_api import sync_playwright
        with _playwright_lock:
            if _playwright_instance[0] is None:
                _playwright_instance[0] = sync_playwright().start()
        p = _playwright_instance[0]
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        _browser_context.browser = browser
        _browser_context.page = page
        _browser_context.playwright = p
        return browser, page
    except ImportError:
        return None, None
    except Exception as e:
        logger.warning("Browser launch failed: %s", e)
        return None, None


def browser_navigate_tool(args: dict, **kwargs) -> str:
    url = args.get("url", "")
    if not url:
        return tool_error("url is required")
    
    browser, page = _get_browser()
    if not browser:
        return tool_result(status="unavailable", message="Browser not available. Install playwright: pip install playwright && playwright install chromium")
    
    try:
        page.goto(url, timeout=30000)
        title = page.title()
        return tool_result(url=url, title=title, status="loaded")
    except Exception as e:
        return tool_result(status="error", message=str(e))


def browser_snapshot_tool(args: dict, **kwargs) -> str:
    browser, page = _get_browser()
    if not page:
        return tool_result(status="unavailable", message="Browser not available")
    try:
        url = page.url
        title = page.title()
        return tool_result(url=url, title=title, status="loaded")
    except Exception as e:
        return tool_result(status="error", message=str(e))


def browser_click_tool(args: dict, **kwargs) -> str:
    browser, page = _get_browser()
    if not page:
        return tool_result(status="unavailable", message="Browser not available")
    ref = args.get("ref")
    if ref is None:
        return tool_error("ref is required")
    try:
        if isinstance(ref, int):
            page.locator(f"> :nth-child({ref})").click()
        else:
            page.click(ref)
        return tool_result(status="clicked", ref=ref)
    except Exception as e:
        return tool_result(status="error", message=str(e))


def browser_type_tool(args: dict, **kwargs) -> str:
    browser, page = _get_browser()
    if not page:
        return tool_result(status="unavailable", message="Browser not available")
    ref = args.get("ref")
    text = args.get("text", "")
    if ref is None:
        return tool_error("ref is required")
    try:
        if isinstance(ref, int):
            page.locator(f"> :nth-child({ref})").fill(text)
        else:
            page.fill(ref, text)
        return tool_result(status="typed", ref=ref)
    except Exception as e:
        return tool_result(status="error", message=str(e))


def browser_scroll_tool(args: dict, **kwargs) -> str:
    browser, page = _get_browser()
    if not page:
        return tool_result(status="unavailable", message="Browser not available")
    direction = args.get("direction", "down")
    try:
        if direction == "down":
            page.evaluate("window.scrollBy(0, window.innerHeight)")
        else:
            page.evaluate("window.scrollBy(0, -window.innerHeight)")
        return tool_result(status="scrolled", direction=direction)
    except Exception as e:
        return tool_result(status="error", message=str(e))


for _name, _handler, _desc in [
    ("browser_navigate", browser_navigate_tool, "Navigate to a URL in the browser"),
    ("browser_snapshot", browser_snapshot_tool, "Get the current browser state"),
    ("browser_click", browser_click_tool, "Click on an element in the browser"),
    ("browser_type", browser_type_tool, "Type text into an input field"),
    ("browser_scroll", browser_scroll_tool, "Scroll the browser page"),
]:
    registry.register(
        name=_name,
        toolset="browser",
        schema={
            "description": _desc,
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "ref": {"type": ["string", "integer"]},
                    "text": {"type": "string"},
                    "direction": {"type": "string", "enum": ["up", "down"]},
                },
            },
        },
        handler=_handler,
    )
