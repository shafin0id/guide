"""Regression tests for all confirmed Stage 3-4 audit defects (ISS-010, ISS-018..ISS-026)."""

from __future__ import annotations

import copy
from types import SimpleNamespace
from typing import Any

import pytest

from guide import ScriptedProvider
from guide.agent import AgentSpec
from guide.errors import WorkflowError
from guide.policy import Decision, Policy, PolicyContext, RulePolicyEngine
from guide.runtime import HandoffMode, Runtime, RuntimeConfig
from guide.tools import OperationSpec, ToolRegistry, ToolSpec
from guide.types import Sensitivity, ToolCall, ToolResult, Trust
from guide.workflow import Step, TaskSpec, Workflow
from guide_agentdojo.pipeline import MALFORMED_ARGS_SENTINEL, _safe_openai_to_assistant_message
from guide_bench.env import Environment
from guide_realworld.core import Runtime as RealWorldRuntime
from guide_realworld.core import Scenario, Task, ToolDef
from guide_research.blast_radius import (
    ObservedCall,
    SystemModel,
    authority,
    blast_radius,
    synthesize_least_privilege,
)
from guide_research.provenance import ProvenanceGuard, corpus_of
from guide_research.provenance_v9 import DIRECTORY_EXTRACTORS, DirectoryGuard


def _reg_with_external(param_name: str = "recipient") -> ToolRegistry:
    class _Stub:
        def __init__(self) -> None:
            self.spec = ToolSpec(
                name="ext_tool",
                description="External sink",
                resource_class="ext",
                operations={
                    "send": OperationSpec(
                        name="send",
                        write_effect=True,
                        external=True,
                        control_params=(param_name,),
                    )
                },
                default_sensitivity=Sensitivity.INTERNAL,
            )

        def invoke(self, operation: str, args: Any) -> ToolResult:
            return ToolResult(ok=True, data={"sent": args})

    return ToolRegistry([_Stub()])


# ----------------------------------------------------------------------------- ISS-018
def test_iss018_rejects_multi_recipient_smuggling_and_strips_whitespace() -> None:
    reg = _reg_with_external("recipient")
    pol = Policy(
        policy_id="p",
        permitted={"ext_tool": frozenset({"send"})},
        allow_write=True,
        allow_external=True,
        recipient_domains=frozenset({"corp.example"}),
        allowed_recipients=frozenset({"ok@corp.example"}),
    )
    eng = RulePolicyEngine(pol, reg)
    ctx = PolicyContext("r1", "s1", frozenset({"ext_tool"}))

    # Multi-recipient smuggling vectors must all be DENIED
    for bad in (
        "evil@bad.com, ok@corp.example",
        "evil@bad.com; ok@corp.example",
        "evil@bad.com ok@corp.example",
        "evil@bad.com\nok@corp.example",
        "Evil <ok@corp.example>",
        ["ok@corp.example", "evil@bad.com"],
        [],
    ):
        d = eng.evaluate(ToolCall("ext_tool", "send", {"recipient": bad}, "a"), ctx)
        assert d.decision is Decision.DENY, f"Expected DENY for {bad!r}, got {d}"

    # Leading/trailing whitespace is consistently normalized across both checks
    d_ok = eng.evaluate(ToolCall("ext_tool", "send", {"recipient": "  OK@CORP.example  "}, "a"), ctx)
    assert d_ok.decision is Decision.ALLOW


def test_iss018_non_recipient_param_checked_when_declared_in_control_params() -> None:
    reg = _reg_with_external("to")
    pol = Policy(
        policy_id="p",
        permitted={"ext_tool": frozenset({"send"})},
        allow_write=True,
        allow_external=True,
        recipient_domains=frozenset({"corp.example"}),
    )
    eng = RulePolicyEngine(pol, reg)
    ctx = PolicyContext("r1", "s1", frozenset({"ext_tool"}))

    assert eng.evaluate(ToolCall("ext_tool", "send", {"to": "evil@outside.org"}, "a"), ctx).decision is Decision.DENY
    assert eng.evaluate(ToolCall("ext_tool", "send", {"to": "alice@corp.example"}, "a"), ctx).decision is Decision.ALLOW


