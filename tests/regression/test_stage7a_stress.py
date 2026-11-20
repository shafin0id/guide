"""Stage 7A: Independent offline stress tests, independent reachability oracle, and boundary demos.

Runs against version-2/workspace without any live LLM API calls.
"""

from __future__ import annotations

import copy
import random
import sys
from pathlib import Path
from typing import Any

import pytest

_HERE = Path(__file__).resolve()
_CAND = _HERE.parents[1] / "workspace" / "src"
WORKSPACE_SRC = _CAND if _CAND.is_dir() else (_HERE.parents[2] / "src")
if str(WORKSPACE_SRC) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_SRC))

from guide.agent import AgentSpec  # noqa: E402
from guide.errors import WorkflowError  # noqa: E402
from guide.policy import Decision, Policy, PolicyContext, RulePolicyEngine  # noqa: E402
from guide.runtime import HandoffMode  # noqa: E402
from guide.tools import ToolRegistry  # noqa: E402
from guide.types import Sensitivity, ToolCall, Trust  # noqa: E402
from guide.workflow import Step, TaskSpec, Workflow  # noqa: E402
from guide_bench.env import Environment  # noqa: E402
from guide_realworld.core import Runtime as RealWorldRuntime  # noqa: E402
from guide_realworld.core import Scenario, Task, ToolDef  # noqa: E402
from guide_research.blast_radius import SystemModel, authority, blast_radius  # noqa: E402
from guide_research.provenance import ProvenanceGuard  # noqa: E402
from guide_research.topology_theory import is_chain  # noqa: E402


# ----------------------------------------------------------------------------- Independent Oracle
def independent_reachability_oracle(
    model: SystemModel,
    compromised_agents: set[str],
    injectable_tools: set[str],
    transport_adversary: bool,
) -> tuple[set[str], set[tuple[str, str, str]]]:
    """Genuinely independent fixed-point reachability oracle over (A, J, tau_adv).

    Does NOT call ``influenced()`` or ``blast_radius()``. Computes step influence by
    explicitly simulating seeds (direct compromise, injectable tool, unsigned transport)
    and monotone transitive propagation via context edges and write->read resource-class edges.
    """
    steps = list(model.workflow.order())
    pos = {s.step_id: i for i, s in enumerate(steps)}
    by_id = {s.step_id: s for s in steps}

    # Determine agent candidates per role independently
    role_to_agents: dict[str, set[str]] = {}
    for a in model.agents:
        role_to_agents.setdefault(a.role, set()).add(a.agent_id)

    # Determine writable resource classes per step directly from ToolRegistry + Policy (no authority())
    def step_executable_ops(s: Step) -> set[tuple[str, str, bool, str]]:
        out: set[tuple[str, str, bool, str]] = set()
        p = model.policy
        for tname in s.tools:
            if not model.registry.has(tname):
                continue
            spec = model.registry.get(tname).spec
            for op in spec.operations.values():
                if model.gate == "none":
                    out.add((tname, op.name, op.write_effect, spec.resource_class))
                    continue
                if tname not in p.permitted or op.name not in p.permitted[tname]:
                    continue
                if op.write_effect and not p.allow_write:
                    continue
                if op.external and not p.allow_external:
                    continue
                if spec.column_sensitivity and spec.columns_param:
                    col_allow = p.allowed_columns.get(tname)
                    ok_cols = [
                        c
                        for c, cs in spec.column_sensitivity.items()
                        if cs <= p.max_sensitivity and (col_allow is None or c in col_allow)
                    ]
                    if not ok_cols:
                        continue
                elif spec.default_sensitivity > p.max_sensitivity:
                    continue
                out.add((tname, op.name, op.write_effect, spec.resource_class))
        return out

    ops_by_step = {s.step_id: step_executable_ops(s) for s in steps}
    writable_rc = {
        sid: {rc for _, _, is_w, rc in ops if is_w} for sid, ops in ops_by_step.items()
    }
    readable_rc = {
        s.step_id: {model.registry.get(t).spec.resource_class for t in s.tools if model.registry.has(t)}
        for s in steps
    }

    # Seed set
    infl: set[str] = set()
    for s in steps:
        if role_to_agents.get(s.role, set()) & compromised_agents:
            infl.add(s.step_id)
        if set(s.tools) & injectable_tools:
            infl.add(s.step_id)
        if transport_adversary and model.mode is not HandoffMode.SIGNED:
            infl.add(s.step_id)

    # Fixed point closure
    while True:
        added = set()
        for s in steps:
            if s.step_id in infl:
                continue
            for prev_id in infl:
                if pos[prev_id] >= pos[s.step_id]:
                    continue
                # Context channel
                if model.mode is HandoffMode.TRANSCRIPT:
                    added.add(s.step_id)
                    break
                if prev_id in by_id[s.step_id].depends_on:
                    added.add(s.step_id)
                    break
                # State channel
                if writable_rc[prev_id] & readable_rc[s.step_id]:
                    added.add(s.step_id)
                    break
        if not added:
            break
        infl |= added

    caps = {(sid, t, op) for sid in infl for (t, op, _, _) in ops_by_step[sid]}
    return infl, caps


