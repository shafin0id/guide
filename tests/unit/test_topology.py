"""Tests for guide_research.topology (protocol-v7c).

Covers: partition counts against Bell numbers, refinement-monotonicity (the new
proposition in docs/formal_model.md), reproduction of the original blast radius when the
partition is the identity, and determinism of the tie-break.
"""

from __future__ import annotations

import itertools
from dataclasses import replace

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from guide.runtime import HandoffMode
from guide_bench.real_world.configs import load_configs
from guide_research.blast_radius import SystemModel, blast_radius
from guide_research.topology import apply_partition, n_blocks, set_partitions, wbr

BELL = {0: 1, 1: 1, 2: 2, 3: 5, 4: 15, 5: 52, 6: 203}


def test_partition_counts_match_bell_numbers() -> None:
    for n in range(1, 7):
        assert len(set_partitions(n)) == BELL[n], n


def test_partitions_are_valid_restricted_growth_strings() -> None:
    for n in range(1, 6):
        for rgs in set_partitions(n):
            assert rgs[0] == 0
            running_max = 0
            for v in rgs:
                assert 0 <= v <= running_max + 1
                running_max = max(running_max, v)


def test_tie_break_is_deterministic() -> None:
    """Re-running set_partitions must return the same order every time (no set/dict iteration leaks)."""
    a = set_partitions(5)
    b = set_partitions(5)
    assert a == b
    assert a == sorted(a)  # canonical lexicographic order over the RGS


# ----------------------------------------------------------------------------- identity reproduces original BR


def test_identity_partition_reproduces_original_blast_radius() -> None:
    for cfg in load_configs():
        model = SystemModel.for_task(
            cfg.task, cfg.agents, cfg.policy, cfg.registry, mode=HandoffMode.TRANSCRIPT, gate="rule"
        )
        n = len(model.workflow.steps)
        if n > len(cfg.agents):
            continue  # identity partition needs one agent per step; skip configs with fewer agents than steps
        identity = tuple(range(n))
        partitioned = apply_partition(model, identity)
        for agent in model.agents:
            k = frozenset({agent.agent_id})
            br_original = blast_radius(model, k)
            # the matching singleton agent in the partitioned model is a{step_index}
            step_idx = next(i for i, s in enumerate(model.workflow.steps) if agent.role == s.role)
            br_partitioned = blast_radius(partitioned, frozenset({f"a{step_idx}"}))
            assert {(c.tool, c.operation) for c in br_original.capabilities if c.step == model.workflow.steps[step_idx].step_id} <= {
                (c.tool, c.operation) for c in br_partitioned.capabilities
            }


# ----------------------------------------------------------------------------- refinement monotonicity (Proposition 3)


def _refining_pairs(n_steps: int) -> list[tuple[tuple[int, ...], tuple[int, ...]]]:
    """Every (coarse, fine) pair where `fine` refines `coarse` by splitting exactly one block in two."""
    pairs: list[tuple[tuple[int, ...], tuple[int, ...]]] = []
    for coarse in set_partitions(n_steps):
        m = n_blocks(coarse)
        for block in range(m):
            members = [i for i, b in enumerate(coarse) if b == block]
            if len(members) < 2:
                continue
            # split `members` into two non-empty groups; the first group keeps `block`'s id,
            # the second gets a fresh id appended after the current max.
            for r in range(1, len(members)):
                for combo in itertools.combinations(members, r):
                    group_b = set(combo)
                    fine = list(coarse)
                    new_id = m  # fresh block id, placed after existing ones
                    for i in members:
                        if i in group_b:
                            fine[i] = new_id
                    pairs.append((coarse, tuple(fine)))
    return pairs


@settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(
    cfg_idx=st.integers(min_value=0, max_value=len(load_configs()) - 1),
    k=st.sampled_from((1, 2)),
    mode=st.sampled_from((HandoffMode.TRANSCRIPT, HandoffMode.SIGNED)),
)
def test_refinement_monotonicity(cfg_idx: int, k: int, mode: HandoffMode) -> None:
    """Proposition 3 (refinement monotonicity): if partition P' refines P, then for fixed
    mode, policy and k, WBR_k(P') <= WBR_k(P). Any counterexample is soundness-critical —
    see docs/static-analysis-extensions-plan.md §2.3 and §5 (stop condition)."""
    cfg = load_configs()[cfg_idx]
    base = SystemModel.for_task(cfg.task, cfg.agents, cfg.policy, cfg.registry, mode=mode, gate="rule")
    n = len(base.workflow.steps)
    if n > 6:
        return  # restricted to configs with <= 6 steps per plan §2.3 step 1
    for coarse, fine in _refining_pairs(n):
        m_coarse = apply_partition(base, coarse)
        m_fine = apply_partition(base, fine)
        if min(len(m_coarse.agents), len(m_fine.agents)) < k:
            continue
        w_coarse = wbr(m_coarse, k)
        w_fine = wbr(m_fine, k)
        assert w_fine <= w_coarse + 1e-9, (
            f"MONOTONICITY COUNTEREXAMPLE: config={cfg.config_id} k={k} mode={mode.value} "
            f"coarse={coarse} (wbr={w_coarse}) fine={fine} (wbr={w_fine})"
        )
