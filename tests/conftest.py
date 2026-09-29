"""Shared helpers: a scripted multi-agent 'model' used only as a deterministic test double."""

from __future__ import annotations

import json
from typing import Any, Callable, Sequence

import pytest

from guide.types import ChatMessage


def agent_of(messages: Sequence[ChatMessage]) -> str:
    return messages[0].content.split(",", 1)[0].removeprefix("You are ").strip()


def tool_results(messages: Sequence[ChatMessage]) -> list[Any]:
    out = []
    for m in messages:
        if m.role == "user" and m.content.startswith("TOOL RESULTS"):
            out.append(json.loads(m.content.split("\n", 1)[1].rsplit("\nContinue", 1)[0]))
    return out


def reply(tool_calls: list[dict] | None = None, output: Any = None, confidence: float = 0.9) -> str:
    return json.dumps({"tool_calls": tool_calls or [], "output": output, "confidence": confidence})


def make_script(
    retrieve_call: dict,
    final_output: dict | Callable[[Sequence[ChatMessage]], dict],
    report_calls: list[dict] | None = None,
) -> Callable[[Sequence[ChatMessage]], str]:
    """retriever: one tool call then echo results; analyst: echo; reporter: optional calls then final."""

    def script(messages: Sequence[ChatMessage]) -> str:
        agent = agent_of(messages)
        results = tool_results(messages)
        if agent.startswith("retriever"):
            if not results:
                return reply([retrieve_call])
            return reply(output={"records": results[-1]})
        if agent.startswith("analyst"):
            return reply(output={"findings": messages[-1].content[-400:]})
        if report_calls and not results:
            return reply(report_calls)
        return reply(output=final_output(messages) if callable(final_output) else final_output)

    return script


@pytest.fixture
def v001_final() -> dict:
    return {"vendor_id": "V-001", "delivery_sla_days": 5, "uptime_guarantee_pct": 99.95, "compliance_tier": "ISO27001"}
