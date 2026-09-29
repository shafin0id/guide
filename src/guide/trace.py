"""Hash-linked trace (proposal: append_trace) and pluggable observability sinks.

Every routing choice, hand-off result, policy decision, tool event and output is one
event. The ledger stores digests of bulky or sensitive content rather than the content
itself, so an audit log does not become a data-leak channel.

Tamper evidence holds only against parties who cannot rewrite the entire chain; anchoring
the head hash externally (e.g. a WORM store) is a deployment concern.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol, runtime_checkable

from guide.handoff import canonical_json, sha256_hex

_SECRET_KEYS = ("api_key", "authorization", "password", "secret", "token")


def redact(obj: Any) -> Any:
    if isinstance(obj, Mapping):
        return {k: ("[REDACTED]" if any(s in str(k).lower() for s in _SECRET_KEYS) else redact(v)) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [redact(v) for v in obj]
    return obj


@dataclass(frozen=True)
class TraceEvent:
    seq: int
    ts_ms: int
    kind: str
    step_id: str
    principal: str
    data: Mapping[str, Any]
    prev_hash: str
    hash: str

    def body(self) -> dict[str, Any]:
        return {"seq": self.seq, "ts_ms": self.ts_ms, "kind": self.kind, "step_id": self.step_id,
                "principal": self.principal, "data": dict(self.data)}


@runtime_checkable
class EventSink(Protocol):
    def emit(self, event: TraceEvent) -> None: ...


class JsonlSink:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, event: TraceEvent) -> None:
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({**event.body(), "prev_hash": event.prev_hash, "hash": event.hash}) + "\n")


class TraceLedger:
    def __init__(self, run_id: str, objective: str, policy_digest: str, sinks: tuple[EventSink, ...] = ()) -> None:
        self.run_id = run_id
        self.genesis = sha256_hex(canonical_json([run_id, objective, policy_digest]))
        self._events: list[TraceEvent] = []
        self._sinks = sinks

    @property
    def head(self) -> str:
        return self._events[-1].hash if self._events else self.genesis

    @property
    def events(self) -> tuple[TraceEvent, ...]:
        return tuple(self._events)

    def append(self, kind: str, data: Mapping[str, Any], *, step_id: str = "", principal: str = "runtime") -> TraceEvent:
        body = {"seq": len(self._events), "ts_ms": int(time.time() * 1000), "kind": kind, "step_id": step_id,
                "principal": principal, "data": redact(dict(data))}
        prev = self.head
        digest = sha256_hex(prev.encode("ascii") + canonical_json(body))
        event = TraceEvent(prev_hash=prev, hash=digest, **body)
        self._events.append(event)
        for sink in self._sinks:
            sink.emit(event)
        return event

    def verify(self, events: tuple[TraceEvent, ...] | None = None) -> tuple[bool, int | None]:
        """Return (True, None) if the chain is intact, else (False, index of first bad event)."""
        prev = self.genesis
        for i, ev in enumerate(self._events if events is None else events):
            if ev.prev_hash != prev or ev.seq != i:
                return False, i
            if sha256_hex(prev.encode("ascii") + canonical_json(ev.body())) != ev.hash:
                return False, i
            prev = ev.hash
        return True, None
