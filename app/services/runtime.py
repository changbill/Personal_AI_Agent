"""Process-scoped wiring for the agent stack.

The calendar MCP session is the reason this exists. Starting a calendar server session
per request would add process startup to every chat turn and let two turns race for the
same OAuth token file, so the session is opened once and reused, then closed on shutdown.
"""

import logging
import threading
from dataclasses import dataclass

from app.agents.general_agent import GeneralAgent
from app.agents.orchestrator import Orchestrator
from app.agents.schedule_agent import ScheduleAgent
from app.agents.search_agent import SearchAgent
from app.core.config import Settings
from app.services.calendar_gateway import CalendarGateway, start_calendar_gateway
from app.services.http_client import build_json_fetcher
from app.services.orchestrator_service import OrchestratorService
from app.services.time_service import TimeService, build_today_clock
from app.services.weather_service import WeatherService
from app.tools.calendar_tools import build_calendar_tools
from app.tools.time_tools import build_time_tools
from app.tools.weather_tools import build_weather_tools

logger = logging.getLogger(__name__)


@dataclass
class AgentRuntime:
    """Long-lived dependencies shared by every request."""

    settings: Settings
    calendar_gateway: CalendarGateway
    service: OrchestratorService

    def close(self) -> None:
        """Release the calendar session, if one is open."""
        try:
            self.calendar_gateway.close()
        except Exception:
            logger.exception("calendar_mcp_stop_failed")


def build_runtime(settings: Settings) -> AgentRuntime:
    """Open the calendar session and assemble the orchestrator service."""
    calendar_gateway = start_calendar_gateway(settings.calendar_mcp_url)
    calendar_tools = build_calendar_tools(
        gateway=calendar_gateway,
        calendar_id=settings.calendar_id,
        timezone=settings.timezone,
    )

    fetch = build_json_fetcher()
    weather_tools = build_weather_tools(WeatherService(fetch))
    time_tools = build_time_tools(TimeService(fetch), settings.timezone)

    # Resolves today in AGENT_TIMEZONE rather than the host timezone, which would be
    # wrong for the first nine hours of every Korean day on a UTC host.
    today = build_today_clock(settings.timezone)

    return AgentRuntime(
        settings=settings,
        calendar_gateway=calendar_gateway,
        service=OrchestratorService(
            orchestrator=Orchestrator(),
            general_agent=GeneralAgent(settings, tools=time_tools),
            schedule_agent=ScheduleAgent(settings, tools=calendar_tools, today=today),
            search_agent=SearchAgent(settings, tools=weather_tools, today=today),
        ),
    )


_runtime: AgentRuntime | None = None
_lock = threading.Lock()


def get_runtime() -> AgentRuntime:
    """Return the process runtime, building it on first use.

    Built lazily rather than at startup so the app can be created in tests and the docs
    page can be served without a reachable Ollama or calendar server.
    """
    global _runtime
    with _lock:
        if _runtime is None:
            _runtime = build_runtime(Settings.from_env())
        return _runtime


def close_runtime() -> None:
    """Close and forget the process runtime."""
    global _runtime
    with _lock:
        if _runtime is not None:
            _runtime.close()
            _runtime = None
