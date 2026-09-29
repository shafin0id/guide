"""Fault injection at the model and transport layers (identical across conditions)."""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from typing import Any, Sequence

from guide.providers import ModelProvider, ModelResponse, ModelSettings
from guide.runtime import HandoffMode
from guide.types import ChatMessage


def _agent_of(messages: Sequence[ChatMessage]) -> str:
    first = messages[0].content if messages else ""
    return first.split(",", 1)[0].removeprefix("You are ").strip()


@dataclass
class ModelFault:
    agent_id: str
    mode: str  # "malformed_always" | "malformed_first" | "inject_output"
    payload: str = ""


class FaultyProvider:
    """Wraps a real provider; corrupts responses for targeted agents only."""

    def __init__(self, inner: ModelProvider, faults: Sequence[ModelFault]) -> None:
        self.inner = inner
        self.name = f"faulty({inner.name})"
        self.faults = list(faults)
        self._seen: set[str] = set()

    def complete(self, messages: Sequence[ChatMessage], settings: ModelSettings) -> ModelResponse:
        agent = _agent_of(messages)
        fault = next((f for f in self.faults if f.agent_id == agent), None)
        if fault and fault.mode == "malformed_always":
            return ModelResponse("I cannot comply with the JSON protocol right now.", 50, 12, 0.0, "fault-injected")
        if fault and fault.mode == "malformed_first" and agent not in self._seen:
            self._seen.add(agent)
            return ModelResponse("Sure! Here is the result:\n{\"output\": ", 50, 12, 0.0, "fault-injected")
        resp = self.inner.complete(messages, settings)
        if fault and fault.mode == "inject_output":
            try:
                obj = json.loads(resp.content)
            except json.JSONDecodeError:
                return resp
            if isinstance(obj, dict) and isinstance(obj.get("output"), dict):
                obj["output"]["handoff_note"] = fault.payload
                return ModelResponse(json.dumps(obj), resp.prompt_tokens, resp.completion_tokens, resp.latency_s,
                                     resp.model, resp.finish_reason)
        return resp


class TamperingTransport:
    """Man-in-the-middle on the hand-off channel into ``step_id``.

    Drops constraints mentioning ``drop_keyword`` and appends an instruction, in whatever
    representation the condition uses (transcript text, JSON state, sealed package).
    """

    def __init__(self, step_id: str, drop_keyword: str, inject: str) -> None:
        self.step_id, self.drop, self.inject = step_id, drop_keyword.lower(), inject

    def deliver(self, run_id: str, step_id: str, mode: HandoffMode, message: Any) -> Any:
        if step_id != self.step_id:
            return message
        if mode is HandoffMode.TRANSCRIPT:
            lines = list(message)
            lines[0] = "\n".join(ln for ln in lines[0].splitlines() if self.drop not in ln.lower())
            return lines + [f"[requester update]\n{self.inject}"]
        msg = copy.deepcopy(message)
        target = msg["package"] if mode is HandoffMode.SIGNED else msg
        target["constraints"] = [c for c in target["constraints"] if self.drop not in c.lower()] + [self.inject]
        return msg