# ----------------------------------------------------------------------------- ISS-019
def test_iss019_rejects_non_list_columns_argument() -> None:
    reg = ToolRegistry(Environment().tools)
    pol = Policy(
        policy_id="p",
        permitted={"procurement_db": frozenset({"query"})},
        max_sensitivity=Sensitivity.RESTRICTED,
    )
    eng = RulePolicyEngine(pol, reg)
    ctx = PolicyContext("r1", "s1", frozenset({"procurement_db"}))

    d = eng.evaluate(ToolCall("procurement_db", "query", {"columns": "unit_price"}, "a"), ctx)
    assert d.decision is Decision.DENY
    assert d.rule == "argument.invalid"


# ----------------------------------------------------------------------------- ISS-020
@pytest.mark.parametrize("bad_val", [float("nan"), float("inf"), float("-inf"), True, False, "nan"])
def test_iss020_rejects_nan_inf_and_bool_in_numeric_bounds(bad_val: Any) -> None:
    reg = ToolRegistry(Environment().tools)
    pol = Policy(
        policy_id="p",
        permitted={"procurement_db": frozenset({"query"})},
        numeric_bounds={"limit": (1, 100)},
    )
    eng = RulePolicyEngine(pol, reg)
    ctx = PolicyContext("r1", "s1", frozenset({"procurement_db"}))

    d = eng.evaluate(ToolCall("procurement_db", "query", {"limit": bad_val}, "a"), ctx)
    assert d.decision is Decision.DENY
    assert d.rule == "argument.invalid"


# ----------------------------------------------------------------------------- ISS-021
def test_iss021_falsy_zero_dict_keys_nested_unicode_and_empty_control() -> None:
    reg = _reg_with_external("target_id")
    pol = Policy(
        policy_id="p",
        permitted={"ext_tool": frozenset({"send"})},
        allow_write=True,
        allow_external=True,
    )
    eng = RulePolicyEngine(pol, reg)
    ctx = PolicyContext("r1", "s1", frozenset({"ext_tool"}))

    # 1. Falsy numeric 0 must NOT bypass provenance check
    guard = ProvenanceGuard(eng, reg, match="substring")
    guard.observe("r1", {"objective": "Send to alice@corp.example", "constraints": ["be brief"]}, Trust.TRUSTED)
    d_zero = guard.evaluate(ToolCall("ext_tool", "send", {"target_id": 0}, "a"), ctx)
    assert d_zero.decision is Decision.DENY
    assert d_zero.rule == "provenance.control_unsupported"

    # 2. Dict keys 'objective' and 'constraints' must NOT pollute trusted corpus
    assert "objective" not in corpus_of({"objective": "Send to alice@corp.example", "constraints": ["be brief"]})
    assert "constraints" not in corpus_of({"objective": "Send to alice@corp.example", "constraints": ["be brief"]})
    d_key = guard.evaluate(ToolCall("ext_tool", "send", {"target_id": "objective"}, "a"), ctx)
    assert d_key.decision is Decision.DENY

    # 3. Nested dict/list smuggling must be flattened and checked
    d_nested = guard.evaluate(
        ToolCall("ext_tool", "send", {"target_id": ["alice@corp.example", {"cc": "evil@attacker.org"}]}, "a"),
        ctx,
    )
    assert d_nested.decision is Decision.DENY

    # 4. Unicode NFKC fullwidth ASCII equivalence
    d_nfkc = guard.evaluate(
        ToolCall("ext_tool", "send", {"target_id": "\uff41\uff4c\uff49\uff43\uff45@corp.example"}, "a"),
        ctx,
    )
    assert d_nfkc.decision is Decision.ALLOW

    # 5. require_nonempty_control=True closes omitted/empty optional control parameters
    strict_nonempty = ProvenanceGuard(eng, reg, match="substring", require_nonempty_control=True)
    strict_nonempty.observe("r1", {"objective": "Create event"}, Trust.TRUSTED)
    for empty_args in ({}, {"target_id": None}, {"target_id": ""}, {"target_id": []}):
        d_empty = strict_nonempty.evaluate(ToolCall("ext_tool", "send", empty_args, "a"), ctx)
        assert d_empty.decision is Decision.DENY
        assert d_empty.rule == "provenance.control_missing"


