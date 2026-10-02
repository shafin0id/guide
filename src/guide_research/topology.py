"""Protocol v7c: blast-radius-minimal agent topology.

For a fixed workflow (steps and nominal calls), explores every way of partitioning its
steps across agents (one partition block = one agent), crossed with hand-off mode
(TRANSCRIPT / SIGNED) and policy (nominal / least-privilege), and computes the worst-case
blast-radius fraction WBR_k for k = 1, 2 compromised agents. See
docs/static-analysis-extensions-plan.md §2 for the frozen specification.

Core (`guide`) never imports this module (layer rule Core <- Research <- Bench).
"""

from __future__ import annotations

import itertools
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, replace

from guide.agent import AgentSpec
from guide.runtime import HandoffMode
from guide.workflow import Step, Workflow
from guide_research.blast_radius import SystemModel, authority, blast_radius

# ----------------------------------------------------------------------------- set partitions


def set_partitions(n: int) -> list[tuple[int, ...]]:
    """All partitions of {0..n-1} as restricted-growth strings (RGS), canonical order.

    An RGS a[0..n-1] has a[0] = 0 and a[i] <= 1 + max(a[0..i-1]). Enumeration order is
    lexicographic over the RGS itself, which is the canonical order for this plan (frozen
    tie-break: lexicographically smallest RGS wins a tie).
    """
    if n == 0:
        return []
    result: list[tuple[int, ...]] = []
    a = [0] * n

    def rec(i: int, max_so_far: int) -> None:
        if i == n:
            result.append(tuple(a))
            return
        for v in range(max_so_far + 2):
            a[i] = v
            rec(i + 1, max(max_so_far, v))

    rec(1, 0)
    return result


def n_blocks(rgs: Sequence[int]) -> int:
    return max(rgs) + 1 if rgs else 0


# ----------------------------------------------------------------------------- model construction


def apply_partition(model: SystemModel, rgs: Sequence[int]) -> SystemModel:
    """Rebuild `model` with its steps reassigned to one agent per partition block.

    Block i gets role f"r{i}" and agent AgentSpec(f"a{i}", f"r{i}", ""). Each step keeps
    its id, tools, instruction and depends_on; only its role changes (dataclasses.replace).
    """
    steps = model.workflow.steps
    if len(rgs) != len(steps):
        raise ValueError(f"partition length {len(rgs)} != step count {len(steps)}")
    new_steps = tuple(replace(s, role=f"r{rgs[i]}") for i, s in enumerate(steps))
    m = n_blocks(rgs)
    agents = tuple(AgentSpec(f"a{i}", f"r{i}", "") for i in range(m))
    return replace(model, workflow=Workflow(new_steps), agents=agents)


# ----------------------------------------------------------------------------- WBR


def _distinct_sinks(caps: Iterable) -> frozenset[tuple[str, str]]:  # type: ignore[type-arg]
    return frozenset((c.tool, c.operation) for c in caps if c.is_sink)


def total_sinks_star(model: SystemModel) -> frozenset[tuple[str, str]]:
    """Sinks*(c): distinct (tool, operation) write/external pairs reachable by ANY single
    step's authority under this model (the union over all steps, i.e. the structural ceiling)."""
    out: set[tuple[str, str]] = set()
    for step in model.workflow.steps:
        out |= _distinct_sinks(authority(model, step))
    return frozenset(out)


def wbr(model: SystemModel, k: int, sinks_star: frozenset[tuple[str, str]] | None = None) -> float:
    """WBR_k: worst-case blast-radius fraction over every agent subset of size k.

    Returns 0.0 if there are fewer than k agents (k=2 is skipped by the caller in that case,
    but this returns a well-defined 0.0 rather than raising) or if Sinks* is empty.
    """
    agent_ids = [a.agent_id for a in model.agents]
    if sinks_star is None:
        sinks_star = total_sinks_star(model)
    denom = len(sinks_star)
    if denom == 0 or len(agent_ids) < k:
        return 0.0
    worst = 0
    for subset in itertools.combinations(agent_ids, k):
        br = blast_radius(model, frozenset(subset))
        reached = len(_distinct_sinks(br.capabilities))
        worst = max(worst, reached)
    return worst / denom


# ----------------------------------------------------------------------------- frontier


@dataclass(frozen=True)
class FrontierRow:
    config_id: str
    mode: str
    policy_kind: str  # "nominal" | "least_privilege"
    m_blocks: int
    k: int
    min_wbr: float
    argmin_rgs: tuple[int, ...]
    n_tied: int


def frontier(
    config_id: str,
    base_model: SystemModel,
    mode: HandoffMode,
    policy_kind: str,
    k_values: tuple[int, ...] = (1, 2),
) -> list[FrontierRow]:
    """For each block count m = 1..n_steps, the minimum WBR_k over all partitions with m
    blocks, the (lexicographically smallest, on tie) argmin RGS, and the tie count."""
    n_steps = len(base_model.workflow.steps)
    model = replace(base_model, mode=mode)
    sinks_star = total_sinks_star(apply_partition(model, tuple(range(n_steps))))  # identity partition ceiling
    all_rgs = set_partitions(n_steps)
    by_m: dict[int, list[tuple[int, ...]]] = {}
    for rgs in all_rgs:
        by_m.setdefault(n_blocks(rgs), []).append(rgs)

    rows: list[FrontierRow] = []
    for k in k_values:
        for m in range(1, n_steps + 1):
            if m < k:
                continue  # fewer blocks than k: WBR_k undefined for this m, skip per §2.2
            best_wbr = None
            best_rgs = None
            tied = 0
            for rgs in sorted(by_m.get(m, [])):
                partitioned = apply_partition(model, rgs)
                w = wbr(partitioned, k, sinks_star=sinks_star)
                if best_wbr is None or w < best_wbr:
                    best_wbr = w
                    best_rgs = rgs
                    tied = 1
                elif w == best_wbr:
                    tied += 1
            if best_wbr is not None and best_rgs is not None:
                rows.append(FrontierRow(config_id, mode.value, policy_kind, m, k, best_wbr, best_rgs, tied))
    return rows
