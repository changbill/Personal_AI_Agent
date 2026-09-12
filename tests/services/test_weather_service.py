from typing import Any

import pytest

from app.services.weather_service import (
    FORECAST_URL,
    GEOCODING_URL,
    WeatherLookupError,
    WeatherService,
    format_current_weather,
    parse_place,
)
from app.tools.weather_tools import build_weather_tools

pytestmark = pytest.mark.unit

GEOCODING_SAMPLE = {
    "results": [
        {
            "name": "인천",
            "latitude": 37.45646,
            "longitude": 126.70515,
            "country": "대한민국",
        }
    ]
}

FORECAST_SAMPLE = {
    "current": {
        "time": "2026-09-12T14:00",
        "temperature_2m": 24.3,
        "relative_humidity_2m": 68,
        "precipitation": 0.0,
        "weather_code": 3,
    }
}


class StubFetcher:
    """Returns a canned payload per URL and records the query it was given."""

    def __init__(self, payloads: dict[str, dict[str, Any]]) -> None:
        self.payloads = payloads
        self.requests: list[tuple[str, dict[str, Any]]] = []

    def __call__(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        self.requests.append((url, params))
        return self.payloads[url]


def test_the_first_geocoding_match_is_used() -> None:
    place = parse_place(GEOCODING_SAMPLE, "인천")

    assert place.name == "인천"
    assert place.latitude == pytest.approx(37.45646)


def test_a_place_with_no_match_is_an_error() -> None:
    with pytest.raises(WeatherLookupError, match="위치를 찾을 수 없습니다"):
        parse_place({"results": []}, "없는도시")


def test_a_malformed_geocoding_entry_is_an_error() -> None:
    with pytest.raises(WeatherLookupError):
        parse_place({"results": [{"name": "인천"}]}, "인천")


def test_current_conditions_render_as_one_korean_line() -> None:
    rendered = format_current_weather(FORECAST_SAMPLE, "인천")

    assert rendered == (
        "인천 현재 흐림, 기온 24.3도, 습도 68%, 강수 0.0mm, 기준 2026-09-12T14:00"
    )


def test_an_unknown_weather_code_still_renders() -> None:
    rendered = format_current_weather(
        {"current": {"temperature_2m": 10, "weather_code": 1234}}, "인천"
    )

    assert "상태 미확인" in rendered
    assert "기온 10도" in rendered


@pytest.mark.parametrize(
    "payload",
    [{}, {"current": None}, {"current": {"weather_code": 0}}],
)
def test_a_forecast_without_usable_data_is_an_error(payload: dict[str, Any]) -> None:
    with pytest.raises(WeatherLookupError):
        format_current_weather(payload, "인천")


def test_a_place_outside_the_directory_is_geocoded_then_forecast() -> None:
    fetcher = StubFetcher(
        {GEOCODING_URL: GEOCODING_SAMPLE, FORECAST_URL: FORECAST_SAMPLE}
    )

    result = WeatherService(fetcher).current_weather("  도쿄  ")

    assert "인천 현재 흐림" in result
    assert [url for url, _ in fetcher.requests] == [GEOCODING_URL, FORECAST_URL]
    assert fetcher.requests[0][1]["name"] == "도쿄"
    assert fetcher.requests[1][1]["latitude"] == pytest.approx(37.45646)


def test_a_korean_city_skips_geocoding_and_uses_the_directory_coordinate() -> None:
    fetcher = StubFetcher({FORECAST_URL: FORECAST_SAMPLE})

    result = WeatherService(fetcher).current_weather("  서울특별시  ")

    assert "서울 현재 흐림" in result
    assert [url for url, _ in fetcher.requests] == [FORECAST_URL]
    assert fetcher.requests[0][1]["latitude"] == pytest.approx(37.5660)


def test_a_korean_query_prefers_a_korean_result_over_a_higher_ranked_foreign_one() -> (
    None
):
    payload = {
        "results": [
            {
                "name": "Séoul",
                "latitude": 6.0,
                "longitude": 12.0,
                "country_code": "CM",
            },
            {
                "name": "학동",
                "latitude": 37.5,
                "longitude": 127.0,
                "country_code": "KR",
            },
        ]
    }

    place = parse_place(payload, "학동", prefer_country_code="KR")

    assert place.name == "학동"


def test_without_a_preferred_country_the_first_result_still_wins() -> None:
    payload = {
        "results": [
            {"name": "Paris", "latitude": 48.9, "longitude": 2.3, "country_code": "FR"},
            {
                "name": "파리",
                "latitude": 37.5,
                "longitude": 127.0,
                "country_code": "KR",
            },
        ]
    }

    assert parse_place(payload, "Paris").name == "Paris"


def test_a_blank_city_never_reaches_the_network() -> None:
    fetcher = StubFetcher({})

    with pytest.raises(WeatherLookupError):
        WeatherService(fetcher).current_weather("   ")

    assert fetcher.requests == []


def test_the_weather_tool_is_the_only_search_tool_and_states_its_limits() -> None:
    fetcher = StubFetcher(
        {GEOCODING_URL: GEOCODING_SAMPLE, FORECAST_URL: FORECAST_SAMPLE}
    )
    tools = build_weather_tools(WeatherService(fetcher))

    assert [each.tool_name for each in tools] == ["get_weather"]
    description = tools[0].tool_spec["description"]
    assert "Use when:" in description
    assert "Do not use when:" in description
    assert "인천 현재 흐림" in tools[0](city="인천")
