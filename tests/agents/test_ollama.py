"""Real Ollama checks; skipped when the local runtime is unavailable."""

import urllib.error
import urllib.request

import pytest

from app.agents.general_agent import GeneralAgent
from app.core.config import Settings

pytestmark = pytest.mark.llm


def _settings_or_skip() -> Settings:
    try:
        settings = Settings.from_env()
    except RuntimeError as error:
        pytest.skip(str(error))

    try:
        with urllib.request.urlopen(f"{settings.ollama_host}/api/tags", timeout=1):
            pass
    except (urllib.error.URLError, TimeoutError) as error:
        pytest.skip(f"Ollama를 사용할 수 없습니다: {error}")
    return settings


def test_general_agent_uses_running_ollama_without_thinking_output() -> None:
    response = GeneralAgent(_settings_or_skip()).respond("한 단어로 인사해 주세요.")

    assert response
    assert "<think>" not in response.lower()
