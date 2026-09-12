from typing import Any

import pytest

from app.models.schedule import ScheduleInputError
from app.services.calendar_gateway import UnavailableCalendarGateway
from app.tools.calendar_tools import CALENDAR_TOOL_NAMES, build_calendar_tools

pytestmark = pytest.mark.unit


class StubGateway:
    """Available gateway that records what the tools asked the calendar to do."""

    def __init__(self, result: str = "ok") -> None:
        self.result = result
        self.calls: list[tuple[str, dict[str, Any]]] = []

    @property
    def is_available(self) -> bool:
        return True

    def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        self.calls.append((name, arguments))
        return self.result

    def close(self) -> None:
        return None


def _tools(gateway: Any) -> dict[str, Any]:
    built = build_calendar_tools(gateway, calendar_id="primary", timezone="Asia/Seoul")
    return {each.tool_name: each for each in built}


def test_no_tools_are_offered_when_no_calendar_is_reachable() -> None:
    assert (
        build_calendar_tools(
            UnavailableCalendarGateway(), calendar_id="primary", timezone="Asia/Seoul"
        )
        == []
    )


def test_exactly_the_four_documented_tools_are_registered() -> None:
    assert tuple(_tools(StubGateway())) == CALENDAR_TOOL_NAMES


def test_every_description_states_when_not_to_call_the_tool() -> None:
    for each in _tools(StubGateway()).values():
        description = each.tool_spec["description"]
        assert "Use when:" in description
        assert "Do not use when:" in description


def test_get_schedule_queries_the_requested_range() -> None:
    gateway = StubGateway("9월 12일 15:00 치과")

    result = _tools(gateway)["get_schedule"](
        start_date="2026-09-12", end_date="2026-09-12"
    )

    assert result == "9월 12일 15:00 치과"
    assert gateway.calls == [
        (
            "list-events",
            {
                "calendarId": "primary",
                "timeMin": "2026-09-12T00:00:00",
                "timeMax": "2026-09-13T00:00:00",
                "timeZone": "Asia/Seoul",
            },
        )
    ]


def test_create_schedule_sends_the_validated_draft() -> None:
    gateway = StubGateway("생성 완료")

    result = _tools(gateway)["create_schedule"](
        summary="치과",
        start_datetime="2026-09-12T15:00:00",
        end_datetime="2026-09-12T16:00:00",
    )

    assert result == "생성 완료"
    name, arguments = gateway.calls[0]
    assert name == "create-event"
    assert arguments["summary"] == "치과"
    assert arguments["timeZone"] == "Asia/Seoul"


def test_update_schedule_sends_only_the_changed_fields() -> None:
    gateway = StubGateway("수정 완료")

    _tools(gateway)["update_schedule"](event_id="evt-1", location="본사 3층")

    name, arguments = gateway.calls[0]
    assert name == "update-event"
    assert arguments["eventId"] == "evt-1"
    assert arguments["location"] == "본사 3층"
    assert "start" not in arguments


def test_delete_schedule_sends_the_event_id() -> None:
    gateway = StubGateway("삭제 완료")

    _tools(gateway)["delete_schedule"](event_id="evt-1")

    assert gateway.calls == [
        ("delete-event", {"calendarId": "primary", "eventId": "evt-1"})
    ]


def test_invalid_arguments_never_reach_the_calendar() -> None:
    gateway = StubGateway()
    tools = _tools(gateway)

    with pytest.raises(ScheduleInputError):
        tools["get_schedule"](start_date="내일", end_date="모레")
    with pytest.raises(ScheduleInputError):
        tools["create_schedule"](
            summary="회의",
            start_datetime="2026-09-12T16:00:00",
            end_datetime="2026-09-12T15:00:00",
        )
    with pytest.raises(ScheduleInputError):
        tools["update_schedule"](event_id="evt-1")
    with pytest.raises(ScheduleInputError):
        tools["delete_schedule"](event_id="")

    assert gateway.calls == []
