from typing import Any

import pytest

from app.services.calendar_gateway import (
    ALLOWED_MCP_TOOLS,
    CalendarToolError,
    CalendarUnavailableError,
    McpCalendarGateway,
    UnavailableCalendarGateway,
    extract_result_text,
    start_calendar_gateway,
)

pytestmark = pytest.mark.unit


class StubMcpClient:
    """Records calls and returns a canned MCP tool result."""

    def __init__(self, result: dict[str, Any]) -> None:
        self.result = result
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.stopped = False

    def call_tool_sync(
        self, tool_use_id: str, name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        self.calls.append((name, arguments))
        return self.result

    def stop(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.stopped = True


def test_text_blocks_are_joined_and_json_blocks_are_rendered() -> None:
    result = {
        "content": [
            {"text": "9월 12일 15:00 치과"},
            {"json": {"id": "evt-1"}},
            {"text": "   "},
            "not-a-block",
        ]
    }

    assert extract_result_text(result) == "9월 12일 15:00 치과\n{'id': 'evt-1'}"


def test_empty_content_renders_as_an_empty_string() -> None:
    assert extract_result_text({"content": []}) == ""
    assert extract_result_text({}) == ""


def test_successful_call_forwards_arguments_and_returns_text() -> None:
    client = StubMcpClient({"status": "success", "content": [{"text": "일정 1건"}]})
    gateway = McpCalendarGateway(client)  # type: ignore[arg-type]

    result = gateway.call_tool("list-events", {"calendarId": "primary"})

    assert result == "일정 1건"
    assert client.calls == [("list-events", {"calendarId": "primary"})]
    assert gateway.is_available is True


def test_error_status_becomes_a_calendar_tool_error() -> None:
    client = StubMcpClient({"status": "error", "content": [{"text": "권한 없음"}]})
    gateway = McpCalendarGateway(client)  # type: ignore[arg-type]

    with pytest.raises(CalendarToolError, match="권한 없음"):
        gateway.call_tool("list-events", {"calendarId": "primary"})


def test_application_level_error_flag_becomes_a_calendar_tool_error() -> None:
    client = StubMcpClient(
        {"status": "success", "isError": True, "content": [{"text": "없는 일정"}]}
    )
    gateway = McpCalendarGateway(client)  # type: ignore[arg-type]

    with pytest.raises(CalendarToolError, match="없는 일정"):
        gateway.call_tool("delete-event", {"eventId": "evt-9"})


def test_tools_outside_the_allow_list_are_refused_before_any_call() -> None:
    client = StubMcpClient({"status": "success", "content": [{"text": "ok"}]})
    gateway = McpCalendarGateway(client)  # type: ignore[arg-type]

    with pytest.raises(CalendarToolError):
        gateway.call_tool("manage-accounts", {})

    assert client.calls == []


def test_allow_list_holds_exactly_the_four_tools_the_application_uses() -> None:
    assert ALLOWED_MCP_TOOLS == (
        "list-events",
        "create-event",
        "update-event",
        "delete-event",
    )


def test_unavailable_gateway_reports_itself_and_refuses_calls() -> None:
    gateway = UnavailableCalendarGateway()

    assert gateway.is_available is False
    with pytest.raises(CalendarUnavailableError):
        gateway.call_tool("list-events", {})
    assert gateway.close() is None


def test_closing_an_mcp_gateway_stops_the_session() -> None:
    client = StubMcpClient({"status": "success", "content": []})
    McpCalendarGateway(client).close()  # type: ignore[arg-type]

    assert client.stopped is True


@pytest.mark.parametrize("url", [None, "", "   "])
def test_missing_url_yields_the_unavailable_gateway(url: str | None) -> None:
    assert start_calendar_gateway(url).is_available is False
