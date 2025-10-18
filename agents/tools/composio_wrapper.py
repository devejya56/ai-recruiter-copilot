"""Composio Wrapper for Tool/Action Orchestration

This module wraps Composio (or a similar tool orchestration framework)
to provide a unified interface for invoking third-party tools/services
within the recruiter copilot.
"""
from typing import Any, Dict, Optional, Callable
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ToolExecutionError(Exception):
    pass


class ComposioWrapper:
    """Wrapper to register and invoke tools with standardized I/O."""

    def __init__(self):
        self._registry: Dict[str, Callable[..., Any]] = {}

    def register(self, name: str, func: Callable[..., Any]) -> None:
        if name in self._registry:
            logger.warning("Overwriting existing tool: %s", name)
        self._registry[name] = func
        logger.info("Registered tool: %s", name)

    def available_tools(self) -> Dict[str, Callable[..., Any]]:
        return dict(self._registry)

    def invoke(self, name: str, /, **kwargs: Any) -> Any:
        if name not in self._registry:
            raise ToolExecutionError(f"Tool not found: {name}")
        try:
            logger.info("Invoking tool: %s with args=%s", name, kwargs)
            result = self._registry[name](**kwargs)
            logger.info("Tool %s completed", name)
            return result
        except Exception as e:
            logger.exception("Tool %s failed: %s", name, e)
            raise ToolExecutionError(str(e)) from e


def create_default_wrapper() -> ComposioWrapper:
    wrapper = ComposioWrapper()

    # Example registrations (no-op defaults)
    wrapper.register("send_email", lambda to, subject, body: {
        "status": "sent", "to": to, "subject": subject
    })
    wrapper.register("search_candidates", lambda query: {
        "results": [], "query": query
    })
    return wrapper


if __name__ == "__main__":
    w = create_default_wrapper()
    print("Tools:", list(w.available_tools().keys()))
    print("Invoke:", w.invoke("search_candidates", query="python developer"))
