"""The one place the application reaches the network for JSON.

Every external-information service takes a JsonFetcher rather than calling httpx itself,
so the parsing and fallback rules stay verifiable offline in a unit test.
"""

from typing import Any, Protocol

DEFAULT_TIMEOUT_SECONDS = 5.0


class HttpFetchError(RuntimeError):
    """Raised when a JSON document cannot be fetched or is not an object."""


class JsonFetcher(Protocol):
    """Fetches one JSON document."""

    def __call__(self, url: str, params: dict[str, Any]) -> dict[str, Any]: ...


def build_json_fetcher(timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS) -> JsonFetcher:
    """Create the real network fetcher. httpx is imported lazily so tests stay offline."""
    import httpx

    def fetch(url: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            response = httpx.get(url, params=params, timeout=timeout_seconds)
            response.raise_for_status()
            payload = response.json()
        except Exception as error:
            raise HttpFetchError(f"{url} 호출이 실패했습니다: {error}") from error
        if not isinstance(payload, dict):
            raise HttpFetchError(f"예상하지 못한 응답 형식입니다: {url}")
        return payload

    return fetch
