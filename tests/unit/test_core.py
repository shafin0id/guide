from __future__ import annotations

import dataclasses

import pytest

from guide import (
    ContentStore,
    Decision,
    IntegrityError,
    IntentPackage,
    KeyRing,
    Policy,
    PolicyContext,
    RulePolicyEngine,
    Sensitivity,
    Step,
    ToolCall,
    ToolRegistry,
    TraceLedger,
    Workflow,
    WorkflowError,
    open_sealed,
    seal,
)
from guide.agent import parse_reply
from guide.errors import MalformedOutputError
from guide.routing import BayesUCBRouter, StaticRouter, beta_cdf, beta_ppf
from guide_bench.env import Environment

# ----------------------------------------------------------------------------- routing


@pytest.mark.parametrize("q,a,b", [(0.5, 1, 1), (0.9, 2, 5), (0.99, 10, 3), (0.999, 1, 30), (0.05, 40, 40)])
def test_beta_ppf_matches_scipy(q, a, b):
    scipy_stats = pytest.importorskip("scipy.stats")
    assert beta_ppf(q, a, b, pure=True) == pytest.approx(scipy_stats.beta.ppf(q, a, b), abs=1e-7)
    assert beta_ppf(q, a, b) == pytest.approx(beta_ppf(q, a, b, pure=True), abs=1e-7)
    assert beta_cdf(scipy_stats.beta.ppf(q, a, b), a, b) == pytest.approx(q, abs=1e-8)


def test_bayes_ucb_warmup_then_prefers_better_agent():
    r = BayesUCBRouter()
    assert r.select("d", ["a", "b"]).rule == "warmup"
    r.update("d", "a", True)
    assert r.select("d", ["a", "b"]).agent == "b"
    r.update("d", "b", False)
    for _ in range(20):
        r.update("d", "a", True)
        r.update("d", "b", False)
    d = r.select("d", ["a", "b"])
    assert d.rule == "bayes_ucb" and d.agent == "a"


def test_bayes_ucb_discount_forgets_old_evidence():
    r = BayesUCBRouter(discount=0.5)
    for _ in range(30):
        r.update("d", "a", True)
    a, b = r.posterior("d", "a")
    assert a < 3.1 and b == pytest.approx(1.0)


def test_failure_penalty_only_on_confident_failure():
    r = BayesUCBRouter(failure_penalty=5.0)
    r.update("d", "a", False, confidence=0.5)
    assert r.posterior("d", "a")[1] == 2.0
    r.update("d", "a", False, confidence=0.95)
    assert r.posterior("d", "a")[1] == 8.0


def test_static_router():
    assert StaticRouter().select("d", ["x", "y"]).agent == "x"
    assert StaticRouter({"d": "y"}).select("d", ["x", "y"]).agent == "y"


# ----------------------------------------------------------------------------- policy


@pytest.fixture
def gate():
    env = Environment()
    reg = ToolRegistry(env.tools)
    pol = Policy(
        "p",
        {"procurement_db": frozenset({"query"}), "email": frozenset({"send"})},
        allow_external=True,
        recipient_domains=frozenset({"corp.example"}),
    )
    return RulePolicyEngine(pol, reg)


CTX = PolicyContext("run", "s", frozenset({"procurement_db", "email"}))


def call(tool, op, **args):
    return ToolCall(tool, op, args, "agent")


def test_unknown_and_unpermitted_tools_denied(gate):
    assert gate.evaluate(call("nope", "x"), CTX).rule == "tool.unknown"
    assert gate.evaluate(call("incident_logs", "query"), CTX).rule == "tool.not_permitted"
    assert gate.evaluate(call("procurement_db", "delete", vendor_id="V-1"), CTX).rule == "tool.not_permitted"


def test_tool_must_be_delegated_to_step(gate):
    ctx = PolicyContext("run", "s", frozenset({"email"}))
    assert gate.evaluate(call("procurement_db", "query"), ctx).rule == "tool.not_delegated"


