"""Open-Meteo weather lookups.

Open-Meteo needs no API key for non-commercial use, which is why it is the first
external information source in this project: a paid or account-bound search API would
break the cost constraint before the agent is even useful.

The HTTP call is injected as a JsonFetcher so the parsing rules can be verified against
recorded payloads without reaching the network in a unit test.
"""

from typing import Any

from app.services import place_directory
from app.services.http_client import JsonFetcher
from app.services.place_directory import Place

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Enough candidates for the preferred country to be present when the top hit is a
# same-named place elsewhere.
GEOCODING_CANDIDATES = 5

CURRENT_VARIABLES = "temperature_2m,relative_humidity_2m,precipitation,weather_code"

WEATHER_CODES = {
    0: "맑음",
    1: "대체로 맑음",
    2: "부분적으로 흐림",
    3: "흐림",
    45: "안개",
    48: "서리 안개",
    51: "약한 이슬비",
    53: "이슬비",
    55: "강한 이슬비",
    61: "약한 비",
    63: "비",
    65: "강한 비",
    71: "약한 눈",
    73: "눈",
    75: "강한 눈",
    80: "소나기",
    81: "강한 소나기",
    82: "매우 강한 소나기",
    95: "천둥번개",
    96: "천둥번개와 우박",
    99: "강한 천둥번개와 우박",
}


class WeatherLookupError(RuntimeError):
    """Raised when a place cannot be resolved or the forecast is unusable."""


def contains_hangul(text: str) -> bool:
    """Tell a Korean query from a romanized one, to know which country to prefer."""
    return any("가" <= character <= "힣" for character in text)


def parse_place(
    payload: dict[str, Any], query: str, prefer_country_code: str | None = None
) -> Place:
    """Pick the best geocoding match, or fail loudly.

    The first result is not always the right one: a Korean query can rank a same-named
    village abroad above the city that was meant, so a preferred country wins when the
    response carries one.
    """
    results = payload.get("results") or []
    if not results:
        raise WeatherLookupError(f"위치를 찾을 수 없습니다: {query}")

    chosen = results[0]
    if prefer_country_code:
        chosen = next(
            (
                result
                for result in results
                if result.get("country_code") == prefer_country_code
            ),
            chosen,
        )
    try:
        return Place(
            name=str(chosen["name"]),
            latitude=float(chosen["latitude"]),
            longitude=float(chosen["longitude"]),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise WeatherLookupError(f"위치 응답을 해석할 수 없습니다: {query}") from error


def format_current_weather(payload: dict[str, Any], place_name: str) -> str:
    """Render the current-conditions block as one short Korean line."""
    current = payload.get("current")
    if not isinstance(current, dict):
        raise WeatherLookupError(f"{place_name}의 현재 날씨 데이터가 없습니다")

    temperature = current.get("temperature_2m")
    if temperature is None:
        raise WeatherLookupError(f"{place_name}의 기온 데이터가 없습니다")

    condition = WEATHER_CODES.get(current.get("weather_code"), "상태 미확인")
    parts = [f"{place_name} 현재 {condition}", f"기온 {temperature}도"]

    humidity = current.get("relative_humidity_2m")
    if humidity is not None:
        parts.append(f"습도 {humidity}%")
    precipitation = current.get("precipitation")
    if precipitation is not None:
        parts.append(f"강수 {precipitation}mm")
    observed_at = current.get("time")
    if observed_at:
        parts.append(f"기준 {observed_at}")
    return ", ".join(parts)


class WeatherService:
    """Resolves a place name and returns its current conditions."""

    def __init__(self, fetch: JsonFetcher) -> None:
        self._fetch = fetch

    def current_weather(self, place: str) -> str:
        query = place.strip()
        if not query:
            raise WeatherLookupError("도시 이름이 비어 있습니다")

        # The directory answers most Korean requests without a geocoding round trip,
        # and answers them correctly where the romanized index does not.
        located = place_directory.lookup(query)
        if located is None:
            korean = contains_hangul(query)
            located = parse_place(
                self._fetch(
                    GEOCODING_URL,
                    {
                        "name": query,
                        "count": GEOCODING_CANDIDATES,
                        "language": "ko",
                        "format": "json",
                    },
                ),
                query,
                prefer_country_code="KR" if korean else None,
            )
        forecast = self._fetch(
            FORECAST_URL,
            {
                "latitude": located.latitude,
                "longitude": located.longitude,
                "current": CURRENT_VARIABLES,
                "timezone": "auto",
            },
        )
        return format_current_weather(forecast, located.name)
