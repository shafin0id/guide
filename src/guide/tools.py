"""Tool contracts.

A tool declares its security-relevant metadata (operations, write effects, external sinks,
column sensitivity) in a :class:`ToolSpec`. Policy engines read this metadata; they never
trust attributes declared by the agent that proposes a call.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Protocol, runtime_checkable

from guide.errors import ToolNotFoundError
from guide.types import Sensitivity, ToolResult


@dataclass(frozen=True)
class OperationSpec:
    name: str
    description: str = ""
    write_effect: bool = False  # mutates state
    external: bool = False  # moves data across the trust boundary (e-mail, webhooks, ...)
    params: Mapping[str, str] = field(default_factory=dict)  # name -> description (for prompts)
    control_params: tuple[str, ...] = ()  # args that choose WHERE an effect lands (recipient, url, path)


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    resource_class: str
    operations: Mapping[str, OperationSpec]
    column_sensitivity: Mapping[str, Sensitivity] = field(default_factory=dict)
    default_sensitivity: Sensitivity = Sensitivity.INTERNAL
    columns_param: str | None = None  # name of the arg selecting columns, if the tool supports it

    def sensitivity_of(self, column: str) -> Sensitivity:
        return self.column_sensitivity.get(column, self.default_sensitivity)

    def describe(self) -> str:
        lines = [f"- {self.name}: {self.description}"]
        if self.column_sensitivity:
            cols = ", ".join(f"{c} ({s.name})" for c, s in self.column_sensitivity.items())
            lines.append(f"    columns (data classification): {cols}")
        for op in self.operations.values():
            params = ", ".join(f"{k} ({v})" for k, v in op.params.items()) or "none"
            lines.append(f"    operation {op.name}: {op.description} params: {params}")
        return "\n".join(lines)


@runtime_checkable
class Tool(Protocol):
    spec: ToolSpec

    def invoke(self, operation: str, args: Mapping[str, Any]) -> ToolResult: ...


class ToolRegistry:
    def __init__(self, tools: Iterable[Tool] = ()) -> None:
        self._tools: dict[str, Tool] = {}
        for tool in tools:
            self.register(tool)

    def register(self, tool: Tool) -> None:
        if tool.spec.name in self._tools:
            raise ValueError(f"duplicate tool name: {tool.spec.name}")
        self._tools[tool.spec.name] = tool

    def get(self, name: str) -> Tool:
        try:
            return self._tools[name]
        except KeyError:
            raise ToolNotFoundError(f"unknown tool: {name}") from None

    def has(self, name: str) -> bool:
        return name in self._tools

    def describe(self, names: Iterable[str]) -> str:
        return "\n".join(self._tools[n].spec.describe() for n in names if n in self._tools)
