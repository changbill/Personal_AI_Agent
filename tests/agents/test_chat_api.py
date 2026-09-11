import pytest
from fastapi.testclient import TestClient

from app import api
from app.main import create_app

pytestmark = pytest.mark.unit


class StubGeneralAgent:
    def respond(self, message: str) -> str:
        return f"응답: {message}"


def test_chat_returns_agent_response(monkeypatch: pytest.MonkeyPatch) -> None:
    application = create_app()
    monkeypatch.setattr(api.chat, "get_general_agent", StubGeneralAgent)

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
