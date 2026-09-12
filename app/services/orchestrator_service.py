"""Application boundary for routing one request to one agent."""

from dataclasses import dataclass
from typing import Protocol

from app.agents.orchestrator import AgentName, Orchestrator
from app.agents.reply import AgentReply, ToolCall


class RespondingAgent(Protocol):
    """Minimal contract shared by chat agents."""

    def respond(self, message: str) -> AgentReply: ...


@dataclass(frozen=True)
class RoutedResponse:
    """An agent reply together with the verified selection that produced it."""

    selected_agent: AgentName
    response: str
    tool_calls: tuple[ToolCall, ...] = ()

    @property
    def tool_names(self) -> tuple[str, ...]:
        return tuple(call.name for call in self.tool_calls)

    @property
    def all_tools_succeeded(self) -> bool:
        return all(call.succeeded for call in self.tool_calls)


class OrchestratorService:
    """Validate a selection and invoke exactly one matching specialist."""

    def __init__(
        self,
        orchestrator: Orchestrator,
        general_agent: RespondingAgent,
        schedule_agent: RespondingAgent,
        search_agent: RespondingAgent,
    ) -> None:
        self._orchestrator = orchestrator
        self._agents = {
            AgentName.GENERAL: general_agent,
            AgentName.SCHEDULE: schedule_agent,
            AgentName.SEARCH: search_agent,
        }

    @property
    def routable_agents(self) -> frozenset[AgentName]:
        """Which selections this service can actually serve."""
        return frozenset(self._agents)

    def respond(self, message: str) -> RoutedResponse:
        selected_agent = self._orchestrator.select(message)
        if not isinstance(selected_agent, AgentName):
            selected_agent = AgentName.GENERAL

        reply = self._agents[selected_agent].respond(message)
        return RoutedResponse(
            selected_agent=selected_agent,
            response=reply.text,
            tool_calls=reply.tool_calls,
        )
