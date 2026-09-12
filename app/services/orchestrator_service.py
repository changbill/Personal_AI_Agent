"""Application boundary for routing one request to one agent."""

from dataclasses import dataclass
from typing import Protocol

from app.agents.orchestrator import AgentName, Orchestrator


class RespondingAgent(Protocol):
    """Minimal contract shared by chat agents."""

    def respond(self, message: str) -> str: ...


@dataclass(frozen=True)
class RoutedResponse:
    """An agent response together with the verified selection that produced it."""

    selected_agent: AgentName
    response: str


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

    def respond(self, message: str) -> RoutedResponse:
        selected_agent = self._orchestrator.select(message)
        if not isinstance(selected_agent, AgentName):
            selected_agent = AgentName.GENERAL

        response = self._agents[selected_agent].respond(message)
        return RoutedResponse(selected_agent=selected_agent, response=response)
