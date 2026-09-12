"""Search specialist holding only the weather tool in Phase 3-A.

Web and place search wait for Phase 3-B, where a provider has to be chosen. Leaving them
unregistered is deliberate: an advertised tool that cannot work teaches the model to
claim results it never fetched.
"""

from collections.abc import Callable
from datetime import date
from typing import Any

from strands import Agent

from app.agents.model_factory import build_ollama_model
from app.agents.prompts import search_system_prompt
from app.agents.reply import AgentReply, summarize_tool_calls
from app.core.config import Settings


class SearchAgent:
    """Answer live-information requests without fabricating results."""

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
            system_prompt=search_system_prompt(
                today=self._today(),
                timezone=self._settings.timezone,
                weather_available=bool(self._tools),
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
