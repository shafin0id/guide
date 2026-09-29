"""Core value types shared across GUIDE components.

These are deliberately plain frozen dataclasses so the core has no runtime dependency on a
validation library. Mutable run bookkeeping lives in :mod:`guide.runtime.state`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Any, Mapping


class Sensitivity(IntEnum):
    """Ordered data-classification levels. Higher value = more sensitive."""

    PUBLIC = 0
    INTERNAL = 1
    CONFIDENTIAL = 2
    RESTRICTED = 3

    @classmethod
    def parse(cls, value: "str | int | Sensitivity") -> "Sensitivity":
        if isinstance(value, Sensitivity):
            return value
        if isinstance(value, int):
            return cls(value)
        return cls[value.upper()]


class Trust(str, Enum):
    """Provenance class of a piece of content entering an agent's context."""

    TRUSTED = "trusted"  # principal-authored: task objective, constraints, policy
    UNTRUSTED = "untrusted"  # external: tool outputs, documents, retrieved content


@dataclass(frozen=True)
class ChatMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass(frozen=True)
class ToolCall:
    """An action an agent *proposes*. Nothing executes until a policy decision allows it."""

    tool: str
    operation: str
    args: Mapping[str, Any]
    principal: str
    reason: str = ""


@dataclass(frozen=True)
class ToolResult:
    """Outcome of a tool invocation, with the provenance class of its content."""

    ok: bool
    data: Any = None
    error: str | None = None
    trust: Trust = Trust.UNTRUSTED


@dataclass(frozen=True)
class Usage:
    model_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0

    def __add__(self, other: "Usage") -> "Usage":
        return Usage(
            self.model_calls + other.model_calls,
            self.prompt_tokens + other.prompt_tokens,
            self.completion_tokens + other.completion_tokens,
        )

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens
