"""Topology floor (Proposition 4) and chain/dominating-source structural predicates.

Formal proof in docs/formal_model.md.
Implements closed-form floor, step reachability under the finest partition,
and chain/dominating-source structural checks.
(The Protocol v8 M2 benchmark runner lives in guide_bench.topology_v8.)
"""

from __future__ import annotations

from collections.abc import Iterable

from guide.workflow import Step, Workflow
from guide_research import topology
from guide_research.blast_radius import SystemModel, blast_radius


def step_reach(model: SystemModel, step_id: str) -> frozenset[tuple[str, str]]:
    """R(s): distinct (tool, operation) sinks reachable when step s is compromised
    under the finest partition Pi_bot (one agent per step).
    """
    steps = model.workflow.steps
    n = len(steps)
    fine_model = topology.apply_partition(model, tuple(range(n)))
    try:
        idx = next(i for i, s in enumerate(steps) if s.step_id == step_id)
    except StopIteration as err:
        raise KeyError(f"Step '{step_id}' not found in workflow") from err
    agent_id = fine_model.agents[idx].agent_id
    br = blast_radius(fine_model, frozenset([agent_id]))
    return topology._distinct_sinks(br.capabilities)


def closed_form_floor(model: SystemModel) -> float:
    """Proposition 4(a): min_Pi WBR_1(Pi) = max_s |R(s)| / |Sinks*|."""
    sinks_star = topology.total_sinks_star(model)
    denom = len(sinks_star)
    if denom == 0:
        return 0.0
    steps = model.workflow.steps
    if not steps:
        return 0.0
    max_reach = max(len(step_reach(model, s.step_id)) for s in steps)
    return max_reach / denom


def has_dominating_source(workflow: Workflow, sink_steps: Iterable[str | Step]) -> bool:
    """True iff some step r reaches every step in sink_steps along depends_on edges."""
    sink_ids = {s if isinstance(s, str) else s.step_id for s in sink_steps}
    if not sink_ids:
        return False

    adj: dict[str, set[str]] = {s.step_id: set() for s in workflow.steps}
    for s in workflow.steps:
        for p in s.depends_on:
            if p in adj:
                adj[p].add(s.step_id)

    for r in workflow.steps:
        visited: set[str] = set()
        queue = [r.step_id]
        while queue:
            curr = queue.pop(0)
            if curr not in visited:
                visited.add(curr)
                queue.extend(adj.get(curr, set()) - visited)
        if sink_ids.issubset(visited):
            return True
    return False


def is_chain(workflow: Workflow) -> bool:
    """True iff every non-first step has depends_on == (previous step id,) in list order."""
    steps = workflow.steps
    if not steps:
        return True
    if steps[0].depends_on != ():
        return False
    for i in range(1, len(steps)):
        if steps[i].depends_on != (steps[i - 1].step_id,):
            return False
    return True
