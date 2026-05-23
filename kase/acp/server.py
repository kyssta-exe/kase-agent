"""ACP server for editor integration (VS Code, JetBrains, etc.)."""

import json
import logging
import sys
from typing import Any, Dict, Optional

from kase.agent.core import AIAgent
from kase.tools.registry import registry

logger = logging.getLogger(__name__)


class ACPServer:
    """Agent Communication Protocol over stdin/stdout JSON-RPC."""

    def __init__(self):
        self.agent: Optional[AIAgent] = None
        self._request_id = 0

    def handle_request(self, request: Dict) -> Dict:
        method = request.get("method", "")
        params = request.get("params", {})
        req_id = request.get("id", self._request_id)
        self._request_id = req_id
        
        handlers = {
            "initialize": self._handle_initialize,
            "shutdown": self._handle_shutdown,
            "tools/list": self._handle_tools_list,
            "tools/call": self._handle_tools_call,
            "resources/list": self._handle_resources_list,
            "prompts/list": self._handle_prompts_list,
            "sampling/createMessage": self._handle_sampling,
        }
        
        handler = handlers.get(method)
        if not handler:
            return self._error(req_id, -32601, f"Method not found: {method}")
        
        try:
            result = handler(params)
            return {"jsonrpc": "2.0", "id": req_id, "result": result}
        except Exception as e:
            logger.error("ACP method %s error: %s", method, e)
            return self._error(req_id, -32603, str(e))

    def _error(self, req_id: int, code: int, message: str) -> Dict:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}

    def _handle_initialize(self, params: Dict) -> Dict:
        self.agent = AIAgent(platform="acp")
        return {
            "protocolVersion": "0.1.0",
            "capabilities": {
                "tools": {},
                "resources": {},
                "prompts": {},
                "sampling": {},
            },
            "serverInfo": {"name": "kase-acp", "version": "1.0.0"},
        }

    def _handle_shutdown(self, params: Dict) -> Dict:
        return {}

    def _handle_tools_list(self, params: Dict) -> Dict:
        tool_names = registry.get_all_tool_names()
        definitions = registry.get_definitions(set(tool_names))
        return {"tools": definitions}

    def _handle_tools_call(self, params: Dict) -> Dict:
        name = params.get("name", "")
        args = params.get("arguments", {})
        result = registry.dispatch(name, args)
        return {"content": [{"type": "text", "text": result}]}

    def _handle_resources_list(self, params: Dict) -> Dict:
        return {"resources": []}

    def _handle_prompts_list(self, params: Dict) -> Dict:
        return {"prompts": []}

    def _handle_sampling(self, params: Dict) -> Dict:
        if not self.agent:
            return self._error(self._request_id, -32000, "Not initialized")
        messages = params.get("messages", [])
        system = next((m["content"] for m in messages if m["role"] == "system"), None)
        user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")
        
        response = self.agent.chat(str(user_msg))
        return {
            "model": self.agent.model,
            "role": "assistant",
            "content": [{"type": "text", "text": response}],
        }

    def run_stdio(self) -> None:
        logger.info("ACP server starting on stdio")
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
                response = self.handle_request(request)
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
            except json.JSONDecodeError:
                logger.warning("Invalid ACP request: %s", line[:200])
            except Exception as e:
                logger.error("ACP error: %s", e)


def run_acp_server():
    server = ACPServer()
    server.run_stdio()
