"""Tool execution helpers for sequential and concurrent dispatch."""

import concurrent.futures
import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ToolExecutor:
    def __init__(self, max_workers: int = 4):
        self._max_workers = max_workers

    def execute_sequential(self, tools: List[Dict], dispatch_fn: Callable) -> List[Dict]:
        results = []
        for tool in tools:
            try:
                result = dispatch_fn(tool)
                results.append(result)
            except Exception as e:
                logger.error("Tool execution error: %s", e)
                results.append({"error": str(e)})
        return results

    def execute_concurrent(self, tools: List[Dict], dispatch_fn: Callable) -> List[Dict]:
        results = [None] * len(tools)
        with concurrent.futures.ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            future_map = {executor.submit(dispatch_fn, tool): i for i, tool in enumerate(tools)}
            for future in concurrent.futures.as_completed(future_map):
                idx = future_map[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    logger.error("Concurrent tool execution error: %s", e)
                    results[idx] = {"error": str(e)}
        return results
