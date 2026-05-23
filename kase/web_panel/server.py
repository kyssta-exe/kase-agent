"""Kase Web Panel — FastAPI server for chat, settings, and analytics."""

import json
import logging
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_agent_instance = None
_analytics = None
_config = None


def init_web_panel(agent, analytics=None, config=None):
    global _agent_instance, _analytics, _config
    _agent_instance = agent
    _analytics = analytics
    _config = config or {}


def create_app():
    from fastapi import FastAPI, HTTPException, Query, Request
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    from pydantic import BaseModel

    app = FastAPI(title="Kase Web Panel", version="1.0.0")

    templates_dir = Path(__file__).resolve().parent / "templates"
    static_dir = Path(__file__).resolve().parent / "static"
    templates = Jinja2Templates(directory=str(templates_dir))

    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    class ChatMessage(BaseModel):
        message: str
        session_id: str = ""

    class SettingsUpdate(BaseModel):
        key: str
        value: Any

    conversations: Dict[str, List[Dict]] = {}

    def _get_agent():
        if _agent_instance:
            return _agent_instance
        try:
            from kase.agent.core import AIAgent
            return AIAgent(quiet_mode=True)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Agent not available: {e}")

    def _record_call(model="", provider="", task_type="agentic",
                     prompt_tokens=0, completion_tokens=0,
                     duration_ms=0.0, success=True, error="",
                     tool_calls=0, fallback_used=False):
        if _analytics:
            agent = _get_agent()
            _analytics.record_call(
                session_id=agent.session_id,
                model=model or agent.model,
                provider=provider or agent.provider,
                task_type=task_type,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                duration_ms=duration_ms,
                success=success,
                error=error,
                tool_calls=tool_calls,
                fallback_used=fallback_used,
            )

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})

    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard(request: Request):
        return templates.TemplateResponse("dashboard.html", {"request": request})

    @app.get("/settings", response_class=HTMLResponse)
    async def settings_page(request: Request):
        return templates.TemplateResponse("settings.html", {"request": request})

    @app.post("/api/chat")
    async def chat(msg: ChatMessage):
        agent = _get_agent()
        start = time.monotonic()
        try:
            result = agent.run_conversation(msg.message)
            duration = (time.monotonic() - start) * 1000
            usage = result.get("usage", {})
            route = agent._model_router.get_route() if hasattr(agent, "_model_router") else None
            _record_call(
                model=agent.model,
                provider=agent.provider,
                task_type=agent._model_router.active_task if hasattr(agent, "_model_router") else "agentic",
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                duration_ms=duration,
                success=True,
                tool_calls=result.get("tool_calls", 0),
            )
            return {
                "response": result.get("final_response", ""),
                "session_id": agent.session_id,
                "usage": usage,
                "model": agent.model,
                "provider": agent.provider,
            }
        except Exception as e:
            duration = (time.monotonic() - start) * 1000
            _record_call(success=False, error=str(e), duration_ms=duration)
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/chat/stream")
    async def chat_stream(msg: ChatMessage):
        from fastapi.responses import StreamingResponse
        import asyncio

        agent = _get_agent()
        messages = agent._messages.copy()
        messages.append({"role": "user", "content": msg.message})

        async def generate():
            full_response = ""
            try:
                route = agent._model_router.get_route() if hasattr(agent, "_model_router") else None
                client = agent._model_router.get_client() if hasattr(agent, "_model_router") else None
                if not client:
                    client = agent._client

                stream = client.chat.completions.create(
                    model=agent.model,
                    messages=messages,
                    stream=True,
                )
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        yield f"data: {json.dumps({'content': content})}\n\n"
                    await asyncio.sleep(0)

                yield f"data: {json.dumps({'done': True, 'full_response': full_response})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    @app.get("/api/conversation/{session_id}")
    async def get_conversation(session_id: str):
        agent = _get_agent()
        return {"messages": agent._messages[-100:]}

    @app.post("/api/reset")
    async def reset_conversation():
        agent = _get_agent()
        agent.reset_session()
        return {"status": "reset"}

    @app.get("/api/status")
    async def get_status():
        agent = _get_agent()
        status = agent.get_status()
        return status

    @app.get("/api/models")
    async def get_models():
        from kase.providers import registry as provider_registry
        providers = provider_registry.list_providers()
        models = {}
        for p in providers:
            profile = provider_registry.get_provider(p)
            if profile:
                models[p] = {
                    "models": profile.models,
                    "base_url": profile.base_url,
                    "display_name": profile.display_name,
                }
        return {"providers": providers, "models": models}

    @app.get("/api/analytics/overview")
    async def analytics_overview(hours: int = Query(24, ge=1, le=8760)):
        if not _analytics:
            return {"error": "Analytics not enabled"}
        overview = _analytics.get_overview(hours=hours)
        all_time = _analytics.get_all_time_stats()
        overview.update(all_time)
        return overview

    @app.get("/api/analytics/models")
    async def analytics_models(hours: int = Query(168, ge=1, le=8760)):
        if not _analytics:
            return {"error": "Analytics not enabled"}
        return {"models": _analytics.get_model_breakdown(hours=hours)}

    @app.get("/api/analytics/tasks")
    async def analytics_tasks(hours: int = Query(168, ge=1, le=8760)):
        if not _analytics:
            return {"error": "Analytics not enabled"}
        return {"tasks": _analytics.get_task_breakdown(hours=hours)}

    @app.get("/api/analytics/timeline")
    async def analytics_timeline(hours: int = Query(168, ge=1, le=8760),
                                  interval: str = Query("hour", pattern="^(hour|day)$")):
        if not _analytics:
            return {"error": "Analytics not enabled"}
        return {"timeline": _analytics.get_token_timeline(hours=hours, interval=interval)}

    @app.get("/api/analytics/recent")
    async def analytics_recent(limit: int = Query(50, ge=1, le=500)):
        if not _analytics:
            return {"error": "Analytics not enabled"}
        return {"calls": _analytics.get_recent_calls(limit=limit)}

    @app.get("/api/config")
    async def get_config():
        from kase.cli.config import load_config
        cfg = load_config()
        return cfg

    @app.post("/api/config")
    async def update_config(update: SettingsUpdate):
        from kase.cli.config import load_config, save_config
        cfg = load_config()
        keys = update.key.split(".")
        target = cfg
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        target[keys[-1]] = update.value
        save_config(cfg)
        return {"status": "updated", "key": update.key, "value": update.value}

    @app.get("/api/config/multi-model")
    async def get_multi_model_config():
        agent = _get_agent()
        if hasattr(agent, "_model_router"):
            return agent._model_router.config_to_dict()
        return {}

    @app.post("/api/config/multi-model")
    async def update_multi_model_config(data: Dict):
        agent = _get_agent()
        if hasattr(agent, "_model_router"):
            router = agent._model_router
            for task, config in data.items():
                from kase.agent.model_router import ModelRoute
                route = ModelRoute(
                    task_type=task,
                    model=config.get("model", "gpt-4o"),
                    provider=config.get("provider", "openai"),
                    base_url=config.get("base_url", ""),
                    context_length=config.get("context_length", 128000),
                    temperature=config.get("temperature", 0.7),
                )
                router.set_route(task, route)
        return {"status": "updated"}

    @app.get("/api/memories")
    async def get_memories(query: str = "", limit: int = Query(50, ge=1, le=500)):
        agent = _get_agent()
        if hasattr(agent, "_long_term_memory") and agent._long_term_memory:
            if query:
                return {"memories": agent._long_term_memory.recall(query, limit=limit)}
            return {"memories": agent._long_term_memory.get_all(limit=limit)}
        return {"memories": []}

    @app.post("/api/teach")
    async def teach(data: Dict):
        agent = _get_agent()
        content = data.get("content", "")
        mem_type = data.get("type", "fact")
        if not content:
            raise HTTPException(status_code=400, detail="content is required")
        mid = agent.teach(content, mem_type)
        return {"status": "learned", "id": mid}

    @app.delete("/api/memories/{memory_id}")
    async def delete_memory(memory_id: str):
        agent = _get_agent()
        if hasattr(agent, "_long_term_memory") and agent._long_term_memory:
            agent._long_term_memory.delete(memory_id)
        return {"status": "deleted"}

    return app