def test_restricted_columns_are_bounded_not_trusted_from_proposer(gate):
    d = gate.evaluate(call("procurement_db", "query", columns=["vendor_id", "unit_price_usd"]), CTX)
    assert d.decision is Decision.BOUND and d.call.args["columns"] == ["vendor_id"]
    d_all = gate.evaluate(call("procurement_db", "query"), CTX)  # "all columns" is projected too
    assert "unit_price_usd" not in d_all.call.args["columns"] and "vendor_id" in d_all.call.args["columns"]
    assert gate.evaluate(call("procurement_db", "query", columns=["unit_price_usd"]), CTX).decision is Decision.DENY


def test_unknown_column_is_denied_with_valid_names_not_silently_dropped(gate):
    """Pilot finding #1: silently removing a misspelled column made agents report null values."""
    d = gate.evaluate(call("procurement_db", "query", columns=["sla_delivery_days"]), CTX)
    assert d.rule == "argument.unknown_column" and "delivery_sla_days" in d.reason
    res = Environment().tools[0].invoke("query", {"columns": ["sla_delivery_days"]})
    assert not res.ok and "delivery_sla_days" in res.error


def test_numeric_bound_is_projection_onto_interval(gate):
    d = gate.evaluate(call("procurement_db", "query", columns=["vendor_id"], limit=100000), CTX)
    assert d.decision is Decision.BOUND and d.call.args["limit"] == 100
    assert (
        gate.evaluate(call("procurement_db", "query", columns=["vendor_id"], limit="lots"), CTX).rule
        == "argument.invalid"
    )


def test_external_recipient_domain_allow_list(gate):
    ok = gate.evaluate(call("email", "send", recipient="a@corp.example", subject="s", body="b"), CTX)
    assert ok.decision is Decision.ALLOW
    bad = gate.evaluate(call("email", "send", recipient="a@evil.example", subject="s", body="b"), CTX)
    assert bad.rule == "external.recipient_domain"


def test_policy_digest_is_stable_and_sensitive():
    a = Policy("p", {"t": frozenset({"x", "y"})})
    b = Policy("p", {"t": frozenset({"y", "x"})})
    assert a.digest() == b.digest()
    assert a.digest() != dataclasses.replace(a, allow_write=True).digest()


# ----------------------------------------------------------------------------- hand-off


def _pkg(**kw) -> IntentPackage:
    base = dict(
        run_id="r",
        handoff_id="h",
        parent_hash="p" * 64,
        sender="alice",
        receiver="bob",
        objective="o",
        constraints=("c1",),
        input_refs=(),
        permitted_tools=("t",),
        expected_schema={},
        issued_at_ms=0,
        expiry_ms=10**15,
    )
    base.update(kw)
    return IntentPackage(**base)


@pytest.fixture
def keys():
    k = KeyRing()
    for p in ("alice", "bob", "mallory"):
        k.enroll(p)
    return k


def test_seal_open_roundtrip(keys):
    pkg = _pkg()
    assert open_sealed(seal(pkg, keys), keys, expected_parent="p" * 64, expected_receiver="bob") == pkg


@pytest.mark.parametrize(
    "mutate,reason",
    [
        (lambda w: w["package"].__setitem__("constraints", []), "content"),
        (lambda w: w["package"].pop("objective"), "schema"),
        (lambda w: w["package"].__setitem__("extra", 1), "schema"),
        (lambda w: w["package"].__setitem__("expiry_ms", "soon"), "schema"),
        (lambda w: w.__setitem__("signature", "00" * 64), "signature"),
        (lambda w: w.__setitem__("link_hash", "0" * 64), "content"),
    ],
)
def test_tampering_is_rejected(keys, mutate, reason):
    wire = seal(_pkg(), keys)
    mutate(wire)
    with pytest.raises(IntegrityError) as exc:
        open_sealed(wire, keys, expected_parent="p" * 64, expected_receiver="bob")
    assert exc.value.reason.startswith(reason)


