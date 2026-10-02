"""Tests for guide_bench.mining.audit statistical helpers and model-building (protocol-v7b)."""

from __future__ import annotations

from guide.runtime import HandoffMode
from guide_bench.mining.audit import fisher_exact_two_sided, wilson_interval
from guide_bench.mining.common import ExtractedAgent, ExtractedConfig, ExtractedStep
from guide_bench.mining.to_model import build_model


def test_wilson_interval_known_value() -> None:
    lo, hi = wilson_interval(28, 97)
    p = 28 / 97
    assert lo <= p <= hi
    assert 0.20 < lo < p < hi < 0.40  # sanity bound: interval brackets p=0.289 and is reasonably tight at n=97


def test_wilson_interval_zero_n() -> None:
    assert wilson_interval(0, 0) == (0.0, 0.0)


def test_fisher_exact_matches_known_case() -> None:
    # Classic textbook table: [[1,9],[11,3]] -> two-sided p ~ 0.0013 (Fisher's "Lady Tasting Tea"-style check)
    p = fisher_exact_two_sided(1, 9, 11, 3)
    assert 0.0005 < p < 0.01


def test_fisher_exact_symmetric_table_gives_high_p() -> None:
    p = fisher_exact_two_sided(10, 10, 10, 10)
    assert p > 0.5


def test_build_model_two_agent_shared_tool_creates_state_flow() -> None:
    """Two agents sharing the same tool id must share a resource_class, enabling a state-flow
    influence path per Definition 2 rule St."""
    cfg = ExtractedConfig(
        framework="crewai", repo="x/y", sha="abc", file="f.py",
        agents=[ExtractedAgent("a1", "worker", ["shared_db"]), ExtractedAgent("a2", "writer", ["shared_db"])],
        steps=[
            ExtractedStep("s1", "a1", ["shared_db"], []),
            ExtractedStep("s2", "a2", ["shared_db"], []),
        ],
    )
    model, log = build_model(cfg, mode=HandoffMode.TRANSCRIPT)
    assert model.registry.get("shared_db").spec.resource_class == "shared_db"
    assert log["shared_db"] == ("read", "default_read")  # "shared_db" tokenises to no write/external keyword