def run_web_panel(host: str = "127.0.0.1", port: int = 8080,
                  agent=None, analytics=None, config=None,
                  bg: bool = False):
    try:
        import uvicorn
    except ImportError:
        import subprocess
        import sys
        print("Installing uvicorn...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "uvicorn"])
        import uvicorn

    init_web_panel(agent, analytics, config)
    app = create_app()

    if bg:
        import threading
        t = threading.Thread(
            target=uvicorn.run,
            args=(app,),
            kwargs={"host": host, "port": port, "log_level": "info"},
            daemon=True,
        )
        t.start()
        print(f"  Kase Web Panel started: http://{host}:{port}")
        print(f"  Dashboard: http://{host}:{port}/dashboard")
        return t
    else:
        print(f"  Kase Web Panel: http://{host}:{port}")
        print(f"  Dashboard: http://{host}:{port}/dashboard")
        uvicorn.run(app, host=host, port=port, log_level="info")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Kase Web Panel")
    parser.add_argument("port", nargs="?", type=int, default=8080, help="Port (default: 8080)")
    parser.add_argument("--host", default="127.0.0.1", help="Host (default: 127.0.0.1)")
    parser.add_argument("--bg", action="store_true", help="Run in background")
    args = parser.parse_args()
    run_web_panel(host=args.host, port=args.port, bg=args.bg)


if __name__ == "__main__":
    main()
