import json
import logging

import pytest
from fastapi.testclient import TestClient

from app import api
from app.agents.orchestrator import AgentName
from app.agents.reply import ToolCall
from app.core.logging import JsonFormatter
from app.main import create_app
from app.services.orchestrator_service import RoutedResponse

pytestmark = pytest.mark.unit


class StubOrchestratorService:
    def __init__(self, tool_calls: tuple[ToolCall, ...] = ()) -> None:
        self.tool_calls = tool_calls

    def respond(self, message: str) -> RoutedResponse:
        return RoutedResponse(
            selected_agent=AgentName.GENERAL,
            response=f"응답: {message}",
            tool_calls=self.tool_calls,
        )


def test_chat_returns_agent_response(monkeypatch: pytest.MonkeyPatch) -> None:
    application = create_app()
    monkeypatch.setattr(api.chat, "get_orchestrator_service", StubOrchestratorService)

    with TestClient(application) as client:
        response = client.post(
            "/chat",
            json={
                "user_id": "user-1",
                "session_id": "session-1",
                "message": "안녕하세요",
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "response": "응답: 안녕하세요",
        "session_id": "session-1",
    }


def _emitted_events(stderr: str) -> list[dict[str, object]]:
    """Parse the structured log lines the application actually wrote."""
    events = []
    for line in stderr.splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def test_chat_log_records_which_tools_ran_and_which_failed(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    application = create_app()
    monkeypatch.setattr(
        api.chat,
        "get_orchestrator_service",
        lambda: StubOrchestratorService(
            tool_calls=(
                ToolCall(name="get_schedule", call_count=1, success_count=1),
                ToolCall(name="create_schedule", call_count=1, success_count=0),
            )
        ),
    )

    with TestClient(application) as client:
        client.post(
            "/chat",
            json={
                "user_id": "user-1",
                "session_id": "session-1",
                "message": "안녕하세요",
            },
        )

    completed = [
        event
        for event in _emitted_events(capsys.readouterr().err)
        if event.get("event") == "chat_request_completed"
    ]
    assert len(completed) == 1
    assert completed[0]["tools_used"] == ["get_schedule", "create_schedule"]
    assert completed[0]["tools_failed"] == ["create_schedule"]
    assert completed[0]["selected_agent"] == "general"


def test_structured_log_serializes_the_tool_fields() -> None:
    record = logging.LogRecord(
        name="app.api.chat",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="chat_request_completed",
        args=(),
        exc_info=None,
    )
    record.tools_used = ["get_schedule"]
    record.tools_failed = ["create_schedule"]

    payload = json.loads(JsonFormatter().format(record))

    assert payload["tools_used"] == ["get_schedule"]
    assert payload["tools_failed"] == ["create_schedule"]


def test_chat_does_not_log_the_message_content(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    application = create_app()
    monkeypatch.setattr(api.chat, "get_orchestrator_service", StubOrchestratorService)

    with TestClient(application) as client:
        client.post(
            "/chat",
            json={
                "user_id": "user-1",
                "session_id": "session-1",
                "message": "비밀 진료 기록",
            },
        )

    stderr = capsys.readouterr().err
    assert _emitted_events(stderr)
    assert "비밀 진료 기록" not in stderr


def test_chat_rejects_blank_message() -> None:
    application = create_app()

    with TestClient(application) as client:
        response = client.post(
            "/chat",
            json={"user_id": "user-1", "session_id": "session-1", "message": "   "},
        )

    assert response.status_code == 422


def test_chat_page_serves_browser_interface() -> None:
    application = create_app()

    with TestClient(application) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "Personal AI Agent" in response.text
    assert 'src="/static/chat.js"' in response.text
