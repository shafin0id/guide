"""Protocol v7b: build a GUIDE SystemModel from one ExtractedConfig. See plan §3.4.

Registry: one ToolSpec per tool id, one operation named after the tool id, write_effect/
external from classify_tool, no control params, resource_class = tool id (so a state flow
only occurs when two agents share the same tool). Policy permits everything, gate="none" --
that is how these systems are actually deployed (no GUIDE in the loop).
"""

from __future__ import annotations

from guide.agent import AgentSpec
from guide.policy import Policy
from guide.runtime import HandoffMode
from guide.tools import OperationSpec, Tool, ToolRegistry, ToolSpec
from guide.types import Sensitivity, ToolResult
from guide.workflow import Step, Workflow
from guide_bench.mining.classify import classify_tool
from guide_bench.mining.common import ExtractedConfig
from guide_research.blast_radius import SystemModel


class _StubTool:
    """Static-analysis-only stand-in. Never invoked (mined code is never executed)."""

    def __init__(self, spec: ToolSpec) -> None:
        self.spec = spec

    def invoke(self, operation: str, args: object) -> ToolResult:  # pragma: no cover
        return ToolResult(tool=self.spec.name, operation=operation, output=None)


def build_registry(tool_ids: set[str]) -> tuple[ToolRegistry, dict[str, tuple[str, str]]]:
    """Returns (registry, classification_log) where classification_log maps tool_id ->
    (classification, triggering_rule)."""
    reg = ToolRegistry()
    log: dict[str, tuple[str, str]] = {}
    for tool_id in sorted(tool_ids):
        cls, rule = classify_tool(tool_id)
        log[tool_id] = (cls, rule)
        op = OperationSpec(
            name=tool_id,
            write_effect=cls in ("write", "external"),
            external=cls == "external",
            control_params=(),
        )
        spec = ToolSpec(name=tool_id, description="", resource_class=tool_id, operations={tool_id: op}, default_sensitivity=Sensitivity.INTERNAL)
        reg.register(_StubTool(spec))  # type: ignore[arg-type]
    return reg, log


def build_model(cfg: ExtractedConfig, mode: HandoffMode = HandoffMode.TRANSCRIPT) -> tuple[SystemModel, dict[str, tuple[str, str]]]:
    """Builds a SystemModel from one mined config under gate="none" (undefended, as deployed)."""
    all_tools: set[str] = set()
    for step in cfg.steps:
        all_tools.update(step.tools)
    registry, log = build_registry(all_tools)

    permitted = {t: frozenset({t}) for t in all_tools}
    policy = Policy(policy_id=f"mined-{cfg.framework}", permitted=permitted, max_sensitivity=Sensitivity.RESTRICTED, allow_write=True, allow_external=True)

    agent_ids = {s.agent for s in cfg.steps}
    agents = tuple(AgentSpec(aid, aid, "") for aid in sorted(agent_ids))
    steps = tuple(
        Step(step_id=s.step_id, role=s.agent, instruction="", tools=tuple(s.tools), depends_on=tuple(s.depends_on))
        for s in cfg.steps
    )
    model = SystemModel(
        workflow=Workflow(steps), agents=agents, policy=policy, registry=registry,
        trusted_corpus="", mode=mode, gate="none",
    )
    return model, log
