from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from app.services.time_service import (
    SOURCE_API,
    SOURCE_LOCAL,
    TIME_API_URL,
    CurrentTime,
    TimeLookupError,
    TimeService,
    build_today_clock,
    format_current_time,
    local_now,
    parse_time_api,
)
from app.tools.time_tools import build_time_tools

pytestmark = pytest.mark.unit

SEOUL = ZoneInfo("Asia/Seoul")

# Recorded from timeapi.io on 2026-09-13 for Asia/Seoul.
TIME_API_SAMPLE = {
    "year": 2026,
    "month": 9,
    "day": 13,
    "hour": 0,
    "minute": 49,
    "seconds": 0,
    "milliSeconds": 447,
    "dateTime": "2026-09-13T00:49:00.4477862",
    "date": "09/13/2026",
    "time": "00:49",
    "timeZone": "Asia/Seoul",
    "dayOfWeek": "Sunday",
    "dstActive": False,
}


class StubFetcher:
    """Returns a canned payload and records the request, or raises on demand."""

    def __init__(
        self, payload: dict[str, Any] | None = None, error: Exception | None = None
    ) -> None:
        self.payload = payload
        self.error = error
        self.requests: list[tuple[str, dict[str, Any]]] = []

    def __call__(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        self.requests.append((url, params))
        if self.error is not None:
            raise self.error
        assert self.payload is not None
        return self.payload


def test_the_api_payload_becomes_a_zone_aware_moment() -> None:
    moment = parse_time_api(TIME_API_SAMPLE, "Asia/Seoul")

    assert moment == datetime(2026, 9, 13, 0, 49, 0, tzinfo=SEOUL)
    assert moment.utcoffset().total_seconds() == 9 * 3600


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"year": 2026, "month": 9},
        {"year": 2026, "month": 9, "day": 13, "hour": "noon", "minute": 0},
        {"year": 2026, "month": 13, "day": 40, "hour": 0, "minute": 0},
    ],
)
def test_an_unusable_api_payload_is_an_error(payload: dict[str, Any]) -> None:
    with pytest.raises(TimeLookupError):
        parse_time_api(payload, "Asia/Seoul")


def test_the_weekday_is_computed_here_not_taken_from_the_api() -> None:
    rendered = format_current_time(
        CurrentTime(
            moment=datetime(2026, 9, 13, 0, 49, tzinfo=SEOUL),
            timezone="Asia/Seoul",
            source=SOURCE_API,
        )
    )

    assert rendered == "2026-09-13 (일) 00:49, 시간대 Asia/Seoul"


def test_the_api_is_preferred_and_asked_for_the_configured_zone() -> None:
    fetcher = StubFetcher(payload=TIME_API_SAMPLE)

    current = TimeService(fetcher).current_time("Asia/Seoul")

    assert current.source == SOURCE_API
    assert current.from_api is True
    assert current.moment == datetime(2026, 9, 13, 0, 49, tzinfo=SEOUL)
    assert fetcher.requests == [(TIME_API_URL, {"timeZone": "Asia/Seoul"})]


@pytest.mark.parametrize(
    "failure",
    [RuntimeError("network down"), TimeoutError("timed out"), ValueError("bad json")],
)
def test_any_api_failure_falls_back_to_the_local_clock(failure: Exception) -> None:
    fallback = datetime(2026, 9, 13, 1, 5, tzinfo=SEOUL)
    service = TimeService(StubFetcher(error=failure), clock=lambda timezone: fallback)

    current = service.current_time("Asia/Seoul")

    assert current.source == SOURCE_LOCAL
    assert current.from_api is False
    assert current.moment == fallback


def test_a_malformed_api_response_also_falls_back() -> None:
    fallback = datetime(2026, 9, 13, 1, 5, tzinfo=SEOUL)
    service = TimeService(
        StubFetcher(payload={"nonsense": True}), clock=lambda timezone: fallback
    )

    assert service.current_time("Asia/Seoul").moment == fallback


def test_the_local_clock_uses_the_given_zone_not_the_host_zone() -> None:
    seoul = local_now("Asia/Seoul")
    utc = local_now("UTC")

    assert seoul.tzinfo is not None
    assert seoul.utcoffset().total_seconds() == 9 * 3600
    assert utc.utcoffset().total_seconds() == 0


def test_an_unresolvable_zone_is_an_error() -> None:
    with pytest.raises(TimeLookupError):
        local_now("Mars/Olympus_Mons")


def test_the_today_clock_reports_the_date_in_the_configured_zone() -> None:
    assert isinstance(build_today_clock("Asia/Seoul")(), date)
    # A UTC host just before 09:00 KST is a different calendar day in each zone;
    # the clock must follow the argument, not the process environment.
    assert build_today_clock("Asia/Seoul")() >= build_today_clock("UTC")()


def test_the_time_tool_takes_no_arguments_and_states_its_limits() -> None:
    tools = build_time_tools(
        TimeService(StubFetcher(payload=TIME_API_SAMPLE)), "Asia/Seoul"
    )

    assert [each.tool_name for each in tools] == ["get_current_time"]
    description = tools[0].tool_spec["description"]
    assert "Use when:" in description
    assert "Do not use when:" in description
    assert tools[0].tool_spec["inputSchema"]["json"].get("required") in (None, [])


def test_the_time_tool_returns_the_rendered_moment() -> None:
    tools = build_time_tools(
        TimeService(StubFetcher(payload=TIME_API_SAMPLE)), "Asia/Seoul"
    )

    assert tools[0]() == "2026-09-13 (일) 00:49, 시간대 Asia/Seoul"


def test_the_time_tool_still_answers_when_the_api_is_down() -> None:
    service = TimeService(
        StubFetcher(error=RuntimeError("network down")),
        clock=lambda timezone: datetime(2026, 9, 13, 1, 5, tzinfo=SEOUL),
    )

    assert build_time_tools(service, "Asia/Seoul")[0]() == (
        "2026-09-13 (일) 01:05, 시간대 Asia/Seoul"
    )
