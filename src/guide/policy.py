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
import math
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from guide.tools import ToolRegistry
from guide.types import Sensitivity, ToolCall


def normalize_recipient(raw: Any) -> str | None:
    """Return normalized single destination identifier, or ``None`` if malformed/smuggled.

    Rejects multi-recipient delimiters (commas, semicolons, angle brackets) and all Unicode
    control/format characters (ASCII controls including NUL, newlines, zero-width, bidi overrides).
    """
    if raw is None or isinstance(raw, bool | list | tuple | dict | set | frozenset):
        return None
    addr = unicodedata.normalize("NFKC", str(raw)).strip().lower()
    if (
        not addr
        or any(ch in addr for ch in (",", ";", "<", ">", "\n", "\r", "\t"))
        or any(unicodedata.category(ch)[0] == "C" for ch in addr)
    ):
        return None
    return addr


def parse_single_recipient(raw: Any) -> tuple[str, str] | None:
    """Return ``(normalized_address, domain)`` for a single well-formed email recipient, or ``None``.

    Rejects multi-recipient smuggling (commas, semicolons, angle brackets, internal whitespace,
    control/format chars, or multiple ``@`` signs) while normalizing surrounding whitespace, case, and NFKC.
    """
    addr = normalize_recipient(raw)
    if addr is None or any(ch.isspace() for ch in addr):
        return None
    if addr.count("@") != 1:
        return None
    local, domain = addr.split("@", 1)
    if not local or not domain:
        return None
    return addr, domain


def recipient_values(args: Mapping[str, Any], param: str) -> list[Any] | None:
    """Extract recipient element(s) for ``param``; returns ``None`` if absent or empty list."""
    raw = args.get(param)
    if raw is None:
        return None
    if isinstance(raw, list | tuple):
        return list(raw) if raw else None
    return [raw]


def external_recipient_params(control_params: tuple[str, ...]) -> tuple[str, ...]:
    """Parameters subject to policy recipient-domain / exact-recipient allow-lists."""
    return control_params if control_params else ("recipient",)


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
    allowed_columns: Mapping[str, frozenset[str]] = field(default_factory=dict)  # tool -> column allow-list
    allowed_recipients: frozenset[str] = frozenset()  # exact, lower-case; empty = no exact allow-list

    def digest(self) -> str:
        doc = {
            "policy_id": self.policy_id,
            "permitted": {k: sorted(v) for k, v in sorted(self.permitted.items())},
            "max_sensitivity": self.max_sensitivity.name,
            "allow_write": self.allow_write,
            "allow_external": self.allow_external,
            "numeric_bounds": {k: list(v) for k, v in sorted(self.numeric_bounds.items())},
            "recipient_domains": sorted(self.recipient_domains),
            "allowed_columns": {k: sorted(v) for k, v in sorted(self.allowed_columns.items())},
            "allowed_recipients": sorted(self.allowed_recipients),
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
            if p.recipient_domains or p.allowed_recipients:
                norm_domains = frozenset(unicodedata.normalize("NFKC", d).strip().lower() for d in p.recipient_domains)
                norm_exact = frozenset(unicodedata.normalize("NFKC", a).strip().lower() for a in p.allowed_recipients)
                rcpt_params = external_recipient_params(op.control_params)
                any_present = False
                for param in rcpt_params:
                    vals = recipient_values(call.args, param)
                    if vals is None:
                        continue
                    any_present = True
                    for v in vals:
                        if norm_domains:
                            parsed = parse_single_recipient(v)
                            if parsed is None:
                                return _deny(
                                    call,
                                    "external.recipient_domain",
                                    f"malformed or multi-address recipient in '{param}'",
                                )
                            addr, domain = parsed
                            if domain not in norm_domains:
                                return _deny(
                                    call,
                                    "external.recipient_domain",
                                    f"recipient domain '{domain}' not allow-listed",
                                )
                            if norm_exact and addr not in norm_exact:
                                return _deny(
                                    call,
                                    "external.recipient_not_allowed",
                                    "recipient is not on the exact allow-list",
                                )
                        elif norm_exact:
                            norm_dest = normalize_recipient(v)
                            if norm_dest is None or norm_dest not in norm_exact:
                                return _deny(
                                    call,
                                    "external.recipient_not_allowed",
                                    "recipient is not on the exact allow-list",
                                )
                if not any_present:
                    if norm_domains:
                        return _deny(
                            call,
                            "external.recipient_domain",
                            f"missing or empty recipient across {rcpt_params}",
                        )
                    return _deny(
                        call,
                        "external.recipient_not_allowed",
                        f"missing or empty recipient across {rcpt_params}",
                    )

        args: dict[str, Any] = dict(call.args)
        bounded: list[str] = []

        # Sensitivity: derived from tool metadata, never from the proposer.
        if spec.column_sensitivity and spec.columns_param:
            requested = args.get(spec.columns_param)
            if requested is not None and not isinstance(requested, list | tuple):
                return _deny(
                    call,
                    "argument.invalid",
                    f"argument '{spec.columns_param}' must be a list or tuple of column names",
                )
            all_cols = list(spec.column_sensitivity)
            cols = list(requested) if requested else all_cols
            unknown = [c for c in cols if c not in spec.column_sensitivity]
            if unknown:
                valid = [
                    c
                    for c in all_cols
                    if spec.sensitivity_of(c) <= p.max_sensitivity
                    and (call.tool not in p.allowed_columns or c in p.allowed_columns[call.tool])
                ]
                return _deny(call, "argument.unknown_column", f"unknown columns {unknown}; permitted columns: {valid}")
            column_allow = p.allowed_columns.get(call.tool)
            allowed = [
                c
                for c in cols
                if spec.sensitivity_of(c) <= p.max_sensitivity and (column_allow is None or c in column_allow)
            ]
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
                raw_num = args[name]
                if isinstance(raw_num, bool):
                    return _deny(call, "argument.invalid", f"argument '{name}' must be numeric, not bool")
                try:
                    value = float(raw_num)
                except (TypeError, ValueError):
                    return _deny(call, "argument.invalid", f"argument '{name}' is not numeric")
                if not math.isfinite(value):
                    return _deny(call, "argument.invalid", f"argument '{name}' must be a finite number")
                clamped = min(max(value, lo), hi)
                if clamped != value:
                    args[name] = int(clamped) if float(clamped).is_integer() else clamped
                    bounded.append(f"{name} {value:g}->{clamped:g}")

        # Recipient checks above validate the proposed destination. A numeric/column
        # bound must not silently change that destination after authorization.
        if op.external and (p.recipient_domains or p.allowed_recipients):
            for param in external_recipient_params(op.control_params):
                if args.get(param) != call.args.get(param):
                    return _deny(call, "external.recipient_changed", "bounding changed an authorized recipient")

        revised = replace(call, args=args)
        if bounded:
            return PolicyDecision(Decision.BOUND, revised, "bound", "; ".join(bounded))
        return PolicyDecision(Decision.ALLOW, revised, "allow", "within policy")
