"""Workflow and task definitions (dependency DAG validated with Kahn's algorithm)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from guide.errors import WorkflowError


@dataclass(frozen=True)
class Step:
    step_id: str
    role: str
    instruction: str
    tools: tuple[str, ...] = ()
    depends_on: tuple[str, ...] = ()


@dataclass(frozen=True)
class Workflow:
    steps: tuple[Step, ...]

    def stages(self) -> list[list[Step]]:
        """Topological stages; steps in one stage are mutually independent."""
        ids = [s.step_id for s in self.steps]
        if len(set(ids)) != len(ids):
            raise WorkflowError("duplicate step ids")
        by_id = {s.step_id: s for s in self.steps}
        indeg = {s.step_id: 0 for s in self.steps}
        children: dict[str, list[str]] = {i: [] for i in ids}
        for s in self.steps:
            for dep in s.depends_on:
                if dep not in by_id:
                    raise WorkflowError(f"step {s.step_id} depends on unknown step {dep}")
                indeg[s.step_id] += 1
                children[dep].append(s.step_id)
        frontier = [i for i in ids if indeg[i] == 0]
        stages: list[list[Step]] = []
        seen = 0
        while frontier:
            stages.append([by_id[i] for i in frontier])
            seen += len(frontier)
            nxt: list[str] = []
            for i in frontier:
                for c in children[i]:
                    indeg[c] -= 1
                    if indeg[c] == 0:
                        nxt.append(c)
            frontier = sorted(nxt, key=ids.index)
        if seen != len(ids):
            raise WorkflowError("workflow contains a dependency cycle")
        return stages

    def order(self) -> list[Step]:
        return [s for stage in self.stages() for s in stage]


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    domain: str
    objective: str
    constraints: tuple[str, ...]
    output_schema: Mapping[str, Any]
    workflow: Workflow
    metadata: Mapping[str, Any] = field(default_factory=dict)
