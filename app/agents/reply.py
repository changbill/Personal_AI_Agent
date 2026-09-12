"""What an agent hands back, including which tools actually ran.

Phase 1 and 2 discarded the Strands AgentResult and returned a bare string, so the
request log could only ever report an empty tool list. The tool-call summary is built by
a pure function here so the logging contract is verifiable without an LLM.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToolCall:
    """How often one tool ran during a single agent invocation."""

    name: str
    call_count: int
    success_count: int

    @property
    def failure_count(self) -> int:
        return max(self.call_count - self.success_count, 0)

    @property
    def succeeded(self) -> bool:
        return self.call_count > 0 and self.failure_count == 0


@dataclass(frozen=True)
class AgentReply:
    """One agent response together with its tool usage."""

    text: str
    tool_calls: tuple[ToolCall, ...] = ()

    @property
    def tool_names(self) -> tuple[str, ...]:
        return tuple(call.name for call in self.tool_calls)

    @property
    def all_tools_succeeded(self) -> bool:
        return all(call.succeeded for call in self.tool_calls)


def summarize_tool_calls(tool_metrics: Mapping[str, Any]) -> tuple[ToolCall, ...]:
    """Convert Strands tool metrics into an ordered, loggable summary.

    Accepts the ``tool_metrics`` mapping from ``AgentResult.metrics``. Entries that never
    ran are dropped; the order is by tool name so the log is stable across requests.
    """
    calls = []
    for name in sorted(tool_metrics):
        metrics = tool_metrics[name]
        call_count = int(getattr(metrics, "call_count", 0))
        if call_count <= 0:
            continue
        calls.append(
            ToolCall(
                name=name,
                call_count=call_count,
                success_count=int(getattr(metrics, "success_count", 0)),
            )
        )
    return tuple(calls)
