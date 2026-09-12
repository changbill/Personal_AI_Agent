"""Runtime configuration sourced exclusively from environment variables."""

import os
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_TIMEZONE = "Asia/Seoul"
DEFAULT_CALENDAR_ID = "primary"


@dataclass(frozen=True)
class Settings:
    ollama_host: str
    ollama_model: str
    ollama_num_ctx: int
    timezone: str = DEFAULT_TIMEZONE
    calendar_mcp_url: str | None = None
    calendar_id: str = DEFAULT_CALENDAR_ID

    @classmethod
    def from_env(cls, env_file: Path | None = None) -> "Settings":
        load_dotenv(env_file or _PROJECT_ROOT / ".env", override=False)
        try:
            num_ctx = int(os.environ["OLLAMA_NUM_CTX"])
            settings = cls(
                ollama_host=os.environ["OLLAMA_HOST"],
                ollama_model=os.environ["OLLAMA_MODEL"],
                ollama_num_ctx=num_ctx,
                timezone=os.environ.get("AGENT_TIMEZONE", DEFAULT_TIMEZONE),
                # Absent means no calendar. The schedule agent then answers without tools
                # instead of failing the request, so the API runs before OAuth is set up.
                calendar_mcp_url=_optional(os.environ.get("CALENDAR_MCP_URL")),
                calendar_id=os.environ.get("CALENDAR_ID", DEFAULT_CALENDAR_ID),
            )
        except KeyError as error:
            raise RuntimeError(f"필수 환경변수가 없습니다: {error.args[0]}") from error
        except ValueError as error:
            raise RuntimeError("OLLAMA_NUM_CTX는 정수여야 합니다") from error

        if not settings.ollama_host.strip() or not settings.ollama_model.strip():
            raise RuntimeError("OLLAMA_HOST와 OLLAMA_MODEL은 비어 있을 수 없습니다")
        if settings.ollama_num_ctx <= 0:
            raise RuntimeError("OLLAMA_NUM_CTX는 양수여야 합니다")
        if not settings.timezone.strip():
            raise RuntimeError("AGENT_TIMEZONE은 비어 있을 수 없습니다")
        # Validated at startup, not at first use: an unresolvable timezone would
        # otherwise surface as a wrong date inside a prompt rather than as an error.
        try:
            ZoneInfo(settings.timezone)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise RuntimeError(
                f"AGENT_TIMEZONE이 유효한 IANA 시간대가 아닙니다: {settings.timezone}"
            ) from error
        if not settings.calendar_id.strip():
            raise RuntimeError("CALENDAR_ID는 비어 있을 수 없습니다")
        return settings


def _optional(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    return value.strip()
