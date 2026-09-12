import pytest

from app.agents.orchestrator import AgentName
from app.core.config import Settings
from app.services import runtime as runtime_module
from app.services.runtime import AgentRuntime, build_runtime, close_runtime

pytestmark = pytest.mark.unit

SETTINGS = Settings(
    ollama_host="http://ollama:11434",
    ollama_model="qwen3.5:2b-q4_K_M",
    ollama_num_ctx=2048,
    timezone="Asia/Seoul",
)


@pytest.fixture(autouse=True)
def reset_process_runtime() -> None:
    runtime_module._runtime = None
    yield
    runtime_module._runtime = None


def test_no_calendar_url_still_builds_a_working_service() -> None:
    built = build_runtime(SETTINGS)

    assert built.calendar_gateway.is_available is False
    # Every agent stays routable; the schedule agent just holds no tools.
    assert built.service.routable_agents == frozenset(AgentName)


class StubGateway:
    def __init__(self) -> None:
        self.closed = False

    @property
    def is_available(self) -> bool:
        return True

    def call_tool(self, name: str, arguments: dict) -> str:
        return "ok"

    def close(self) -> None:
        self.closed = True


def test_closing_the_runtime_releases_the_calendar_session() -> None:
    gateway = StubGateway()
    built = build_runtime(SETTINGS)
    built.calendar_gateway = gateway

    built.close()

    assert gateway.closed is True


class FailingGateway(StubGateway):
    def close(self) -> None:
        raise RuntimeError("session already gone")


def test_a_failing_close_does_not_propagate() -> None:
    built = build_runtime(SETTINGS)
    built.calendar_gateway = FailingGateway()

    built.close()


def test_close_runtime_is_safe_when_nothing_was_built() -> None:
    close_runtime()

    assert runtime_module._runtime is None


def test_close_runtime_forgets_the_cached_runtime() -> None:
    gateway = StubGateway()
    runtime_module._runtime = AgentRuntime(
        settings=SETTINGS,
        calendar_gateway=gateway,  # type: ignore[arg-type]
        service=build_runtime(SETTINGS).service,
    )

    close_runtime()

    assert gateway.closed is True
    assert runtime_module._runtime is None
