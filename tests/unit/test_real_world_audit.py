"""Regression tests for the real-world configuration study (Task 5 / protocol-v4)."""

from __future__ import annotations

from guide_bench.real_world.audit import audit_one
from guide_bench.real_world.configs import load_configs


def test_dataset_size_and_pattern_coverage() -> None:
    cfgs = load_configs()
    assert 15 <= len(cfgs) <= 20
    domains = {c.domain for c in cfgs}
    patterns = {c.pattern for c in cfgs}
    assert domains == {"customer_support", "sql_analysis", "it_change_mgmt", "doc_retrieval_synthesis", "code_review"}
    assert patterns == {"langgraph", "crewai", "autogen"}
    for pat in patterns:
        assert sum(1 for c in cfgs if c.pattern == pat) >= 3


def test_config_ids_unique() -> None:
    cfgs = load_configs()
    ids = [c.config_id for c in cfgs]
    assert len(set(ids)) == len(ids)


def test_every_nominal_call_is_admitted_by_its_own_config_authority() -> None:
    """synthesize_least_privilege raises if a nominal call is outside authority; audit_one must not raise."""
    for cfg in load_configs():
        audit_one(cfg)  # raises ValueError on inconsistency


def test_least_privilege_never_denies_a_nominal_call() -> None:
    for cfg in load_configs():
        result = audit_one(cfg)
        assert result["nominal_calls_denied_under_lp"] == 0, cfg.config_id
        assert result["nominal_preserved"] is True


def test_least_privilege_never_increases_sink_capabilities() -> None:
    for cfg in load_configs():
        result = audit_one(cfg)
        assert result["lp_sink_total"] <= result["nominal_sink_total"], cfg.config_id
