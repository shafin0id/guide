"""Policy generation for AgentDojo suites under GUIDE containment."""

from __future__ import annotations

from collections.abc import Iterable

from agentdojo.functions_runtime import Function

from guide.policy import Policy
from guide.types import Sensitivity


def build_suite_policy(suite_name: str, functions: Iterable[Function]) -> Policy:
    """Constructs a Policy permitting all functions in the suite."""
    permitted: dict[str, frozenset[str]] = {
        f.name: frozenset({f.name}) for f in functions
    }
    return Policy(
        policy_id=f"policy-dojo-{suite_name}",
        permitted=permitted,
        max_sensitivity=Sensitivity.RESTRICTED,
        allow_write=True,
        allow_external=True,
        numeric_bounds={"limit": (1, 100)},
    )
