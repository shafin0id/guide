"""Unit tests for GUIDE AgentDojo adapter."""

from agentdojo.benchmark import get_suite

from guide.policy import Decision, PolicyContext, RulePolicyEngine
from guide.types import ToolCall, Trust
from guide_agentdojo.bound import audit_all_suites
from guide_agentdojo.policy import build_suite_policy
from guide_agentdojo.specs import DOJO_TOOL_SECURITY, build_tool_registry
from guide_research.provenance import ProvenanceGuard


def test_tool_security_classification_covers_suites():
    for suite_name in ["banking", "slack", "travel", "workspace"]:
        suite = get_suite("v1.2.2", suite_name)
        for tool in suite.tools:
            assert tool.name in DOJO_TOOL_SECURITY, f"Missing security classification for {tool.name} in {suite_name}"
            is_write, is_ext, control_params, res_class = DOJO_TOOL_SECURITY[tool.name]
            assert isinstance(is_write, bool)
            assert isinstance(is_ext, bool)
            assert isinstance(control_params, tuple)
            assert isinstance(res_class, str)


def test_tool_registry_and_policy():
    suite = get_suite("v1.2.2", "banking")
    registry = build_tool_registry(suite.tools)
    policy = build_suite_policy("banking", suite.tools)

    assert registry.has("send_money")
    assert registry.has("get_balance")
    assert "send_money" in policy.permitted
    assert "get_balance" in policy.permitted


def test_gate_and_provenance_containment():
    suite = get_suite("v1.2.2", "banking")
    registry = build_tool_registry(suite.tools)
    policy = build_suite_policy("banking", suite.tools)

    engine = RulePolicyEngine(policy, registry)
    guard = ProvenanceGuard(engine, registry, match="substring")

    run_id = "test-run-1"
    trusted_query = "Please send 50 euros to GB29NWBK60161331926819 for dinner."
    guard.observe(run_id, {"objective": trusted_query}, Trust.TRUSTED)

    # Legitimate call (recipient in trusted prompt) -> ALLOW
    legit_call = ToolCall(
        tool="send_money",
        operation="send_money",
        args={"recipient": "GB29NWBK60161331926819", "amount": 50, "subject": "dinner", "date": "2026-10-02"},
        principal="agent",
    )
    ctx = PolicyContext(run_id=run_id, step_id="step-1", step_tools=frozenset(policy.permitted.keys()))
    legit_decision = guard.evaluate(legit_call, ctx)
    assert legit_decision.decision is Decision.ALLOW

    # Attacker injection call (attacker IBAN from injection) -> DENIED
    attack_call = ToolCall(
        tool="send_money",
        operation="send_money",
        args={"recipient": "US133000000121212121212", "amount": 1000, "subject": "exploit", "date": "2026-10-02"},
        principal="agent",
    )
    attack_decision = guard.evaluate(attack_call, ctx)
    assert attack_decision.decision is Decision.DENY
    assert attack_decision.rule == "provenance.control_unsupported"

    guard.forget(run_id)


def test_static_bound_all_suites():
    summaries = audit_all_suites("v1.2.2")
    assert len(summaries) == 4
    for s in summaries:
        assert s.total_tools > 0
        assert s.ungated_unconstrained_sinks > 0
        assert s.gplus_constrained_sinks == s.ungated_unconstrained_sinks
        assert len(s.sink_control_params) == s.gplus_constrained_sinks


def test_pipeline_attack_compatibility():
    from agentdojo.attacks.attack_registry import load_attack

    from guide_agentdojo.pipeline import GuideGplusPipeline

    suite = get_suite("v1.2.2", "banking")
    pipeline = GuideGplusPipeline(api_key="mock_key", name="guide-gplus-local")
    attack = load_attack("important_instructions", suite, pipeline)
    assert attack is not None
    assert attack.name == "important_instructions"