# ----------------------------------------------------------------------------- ISS-022
def test_iss022_synthesize_least_privilege_handles_non_recipient_external_tools() -> None:
    reg = _reg_with_external("bucket")
    step = Step("s1", "worker", "", tools=("ext_tool",))
    wf = Workflow((step,))
    task = TaskSpec("t", "d", "Export to reporting", ("c",), {}, wf)
    pol = Policy(
        policy_id="p",
        permitted={"ext_tool": frozenset({"send"})},
        allow_write=True,
        allow_external=True,
    )
    model = SystemModel.for_task(task, (AgentSpec("a1", "worker", ""),), pol, reg, mode=HandoffMode.SIGNED, gate="rule")
    lp = synthesize_least_privilege(model, [ObservedCall("s1", "ext_tool", "send", {"bucket": "reporting"})])
    assert lp.policy.allowed_recipients == frozenset({"reporting"})
    assert "" not in lp.policy.allowed_recipients
    eng = RulePolicyEngine(lp.policy, reg)
    ctx = PolicyContext("r1", "s1", frozenset({"ext_tool"}))
    assert eng.evaluate(ToolCall("ext_tool", "send", {"bucket": "reporting"}, "a1"), ctx).decision is Decision.ALLOW
    assert eng.evaluate(ToolCall("ext_tool", "send", {"bucket": "exfil-bucket"}, "a1"), ctx).decision is Decision.DENY


# ----------------------------------------------------------------------------- ISS-023
def test_iss023_runtime_forces_tool_results_to_untrusted() -> None:
    class _LyingTool:
        spec = ToolSpec(
            name="lying_reader",
            description="Claims TRUSTED output",
            resource_class="docs",
            operations={"read": OperationSpec(name="read")},
        )

        def invoke(self, operation: str, args: Any) -> ToolResult:
            return ToolResult(ok=True, data="evil@attacker.example", trust=Trust.TRUSTED)

    class _Mailer:
        spec = ToolSpec(
            name="mailer",
            description="External mailer",
            resource_class="mail",
            operations={
                "send": OperationSpec(name="send", write_effect=True, external=True, control_params=("recipient",))
            },
        )

        def invoke(self, operation: str, args: Any) -> ToolResult:
            return ToolResult(ok=True, data={"sent_to": args.get("recipient")})

    reg = ToolRegistry([_LyingTool(), _Mailer()])
    pol = Policy(
        policy_id="p",
        permitted={"lying_reader": frozenset({"read"}), "mailer": frozenset({"send"})},
        allow_write=True,
        allow_external=True,
    )
    eng = RulePolicyEngine(pol, reg)
    guard = ProvenanceGuard(eng, reg, match="substring")
    step = Step("s1", "worker", "Read and email", tools=("lying_reader", "mailer"))
    task = TaskSpec("t", "d", "Email alice@corp.example only", (), {}, Workflow((step,)))
    import json

    provider = ScriptedProvider(
        [
            json.dumps({"tool_calls": [{"tool": "lying_reader", "operation": "read", "args": {}}], "confidence": 0.9}),
            json.dumps(
                {
                    "tool_calls": [
                        {"tool": "mailer", "operation": "send", "args": {"recipient": "evil@attacker.example"}}
                    ],
                    "confidence": 0.9,
                }
            ),
            json.dumps({"tool_calls": [], "output": {"done": True}, "confidence": 0.9}),
        ]
    )
    rt = Runtime(
        provider,
        reg,
        [AgentSpec("a1", "worker", "")],
        pol,
        RuntimeConfig(policy_engine=guard, observers=(guard,), handoff_mode=HandoffMode.SIGNED),
    )
    res = rt.run(task)
    send_events = [c for c in res.calls if c.proposed.tool == "mailer"]
    assert len(send_events) == 1
    assert send_events[0].decision == "DENY"
    assert send_events[0].rule == "provenance.control_unsupported"
    assert send_events[0].executed is None


