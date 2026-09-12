"""Current date and time, from an external API with a local clock behind it.

Two things live here for one reason each.

`current_time` backs the get_current_time tool. Its source is timeapi.io, which needs no
API key. worldtimeapi.org was the obvious alternative and is sunset: it refuses the
connection outright. A time lookup must never be the thing that fails a request, so a
network error falls back to the local clock and records which source was used.

`build_today_clock` fixes a narrower problem. `date.today()` reads the operating system
timezone, not AGENT_TIMEZONE, so on a UTC host the injected date was wrong from midnight
until 09:00 Korean time. The clock resolves the date in the configured timezone instead,
with no network call, because a date the whole prompt depends on cannot wait on a request.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from app.services.http_client import JsonFetcher

logger = logging.getLogger(__name__)

TIME_API_URL = "https://timeapi.io/api/Time/current/zone"

WEEKDAY_NAMES = ("월", "화", "수", "목", "금", "토", "일")

SOURCE_API = "timeapi.io"
SOURCE_LOCAL = "local"


class TimeLookupError(RuntimeError):
    """Raised when neither the time API nor the local clock can answer."""


def local_now(timezone: str) -> datetime:
    """Return the current moment in the given IANA timezone."""
    try:
        return datetime.now(ZoneInfo(timezone))
    except Exception as error:
        raise TimeLookupError(f"시간대를 해석할 수 없습니다: {timezone}") from error


def build_today_clock(timezone: str) -> Callable[[], date]:
    """Create a clock that reports today in the configured timezone, not the host one."""

    def today() -> date:
        return local_now(timezone).date()

    return today


@dataclass(frozen=True)
class CurrentTime:
    """One resolved moment together with where it came from."""

    moment: datetime
    timezone: str
    source: str

    @property
    def from_api(self) -> bool:
        return self.source == SOURCE_API


def parse_time_api(payload: dict[str, Any], timezone: str) -> datetime:
    """Build a moment from the timeapi.io discrete fields.

    The discrete integers are used rather than the dateTime string because that string
    carries seven fractional digits, which is outside what this project wants to depend on.
    """
    try:
        return datetime(
            year=int(payload["year"]),
            month=int(payload["month"]),
            day=int(payload["day"]),
            hour=int(payload["hour"]),
            minute=int(payload["minute"]),
            second=int(payload.get("seconds", 0)),
            tzinfo=ZoneInfo(timezone),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise TimeLookupError(f"시간 응답을 해석할 수 없습니다: {timezone}") from error


def format_current_time(current: CurrentTime) -> str:
    """Render one moment as a single Korean line for the model to read."""
    moment = current.moment
    weekday = WEEKDAY_NAMES[moment.weekday()]
    return (
        f"{moment.date().isoformat()} ({weekday}) "
        f"{moment.strftime('%H:%M')}, 시간대 {current.timezone}"
    )


class TimeService:
    """Resolves the current moment, preferring the external API."""

    def __init__(
        self,
        fetch: JsonFetcher,
        clock: Callable[[str], datetime] = local_now,
    ) -> None:
        self._fetch = fetch
        self._clock = clock

    def current_time(self, timezone: str) -> CurrentTime:
        """Read the current moment, falling back to the local clock on any API failure."""
        try:
            payload = self._fetch(TIME_API_URL, {"timeZone": timezone})
            return CurrentTime(
                moment=parse_time_api(payload, timezone),
                timezone=timezone,
                source=SOURCE_API,
            )
        except Exception:
            # Logged rather than raised: an unreachable time API must not break a reply,
            # and the fallback needs to be visible when the answer is later questioned.
            logger.warning("time_api_unavailable_using_local_clock", exc_info=True)

        return CurrentTime(
            moment=self._clock(timezone), timezone=timezone, source=SOURCE_LOCAL
        )
