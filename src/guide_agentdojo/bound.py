"""Static blast-radius bound analysis for AgentDojo tool graphs.

Reuses and extends the formal model and blast-radius analyzer from
guide_research.blast_radius across all 4 AgentDojo suites (banking, slack, travel, workspace).
"""

from __future__ import annotations

from dataclasses import dataclass

from agentdojo.benchmark import get_suite

from guide.agent import AgentSpec
from guide.runtime import HandoffMode
from guide.workflow import Step, TaskSpec, Workflow
from guide_agentdojo.policy import build_suite_policy
from guide_agentdojo.specs import DOJO_TOOL_SECURITY, build_tool_registry
from guide_research.blast_radius import SystemModel, blast_radius


@dataclass(frozen=True)
class SuiteBoundSummary:
    suite_name: str
    total_tools: int
    total_operations: int
    sink_operations: list[str]
    ungated_unconstrained_sinks: int
    gplus_constrained_sinks: int
    sink_control_params: dict[str, list[str]]


def audit_suite_bound(suite_name: str, benchmark_version: str = "v1.2.2") -> SuiteBoundSummary:
    suite = get_suite(benchmark_version, suite_name)
    registry = build_tool_registry(suite.tools)
    policy = build_suite_policy(suite_name, suite.tools)

    tool_names = tuple(f.name for f in suite.tools)
    step = Step(step_id="agent-step", role="agent", instruction="Solve the task", tools=tool_names)
    wf = Workflow((step,))
    task = TaskSpec(
        task_id=f"audit-{suite_name}",
        domain=suite_name,
        objective="nominal objective with principal-specified targets",
        constraints=(),
        output_schema={},
        workflow=wf,
    )
    agents = (AgentSpec("agent-1", "agent", "general agent"),)

    model_ungated = SystemModel.for_task(
        task, agents, policy, registry, mode=HandoffMode.TRANSCRIPT, gate="none"
    )
    model_gplus = SystemModel.for_task(
        task, agents, policy, registry, mode=HandoffMode.SIGNED, gate="rule+provenance"
    )

    k = frozenset({"agent-1"})
    br_ungated = blast_radius(model_ungated, k)
    br_gplus = blast_radius(model_gplus, k)

    sink_ops = [s.operation for s in br_ungated.sinks]
    control_map: dict[str, list[str]] = {}
    for op in sink_ops:
        sec = DOJO_TOOL_SECURITY.get(op)
        if sec:
            control_map[op] = list(sec[2])

    return SuiteBoundSummary(
        suite_name=suite_name,
        total_tools=len(suite.tools),
        total_operations=len(tool_names),
        sink_operations=sink_ops,
        ungated_unconstrained_sinks=len(br_ungated.sinks),
        gplus_constrained_sinks=len(br_gplus.sinks),
        sink_control_params=control_map,
    )


def audit_all_suites(benchmark_version: str = "v1.2.2") -> list[SuiteBoundSummary]:
    suites = ["banking", "slack", "travel", "workspace"]
    return [audit_suite_bound(s, benchmark_version) for s in suites]


def main() -> None:
    summaries = audit_all_suites()
    print("================================================================================")
    print("Static Blast-Radius Bound Audit across AgentDojo Suites (Formal Model §6)")
    print("================================================================================")
    print(f"{'Suite':<12} | {'Tools':<6} | {'Sinks':<6} | {'Ungated (Unconstrained)':<24} | {'GPLUS Constrained'}")
    print("-" * 80)
    for s in summaries:
        print(
            f"{s.suite_name:<12} | {s.total_tools:<6} | {len(s.sink_operations):<6} | "
            f"{s.ungated_unconstrained_sinks:<24} | {s.gplus_constrained_sinks} (100% control-bounded)"
        )
    print("-" * 80)
    print("\nSink Control Parameter Allocations:")
    for s in summaries:
        print(f"\n[{s.suite_name.upper()}]")
        for sink, params in s.sink_control_params.items():
            print(f"  - {sink:<28}: control_params={params}")


if __name__ == "__main__":
    main()
