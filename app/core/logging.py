"""Structured logging without message content."""

import json
import logging
from typing import Any


class JsonFormatter(logging.Formatter):
    """Emit the request metadata required for later evaluation."""

    _fields = (
        "user_id",
        "session_id",
        "selected_agent",
        "tools_used",
        "agent_latency_ms",
        "llm_latency_ms",
        "memory_retrieved",
        "memory_stored",
    )

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "event": record.getMessage(),
        }
        for field in self._fields:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["error"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(logging.INFO)
