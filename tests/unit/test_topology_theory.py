"""Unit and property tests for Proposition 4 (topology floor) - Protocol v8."""

from __future__ import annotations

from dataclasses import replace

from hypothesis import given, settings
from hypothesis import strategies as st

from guide.agent import AgentSpec
from guide.policy import Policy
from guide.runtime import HandoffMode
from guide.tools import OperationSpec, ToolRegistry, ToolSpec
from guide.types import Sensitivity, ToolResult
from guide.workflow import Step, Workflow
from guide_bench.real_world.configs import load_configs
from guide_research import topology
from guide_research.blast_radius import ObservedCall, SystemModel, synthesize_least_privilege
from guide_research.topology_theory import closed_form_floor, has_dominating_source


class _ToyTool:
    def __init__(self, spec: ToolSpec) -> None:
        self.spec = spec

    def invoke(self, operation: str, args: object) -> ToolResult:
        return ToolResult(tool=self.spec.name, operation=operation, output=None)


def _build_toy_registry() -> ToolRegistry:
    reg = ToolRegistry()
    toy_tools = [
        ("t_read", False, False, "r0"),
        ("t_w1", True, False, "r1"),
        ("t_w2", True, False, "r2"),
        ("t_x", True, True, "r3"),
    ]
    for name, w, x, res in toy_tools:
        op = OperationSpec(name=name, write_effect=w, external=x, control_params=())
        spec = ToolSpec(
            name=name,
            description="",
            resource_class=res,
            operations={name: op},
            default_sensitivity=Sensitivity.RESTRICTED,
        )
        reg.register(_ToyTool(spec))  # type: ignore[arg-type]
    return reg


def _build_toy_policy() -> Policy:
    return Policy(
        policy_id="toy-policy",
        permitted={t: frozenset({t}) for t in ["t_read", "t_w1", "t_w2", "t_x"]},
        max_sensitivity=Sensitivity.RESTRICTED,
        allow_write=True,
        allow_external=True,
    )


TOY_REGISTRY = _build_toy_registry()
TOY_POLICY = _build_toy_policy()


@st.composite
def random_toy_workflows(draw: st.DrawFn) -> Workflow:
    n = draw(st.integers(1, 5))
    tool_names = ["t_read", "t_w1", "t_w2", "t_x"]
    steps = []
    for i in range(n):
        s_tools = draw(st.sets(st.sampled_from(tool_names), min_size=1))
        earlier_ids = [f"s{j}" for j in range(i)]
        deps = draw(st.sets(st.sampled_from(earlier_ids)) if earlier_ids else st.just(set()))
        steps.append(
            Step(
                step_id=f"s{i}",
                role="r0",
                instruction="",
                tools=tuple(sorted(s_tools)),
                depends_on=tuple(sorted(deps)),
            )
        )
    return Workflow(tuple(steps))


@settings(max_examples=300, deadline=None, derandomize=True, database=None)
@given(
    wf=random_toy_workflows(),
    mode=st.sampled_from([HandoffMode.TRANSCRIPT, HandoffMode.SIGNED]),
)
def test_property_prop4_floor_matches_brute_force(wf: Workflow, mode: HandoffMode) -> None:
    """Prop 4a, 4b, 4c property tests:
    - 4a: min over partitions of WBR_1 equals closed_form_floor
    - 4b: in TRANSCRIPT mode with Sinks* != empty, floor is 1.0
    - 4c: in SIGNED mode where dominating source reaches all sinks, floor is 1.0
    """
    model = SystemModel(
        workflow=wf,
        agents=(AgentSpec("a0", "r0", ""),),
        policy=TOY_POLICY,
        registry=TOY_REGISTRY,
        trusted_corpus="",
        mode=mode,
        gate="rule",
    )

    n_steps = len(wf.steps)
    all_rgs = topology.set_partitions(n_steps)
    sinks_star = topology.total_sinks_star(model)

    cf_floor = closed_form_floor(model)

    # Brute-force minimum over all partitions
    bf_floor = min(topology.wbr(topology.apply_partition(model, rgs), 1, sinks_star=sinks_star) for rgs in all_rgs)

    # Prop 4a
    assert abs(cf_floor - bf_floor) < 1e-9, f"Prop 4a violation: closed_form={cf_floor}, brute_force={bf_floor}"

    # Prop 4b: transcript mode floor is 1 if sinks exist
    if mode == HandoffMode.TRANSCRIPT and len(sinks_star) > 0:
        assert abs(cf_floor - 1.0) < 1e-9, f"Prop 4b violation: transcript mode floor was {cf_floor}, expected 1.0"

    # Prop 4c: signed mode floor is 1 if dominating source reaches all sinks
    sink_steps = [s.step_id for s in wf.steps if any(c.is_sink for c in topology.authority(model, s))]
    if mode == HandoffMode.SIGNED and len(sink_steps) > 0:
        if has_dominating_source(wf, sink_steps):
            assert abs(cf_floor - 1.0) < 1e-9, f"Prop 4c violation: dominating source exists but floor={cf_floor}"


def test_real_configs_prop4_closed_form() -> None:
    """Verifies that for all 19 real-world configs across both modes and both policy variants
    (19 * 2 * 2 = 76 combinations), brute force minimum equals closed form.
    """
    configs = load_configs()
    checked = 0
    for cfg in configs:
        nominal_base = SystemModel.for_task(
            cfg.task, cfg.agents, cfg.policy, cfg.registry, mode=HandoffMode.TRANSCRIPT, gate="rule"
        )
        calls = tuple(ObservedCall(s, t, o, a) for s, t, o, a in cfg.nominal_calls)
        lp = synthesize_least_privilege(nominal_base, calls)
        lp_base = replace(nominal_base, policy=lp.policy, workflow=lp.workflow)

        n_steps = len(cfg.task.workflow.steps)
        all_rgs = topology.set_partitions(n_steps)

        for mode in (HandoffMode.TRANSCRIPT, HandoffMode.SIGNED):
            for base in (nominal_base, lp_base):
                m = replace(base, mode=mode)
                sinks_star = topology.total_sinks_star(m)
                cf = closed_form_floor(m)
                bf = min(topology.wbr(topology.apply_partition(m, rgs), 1, sinks_star=sinks_star) for rgs in all_rgs)
                assert abs(cf - bf) < 1e-9, f"Mismatch in {cfg.config_id} mode={mode}: cf={cf} vs bf={bf}"
                checked += 1

    assert checked == 76
