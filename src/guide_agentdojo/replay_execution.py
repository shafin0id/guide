"""Apply the executable call returned by the policy during offline replay."""
from __future__ import annotations

from typing import Any

from guide.policy import PolicyDecision


def execute_admitted_decision(runtime: Any, environment: Any, decision: PolicyDecision) -> tuple[Any, Any]:
    """Never execute a denied proposal; honor argument transformations for BOUND."""
    if not decision.executes:
        raise ValueError("cannot execute a denied replay call")
    return runtime.run_function(environment, decision.call.operation, dict(decision.call.args))
