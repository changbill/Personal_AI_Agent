"""Schedule specialist without calendar tools in Phase 2."""

from strands import Agent
from strands.models.ollama import OllamaModel

from app.core.config import Settings


class ScheduleAgent:
    """Respond to schedule requests without fabricating calendar data."""

    def __init__(self, settings: Settings) -> None:
        self._agent = Agent(
            model=OllamaModel(
                host=settings.ollama_host,
                model_id=settings.ollama_model,
                additional_args={"think": False},
                options={"num_ctx": settings.ollama_num_ctx},
                temperature=0,
            ),
            system_prompt=(
                "한국어로 간결하게 답변하는 일정 관리 전문 비서입니다. "
                "현재는 실제 캘린더 조회·생성·수정 도구가 없습니다. "
                "확인하지 못한 일정이나 변경 결과를 사실처럼 말하지 마세요."
            ),
        )

    def respond(self, message: str) -> str:
        response = str(self._agent(message)).strip()
        if not response:
            raise RuntimeError("모델이 비어 있는 응답을 반환했습니다")
        return response