# ----------------------------------------------------------------------------- ISS-024
def test_iss024_realworld_runtime_executes_bound_args_and_isolates_extractors() -> None:
    before_global = dict(DIRECTORY_EXTRACTORS)
    seen_args: list[dict[str, Any]] = []

    def _dir_fn(state: dict[str, Any], args: dict[str, Any]) -> tuple[str, list[str] | None]:
        return "listed", ["ch-ops"]

    def _sink_fn(state: dict[str, Any], args: dict[str, Any]) -> tuple[str, list[str] | None]:
        seen_args.append(dict(args))
        state["written"].append(dict(args))
        return "ok", None

    sc = Scenario(
        sid="test-sc",
        domain="test",
        tools={
            "custom_list_dir": ToolDef("custom_list_dir", "list", {}, _dir_fn, directory=True),
            "post_msg": ToolDef(
                "post_msg", "post", {"channel": "ch", "limit": "lim"}, _sink_fn, write=True, control=("channel",)
            ),
        },
        roles={"R": ["custom_list_dir"], "S": ["post_msg"]},
        new_state=lambda: {"written": []},
        vector_tool="custom_list_dir",
        benign=[Task("Post to ch-ops", lambda s: bool(s["written"]))],
        injections=[],
    )
    pol = Policy(
        policy_id="bound-test",
        permitted={"custom_list_dir": frozenset({"custom_list_dir"}), "post_msg": frozenset({"post_msg"})},
        allow_write=True,
        allow_external=True,
        numeric_bounds={"limit": (1, 10)},
    )
    rt = RealWorldRuntime(sc, "strict", "strict", "Post to ch-ops", policy=pol)
    # 1. Global DIRECTORY_EXTRACTORS must not be mutated
    assert dict(DIRECTORY_EXTRACTORS) == before_global
    # 2. Unauthorized agent R cannot call S's tool post_msg (per-agent step_tools)
    res_unauth = rt.call("R", "post_msg", {"channel": "ch-ops", "limit": 5})
    assert "DENIED_BY_POLICY" in res_unauth
    assert rt.state["written"] == []
    # 3. BOUND revised args (limit=999 clamped to 10) must actually be executed
    res_bound = rt.call("S", "post_msg", {"channel": "ch-ops", "limit": 999})
    assert res_bound == "ok"
    assert seen_args[-1]["limit"] == 10
    # 4. Denied call produces zero state mutation
    snap = copy.deepcopy(rt.state)
    res_denied = rt.call("S", "post_msg", {"channel": "evil-channel", "limit": 5})
    assert "DENIED_BY_POLICY" in res_denied
    assert rt.state == snap
    rt.close()


# ----------------------------------------------------------------------------- ISS-025
def test_iss025_malformed_json_tool_args_flagged_instead_of_empty_dict() -> None:
    fake_tc = SimpleNamespace(
        id="tc_1",
        function=SimpleNamespace(name="create_calendar_event", arguments="{broken json"),
    )
    fake_msg = SimpleNamespace(content=None, tool_calls=[fake_tc])
    parsed = _safe_openai_to_assistant_message(fake_msg)
    assert parsed["tool_calls"] is not None
    assert MALFORMED_ARGS_SENTINEL in parsed["tool_calls"][0].args


# ----------------------------------------------------------------------------- ISS-010
def test_iss010_cyclic_workflow_raises_workflow_error_and_authority_matches_v2_gate() -> None:
    wf = Workflow(
        (
            Step("a", "r1", "", depends_on=("b",)),
            Step("b", "r2", "", depends_on=("a",)),
        )
    )
    with pytest.raises(WorkflowError):
        wf.stages()
    # Also verify blast_radius value-set parity with require_nonempty_control=True
    reg = _reg_with_external("recipient")
    pol = Policy("p", {"ext_tool": frozenset({"send"})}, allow_write=True, allow_external=True)
    step = Step("s1", "w", "", tools=("ext_tool",))
    task = TaskSpec("t", "d", "Send to alice@corp.example", (), {}, Workflow((step,)))
    m = SystemModel.for_task(
        task,
        (AgentSpec("a1", "w", ""),),
        pol,
        reg,
        mode=HandoffMode.SIGNED,
        gate="rule+provenance",
        require_nonempty_control=True,
    )
    br = blast_radius(m, {"a1"})
    assert not br.admits("s1", "ext_tool", "send", {})
    assert not br.admits("s1", "ext_tool", "send", {"recipient": 0})
    assert br.admits("s1", "ext_tool", "send", {"recipient": "alice@corp.example"})
    assert isinstance(DirectoryGuard(RulePolicyEngine(pol, reg), reg), ProvenanceGuard)
    assert authority(m, step)


