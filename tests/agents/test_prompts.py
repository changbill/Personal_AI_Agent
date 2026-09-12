import re
from datetime import date

import pytest

from app.agents.prompts import (
    GENERAL_SYSTEM_PROMPT,
    format_today,
    general_system_prompt,
    schedule_system_prompt,
    search_system_prompt,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("today", "expected"),
    [
        (date(2026, 9, 12), "2026-09-12 (토)"),
        (date(2026, 9, 14), "2026-09-14 (월)"),
        (date(2026, 9, 13), "2026-09-13 (일)"),
    ],
)
def test_today_is_rendered_with_its_korean_weekday(today: date, expected: str) -> None:
    assert format_today(today) == expected


def test_the_schedule_prompt_injects_the_date_so_the_model_never_parses_it() -> None:
    prompt = schedule_system_prompt(
        today=date(2026, 9, 12), timezone="Asia/Seoul", calendar_available=True
    )

    assert "2026-09-12 (토)" in prompt
    assert "Asia/Seoul" in prompt
    assert "ISO 8601" in prompt


def test_the_schedule_prompt_demands_an_event_id_lookup_when_tools_exist() -> None:
    prompt = schedule_system_prompt(
        today=date(2026, 9, 12), timezone="Asia/Seoul", calendar_available=True
    )

    assert "get_schedule" in prompt
    assert "연결되어 있지 않아" not in prompt


def test_the_schedule_prompt_forbids_inventing_events_without_a_calendar() -> None:
    prompt = schedule_system_prompt(
        today=date(2026, 9, 12), timezone="Asia/Seoul", calendar_available=False
    )

    assert "연결되어 있지 않아" in prompt
    assert "사실처럼 말하지 마세요" in prompt
    assert "get_schedule" not in prompt


def test_the_search_prompt_names_the_weather_tool_only_when_it_exists() -> None:
    with_tool = search_system_prompt(
        today=date(2026, 9, 12), timezone="Asia/Seoul", weather_available=True
    )
    without_tool = search_system_prompt(
        today=date(2026, 9, 12), timezone="Asia/Seoul", weather_available=False
    )

    assert "get_weather" in with_tool
    assert "get_weather" not in without_tool
    assert "사실처럼 말하지 마세요" in without_tool
    assert "2026-09-12 (토)" in with_tool


def test_the_general_prompt_stays_bare_without_the_time_tool() -> None:
    assert general_system_prompt(time_tool_available=False) == GENERAL_SYSTEM_PROMPT


def test_the_general_prompt_names_the_time_tool_when_it_exists() -> None:
    prompt = general_system_prompt(time_tool_available=True)

    assert "get_current_time" in prompt
    assert "추측하지 말고" in prompt
    assert "날짜와 무관한 대화에서는 도구를 사용하지 마세요" in prompt


def test_the_general_prompt_never_states_a_date() -> None:
    # This agent answers date questions by calling the tool. A date in the prompt would
    # let it answer from stale text instead, which is the whole point of the tool.
    prompt = general_system_prompt(time_tool_available=True)

    assert "오늘은" not in prompt
    assert not re.search(r"\d{4}-\d{2}-\d{2}", prompt)
