"""The current-time tool, registered only on the General Agent.

Schedule and Search agents already receive today's date in their system prompt, so a tool
call there would buy nothing and cost one extra model round trip, which on this 2B CPU
model is roughly fifteen seconds. The General Agent had no date context at all, which is
the gap this fills.
"""

from typing import Any

from strands import tool

from app.services.time_service import TimeService, format_current_time

TIME_TOOL_NAMES = ("get_current_time",)


def build_time_tools(service: TimeService, timezone: str) -> list[Any]:
    """Bind the current-time tool to one time service and one configured timezone."""

    @tool(
        name="get_current_time",
        description=(
            "지금의 날짜·요일·시각을 조회한다. "
            "Use when: 사용자가 현재 날짜나 시각, 오늘이 무슨 요일인지 물어볼 때. "
            "Do not use when: 일정을 조회하거나 변경할 때. 날씨를 물어볼 때. "
            "날짜와 무관한 일반 대화일 때."
        ),
    )
    def get_current_time() -> str:
        """Read the current date, weekday and time."""
        return format_current_time(service.current_time(timezone))

    return [get_current_time]
