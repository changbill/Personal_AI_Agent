"""System prompts assembled by rule, not by asking the model.

Today's date and weekday are resolved in code and injected as text. A small local model
cannot reliably turn "내일" into a date on its own, and asking it to would cost an extra
inference round trip on every schedule request.
"""

from datetime import date

WEEKDAY_NAMES = ("월", "화", "수", "목", "금", "토", "일")

GENERAL_SYSTEM_PROMPT = "한국어로 간결하고 정확하게 답변하는 개인 비서입니다."


def general_system_prompt(time_tool_available: bool) -> str:
    """Build the General Agent prompt.

    No date is injected here. This agent answers date questions by calling the tool, so
    stating a date in the prompt would let it answer from stale text instead.
    """
    if not time_tool_available:
        return GENERAL_SYSTEM_PROMPT
    return (
        f"{GENERAL_SYSTEM_PROMPT}"
        " 현재 날짜나 시각을 물어보면 추측하지 말고 get_current_time 도구를 사용하세요."
        " 날짜와 무관한 대화에서는 도구를 사용하지 마세요."
    )


def format_today(today: date) -> str:
    """Render the current date with its Korean weekday, e.g. 2026-09-12 (금)."""
    return f"{today.isoformat()} ({WEEKDAY_NAMES[today.weekday()]})"


def schedule_system_prompt(today: date, timezone: str, calendar_available: bool) -> str:
    """Build the Schedule Agent prompt for one request."""
    lines = [
        "한국어로 간결하게 답변하는 일정 관리 전문 비서입니다.",
        f"오늘은 {format_today(today)}이고 시간대는 {timezone}입니다.",
        "상대적인 날짜 표현은 오늘을 기준으로 계산해 도구에 ISO 8601 형식으로 전달하세요.",
    ]
    if calendar_available:
        lines.extend(
            [
                "일정을 조회·생성·수정·삭제할 때는 반드시 도구를 사용하세요.",
                "일정을 수정하거나 삭제하려면 event_id가 필요합니다. 모르면 먼저 get_schedule로 조회하세요.",
                "도구가 실패하면 실패했다고 말하고, 조회하지 못한 일정을 있는 것처럼 말하지 마세요.",
            ]
        )
    else:
        lines.extend(
            [
                "현재 캘린더 서버에 연결되어 있지 않아 일정을 조회하거나 변경할 수 없습니다.",
                "확인하지 못한 일정이나 변경 결과를 사실처럼 말하지 마세요.",
            ]
        )
    return " ".join(lines)


def search_system_prompt(today: date, timezone: str, weather_available: bool) -> str:
    """Build the Search Agent prompt for one request."""
    lines = [
        "한국어로 간결하게 답변하는 실시간 정보 전문 비서입니다.",
        f"오늘은 {format_today(today)}이고 시간대는 {timezone}입니다.",
    ]
    if weather_available:
        lines.extend(
            [
                "날씨를 물어보면 반드시 get_weather 도구를 사용하세요.",
                "웹 검색과 장소 검색 도구는 아직 없습니다. 확인하지 못한 최신 정보를 사실처럼 말하지 마세요.",
            ]
        )
    else:
        lines.append(
            "현재 웹 검색·날씨·장소 조회 도구가 없습니다. 확인하지 못한 최신 정보를 사실처럼 말하지 마세요."
        )
    return " ".join(lines)
