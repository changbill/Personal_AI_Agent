import pytest

from app.core.config import Settings

pytestmark = pytest.mark.unit


def test_settings_reads_required_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OLLAMA_HOST", "http://ollama:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3.5:2b-q4_K_M")
    monkeypatch.setenv("OLLAMA_NUM_CTX", "2048")

    assert Settings.from_env() == Settings(
        ollama_host="http://ollama:11434",
        ollama_model="qwen3.5:2b-q4_K_M",
        ollama_num_ctx=2048,
    )


def test_settings_rejects_missing_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    monkeypatch.delenv("OLLAMA_NUM_CTX", raising=False)

    with pytest.raises(RuntimeError, match="OLLAMA_NUM_CTX"):
        Settings.from_env()
