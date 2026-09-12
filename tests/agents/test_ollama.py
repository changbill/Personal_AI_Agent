"""Real Ollama checks; skipped when the local runtime is unavailable.

Tool selection depends on the model and on the tool descriptions, so these run when the
model, a prompt or a tool description changes, not on every edit.
"""

import urllib.error
import urllib.request

import pytest

from app.agents.general_agent import GeneralAgent
from app.agents.schedule_agent import ScheduleAgent
from app.agents.search_agent import SearchAgent
from app.core.config import Settings
from app.services.time_service import TimeService, build_today_clock
from app.services.weather_service import WeatherService
from app.tools.calendar_tools import build_calendar_tools
from app.tools.time_tools import build_time_tools
from app.tools.weather_tools import build_weather_tools

pytestmark = pytest.mark.llm


def _settings_or_skip() -> Settings:
    try:
        settings = Settings.from_env()
    except RuntimeError as error:
        pytest.skip(str(error))

    try:
        with urllib.request.urlopen(f"{settings.ollama_host}/api/tags", timeout=1):
            pass
    except (urllib.error.URLError, TimeoutError) as error:
        pytest.skip(f"Ollama를 사용할 수 없습니다: {error}")
    return settings


class RecordingGateway:
    """Available calendar that records calls instead of reaching Google."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    @property
    def is_available(self) -> bool:
        return True

    def call_tool(self, name: str, arguments: dict) -> str:
        self.calls.append((name, arguments))
        return "2026-09-13 15:00 치과 (event_id: evt-1)"

    def close(self) -> None:
        return None


def test_general_agent_uses_running_ollama_without_thinking_output() -> None:
    reply = GeneralAgent(_settings_or_skip()).respond("한 단어로 인사해 주세요.")

    assert reply.text
    assert "<think>" not in reply.text.lower()
    assert reply.tool_calls == ()


def test_schedule_agent_calls_the_schedule_lookup_tool() -> None:
    settings = _settings_or_skip()
    gateway = RecordingGateway()
    tools = build_calendar_tools(
        gateway, calendar_id=settings.calendar_id, timezone=settings.timezone
    )

    reply = ScheduleAgent(
        settings, tools=tools, today=build_today_clock(settings.timezone)
    ).respond("내일 일정 알려줘")

    assert "get_schedule" in reply.tool_names, (
        f"일정 조회 도구를 호출하지 않았습니다: {reply.tool_names} / {reply.text}"
    )
    assert gateway.calls and gateway.calls[0][0] == "list-events"


def test_search_agent_calls_the_weather_tool() -> None:
    settings = _settings_or_skip()
    requested: list[str] = []

    class RecordingWeather(WeatherService):
        def current_weather(self, place: str) -> str:
            requested.append(place)
            return "인천 현재 흐림, 기온 24.3도"

    tools = build_weather_tools(RecordingWeather(lambda url, params: {}))

    reply = SearchAgent(
        settings, tools=tools, today=build_today_clock(settings.timezone)
    ).respond("오늘 인천 날씨 알려줘")

    assert "get_weather" in reply.tool_names, (
        f"날씨 도구를 호출하지 않았습니다: {reply.tool_names} / {reply.text}"
    )
    assert requested


def test_general_agent_calls_the_time_tool_for_a_date_question() -> None:
    settings = _settings_or_skip()
    requested: list[str] = []

    class RecordingTime(TimeService):
        def current_time(self, timezone: str):
            requested.append(timezone)
            return super().current_time(timezone)

    tools = build_time_tools(RecordingTime(lambda url, params: {}), settings.timezone)

    reply = GeneralAgent(settings, tools=tools).respond("오늘 며칠이야?")

    assert "get_current_time" in reply.tool_names, (
        f"시간 도구를 호출하지 않았습니다: {reply.tool_names} / {reply.text}"
    )
    assert requested == [settings.timezone]


def test_general_agent_leaves_the_time_tool_alone_for_unrelated_chat() -> None:
    settings = _settings_or_skip()
    tools = build_time_tools(TimeService(lambda url, params: {}), settings.timezone)

    reply = GeneralAgent(settings, tools=tools).respond(
        "파이썬 리스트와 튜플의 차이를 한 문장으로 설명해줘."
    )

    assert "get_current_time" not in reply.tool_names, (
        f"관련 없는 대화에서 시간 도구를 호출했습니다: {reply.text}"
    )