def test_lineage_receiver_and_expiry_checks(keys):
    wire = seal(_pkg(expiry_ms=5), keys)
    with pytest.raises(IntegrityError, match="lineage"):
        open_sealed(wire, keys, expected_parent="q" * 64, expected_receiver="bob")
    with pytest.raises(IntegrityError, match="routing"):
        open_sealed(wire, keys, expected_parent="p" * 64, expected_receiver="mallory")
    with pytest.raises(IntegrityError, match="expiry"):
        open_sealed(wire, keys, expected_parent="p" * 64, expected_receiver="bob", now_ms=6)


def test_sender_spoofing_is_rejected_with_per_principal_keys(keys):
    forged = _pkg(sender="alice")
    link = forged.link_hash()
    wire = {"package": forged.to_dict(), "link_hash": link, "signature": keys.sign("mallory", link.encode())}
    with pytest.raises(IntegrityError, match="signature"):
        open_sealed(wire, keys, expected_parent="p" * 64, expected_receiver="bob")


def test_content_store_detects_tampering():
    cas = ContentStore()
    ref = cas.put({"a": 1})
    assert cas.get(ref) == {"a": 1}
    cas._blobs[ref] = b'{"a":2}'
    with pytest.raises(IntegrityError):
        cas.get(ref)


# ----------------------------------------------------------------------------- trace


def test_trace_chain_and_tamper_detection():
    led = TraceLedger("r", "o", "pd")
    for i in range(4):
        led.append("k", {"i": i, "api_key": "secret"})
    assert led.verify() == (True, None)
    assert led.events[0].data["api_key"] == "[REDACTED]"
    evs = list(led.events)
    evs[2] = dataclasses.replace(evs[2], data={"i": 99})
    assert led.verify(tuple(evs)) == (False, 2)


# ----------------------------------------------------------------------------- workflow + protocol


def test_workflow_order_and_validation():
    wf = Workflow(
        (Step("c", "r", "", depends_on=("a", "b")), Step("a", "r", ""), Step("b", "r", "", depends_on=("a",)))
    )
    assert [s.step_id for s in wf.order()] == ["a", "b", "c"]
    with pytest.raises(WorkflowError, match="cycle"):
        Workflow((Step("a", "r", "", depends_on=("b",)), Step("b", "r", "", depends_on=("a",)))).order()
    with pytest.raises(WorkflowError, match="unknown"):
        Workflow((Step("a", "r", "", depends_on=("z",)),)).order()


def test_parse_reply():
    assert parse_reply('{"tool_calls": [], "output": {"x": 1}, "confidence": 0.7}').output == {"x": 1}
    assert parse_reply('```json\n{"tool_calls": [{"tool": "t", "operation": "o"}]}\n```').tool_calls[0]["args"] == {}
    for bad in ["not json", "[]", '{"tool_calls": "x"}', '{"tool_calls": []}', '{"tool_calls": [{"tool": 1}]}']:
        with pytest.raises(MalformedOutputError):
            parse_reply(bad)


def test_sensitivity_parse():
    assert Sensitivity.parse("restricted") is Sensitivity.RESTRICTED


def test_numeric_bounding_cannot_change_authorized_recipient():
    from guide.tools import OperationSpec, ToolSpec
    from guide.types import ToolResult

    class NumericDestinationTool:
        spec = ToolSpec(
            "notify", "numeric destination", "messages",
            {"send": OperationSpec("send", external=True, control_params=("recipient",))},
        )

        def invoke(self, operation, args):
            return ToolResult(True, args)

    reg = ToolRegistry([NumericDestinationTool()])
    policy = Policy(
        "numeric-recipient", {"notify": frozenset({"send"})},
        allow_external=True, allowed_recipients=frozenset({"100"}),
        numeric_bounds={"recipient": (0, 10)},
    )
    decision = RulePolicyEngine(policy, reg).evaluate(
        ToolCall("notify", "send", {"recipient": "100"}, "agent"),
        PolicyContext("run", "step", frozenset({"notify"})),
    )
    assert decision.decision is Decision.DENY
    assert decision.rule == "external.recipient_changed"
