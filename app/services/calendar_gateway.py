"""The only boundary in the application that knows the calendar lives behind MCP.

Tools depend on the CalendarGateway protocol, so their behaviour is verifiable without
starting an MCP server. The MCP session is process-scoped: one server process per API
process, not one per request, because a per-request spawn would add startup latency to
every chat turn and make two turns race for the same OAuth token file.
"""

import logging
import uuid
from typing import Any, Protocol

from strands.tools.mcp import MCPClient

logger = logging.getLogger(__name__)

ALLOWED_MCP_TOOLS = (
    "list-events",
    "create-event",
    "update-event",
    "delete-event",
)
"""The four calendar server tools this application calls.

The server exposes twelve. The rest stay unreachable: every extra tool is another way for
a 2B model to pick wrong, and the application never needs them.
"""


class CalendarUnavailableError(RuntimeError):
    """Raised when no calendar backend is reachable."""


class CalendarToolError(RuntimeError):
    """Raised when the calendar backend reports a failed tool call."""


class CalendarGateway(Protocol):
    """Minimal contract the calendar tools depend on."""

    @property
    def is_available(self) -> bool: ...

    def call_tool(self, name: str, arguments: dict[str, Any]) -> str: ...

    def close(self) -> None: ...


class UnavailableCalendarGateway:
    """Stands in when no calendar server is configured or reachable.

    A missing calendar must degrade the schedule answer, not fail the whole request.
    """

    @property
    def is_available(self) -> bool:
        return False

    def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        raise CalendarUnavailableError(
            "캘린더 서버에 연결되어 있지 않아 일정을 조회하거나 변경할 수 없습니다"
        )

    def close(self) -> None:
        return None


class McpCalendarGateway:
    """Calls the Google Calendar MCP server over an already started session."""

    def __init__(self, client: MCPClient) -> None:
        self._client = client

    @property
    def is_available(self) -> bool:
        return True

    def close(self) -> None:
        """Shut down the MCP session and its background thread."""
        self._client.stop(None, None, None)

    def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        if name not in ALLOWED_MCP_TOOLS:
            raise CalendarToolError(f"허용되지 않은 캘린더 도구입니다: {name}")

        result = self._client.call_tool_sync(
            tool_use_id=str(uuid.uuid4()), name=name, arguments=arguments
        )
        text = extract_result_text(result)
        if result.get("status") != "success" or result.get("isError"):
            raise CalendarToolError(text or f"{name} 호출이 실패했습니다")
        return text


def extract_result_text(result: dict[str, Any]) -> str:
    """Flatten an MCP tool result into the text a language model can read.

    Kept as a free function so the mapping is testable against recorded server payloads
    without an MCP session.
    """
    parts: list[str] = []
    for block in result.get("content") or []:
        if not isinstance(block, dict):
            continue
        if isinstance(block.get("text"), str):
            parts.append(block["text"])
        elif "json" in block:
            parts.append(str(block["json"]))
    return "\n".join(part for part in parts if part.strip()).strip()


def build_calendar_client(url: str) -> MCPClient:
    """Create an MCP client for the calendar server, filtered to the four tools we call.

    continue_on_error keeps a dead calendar server from raising while the agent loads its
    tools; the caller checks whether any tool actually loaded.
    """
    return MCPClient(
        url=url,
        tool_filters={"allowed": list(ALLOWED_MCP_TOOLS)},
        continue_on_error=True,
        application_name="personal-ai-agent",
    )


def start_calendar_gateway(url: str | None) -> CalendarGateway:
    """Start a calendar session, falling back to the unavailable gateway on any failure."""
    if url is None or not url.strip():
        logger.info("calendar_mcp_not_configured")
        return UnavailableCalendarGateway()

    client = build_calendar_client(url)
    try:
        client.start()
    except Exception:
        logger.exception("calendar_mcp_start_failed")
        return UnavailableCalendarGateway()

    if client.connection_failed:
        logger.warning("calendar_mcp_connection_failed")
        return UnavailableCalendarGateway()

    logger.info("calendar_mcp_connected")
    return McpCalendarGateway(client)
