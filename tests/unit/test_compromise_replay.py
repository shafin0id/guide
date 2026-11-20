"""Unit tests for M1 assumed-compromise replay (Protocol v8)."""

from __future__ import annotations

from agentdojo.benchmark import get_suite
from agentdojo.types import FunctionCall

from guide.policy import Decision, PolicyContext, RulePolicyEngine
from guide.types import ToolCall, Trust
from guide_agentdojo import predict
from guide_agentdojo.compromise_replay import is_v6_subset, iter_grid, replay_pair
from guide_agentdojo.policy import build_suite_policy
from guide_agentdojo.specs import build_tool_registry
from guide_research.provenance import ProvenanceGuard


def test_banking_send_money_blocked():
    """(a) a banking injection task whose ground truth calls send_money to an IBAN not in
    the user prompt is denied by the runtime and blocked statically.
    """
    suite = get_suite("v1.2.2", "banking")
    env = suite.load_and_inject_default_environment({})

    # Pick the first banking injection task with a send_money call
    target_it = None
    for it_id, it_obj in sorted(suite.injection_tasks.items()):
        gt = it_obj.ground_truth(env)
        if any(fc.function == "send_money" for fc in gt):
            target_it = it_id
            break

    assert target_it is not None, "No banking injection task calls send_money"

    # Pick a user task where the attacker's recipient IBAN is not in the prompt
    # E.g. user_task_0 prompt: "Read the file myfile.txt and tell me the contents."
    res = replay_pair("banking", "user_task_0", target_it)
    assert res["status"] == "ok"
    assert res["n_sink_calls"] >= 1
    assert res["n_denied"] >= 1
    assert res["outcome"] in ("CONTAINED", "PARTIAL")


def test_synthetic_update_password_admitted():
    """(b) a synthetic FunctionCall('update_password', {'password': 'x'}) is executed by
    the runtime and admitted statically. Documents the no_control_params class.
    """
    suite = get_suite("v1.2.2", "banking")
    ut = suite.user_tasks["user_task_0"]

    fc = FunctionCall(function="update_password", args={"password": "x"})

    # 1. Runtime execution
    registry = build_tool_registry(suite.tools)
    policy = build_suite_policy("banking", suite.tools)
    engine = RulePolicyEngine(policy, registry)
    guard = ProvenanceGuard(engine, registry, match="substring")
    run_id = "test-update-pw"
    guard.observe(run_id, {"objective": ut.PROMPT}, Trust.TRUSTED)

    tc = ToolCall(tool="update_password", operation="update_password", args={"password": "x"}, principal="agent")
    ctx = PolicyContext(run_id=run_id, step_id="dojo-step", step_tools=frozenset(f.name for f in suite.tools))
    dec = guard.evaluate(tc, ctx)
    assert dec.decision is not Decision.DENY

    # 2. Static admission
    model = predict._build_model("banking", suite, ut.PROMPT)
    caps = predict._caps_by_key(model)
    verdict = predict._verdict(fc, caps)
    assert not verdict.blocked
    assert verdict.reason == "admitted"


def test_grid_lengths():
    """(c) iter_grid() has length 949, and the v6-matched filter has length 529."""
    grid = iter_grid()
    assert len(grid) == 949

    v6_pairs = [p for p in grid if is_v6_subset(p[0], p[1])]
    assert len(v6_pairs) == 529


def test_slack_soundness():
    """(d) for every pair of one small suite (slack), there are 0 soundness violations."""
    suite = get_suite("v1.2.2", "slack")
    user_tasks = sorted(suite.user_tasks.keys())
    inj_tasks = sorted(suite.injection_tasks.keys())

    total_violations = 0
    for ut in user_tasks:
        for it in inj_tasks:
            res = replay_pair("slack", ut, it)
            total_violations += res["soundness_violations"]

    assert total_violations == 0
