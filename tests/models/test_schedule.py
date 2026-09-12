import pytest

from app.models.schedule import (
    MAX_EVENT_DAYS,
    MAX_PERIOD_DAYS,
    ScheduleDeletion,
    ScheduleDraft,
    ScheduleEdit,
    ScheduleInputError,
    SchedulePeriod,
)

pytestmark = pytest.mark.unit


def test_period_covers_an_inclusive_range_as_a_half_open_window() -> None:
    period = SchedulePeriod.parse("2026-09-12", "2026-09-13")

    assert period.to_arguments("primary", "Asia/Seoul") == {
        "calendarId": "primary",
        "timeMin": "2026-09-12T00:00:00",
        "timeMax": "2026-09-14T00:00:00",
        "timeZone": "Asia/Seoul",
    }


def test_period_accepts_a_single_day() -> None:
    period = SchedulePeriod.parse("2026-09-12", "2026-09-12")

    arguments = period.to_arguments("primary", "Asia/Seoul")
    assert arguments["timeMin"] == "2026-09-12T00:00:00"
    assert arguments["timeMax"] == "2026-09-13T00:00:00"


@pytest.mark.parametrize(
    ("start_date", "end_date"),
    [
        ("2026-09-13", "2026-09-12"),
        ("2026-09-12", ""),
        ("12/09/2026", "2026-09-12"),
        ("2026-09-32", "2026-09-32"),
        ("2026-09-12T10:00:00", "2026-09-12T11:00:00"),
    ],
)
def test_period_rejects_malformed_or_reversed_input(
    start_date: str, end_date: str
) -> None:
    with pytest.raises(ScheduleInputError):
        SchedulePeriod.parse(start_date, end_date)


def test_period_rejects_a_range_longer_than_the_cap() -> None:
    with pytest.raises(ScheduleInputError):
        SchedulePeriod.parse("2026-01-01", f"2026-02-{MAX_PERIOD_DAYS:02d}")


def test_draft_omits_fields_the_user_did_not_give() -> None:
    draft = ScheduleDraft.parse(
        summary="  치과  ",
        start_datetime="2026-09-12T15:00:00",
        end_datetime="2026-09-12T16:00:00",
        description="   ",
    )

    assert draft.summary == "치과"
    assert draft.to_arguments("primary", "Asia/Seoul") == {
        "calendarId": "primary",
        "summary": "치과",
        "start": "2026-09-12T15:00:00",
        "end": "2026-09-12T16:00:00",
        "timeZone": "Asia/Seoul",
    }


def test_draft_includes_optional_fields_when_present() -> None:
    draft = ScheduleDraft.parse(
        summary="회의",
        start_datetime="2026-09-12T15:00:00",
        end_datetime="2026-09-12T16:00:00",
        description="분기 검토",
        location="본사 3층",
    )

    arguments = draft.to_arguments("primary", "Asia/Seoul")
    assert arguments["description"] == "분기 검토"
    assert arguments["location"] == "본사 3층"


@pytest.mark.parametrize(
    ("summary", "start_datetime", "end_datetime"),
    [
        ("", "2026-09-12T15:00:00", "2026-09-12T16:00:00"),
        ("회의", "2026-09-12T16:00:00", "2026-09-12T15:00:00"),
        ("회의", "2026-09-12T15:00:00", "2026-09-12T15:00:00"),
        ("회의", "2026-09-12", "2026-09-13"),
        ("회의", "내일 3시", "내일 4시"),
    ],
)
def test_draft_rejects_invalid_input(
    summary: str, start_datetime: str, end_datetime: str
) -> None:
    with pytest.raises(ScheduleInputError):
        ScheduleDraft.parse(summary, start_datetime, end_datetime)


def test_draft_rejects_an_event_longer_than_the_cap() -> None:
    with pytest.raises(ScheduleInputError):
        ScheduleDraft.parse(
            "장기 일정",
            "2026-01-01T00:00:00",
            f"2026-02-{MAX_EVENT_DAYS:02d}T00:00:00",
        )


def test_edit_sends_only_the_requested_changes() -> None:
    edit = ScheduleEdit.parse(event_id="evt-1", summary="새 제목")

    assert edit.to_arguments("primary", "Asia/Seoul") == {
        "calendarId": "primary",
        "eventId": "evt-1",
        "timeZone": "Asia/Seoul",
        "summary": "새 제목",
    }


def test_edit_sends_both_times_together() -> None:
    edit = ScheduleEdit.parse(
        event_id="evt-1",
        start_datetime="2026-09-12T15:00:00",
        end_datetime="2026-09-12T16:00:00",
    )

    arguments = edit.to_arguments("primary", "Asia/Seoul")
    assert arguments["start"] == "2026-09-12T15:00:00"
    assert arguments["end"] == "2026-09-12T16:00:00"
    assert "summary" not in arguments


def test_edit_rejects_a_one_sided_time_change() -> None:
    with pytest.raises(ScheduleInputError):
        ScheduleEdit.parse(event_id="evt-1", start_datetime="2026-09-12T15:00:00")


def test_edit_rejects_a_request_that_changes_nothing() -> None:
    with pytest.raises(ScheduleInputError):
        ScheduleEdit.parse(event_id="evt-1")


def test_edit_requires_an_event_id() -> None:
    with pytest.raises(ScheduleInputError):
        ScheduleEdit.parse(event_id="   ", summary="새 제목")


def test_deletion_requires_an_event_id() -> None:
    assert ScheduleDeletion.parse("evt-1").to_arguments("primary") == {
        "calendarId": "primary",
        "eventId": "evt-1",
    }

    with pytest.raises(ScheduleInputError):
        ScheduleDeletion.parse("")
