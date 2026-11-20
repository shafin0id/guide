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

This is value-level provenance (case-insensitive substring support by default; ``match='token'``
requires an exact token), not full
information-flow control: a value the attacker can make appear in trusted text, or a
destination the task legitimately delegates to external data, is out of scope. Closest
prior art: capability/data-flow separation in CaMeL (Debenedetti et al., 2025) and
information-flow control for agents; the difference studied here is enforcement at the
multi-agent orchestration gate, independent of which agent proposed the action.
"""

from __future__ import annotations

import re
import threading
import unicodedata
from collections.abc import Iterator
from typing import Any, Literal

from guide.policy import Decision, PolicyContext, PolicyDecision, PolicyEngine
from guide.tools import ToolRegistry
from guide.types import ToolCall, Trust


def normalize_text(s: str) -> str:
    """Normalize text with Unicode NFKC and lower-casing."""
    return unicodedata.normalize("NFKC", s).lower()


def _strings(obj: Any) -> Iterator[str]:
    """Yield leaf string values recursively without leaking dictionary keys into the corpus."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _strings(v)
    elif isinstance(obj, list | tuple | set | frozenset):
        for v in obj:
            yield from _strings(v)
    elif obj is not None and not isinstance(obj, bool):
        yield str(obj)


def _control_strings(obj: Any) -> Iterator[str]:
    """Recursively flatten an agent-proposed control argument (including both dict keys and values)."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from _control_strings(k)
            yield from _control_strings(v)
    elif isinstance(obj, list | tuple | set | frozenset):
        for v in obj:
            yield from _control_strings(v)
    elif obj is not None:
        yield str(obj)


def extract_control_values(raw: Any) -> list[str]:
    """Recursively flatten a control argument into normalized non-empty strings.

    Preserves falsy numeric values such as ``0`` and ``0.0`` (fixing ``str(0 or "")`` bypass)
    and inspects both dictionary keys and values so untrusted keys cannot bypass provenance.
    """
    out: list[str] = []
    for item in _control_strings(raw):
        v = normalize_text(item).strip()
        if v:
            out.append(v)
    return out


Match = Literal["substring", "token"]
_TOKEN = re.compile(r"[^\s,;()\[\]{}<>\"'`]+")


def corpus_of(content: Any) -> str:
    """Trusted corpus exactly as the guard builds it from one TRUSTED observation."""
    return "\n".join(normalize_text(s) for s in _strings(content))


def tokens_of(corpus: str) -> frozenset[str]:
    """Whitespace/punctuation-delimited tokens with trailing sentence punctuation removed."""
    return frozenset(t for t in (m.rstrip(".:!?") for m in _TOKEN.findall(normalize_text(corpus))) if t)


def supported(value: str, corpus: str, match: Match) -> bool:
    """Whether a normalised (NFKC, stripped, lower-case) value is supported by the trusted corpus."""
    nv = normalize_text(value).strip()
    nc = normalize_text(corpus)
    return nv in nc if match == "substring" else nv in tokens_of(nc)


class ProvenanceGuard:
    """Wraps any :class:`PolicyEngine`; also acts as the runtime's ContentObserver."""

    def __init__(
        self,
        inner: PolicyEngine,
        registry: ToolRegistry,
        match: Match = "substring",
        *,
        require_nonempty_control: bool = False,
    ) -> None:
        self.inner = inner
        self.registry = registry
        self.match: Match = match
        self.require_nonempty_control = require_nonempty_control
        self._trusted: dict[str, list[str]] = {}
        self._untrusted: dict[str, list[str]] = {}
        self._lock = threading.Lock()

    # ContentObserver
    def observe(self, run_id: str, content: Any, trust: Trust) -> None:
        target = self._trusted if trust is Trust.TRUSTED else self._untrusted
        with self._lock:
            target.setdefault(run_id, []).extend(normalize_text(s) for s in _strings(content))

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
        any_control_value = False
        for param in op.control_params:
            raw = decision.call.args.get(param)
            values = extract_control_values(raw)
            if not values:
                continue
            any_control_value = True
            for v in values:
                if not supported(v, trusted, self.match):
                    origin = "untrusted content" if v in untrusted else "no source"
                    return PolicyDecision(
                        Decision.DENY,
                        call,
                        "provenance.control_unsupported",
                        f"'{param}' value is not supported by trusted task content (found in: {origin})",
                    )
        if self.require_nonempty_control and not any_control_value:
            return PolicyDecision(
                Decision.DENY,
                call,
                "provenance.control_missing",
                f"all declared control parameters {op.control_params} are missing or empty",
            )
        return decision
