"""Pre-execution policy enforcement.

The gate turns a proposed :class:`~guide.types.ToolCall` into ALLOW, BOUND (a revised call
that lies inside the permitted set) or DENY, *before* any tool code runs. Decisions are
derived from the active :class:`Policy` and the tool's declared metadata only; nothing the
proposing agent writes (reasons, self-declared sensitivity) can create a permission.

"Bounding" is a projection onto the permitted set: numeric arguments are clamped to their
interval (Euclidean projection onto a box), and a requested column set is intersected with
the permitted columns (the nearest permitted subset under set difference).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any, Mapping, Protocol, runtime_checkable

from guide.tools import ToolRegistry
from guide.types import Sensitivity, ToolCall


class Decision(str, Enum):
    ALLOW = "ALLOW"
    BOUND = "BOUND"
    DENY = "DENY"


@dataclass(frozen=True)
class PolicyDecision:
    decision: Decision
    call: ToolCall  # the call to execute (== proposal for ALLOW, revised for BOUND)
    rule: str  # stable identifier of the rule that produced the decision
    reason: str

    @property
    def executes(self) -> bool:
        return self.decision is not Decision.DENY


@dataclass(frozen=True)
class Policy:
    policy_id: str
    permitted: Mapping[str, frozenset[str]]  # tool name -> permitted operations
    max_sensitivity: Sensitivity = Sensitivity.INTERNAL
    allow_write: bool = False
    allow_external: bool = False
    numeric_bounds: Mapping[str, tuple[float, float]] = field(default_factory=lambda: {"limit": (1, 100)})
    recipient_domains: frozenset[str] = frozenset()  # empty = any domain (when external allowed)

    def digest(self) -> str:
        doc = {
            "policy_id": self.policy_id,
            "permitted": {k: sorted(v) for k, v in sorted(self.permitted.items())},
            "max_sensitivity": self.max_sensitivity.name,
            "allow_write": self.allow_write,
            "allow_external": self.allow_external,
            "numeric_bounds": {k: list(v) for k, v in sorted(self.numeric_bounds.items())},
            "recipient_domains": sorted(self.recipient_domains),
        }
        return hashlib.sha256(json.dumps(doc, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class PolicyContext:
    run_id: str
    step_id: str
    step_tools: frozenset[str]  # least privilege: tools delegated to this step by the hand-off


@runtime_checkable
class PolicyEngine(Protocol):
    def evaluate(self, call: ToolCall, context: PolicyContext) -> PolicyDecision: ...


def _deny(call: ToolCall, rule: str, reason: str) -> PolicyDecision:
    return PolicyDecision(Decision.DENY, call, rule, reason)


class RulePolicyEngine:
    """Deterministic rule-based gate implementing the proposal's allow / bound / deny semantics."""

    def __init__(self, policy: Policy, registry: ToolRegistry) -> None:
        self.policy = policy
        self.registry = registry

    def evaluate(self, call: ToolCall, context: PolicyContext) -> PolicyDecision:
        p = self.policy
        if not self.registry.has(call.tool):
            return _deny(call, "tool.unknown", f"tool '{call.tool}' is not registered")
        spec = self.registry.get(call.tool).spec
        op = spec.operations.get(call.operation)
        if op is None:
            return _deny(call, "operation.unknown", f"operation '{call.operation}' not offered by {call.tool}")
        if call.tool not in p.permitted or call.operation not in p.permitted[call.tool]:
            return _deny(call, "tool.not_permitted", f"{call.tool}.{call.operation} is not in policy {p.policy_id}")
        if call.tool not in context.step_tools:
            return _deny(call, "tool.not_delegated", f"{call.tool} was not delegated to step {context.step_id}")
        if op.write_effect and not p.allow_write:
            return _deny(call, "write.denied", "policy is read-only")
        if op.external:
            if not p.allow_external:
                return _deny(call, "external.denied", "external sinks are not permitted")
            if p.recipient_domains:
                recipient = str(call.args.get("recipient", ""))
                domain = recipient.rsplit("@", 1)[-1].lower() if "@" in recipient else ""
                if domain not in p.recipient_domains:
                    return _deny(call, "external.recipient_domain", f"recipient domain '{domain}' not allow-listed")

        args: dict[str, Any] = dict(call.args)
        bounded: list[str] = []

        # Sensitivity: derived from tool metadata, never from the proposer.
        if spec.column_sensitivity and spec.columns_param:
            requested = args.get(spec.columns_param)
            all_cols = list(spec.column_sensitivity)
            cols = list(requested) if isinstance(requested, (list, tuple)) and requested else all_cols
            unknown = [c for c in cols if c not in spec.column_sensitivity]
            if unknown:
                valid = [c for c in all_cols if spec.sensitivity_of(c) <= p.max_sensitivity]
                return _deny(call, "argument.unknown_column", f"unknown columns {unknown}; permitted columns: {valid}")
            allowed = [c for c in cols if spec.sensitivity_of(c) <= p.max_sensitivity]
            if not allowed:
                return _deny(call, "sensitivity.exceeded", "every requested column exceeds the clearance")
            removed = [c for c in cols if c not in allowed]
            if removed or not requested:
                args[spec.columns_param] = allowed
            if removed:
                bounded.append(f"columns bounded to clearance {p.max_sensitivity.name} (removed {removed})")
        elif spec.default_sensitivity > p.max_sensitivity:
            return _deny(call, "sensitivity.exceeded", f"{call.tool} data is {spec.default_sensitivity.name}")

        for name, (lo, hi) in p.numeric_bounds.items():
            if name in args:
                try:
                    value = float(args[name])
                except (TypeError, ValueError):
                    return _deny(call, "argument.invalid", f"argument '{name}' is not numeric")
                clamped = min(max(value, lo), hi)
                if clamped != value:
                    args[name] = int(clamped) if float(clamped).is_integer() else clamped
                    bounded.append(f"{name} {value:g}->{clamped:g}")

        revised = replace(call, args=args)
        if bounded:
            return PolicyDecision(Decision.BOUND, revised, "bound", "; ".join(bounded))
        return PolicyDecision(Decision.ALLOW, revised, "allow", "within policy")
