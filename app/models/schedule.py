"""Schedule inputs validated by the application, never trusted from the model.

The local model proposes tool arguments; every rule that decides whether a calendar
write is well-formed lives here so it can be tested without an LLM or an MCP server.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

MAX_PERIOD_DAYS = 31
"""Upper bound on one schedule query, so a single lookup cannot flood the context window."""

MAX_EVENT_DAYS = 30
"""Upper bound on the duration of one event. Longer spans are model mistakes."""

MAX_SUMMARY_LENGTH = 200
MAX_TEXT_LENGTH = 2_000


class ScheduleInputError(ValueError):
    """Raised when a proposed tool argument violates an application rule."""


def _require_text(value: str | None, field: str, limit: int) -> str:
    if value is None or not value.strip():
        raise ScheduleInputError(f"{field}는 비어 있을 수 없습니다")
    text = value.strip()
    if len(text) > limit:
        raise ScheduleInputError(f"{field}는 {limit}자를 넘을 수 없습니다")
    return text


def _optional_text(value: str | None, field: str, limit: int) -> str | None:
    if value is None or not value.strip():
        return None
    return _require_text(value, field, limit)


def parse_iso_date(value: str, field: str) -> date:
    """Parse a strict YYYY-MM-DD value, rejecting anything else."""
    text = _require_text(value, field, 10)
    try:
        return date.fromisoformat(text)
    except ValueError as error:
        raise ScheduleInputError(
            f"{field}는 YYYY-MM-DD 형식이어야 합니다: {text}"
        ) from error


def parse_iso_datetime(value: str, field: str) -> datetime:
    """Parse an ISO 8601 datetime, rejecting date-only and malformed values."""
    text = _require_text(value, field, 40)
    if len(text) <= 10:
        raise ScheduleInputError(f"{field}에는 시각이 포함되어야 합니다: {text}")
    try:
        return datetime.fromisoformat(text)
    except ValueError as error:
        raise ScheduleInputError(
            f"{field}는 ISO 8601 날짜시간이어야 합니다: {text}"
        ) from error


@dataclass(frozen=True)
class SchedulePeriod:
    """An inclusive day range to read from the calendar."""

    start: date
    end: date

    @classmethod
    def parse(cls, start_date: str, end_date: str) -> "SchedulePeriod":
        start = parse_iso_date(start_date, "start_date")
        end = parse_iso_date(end_date, "end_date")
        if end < start:
            raise ScheduleInputError("end_date는 start_date보다 이를 수 없습니다")
        if (end - start) > timedelta(days=MAX_PERIOD_DAYS - 1):
            raise ScheduleInputError(f"조회 기간은 최대 {MAX_PERIOD_DAYS}일입니다")
        return cls(start=start, end=end)

    def to_arguments(self, calendar_id: str, timezone: str) -> dict[str, Any]:
        """Build list-events arguments covering the whole inclusive range."""
        return {
            "calendarId": calendar_id,
            "timeMin": f"{self.start.isoformat()}T00:00:00",
            "timeMax": f"{(self.end + timedelta(days=1)).isoformat()}T00:00:00",
            "timeZone": timezone,
        }


@dataclass(frozen=True)
class ScheduleDraft:
    """A new event to create."""

    summary: str
    start: datetime
    end: datetime
    description: str | None = None
    location: str | None = None

    @classmethod
    def parse(
        cls,
        summary: str,
        start_datetime: str,
        end_datetime: str,
        description: str | None = None,
        location: str | None = None,
    ) -> "ScheduleDraft":
        start = parse_iso_datetime(start_datetime, "start_datetime")
        end = parse_iso_datetime(end_datetime, "end_datetime")
        if end <= start:
            raise ScheduleInputError("end_datetime은 start_datetime보다 늦어야 합니다")
        if (end - start) > timedelta(days=MAX_EVENT_DAYS):
            raise ScheduleInputError(f"일정 길이는 최대 {MAX_EVENT_DAYS}일입니다")
        return cls(
            summary=_require_text(summary, "summary", MAX_SUMMARY_LENGTH),
            start=start,
            end=end,
            description=_optional_text(description, "description", MAX_TEXT_LENGTH),
            location=_optional_text(location, "location", MAX_TEXT_LENGTH),
        )

    def to_arguments(self, calendar_id: str, timezone: str) -> dict[str, Any]:
        """Build create-event arguments, omitting fields the user did not give."""
        arguments: dict[str, Any] = {
            "calendarId": calendar_id,
            "summary": self.summary,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "timeZone": timezone,
        }
        if self.description is not None:
            arguments["description"] = self.description
        if self.location is not None:
            arguments["location"] = self.location
        return arguments


@dataclass(frozen=True)
class ScheduleEdit:
    """A partial change to an existing event."""

    event_id: str
    summary: str | None = None
    start: datetime | None = None
    end: datetime | None = None
    location: str | None = None

    @classmethod
    def parse(
        cls,
        event_id: str,
        summary: str | None = None,
        start_datetime: str | None = None,
        end_datetime: str | None = None,
        location: str | None = None,
    ) -> "ScheduleEdit":
        start = (
            parse_iso_datetime(start_datetime, "start_datetime")
            if start_datetime and start_datetime.strip()
            else None
        )
        end = (
            parse_iso_datetime(end_datetime, "end_datetime")
            if end_datetime and end_datetime.strip()
            else None
        )
        # Google rejects a one-sided time change, so require the pair together.
        if (start is None) != (end is None):
            raise ScheduleInputError(
                "시각을 바꾸려면 start_datetime과 end_datetime을 함께 주어야 합니다"
            )
        if start is not None and end is not None and end <= start:
            raise ScheduleInputError("end_datetime은 start_datetime보다 늦어야 합니다")
        edit = cls(
            event_id=_require_text(event_id, "event_id", MAX_TEXT_LENGTH),
            summary=_optional_text(summary, "summary", MAX_SUMMARY_LENGTH),
            start=start,
            end=end,
            location=_optional_text(location, "location", MAX_TEXT_LENGTH),
        )
        if edit.summary is None and edit.start is None and edit.location is None:
            raise ScheduleInputError("변경할 항목을 최소 하나는 주어야 합니다")
        return edit

    def to_arguments(self, calendar_id: str, timezone: str) -> dict[str, Any]:
        """Build update-event arguments carrying only the requested changes."""
        arguments: dict[str, Any] = {
            "calendarId": calendar_id,
            "eventId": self.event_id,
            "timeZone": timezone,
        }
        if self.summary is not None:
            arguments["summary"] = self.summary
        if self.start is not None and self.end is not None:
            arguments["start"] = self.start.isoformat()
            arguments["end"] = self.end.isoformat()
        if self.location is not None:
            arguments["location"] = self.location
        return arguments


@dataclass(frozen=True)
class ScheduleDeletion:
    """An event to remove."""

    event_id: str

    @classmethod
    def parse(cls, event_id: str) -> "ScheduleDeletion":
        return cls(event_id=_require_text(event_id, "event_id", MAX_TEXT_LENGTH))

    def to_arguments(self, calendar_id: str) -> dict[str, Any]:
        """Build delete-event arguments."""
        return {"calendarId": calendar_id, "eventId": self.event_id}