def test_7a_random_dags_full_threat_channels_vs_independent_oracle() -> None:
    """500 randomized DAGs (including disconnected graphs, shared roles, J, tau_adv, state flows)."""
    reg = ToolRegistry(Environment().tools)
    all_tools = ["procurement_db", "incident_logs", "email"]
    rng = random.Random(20261120)

    for trial in range(500):
        n_steps = rng.randint(1, 7)
        n_roles = rng.randint(1, n_steps)
        roles = [f"r{i}" for i in range(n_roles)]
        # Create 1-2 agents per role (multi-agent roles)
        agents = tuple(
            AgentSpec(f"a_{r}_{k}", r, "")
            for r in roles
            for k in range(rng.randint(1, 2))
        )
        steps_list = []
        for i in range(n_steps):
            # Intentionally create disconnected graphs ~30% of the time
            if trial % 3 == 0 and i >= n_steps // 2:
                possible_deps = list(range(n_steps // 2, i))
            else:
                possible_deps = list(range(i))
            deps = tuple(f"s{d}" for d in possible_deps if rng.random() < 0.35)
            tools = tuple(t for t in all_tools if rng.random() < 0.45)
            steps_list.append(Step(f"s{i}", rng.choice(roles), "", tools=tools, depends_on=deps))

        wf = Workflow(tuple(steps_list))
        pol = Policy(
            policy_id=f"p-{trial}",
            permitted={
                "procurement_db": frozenset(o for o in ("query", "delete") if rng.random() < 0.7),
                "incident_logs": frozenset(o for o in ("query", "update_status") if rng.random() < 0.7),
                "email": frozenset({"send"}) if rng.random() < 0.6 else frozenset(),
            },
            max_sensitivity=rng.choice(list(Sensitivity)),
            allow_write=rng.choice([False, True]),
            allow_external=rng.choice([False, True]),
        )
        mode = rng.choice(list(HandoffMode))
        gate = rng.choice(["none", "rule", "rule+provenance"])
        task = TaskSpec(f"t-{trial}", "d", "Email change-board@corp.example", (), {}, wf)
        model = SystemModel.for_task(task, agents, pol, reg, mode=mode, gate=gate)  # type: ignore[arg-type]

        comp = {a.agent_id for a in agents if rng.random() < 0.3}
        inj_tools = {t for t in all_tools if rng.random() < 0.25}
        tau = rng.choice([False, True])

        br = blast_radius(model, comp, injectable_tools=inj_tools, transport_adversary=tau)
        oracle_infl, oracle_caps = independent_reachability_oracle(model, comp, inj_tools, tau)
        got_caps = {(c.step, c.tool, c.operation) for c in br.capabilities}

        assert set(br.influenced) == oracle_infl, f"trial={trial} infl mismatch"
        assert got_caps == oracle_caps, f"trial={trial} caps mismatch"


def test_7a_branching_dag_breaks_linear_chain_floor_prop3_prop4() -> None:
    """Prove empirically that genuine parallel branch isolation DOES reduce worst-case reach (unlike linear chains)."""
    reg = ToolRegistry(Environment().tools)
    pol = Policy(
        policy_id="p",
        permitted={
            "procurement_db": frozenset({"query", "delete"}),
            "incident_logs": frozenset({"query", "update_status"}),
            "email": frozenset({"send"}),
        },
        allow_write=True,
        allow_external=True,
    )
    # Two independent parallel branches (no shared state, no shared dependency)
    wf_branch = Workflow(
        (
            Step("branch_a", "role_a", "", tools=("procurement_db",)),
            Step("branch_b", "role_b", "", tools=("email",)),
        )
    )
    assert not is_chain(wf_branch)

    # Coarse 1-agent partition (shared role across both branches)
    wf_coarse = Workflow(
        (
            Step("branch_a", "shared", "", tools=("procurement_db",)),
            Step("branch_b", "shared", "", tools=("email",)),
        )
    )
    t_coarse = TaskSpec("tc", "d", "o", (), {}, wf_coarse)
    m_coarse = SystemModel.for_task(
        t_coarse, (AgentSpec("a0", "shared", ""),), pol, reg, mode=HandoffMode.SIGNED, gate="rule"
    )
    wbr1_coarse = len(blast_radius(m_coarse, {"a0"}).sinks)

    # Refined 2-agent partition (branch isolated!)
    t_fine = TaskSpec("tf", "d", "o", (), {}, wf_branch)
    m_fine = SystemModel.for_task(
        t_fine,
        (AgentSpec("a1", "role_a", ""), AgentSpec("a2", "role_b", "")),
        pol,
        reg,
        mode=HandoffMode.SIGNED,
        gate="rule",
    )
    wbr1_fine = max(len(blast_radius(m_fine, {aid}).sinks) for aid in ("a1", "a2"))

    # Under SIGNED hand-offs, parallel branch isolation cuts WBR1 from 2 sinks -> 1 sink!
    assert wbr1_coarse == 2
    assert wbr1_fine == 1
    assert wbr1_fine < wbr1_coarse

    # Under TRANSCRIPT hand-offs, even parallel branches leak context -> WBR1 stays 2!
    m_fine_tr = SystemModel.for_task(
        t_fine,
        (AgentSpec("a1", "role_a", ""), AgentSpec("a2", "role_b", "")),
        pol,
        reg,
        mode=HandoffMode.TRANSCRIPT,
        gate="rule",
    )
    wbr1_fine_tr = max(len(blast_radius(m_fine_tr, {aid}).sinks) for aid in ("a1", "a2"))
    assert wbr1_fine_tr == 2


def test_7a_policy_lattice_monotonicity_and_boundary_sizes() -> None:
    """Tightening policy dimensions never expands authority(model, s)."""
    reg = ToolRegistry(Environment().tools)
    step = Step("s1", "w", "", tools=("procurement_db", "email"))
    wf = Workflow((step,))
    task = TaskSpec("t", "d", "Email change-board@corp.example", (), {}, wf)
    agents = (AgentSpec("a1", "w", ""),)

    p_wide = Policy(
        "wide",
        permitted={"procurement_db": frozenset({"query", "delete"}), "email": frozenset({"send"})},
        max_sensitivity=Sensitivity.RESTRICTED,
        allow_write=True,
        allow_external=True,
    )
    p_mid = Policy(
        "mid",
        permitted={"procurement_db": frozenset({"query"}), "email": frozenset({"send"})},
        max_sensitivity=Sensitivity.INTERNAL,
        allow_write=False,
        allow_external=True,
        recipient_domains=frozenset({"corp.example"}),
    )
    p_empty = Policy("empty", permitted={})

    def cap_keys(pol: Policy) -> set[tuple[str, str]]:
        m = SystemModel.for_task(task, agents, pol, reg, mode=HandoffMode.SIGNED, gate="rule")
        return {(c.tool, c.operation) for c in authority(m, step)}

    assert cap_keys(p_empty) == set()
    assert cap_keys(p_empty) <= cap_keys(p_mid) <= cap_keys(p_wide)


def test_7a_allowed_recipient_malicious_content_boundary_explicit() -> None:
    """Explicitly shows the documented guarantee boundary: authorized recipient + malicious content is ADMITTED."""
    reg = ToolRegistry(Environment().tools)
    pol = Policy(
        "p",
        permitted={"email": frozenset({"send"})},
        allow_write=True,
        allow_external=True,
        recipient_domains=frozenset({"corp.example"}),
    )
    guard = ProvenanceGuard(RulePolicyEngine(pol, reg), reg, match="token")
    guard.observe("r1", {"objective": "Send status update to change-board@corp.example"}, Trust.TRUSTED)
    ctx = PolicyContext("r1", "s1", frozenset({"email"}))

    # Malicious body to authorized recipient IS admitted (control-only provenance boundary)
    d = guard.evaluate(
        ToolCall(
            "email",
            "send",
            {"recipient": "change-board@corp.example", "body": "EXFILTRATED SECRET API_KEY=xyz"},
            "a1",
        ),
        ctx,
    )
    assert d.decision is Decision.ALLOW


def test_7a_adapter_zero_state_mutation_on_denial_and_retries() -> None:
    """Denied calls and retried/failing calls in realworld adapter never mutate backend state."""
    call_log: list[str] = []

    def _flaky_sink(state: dict[str, Any], args: dict[str, Any]) -> tuple[str, list[str] | None]:
        call_log.append(args["to"])
        state["sent"].append(args["to"])
        return "sent", None

    sc = Scenario(
        sid="mut-test",
        domain="mail",
        tools={
            "send_mail": ToolDef(
                "send_mail", "send", {"to": "addr"}, _flaky_sink, write=True, external=True, control=("to",)
            )
        },
        roles={"S": ["send_mail"]},
        new_state=lambda: {"sent": []},
        vector_tool="send_mail",
        benign=[Task("Send to alice@corp.example", lambda s: "alice@corp.example" in s["sent"])],
        injections=[],
    )
    rt = RealWorldRuntime(sc, "strict", "strict", "Send to alice@corp.example", require_nonempty_control=True)
    snap0 = copy.deepcopy(rt.state)

    # Repeated attacker attempts (different bypasses) must produce ZERO backend calls / state changes
    for attempt in (
        {"to": "attacker@evil.example"},
        {"to": ""},
        {},
        {"to": "evil@bad.com, alice@corp.example"},
    ):
        resp = rt.call("S", "send_mail", attempt)
        assert "DENIED_BY_POLICY" in resp
        assert rt.state == snap0
        assert call_log == []

    # Legitimate call executes cleanly
    assert rt.call("S", "send_mail", {"to": "alice@corp.example"}) == "sent"
    assert rt.state["sent"] == ["alice@corp.example"]
    rt.close()


def test_7a_cycles_explicitly_rejected() -> None:
    """DAG theorem explicitly excludes cyclic graphs via WorkflowError."""
    for cycle in (
        (Step("s1", "r", "", depends_on=("s1",)),),
        (Step("s1", "r", "", depends_on=("s2",)), Step("s2", "r", "", depends_on=("s1",))),
        (
            Step("s1", "r", "", depends_on=("s3",)),
            Step("s2", "r", "", depends_on=("s1",)),
            Step("s3", "r", "", depends_on=("s2",)),
        ),
    ):
        with pytest.raises(WorkflowError):
            Workflow(cycle).order()
        with pytest.raises(WorkflowError):
            Workflow(cycle).stages()
