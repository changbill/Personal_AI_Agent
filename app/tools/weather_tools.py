"""The single external-information tool the Search Agent gets in Phase 3-A.

Web and place search need a paid or account-bound provider, so they are deferred to
Phase 3-B. Registering one tool here keeps the Search Agent choice unambiguous.
"""

from typing import Any

from strands import tool

from app.services.weather_service import WeatherService

WEATHER_TOOL_NAMES = ("get_weather",)


def build_weather_tools(service: WeatherService) -> list[Any]:
    """Bind the weather tool to one weather service."""

    @tool(
        name="get_weather",
        description=(
            "지정한 도시의 현재 날씨를 조회한다. "
            "Use when: 사용자가 특정 지역의 날씨·기온·강수를 물어볼 때. "
            "Do not use when: 과거나 여러 날 뒤의 예보를 물어볼 때. 날씨와 무관한 검색 요청일 때."
        ),
    )
    def get_weather(city: str) -> str:
        """Read current conditions for one city.

        Args:
            city: 도시 이름. 예: 인천, Seoul.
        """
        return service.current_weather(city)

    return [get_weather]
