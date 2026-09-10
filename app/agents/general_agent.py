"""General conversation agent with no tools or persistent memory."""

from strands import Agent
from strands.models.ollama import OllamaModel

from app.core.config import Settings


class GeneralAgent:
    """Owns one short-lived Strands agent invocation."""

    def __init__(self, settings: Settings) -> None:
        self._agent = Agent(
            model=OllamaModel(
                host=settings.ollama_host,
                model_id=settings.ollama_model,
                additional_args={"think": False},
                options={"num_ctx": settings.ollama_num_ctx},
                temperature=0,
            ),
            system_prompt="한국어로 간결하고 정확하게 답변하는 개인 비서입니다.",
        )

    def respond(self, message: str) -> str:
        """Generate one response without retaining cross-request conversation history."""
        response = str(self._agent(message)).strip()
        if not response:
            raise RuntimeError("모델이 비어 있는 응답을 반환했습니다")
        return response
