"""General conversation agent holding only the current-time tool.

Calendar and weather tools stay off this agent on purpose: a 2B model asked to chat while
holding them reaches for them on unrelated questions. The time tool is the one exception,
because this agent gets no date injected and otherwise cannot answer "오늘 며칠이야".
"""

from typing import Any

from strands import Agent

from app.agents.model_factory import build_ollama_model
from app.agents.prompts import general_system_prompt
from app.agents.reply import AgentReply, summarize_tool_calls
from app.core.config import Settings


class GeneralAgent:
    """Owns one short-lived Strands agent invocation."""

    def __init__(self, settings: Settings, tools: list[Any] | None = None) -> None:
        self._settings = settings
        self._tools = tools or []

    def respond(self, message: str) -> AgentReply:
        """Generate one response without retaining cross-request conversation history."""
        agent = Agent(
            model=build_ollama_model(self._settings),
            system_prompt=general_system_prompt(time_tool_available=bool(self._tools)),
            tools=self._tools,
        )
        result = agent(message)
        text = str(result).strip()
        if not text:
            raise RuntimeError("모델이 비어 있는 응답을 반환했습니다")
        return AgentReply(
            text=text, tool_calls=summarize_tool_calls(result.metrics.tool_metrics)
        )
