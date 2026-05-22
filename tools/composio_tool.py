"""Composio.dev integration — 250+ app integrations for Kase.

Requires COMPOSIO_API_KEY in ~/.kase/.env.
Get one at https://app.composio.dev/
"""

import json
import logging
import os
from typing import Any, Optional

from tools.registry import registry

logger = logging.getLogger(__name__)

def _get_composio_api_key() -> Optional[str]:
    return os.getenv("COMPOSIO_API_KEY", "").strip() or None

def check_composio_available() -> bool:
    """Check if Composio SDK is installed and API key is set."""
    try:
        import composio  # noqa: F401
        return _get_composio_api_key() is not None
    except ImportError:
        return False

def _composio_toolset():
    """Lazy import to avoid pulling composio at module load."""
    from composio import ComposioToolSet
    api_key = _get_composio_api_key()
    return ComposioToolSet(api_key=api_key)

def composio_execute(action: str, params: Optional[str] = None, task_id: str = None) -> str:
    """Execute a Composio action on a connected app.

    Args:
        action: Action identifier in format "APPNAME_ACTIONNAME" (e.g. "GITHUB_STAR_REPO")
        params: JSON string of action parameters
    """
    if not check_composio_available():
        return json.dumps({"error": "Composio not configured. Set COMPOSIO_API_KEY in ~/.kase/.env and install composio-core: pip install composio-core"})
    try:
        toolset = _composio_toolset()
        params_dict = json.loads(params) if params else {}
        result = toolset.execute_action(action=action, params=params_dict)
        return json.dumps({"success": True, "result": str(result)})
    except ImportError:
        return json.dumps({"error": "composio-core not installed. Run: pip install composio-core"})
    except Exception as e:
        return json.dumps({"error": str(e)})

def composio_list_actions(app: str = "", task_id: str = None) -> str:
    """List available Composio actions, optionally filtered by app name.

    Args:
        app: Optional app name to filter (e.g. "github", "gmail", "slack")
    """
    if not check_composio_available():
        return json.dumps({"error": "Composio not configured."})
    try:
        toolset = _composio_toolset()
        actions = toolset.get_actions(app=app) if app else toolset.get_actions()
        action_list = [{"name": a.name, "display_name": a.display_name} for a in actions]
        return json.dumps({"actions": action_list})
    except ImportError:
        return json.dumps({"error": "composio-core not installed."})
    except Exception as e:
        return json.dumps({"error": str(e)})

def composio_list_connections(task_id: str = None) -> str:
    """List all connected Composio app integrations and their status."""
    if not check_composio_available():
        return json.dumps({"error": "Composio not configured."})
    try:
        toolset = _composio_toolset()
        connections = toolset.get_connected_accounts()
        result = []
        for conn in connections:
            result.append({
                "id": conn.id,
                "app": conn.appName,
                "status": conn.status,
                "entity_id": conn.entityId,
            })
        return json.dumps({"connections": result})
    except ImportError:
        return json.dumps({"error": "composio-core not installed."})
    except Exception as e:
        return json.dumps({"error": str(e)})

def composio_connect(app: str, task_id: str = None) -> str:
    """Initiate OAuth connection for a Composio app.

    Returns a connection URL the user must visit to authorize.
    """
    if not check_composio_available():
        return json.dumps({"error": "Composio not configured."})
    try:
        toolset = _composio_toolset()
        connection_request = toolset.initiate_connection(app_name=app)
        return json.dumps({
            "success": True,
            "app": app,
            "connection_url": str(connection_request.connectionUrl),
            "expected_status": "requires_authorization",
        })
    except ImportError:
        return json.dumps({"error": "composio-core not installed."})
    except Exception as e:
        return json.dumps({"error": str(e)})

registry.register(
    name="composio_execute",
    toolset="composio",
    schema={
        "name": "composio_execute",
        "description": "Execute an action on a connected app via Composio (250+ apps: GitHub, Gmail, Slack, Notion, etc.). Requires COMPOSIO_API_KEY.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action identifier like APPNAME_ACTIONNAME (e.g. GITHUB_STAR_REPO, GMAIL_SEND_EMAIL, SLACK_SEND_MESSAGE)",
                },
                "params": {
                    "type": "string",
                    "description": "JSON string of action parameters",
                },
            },
            "required": ["action"],
        },
    },
    handler=lambda args, **kw: composio_execute(
        action=args.get("action", ""),
        params=args.get("params"),
        task_id=kw.get("task_id"),
    ),
    check_fn=check_composio_available,
    requires_env=["COMPOSIO_API_KEY"],
)

registry.register(
    name="composio_list_actions",
    toolset="composio",
    schema={
        "name": "composio_list_actions",
        "description": "List available Composio actions, optionally filtered by app name",
        "parameters": {
            "type": "object",
            "properties": {
                "app": {
                    "type": "string",
                    "description": "Optional app name to filter (e.g. github, gmail, slack, notion)",
                },
            },
        },
    },
    handler=lambda args, **kw: composio_list_actions(
        app=args.get("app", ""),
        task_id=kw.get("task_id"),
    ),
    check_fn=check_composio_available,
    requires_env=["COMPOSIO_API_KEY"],
)

registry.register(
    name="composio_list_connections",
    toolset="composio",
    schema={
        "name": "composio_list_connections",
        "description": "List all connected Composio app integrations",
        "parameters": {"type": "object", "properties": {}},
    },
    handler=lambda args, **kw: composio_list_connections(task_id=kw.get("task_id")),
    check_fn=check_composio_available,
    requires_env=["COMPOSIO_API_KEY"],
)

registry.register(
    name="composio_connect",
    toolset="composio",
    schema={
        "name": "composio_connect",
        "description": "Connect a new app via Composio OAuth. Returns a URL the user must visit to authorize.",
        "parameters": {
            "type": "object",
            "properties": {
                "app": {
                    "type": "string",
                    "description": "App name to connect (e.g. github, gmail, slack, notion, jira, asana, linear)",
                },
            },
            "required": ["app"],
        },
    },
    handler=lambda args, **kw: composio_connect(
        app=args.get("app", ""),
        task_id=kw.get("task_id"),
    ),
    check_fn=check_composio_available,
    requires_env=["COMPOSIO_API_KEY"],
)
