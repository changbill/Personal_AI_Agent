"""The four schedule tools the Schedule Agent is allowed to call.

These are deliberately thin wrappers over the calendar MCP server rather than the
server tools themselves. The wrapper owns the tool name, the Korean description and the
do-not-call conditions, because on a 2B model the description text is the routing logic.
The MCP server tool descriptions are short English one-liners with no negative
conditions, which this project cannot edit.

Every tool validates its arguments through app.models.schedule before touching the
calendar, so a malformed model proposal fails as a tool error instead of a bad write.
"""

from typing import Any

from strands import tool

from app.models.schedule import (
    ScheduleDeletion,
    ScheduleDraft,
    ScheduleEdit,
    SchedulePeriod,
)
from app.services.calendar_gateway import CalendarGateway

CALENDAR_TOOL_NAMES = (
    "get_schedule",
    "create_schedule",
    "update_schedule",
    "delete_schedule",
)


def build_calendar_tools(
    gateway: CalendarGateway, calendar_id: str, timezone: str
) -> list[Any]:
    """Bind the four schedule tools to one calendar gateway.

    Returns an empty list when no calendar is reachable, so the agent is never offered a
    tool that cannot work.
    """
    if not gateway.is_available:
        return []

    @tool(
        name="get_schedule",
        description=(
            "지정한 기간의 사용자 일정을 조회한다. "
            "Use when: 특정 날짜나 기간의 일정을 물어볼 때. 새 일정을 만들기 전에 겹치는 일정을 확인할 때. "
            "Do not use when: 일정을 만들거나 바꾸거나 지울 때. 일정과 무관한 질문일 때."
        ),
    )
    def get_schedule(start_date: str, end_date: str) -> str:
        """Read events in an inclusive day range.

        Args:
            start_date: 조회 시작일. YYYY-MM-DD 형식.
            end_date: 조회 종료일. YYYY-MM-DD 형식. 하루만 조회하면 start_date와 같게 준다.
        """
        period = SchedulePeriod.parse(start_date, end_date)
        return gateway.call_tool(
            "list-events", period.to_arguments(calendar_id, timezone)
        )

    @tool(
        name="create_schedule",
        description=(
            "새 일정을 캘린더에 추가한다. "
            "Use when: 사용자가 약속이나 회의를 새로 잡아 달라고 할 때. "
            "Do not use when: 기존 일정을 조회하거나 바꿀 때. 제목이나 시작·종료 시각을 아직 모를 때."
        ),
    )
    def create_schedule(
        summary: str,
        start_datetime: str,
        end_datetime: str,
        description: str | None = None,
        location: str | None = None,
    ) -> str:
        """Create one event.

        Args:
            summary: 일정 제목.
            start_datetime: 시작 시각. YYYY-MM-DDTHH:MM:SS 형식.
            end_datetime: 종료 시각. YYYY-MM-DDTHH:MM:SS 형식.
            description: 일정 설명. 없으면 생략한다.
            location: 장소. 없으면 생략한다.
        """
        draft = ScheduleDraft.parse(
            summary=summary,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            description=description,
            location=location,
        )
        return gateway.call_tool(
            "create-event", draft.to_arguments(calendar_id, timezone)
        )

    @tool(
        name="update_schedule",
        description=(
            "이미 있는 일정의 내용을 바꾼다. event_id가 반드시 필요하다. "
            "Use when: 사용자가 기존 일정의 시각·제목·장소를 바꿔 달라고 하고 event_id를 알고 있을 때. "
            "Do not use when: event_id를 모를 때. 새 일정을 만들 때. 일정을 지울 때. "
            "event_id를 모르면 먼저 get_schedule로 조회한다."
        ),
    )
    def update_schedule(
        event_id: str,
        summary: str | None = None,
        start_datetime: str | None = None,
        end_datetime: str | None = None,
        location: str | None = None,
    ) -> str:
        """Change one existing event.

        Args:
            event_id: 바꿀 일정의 식별자. get_schedule 결과에서 얻는다.
            summary: 새 제목. 바꾸지 않으면 생략한다.
            start_datetime: 새 시작 시각. end_datetime과 함께 주어야 한다.
            end_datetime: 새 종료 시각. start_datetime과 함께 주어야 한다.
            location: 새 장소. 바꾸지 않으면 생략한다.
        """
        edit = ScheduleEdit.parse(
            event_id=event_id,
            summary=summary,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            location=location,
        )
        return gateway.call_tool(
            "update-event", edit.to_arguments(calendar_id, timezone)
        )

    @tool(
        name="delete_schedule",
        description=(
            "일정을 캘린더에서 지운다. event_id가 반드시 필요하다. "
            "Use when: 사용자가 특정 일정을 취소하거나 삭제해 달라고 하고 event_id를 알고 있을 때. "
            "Do not use when: event_id를 모를 때. 일정 내용만 바꾸면 되는 때. "
            "event_id를 모르면 먼저 get_schedule로 조회한다."
        ),
    )
    def delete_schedule(event_id: str) -> str:
        """Remove one existing event.

        Args:
            event_id: 지울 일정의 식별자. get_schedule 결과에서 얻는다.
        """
        deletion = ScheduleDeletion.parse(event_id)
        return gateway.call_tool("delete-event", deletion.to_arguments(calendar_id))

    return [get_schedule, create_schedule, update_schedule, delete_schedule]
