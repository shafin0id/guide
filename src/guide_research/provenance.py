"""Provenance-aware policy enforcement (experimental; hypothesis H1 in docs/experiments.md).

Problem: an allow-list gate evaluates *what* an action is, not *why* it was proposed. An
injection hidden in tool output can steer a permitted sink (e-mail, ticket, webhook) to an
attacker-chosen destination that is still inside the allow-list.

Mechanism: for operations with side effects (``write_effect`` or ``external``), every
*control argument* (the args that choose where the effect lands, declared by the tool as
``OperationSpec.control_params``) must be supported by principal-authored (TRUSTED)
content -- the task objective, constraints and policy. Values that appear only in
UNTRUSTED content (tool results, retrieved documents) or nowhere at all (hallucinated) are
denied. Data arguments (e.g. an e-mail body) are not constrained by this rule.

This is value-level provenance (exact, case-insensitive substring support), not full
information-flow control: a value the attacker can make appear in trusted text, or a
destination the task legitimately delegates to external data, is out of scope. Closest
prior art: capability/data-flow separation in CaMeL (Debenedetti et al., 2025) and
information-flow control for agents; the difference studied here is enforcement at the
multi-agent orchestration gate, independent of which agent proposed the action.
"""

from __future__ import annotations

import threading
from collections.abc import Iterator
from typing import Any

from guide.policy import Decision, PolicyContext, PolicyDecision, PolicyEngine
from guide.tools import ToolRegistry
from guide.types import ToolCall, Trust


def _strings(obj: Any) -> Iterator[str]:
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield str(k)
            yield from _strings(v)
    elif isinstance(obj, list | tuple | set | frozenset):
        for v in obj:
            yield from _strings(v)
    elif obj is not None and not isinstance(obj, bool):
        yield str(obj)


class ProvenanceGuard:
    """Wraps any :class:`PolicyEngine`; also acts as the runtime's ContentObserver."""

    def __init__(self, inner: PolicyEngine, registry: ToolRegistry) -> None:
        self.inner = inner
        self.registry = registry
        self._trusted: dict[str, list[str]] = {}
        self._untrusted: dict[str, list[str]] = {}
        self._lock = threading.Lock()

    # ContentObserver
    def observe(self, run_id: str, content: Any, trust: Trust) -> None:
        target = self._trusted if trust is Trust.TRUSTED else self._untrusted
        with self._lock:
            target.setdefault(run_id, []).extend(s.lower() for s in _strings(content))

    def forget(self, run_id: str) -> None:
        with self._lock:
            self._trusted.pop(run_id, None)
            self._untrusted.pop(run_id, None)

    # PolicyEngine
    def evaluate(self, call: ToolCall, context: PolicyContext) -> PolicyDecision:
        decision = self.inner.evaluate(call, context)
        if decision.decision is Decision.DENY:
            return decision
        op = self.registry.get(call.tool).spec.operations[call.operation]
        if not (op.write_effect or op.external) or not op.control_params:
            return decision
        with self._lock:
            trusted = "\n".join(self._trusted.get(context.run_id, []))
            untrusted = "\n".join(self._untrusted.get(context.run_id, []))
        for param in op.control_params:
            raw = decision.call.args.get(param)
            values = raw if isinstance(raw, list | tuple) else [raw]
            for value in values:
                v = str(value or "").strip().lower()
                if not v:
                    continue
                if v not in trusted:
                    origin = "untrusted content" if v in untrusted else "no source"
                    return PolicyDecision(
                        Decision.DENY,
                        call,
                        "provenance.control_unsupported",
                        f"'{param}' value is not supported by trusted task content (found in: {origin})",
                    )
        return decision
