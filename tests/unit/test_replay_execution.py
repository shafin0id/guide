from typing import Any

import pytest

from guide.policy import Decision, PolicyDecision
from guide.types import ToolCall
from guide_agentdojo.replay_execution import execute_admitted_decision


class RecordingRuntime:
    def __init__(self) -> None:
        self.calls: list[tuple[Any, str, dict[str, Any]]] = []

    def run_function(self, env: Any, name: str, args: dict[str, Any]) -> tuple[Any, Any]:
        self.calls.append((env, name, args))
        return {"amount": args["amount"]}, None


def test_bound_replay_executes_reduced_amount() -> None:
    rt = RecordingRuntime()
    bounded = ToolCall("transfer", "transfer", {"amount": 10}, "agent")
    decision = PolicyDecision(Decision.BOUND, bounded, "limit", "reduced from 100")
    result, error = execute_admitted_decision(rt, "sandbox", decision)
    assert rt.calls == [("sandbox", "transfer", {"amount": 10})]
    assert result == {"amount": 10}
    assert error is None


def test_denied_replay_has_no_side_effect() -> None:
    rt = RecordingRuntime()
    call = ToolCall("transfer", "transfer", {"amount": 100}, "agent")
    with pytest.raises(ValueError, match="denied"):
        execute_admitted_decision(rt, "sandbox", PolicyDecision(Decision.DENY, call, "deny", "blocked"))
    assert rt.calls == []
