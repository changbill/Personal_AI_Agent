from dataclasses import dataclass

import pytest

from app.agents.reply import AgentReply, ToolCall, summarize_tool_calls

pytestmark = pytest.mark.unit


@dataclass
class StubToolMetrics:
    """Same shape as strands.telemetry.metrics.ToolMetrics for the fields we read."""

    call_count: int
    success_count: int


def test_no_metrics_summarize_to_no_tool_calls() -> None:
    assert summarize_tool_calls({}) == ()


def test_tools_that_never_ran_are_dropped() -> None:
    metrics = {"get_schedule": StubToolMetrics(call_count=0, success_count=0)}

    assert summarize_tool_calls(metrics) == ()


def test_calls_are_summarized_in_name_order() -> None:
    metrics = {
        "get_weather": StubToolMetrics(call_count=1, success_count=1),
        "get_schedule": StubToolMetrics(call_count=2, success_count=1),
    }

    assert summarize_tool_calls(metrics) == (
        ToolCall(name="get_schedule", call_count=2, success_count=1),
        ToolCall(name="get_weather", call_count=1, success_count=1),
    )


def test_a_partially_failed_tool_is_reported_as_failed() -> None:
    call = ToolCall(name="get_schedule", call_count=2, success_count=1)

    assert call.failure_count == 1
    assert call.succeeded is False


def test_a_fully_successful_tool_is_reported_as_succeeded() -> None:
    call = ToolCall(name="get_schedule", call_count=2, success_count=2)

    assert call.failure_count == 0
    assert call.succeeded is True


def test_a_reply_without_tools_reports_an_empty_tool_list() -> None:
    reply = AgentReply(text="안녕하세요")

    assert reply.tool_names == ()
    assert reply.all_tools_succeeded is True


def test_a_reply_exposes_tool_names_and_overall_success() -> None:
    reply = AgentReply(
        text="일정 1건",
        tool_calls=(
            ToolCall(name="get_schedule", call_count=1, success_count=1),
            ToolCall(name="create_schedule", call_count=1, success_count=0),
        ),
    )

    assert reply.tool_names == ("get_schedule", "create_schedule")
    assert reply.all_tools_succeeded is False