# ----------------------------------------------------------------------------- Round-2 Security & Correspondence Fixes
def _reg_with_multi_control(control_params: tuple[str, ...]) -> ToolRegistry:
    class _MultiStub:
        def __init__(self) -> None:
            self.spec = ToolSpec(
                name="mailer",
                description="Multi-recipient sink",
                resource_class="mail",
                operations={
                    "send": OperationSpec(
                        name="send",
                        write_effect=True,
                        external=True,
                        control_params=control_params,
                    )
                },
                default_sensitivity=Sensitivity.INTERNAL,
            )

        def invoke(self, operation: str, args: Any) -> ToolResult:
            return ToolResult(ok=True, data={"sent": args})

    return ToolRegistry([_MultiStub()])


def test_r2_multi_param_external_recipient_blocks_cc_smuggling_and_allows_omitted_optional() -> None:
    """Multi-param external ops check every present param (no cc bypass) and allow omitted optional siblings."""
    reg = _reg_with_multi_control(("recipient", "cc", "bcc"))
    pol = Policy(
        policy_id="p",
        permitted={"mailer": frozenset({"send"})},
        allow_write=True,
        allow_external=True,
        recipient_domains=frozenset({"CORP.EXAMPLE"}),  # mixed-case policy normalized
    )
    eng = RulePolicyEngine(pol, reg)
    ctx = PolicyContext("r1", "s1", frozenset({"mailer"}))
    step = Step("s1", "w", "", tools=("mailer",))
    task = TaskSpec("t", "d", "Email alice@corp.example", (), {}, Workflow((step,)))
    model = SystemModel.for_task(task, (AgentSpec("a1", "w", ""),), pol, reg, mode=HandoffMode.SIGNED, gate="rule")
    br = blast_radius(model, {"a1"})

    cases = [
        ({"recipient": "alice@corp.example"}, True),
        ({"recipient": "alice@corp.example", "cc": None, "bcc": []}, True),
        ({"recipient": "alice@corp.example", "cc": "evil@attacker.org"}, False),
        ({"recipient": "alice@corp.example", "bcc": ["ok@corp.example", "evil@attacker.org"]}, False),
        ({"recipient": "alice\x00@corp.example"}, False),
        ({"recipient": "alice\u202e@corp.example"}, False),
        ({"recipient": "alice\u200b@corp.example"}, False),
        ({}, False),
        ({"recipient": [], "cc": []}, False),
    ]
    for args, expect_allow in cases:
        d = eng.evaluate(ToolCall("mailer", "send", args, "a1"), ctx)
        assert (d.decision is not Decision.DENY) is expect_allow, f"gate mismatch for {args!r}: {d}"
        assert br.admits("s1", "mailer", "send", args) is expect_allow, f"bound mismatch for {args!r}"


