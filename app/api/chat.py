"""Single-turn chat endpoint for Phase 1."""

import logging
import time
from typing import Annotated

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.agents.general_agent import GeneralAgent
from app.agents.orchestrator import Orchestrator
from app.agents.schedule_agent import ScheduleAgent
from app.agents.search_agent import SearchAgent
from app.core.config import Settings
from app.services.orchestrator_service import OrchestratorService

router = APIRouter()
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    user_id: Annotated[str, Field(min_length=1, max_length=128)]
    session_id: Annotated[str, Field(min_length=1, max_length=128)]
    message: Annotated[str, Field(min_length=1, max_length=4_000)]

    @field_validator("user_id", "session_id", "message")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("공백만으로 구성할 수 없습니다")
        return value


class ChatResponse(BaseModel):
    response: str
    session_id: str


def get_orchestrator_service() -> OrchestratorService:
    settings = Settings.from_env()
    return OrchestratorService(
        orchestrator=Orchestrator(),
        general_agent=GeneralAgent(settings),
        schedule_agent=ScheduleAgent(settings),
        search_agent=SearchAgent(settings),
    )


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    service = get_orchestrator_service()
    started_at = time.monotonic()
    try:
        routed_response = service.respond(request.message)
    except Exception as error:
        logger.exception(
            "chat_request_failed",
            extra={
                "user_id": request.user_id,
                "session_id": request.session_id,
                "selected_agent": "unknown",
                "tools_used": [],
                "memory_retrieved": False,
                "memory_stored": False,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="로컬 모델 응답을 생성하지 못했습니다",
        ) from error

    logger.info(
        "chat_request_completed",
        extra={
            "user_id": request.user_id,
            "session_id": request.session_id,
            "selected_agent": routed_response.selected_agent,
            "tools_used": [],
            "agent_latency_ms": round((time.monotonic() - started_at) * 1_000, 2),
            "llm_latency_ms": round((time.monotonic() - started_at) * 1_000, 2),
            "memory_retrieved": False,
            "memory_stored": False,
        },
    )
    return ChatResponse(
        response=routed_response.response, session_id=request.session_id
    )
