"""Specialist agents assemble the prompt and the reply; the model itself is stubbed.

These verify the parts this project owns: which tools the agent is given, whether the
injected date reaches the prompt, and whether tool usage reaches the caller.
"""

from dataclasses import dataclass
from datetime import date
from typing import Any, ClassVar

import pytest

from app.agents.general_agent import GeneralAgent
from app.agents.schedule_agent import ScheduleAgent
from app.agents.search_agent import SearchAgent
from app.core.config import Settings

pytestmark = pytest.mark.unit

SETTINGS = Settings(
    ollama_host="http://ollama:11434",
    ollama_model="qwen3.5:2b-q4_K_M",
    ollama_num_ctx=2048,
    timezone="Asia/Seoul",
)


@dataclass
class StubToolMetrics:
    call_count: int
    success_count: int


class StubResult:
    """Stands in for a Strands AgentResult."""

    def __init__(self, text: str, tool_metrics: dict[str, Any]) -> None:
        self.text = text
        self.metrics = type("Metrics", (), {"tool_metrics": tool_metrics})()

    def __str__(self) -> str:
        return self.text


class StubStrandsAgent:
    """Captures how the agent was constructed and returns a canned result."""

    instances: ClassVar[list["StubStrandsAgent"]] = []
    ran_tool: ClassVar[str] = "get_schedule"

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
        self.prompts: list[str] = []
        StubStrandsAgent.instances.append(self)

    def __call__(self, message: str) -> StubResult:
        self.prompts.append(message)
        return StubResult(
            "  일정 1건  ",
            {self.ran_tool: StubToolMetrics(call_count=1, success_count=1)},
        )


@pytest.fixture(autouse=True)
def reset_instances() -> None:
    StubStrandsAgent.instances = []
    StubStrandsAgent.ran_tool = "get_schedule"


def _patch_agent(monkeypatch: pytest.MonkeyPatch, module: Any) -> None:
    monkeypatch.setattr(module, "Agent", StubStrandsAgent)
    monkeypatch.setattr(module, "build_ollama_model", lambda settings: "model")


def test_schedule_agent_passes_its_tools_and_the_injected_date(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.agents import schedule_agent

    _patch_agent(monkeypatch, schedule_agent)
    tools = ["get_schedule-tool"]

    reply = ScheduleAgent(
        SETTINGS, tools=tools, today=lambda: date(2026, 9, 12)
    ).respond("내일 일정 알려줘")

    constructed = StubStrandsAgent.instances[0]
    assert constructed.kwargs["tools"] is tools
    assert "2026-09-12 (토)" in constructed.kwargs["system_prompt"]
    assert "get_schedule" in constructed.kwargs["system_prompt"]
    assert reply.text == "일정 1건"
    assert reply.tool_names == ("get_schedule",)
    assert reply.all_tools_succeeded is True


def test_schedule_agent_announces_no_calendar_when_it_has_no_tools(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.agents import schedule_agent

    _patch_agent(monkeypatch, schedule_agent)

    ScheduleAgent(SETTINGS, tools=[], today=lambda: date(2026, 9, 12)).respond(
        "내일 일정 알려줘"
    )

    prompt = StubStrandsAgent.instances[0].kwargs["system_prompt"]
    assert "연결되어 있지 않아" in prompt


def test_search_agent_passes_its_tools_and_the_injected_date(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.agents import search_agent

    _patch_agent(monkeypatch, search_agent)
    StubStrandsAgent.ran_tool = "get_weather"
    tools = ["get_weather-tool"]

    reply = SearchAgent(SETTINGS, tools=tools, today=lambda: date(2026, 9, 12)).respond(
        "오늘 인천 날씨 알려줘"
    )

    constructed = StubStrandsAgent.instances[0]
    assert constructed.kwargs["tools"] is tools
    assert "2026-09-12 (토)" in constructed.kwargs["system_prompt"]
    assert "get_weather" in constructed.kwargs["system_prompt"]
    assert reply.tool_names == ("get_weather",)


class NoToolStrandsAgent(StubStrandsAgent):
    def __call__(self, message: str) -> StubResult:
        return StubResult("안녕하세요", {})


class EmptyStrandsAgent(StubStrandsAgent):
    def __call__(self, message: str) -> StubResult:
        return StubResult("   ", {})


def test_an_empty_model_response_is_an_error_not_an_empty_reply(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.agents import schedule_agent

    monkeypatch.setattr(schedule_agent, "Agent", EmptyStrandsAgent)
    monkeypatch.setattr(schedule_agent, "build_ollama_model", lambda settings: "model")

    with pytest.raises(RuntimeError):
        ScheduleAgent(SETTINGS, tools=[], today=lambda: date(2026, 9, 12)).respond(
            "내일 일정 알려줘"
        )


def test_general_agent_passes_its_tool_and_reports_the_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.agents import general_agent

    monkeypatch.setattr(general_agent, "Agent", StubStrandsAgent)
    monkeypatch.setattr(general_agent, "build_ollama_model", lambda settings: "model")
    StubStrandsAgent.ran_tool = "get_current_time"
    tools = ["get_current_time-tool"]

    reply = GeneralAgent(SETTINGS, tools=tools).respond("오늘 며칠이야?")

    constructed = StubStrandsAgent.instances[0]
    assert constructed.kwargs["tools"] is tools
    assert "get_current_time" in constructed.kwargs["system_prompt"]
    assert reply.tool_names == ("get_current_time",)


def test_general_agent_without_tools_reports_no_tool_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.agents import general_agent

    monkeypatch.setattr(general_agent, "Agent", NoToolStrandsAgent)
    monkeypatch.setattr(general_agent, "build_ollama_model", lambda settings: "model")

    reply = GeneralAgent(SETTINGS).respond("안녕")

    constructed = StubStrandsAgent.instances[0]
    assert constructed.kwargs["tools"] == []
    assert "get_current_time" not in constructed.kwargs["system_prompt"]
    assert reply.tool_calls == ()
