from pathlib import Path

import pytest

from app.core.config import DEFAULT_CALENDAR_ID, DEFAULT_TIMEZONE, Settings

pytestmark = pytest.mark.unit

OPTIONAL_KEYS = ("AGENT_TIMEZONE", "CALENDAR_MCP_URL", "CALENDAR_ID")


@pytest.fixture(autouse=True)
def clear_optional_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep an operator .env on the host machine from leaking into these assertions."""
    for key in OPTIONAL_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_settings_reads_required_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("OLLAMA_HOST", "http://ollama:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3.5:2b-q4_K_M")
    monkeypatch.setenv("OLLAMA_NUM_CTX", "2048")

    assert Settings.from_env(tmp_path / ".env") == Settings(
        ollama_host="http://ollama:11434",
        ollama_model="qwen3.5:2b-q4_K_M",
        ollama_num_ctx=2048,
    )


def test_calendar_and_timezone_fall_back_to_documented_defaults(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("OLLAMA_HOST", "http://ollama:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3.5:2b-q4_K_M")
    monkeypatch.setenv("OLLAMA_NUM_CTX", "2048")

    settings = Settings.from_env(tmp_path / ".env")

    assert settings.timezone == DEFAULT_TIMEZONE
    assert settings.calendar_id == DEFAULT_CALENDAR_ID
    # Absent means no calendar, so the API runs before Google OAuth is set up.
    assert settings.calendar_mcp_url is None


@pytest.mark.parametrize("configured", ["", "   "])
def test_a_blank_calendar_url_is_treated_as_no_calendar(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, configured: str
) -> None:
    monkeypatch.setenv("OLLAMA_HOST", "http://ollama:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3.5:2b-q4_K_M")
    monkeypatch.setenv("OLLAMA_NUM_CTX", "2048")
    monkeypatch.setenv("CALENDAR_MCP_URL", configured)

    assert Settings.from_env(tmp_path / ".env").calendar_mcp_url is None


def test_calendar_and_timezone_are_read_from_the_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("OLLAMA_HOST", "http://ollama:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3.5:2b-q4_K_M")
    monkeypatch.setenv("OLLAMA_NUM_CTX", "2048")
    monkeypatch.setenv("AGENT_TIMEZONE", "UTC")
    monkeypatch.setenv("CALENDAR_MCP_URL", " http://calendar-mcp:3000/mcp ")
    monkeypatch.setenv("CALENDAR_ID", "work@example.com")

    settings = Settings.from_env(tmp_path / ".env")

    assert settings.timezone == "UTC"
    assert settings.calendar_mcp_url == "http://calendar-mcp:3000/mcp"
    assert settings.calendar_id == "work@example.com"


def test_settings_loads_env_file_without_overriding_shell_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "OLLAMA_HOST=http://from-dotenv:11434\n"
        "OLLAMA_MODEL=qwen3.5:2b-q4_K_M\n"
        "OLLAMA_NUM_CTX=2048\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("OLLAMA_MODEL", "shell-model:fixed")

    assert Settings.from_env(env_file) == Settings(
        ollama_host="http://from-dotenv:11434",
        ollama_model="shell-model:fixed",
        ollama_num_ctx=2048,
    )


def test_settings_rejects_missing_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    monkeypatch.delenv("OLLAMA_NUM_CTX", raising=False)

    with pytest.raises(RuntimeError, match="OLLAMA_NUM_CTX"):
        Settings.from_env(tmp_path / ".env")


def test_settings_rejects_a_blank_timezone(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("OLLAMA_HOST", "http://ollama:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3.5:2b-q4_K_M")
    monkeypatch.setenv("OLLAMA_NUM_CTX", "2048")
    monkeypatch.setenv("AGENT_TIMEZONE", "   ")

    with pytest.raises(RuntimeError, match="AGENT_TIMEZONE"):
        Settings.from_env(tmp_path / ".env")
