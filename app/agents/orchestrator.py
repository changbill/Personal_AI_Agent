"""Deterministic single-agent routing for Phase 2."""

from enum import StrEnum


class AgentName(StrEnum):
    """Names of agents allowed to handle a chat request."""

    GENERAL = "general"
    SCHEDULE = "schedule"
    SEARCH = "search"


class Orchestrator:
    """Select one specialist without spending a local LLM call on obvious intents."""

    _SCHEDULE_KEYWORDS = ("일정", "스케줄", "캘린더", "약속", "미팅", "회의")
    _SEARCH_KEYWORDS = (
        "날씨",
        "기온",
        "강수",
        "비 올",
        "비 오",
        "눈 올",
        "미세먼지",
        "환율",
        "주가",
        "뉴스",
        "검색",
        "찾아봐",
        "찾아 줘",
        "알아봐",
        "알아 봐",
        "맛집",
        "근처",
    )

    def select(self, message: str) -> AgentName:
        """Return one safe routing target for a non-blank user message."""
        normalized = message.casefold()
        is_schedule_request = any(
            keyword in normalized for keyword in self._SCHEDULE_KEYWORDS
        )
        is_search_request = any(
            keyword in normalized for keyword in self._SEARCH_KEYWORDS
        )

        # Multi-agent requests are outside Phase 2. Avoid a confident but partial action.
        if is_schedule_request and is_search_request:
            return AgentName.GENERAL
        if is_schedule_request:
            return AgentName.SCHEDULE
        if is_search_request:
            return AgentName.SEARCH
        return AgentName.GENERAL
