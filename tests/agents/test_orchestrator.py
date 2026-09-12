import pytest

from app.agents.orchestrator import AgentName, Orchestrator
from app.services.orchestrator_service import OrchestratorService

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("내일 일정 알려줘", AgentName.SCHEDULE),
        ("다음 주 회의 잡아줘", AgentName.SCHEDULE),
        ("오늘 인천 날씨 알려줘", AgentName.SEARCH),
        ("근처 맛집 찾아줘", AgentName.SEARCH),
        ("파이썬 딕셔너리를 설명해줘", AgentName.GENERAL),
        ("비 오면 내일 약속 취소해줘", AgentName.GENERAL),
    ],
)
def test_orchestrator_selects_one_safe_agent(message: str, expected: AgentName) -> None:
    assert Orchestrator().select(message) is expected


class StubAgent:
    def __init__(self, name: str) -> None:
        self.name = name
        self.received_messages: list[str] = []

    def respond(self, message: str) -> str:
        self.received_messages.append(message)
        return f"{self.name}: {message}"


def test_service_calls_only_selected_agent() -> None:
    general = StubAgent("general")
    schedule = StubAgent("schedule")
    search = StubAgent("search")
    service = OrchestratorService(Orchestrator(), general, schedule, search)

    result = service.respond("내일 일정 알려줘")

    assert result.selected_agent is AgentName.SCHEDULE
    assert result.response == "schedule: 내일 일정 알려줘"
    assert general.received_messages == []
    assert schedule.received_messages == ["내일 일정 알려줘"]
    assert search.received_messages == []


class InvalidOrchestrator:
    def select(self, message: str) -> str:
        return "not-an-agent"


def test_service_falls_back_to_general_for_invalid_selection() -> None:
    general = StubAgent("general")
    schedule = StubAgent("schedule")
    search = StubAgent("search")
    service = OrchestratorService(InvalidOrchestrator(), general, schedule, search)  # type: ignore[arg-type]

    result = service.respond("애매한 요청")

    assert result.selected_agent is AgentName.GENERAL
    assert result.response == "general: 애매한 요청"
    assert general.received_messages == ["애매한 요청"]
    assert schedule.received_messages == []
    assert search.received_messages == []
