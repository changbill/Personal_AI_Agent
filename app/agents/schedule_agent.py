"""Schedule specialist backed by the Google Calendar MCP server.

The Strands agent is rebuilt per request because the system prompt carries today's date,
which must be current. The tools and the MCP session are built once and reused: spawning
a calendar session per request would add startup latency to every turn.
"""

from collections.abc import Callable
from datetime import date
from typing import Any

from strands import Agent

from app.agents.model_factory import build_ollama_model
from app.agents.prompts import schedule_system_prompt
from app.agents.reply import AgentReply, summarize_tool_calls
from app.core.config import Settings


class ScheduleAgent:
    """Answer schedule requests using calendar tools when a calendar is reachable."""

    def __init__(
        self,
        settings: Settings,
        tools: list[Any],
        today: Callable[[], date],
    ) -> None:
        self._settings = settings
        self._tools = tools
        self._today = today

    def respond(self, message: str) -> AgentReply:
        agent = Agent(
            model=build_ollama_model(self._settings),
            system_prompt=schedule_system_prompt(
                today=self._today(),
                timezone=self._settings.timezone,
                calendar_available=bool(self._tools),
            ),
            tools=self._tools,
        )
        result = agent(message)
        text = str(result).strip()
        if not text:
            raise RuntimeError("모델이 비어 있는 응답을 반환했습니다")
        return AgentReply(
            text=text, tool_calls=summarize_tool_calls(result.metrics.tool_metrics)
        )
