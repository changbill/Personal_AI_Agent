"""Runtime configuration sourced exclusively from environment variables."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    ollama_host: str
    ollama_model: str
    ollama_num_ctx: int

    @classmethod
    def from_env(cls) -> "Settings":
        try:
            num_ctx = int(os.environ["OLLAMA_NUM_CTX"])
            settings = cls(
                ollama_host=os.environ["OLLAMA_HOST"],
                ollama_model=os.environ["OLLAMA_MODEL"],
                ollama_num_ctx=num_ctx,
            )
        except KeyError as error:
            raise RuntimeError(f"필수 환경변수가 없습니다: {error.args[0]}") from error
        except ValueError as error:
            raise RuntimeError("OLLAMA_NUM_CTX는 정수여야 합니다") from error

        if not settings.ollama_host.strip() or not settings.ollama_model.strip():
            raise RuntimeError("OLLAMA_HOST와 OLLAMA_MODEL은 비어 있을 수 없습니다")
        if settings.ollama_num_ctx <= 0:
            raise RuntimeError("OLLAMA_NUM_CTX는 양수여야 합니다")
        return settings
