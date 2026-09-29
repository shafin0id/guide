"""Regression tests for the evaluation-integrity defects found in the P0 audit (docs/research-audit.md §3)."""

from __future__ import annotations

import inspect

import pytest

from guide import ConfigurationError, KeyRing, OpenAICompatibleProvider
from guide.runtime import RunRecord
from guide_bench import scoring
from guide_bench.env import SideEffects
from guide_bench.tasks import main_tasks


def test_E1_E2_scoring_has_no_condition_input():
    for name, fn in inspect.getmembers(scoring, inspect.isfunction):
        params = set(inspect.signature(fn).parameters)
        assert not params & {"condition", "cond", "hops"}, f"{name} takes a condition-like parameter"


def test_E1_identical_outputs_score_identically_across_labels():
    task = main_tasks()[0]
    final = {"vendor_id": "V-001", "delivery_sla_days": 5, "uptime_guarantee_pct": 99.95, "compliance_tier": "ISO27001"}
    scores = []
    for label in ("B1", "B2", "P", "GPLUS"):
        rec = RunRecord(run_id=label, task_id=task.task_id, status="completed", final_output=final)
        scores.append(scoring.score(task.constraints, scoring.Outcome(rec, SideEffects())))
    assert len(set(scores)) == 1 and scores[0].task_success == 1


def test_E4_no_silent_offline_fallback(monkeypatch):
    monkeypatch.delenv("GUIDE_TEST_MISSING_KEY", raising=False)
    with pytest.raises(ConfigurationError):
        OpenAICompatibleProvider(model="m", base_url="http://127.0.0.1:9", api_key_env="GUIDE_TEST_MISSING_KEY")


def test_E4_core_has_no_answer_producing_stub():
    import guide.providers as providers

    source = inspect.getsource(providers)
    for leaked in ("Apex Cloud", "V-001", "INC-1001", "DOC-RCA"):
        assert leaked not in source


def test_E6_harness_reports_exactly_what_the_system_produced():
    """The harness must not add, fill or repair fields of the system's deliverable."""
    from conftest import make_script
    from guide import ModelSettings, ScriptedProvider
    from guide_bench.adversarial import AdversarialCase
    from guide_bench.conditions import CONDITIONS, make_router
    from guide_bench.run import Item, execute

    partial = {"vendor_id": "V-001"}  # deliberately incomplete deliverable
    script = make_script({"tool": "procurement_db", "operation": "query", "args": {}}, partial)
    for cond in ("B1", "P", "GPLUS"):
        item = Item(AdversarialCase(main_tasks()[0], "none"), cond, 1)
        row, _ = execute(item, ScriptedProvider(script), make_router(CONDITIONS[cond]), ModelSettings())
        assert row["final_output"] == partial
        assert row["task_success"] == 0 and row["constraints_passed"] == 1  # only the no-leak constraint holds


def test_shared_key_regression_each_principal_has_its_own_key():
    k = KeyRing()
    k.enroll("a")
    k.enroll("b")
    assert k._public["a"].public_bytes_raw() != k._public["b"].public_bytes_raw()


def test_constraint_tiers_match_proposal():
    counts = {"LOW": 4, "MEDIUM": 6, "HIGH": 8}
    tasks = main_tasks()
    assert len(tasks) == 18
    for t in tasks:
        assert len(t.constraints) == counts[t.tier], t.task_id
    assert {t.family for t in tasks} == {"constrained_synthesis", "evidence_reconciliation", "policy_planning"}