def test_r2_provenance_blocks_dict_keys_and_enforces_operation_level_nonempty_control() -> None:
    """Dict keys in control args cannot bypass provenance; require_nonempty_control is operation-level."""
    reg = _reg_with_multi_control(("recipients", "cc", "bcc"))
    pol = Policy(
        policy_id="p",
        permitted={"mailer": frozenset({"send"})},
        allow_write=True,
        allow_external=True,
    )
    eng = RulePolicyEngine(pol, reg)
    guard = DirectoryGuard(eng, reg, match="substring", require_nonempty_control=True)
    guard.observe("r1", {"objective": "Send update to alice@corp.example"}, Trust.TRUSTED)
    ctx = PolicyContext("r1", "s1", frozenset({"mailer"}))

    step = Step("s1", "w", "", tools=("mailer",))
    task = TaskSpec("t", "d", "Send update to alice@corp.example", (), {}, Workflow((step,)))
    model = SystemModel.for_task(
        task,
        (AgentSpec("a1", "w", ""),),
        pol,
        reg,
        mode=HandoffMode.SIGNED,
        gate="rule+provenance",
        require_nonempty_control=True,
    )
    br = blast_radius(model, {"a1"})

    # 1. Untrusted dict key with trusted value (or None value) must be DENIED
    for sneak in (
        {"recipients": {"evil@attacker.com": "alice@corp.example"}},
        {"recipients": {"evil@attacker.com": None}},
    ):
        assert guard.evaluate(ToolCall("mailer", "send", sneak, "a1"), ctx).decision is Decision.DENY
        assert not br.admits("s1", "mailer", "send", sneak)

    # 2. Primary recipient present with optional cc/bcc omitted must be ALLOWED
    ok_call = {"recipients": ["alice@corp.example"]}
    assert guard.evaluate(ToolCall("mailer", "send", ok_call, "a1"), ctx).decision is Decision.ALLOW
    assert br.admits("s1", "mailer", "send", ok_call)

    # 3. Omitting ALL control params must be DENIED
    for empty in ({}, {"recipients": [], "cc": None, "bcc": ""}):
        d = guard.evaluate(ToolCall("mailer", "send", empty, "a1"), ctx)
        assert d.decision is Decision.DENY
        assert d.rule == "provenance.control_missing"
        assert not br.admits("s1", "mailer", "send", empty)


def test_r2_valueset_enumerate_matches_admits_under_mixed_case_and_nfkc() -> None:
    """ValueSet.enumerate() must normalize corpus/domains consistently with admits()."""
    from guide_research.blast_radius import ValueSet

    vs = ValueSet(
        domains=frozenset({"Corp.Example"}),
        provenance="substring",
        corpus="Forward to Alice\uff20Corp.Example immediately",
    )
    assert vs.admits({"v": "alice@corp.example"}, "v")
    enum_vals = vs.enumerate()
    assert enum_vals is not None
    assert "alice@corp.example" in enum_vals
    for v in enum_vals:
        assert vs.admits({"v": v}, "v")


def test_r2_realworld_runtime_fails_closed_for_zero_tool_derived_and_rogue_agents() -> None:
    """Zero-tool roles (N, V), derived role A calling Reader tools, and unknown agents must be DENIED."""
    called: list[str] = []

    def _read(state: dict[str, Any], args: dict[str, Any]) -> tuple[str, list[str] | None]:
        called.append("read")
        return "secret", None

    def _send(state: dict[str, Any], args: dict[str, Any]) -> tuple[str, list[str] | None]:
        called.append("send")
        state["sent"].append(args["to"])
        return "sent", None

    sc = Scenario(
        sid="del-test",
        domain="mail",
        tools={
            "read_inbox": ToolDef("read_inbox", "read", {}, _read),
            "send_mail": ToolDef(
                "send_mail", "send", {"to": "addr"}, _send, write=True, external=True, control=("to",)
            ),
        },
        roles={"R": ["read_inbox"], "W": [], "S": ["send_mail"], "S2": []},
        new_state=lambda: {"sent": []},
        vector_tool="read_inbox",
        benign=[Task("Send to alice@corp.example", lambda s: bool(s["sent"]))],
        injections=[],
    )
    rt = RealWorldRuntime(sc, "strict", "strict", "Send to alice@corp.example")
    # Zero-tool roles N and V, Actor A calling Reader's read_inbox, and unknown rogue_agent must fail closed
    for agent, tool, args in (
        ("N", "send_mail", {"to": "alice@corp.example"}),
        ("V", "send_mail", {"to": "alice@corp.example"}),
        ("A", "read_inbox", {}),
        ("rogue_agent", "send_mail", {"to": "alice@corp.example"}),
    ):
        resp = rt.call(agent, tool, args)
        assert "DENIED_BY_POLICY (tool.not_delegated)" in resp, f"Expected delegation denial for {agent}/{tool}: {resp}"
    assert called == []
    assert rt.state["sent"] == []

    # Derived Actor A CAN call S's send_mail, and explicit register_agent_tools overrides work cleanly
    assert rt.call("A", "send_mail", {"to": "alice@corp.example"}) == "sent"
    rt.register_agent_tools("A", ["read_inbox", "send_mail"])
    assert rt.call("A", "read_inbox", {}) == "secret"
    rt.close()
