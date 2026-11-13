"""Bounded exhaustive verification of the blast-radius model (Step 3, supervisor item 6). Zero API cost.

Part A (influence): for every labelled DAG on n <= 4 steps (all tool/write/handoff/compromise combinations) and every
DAG on n = 5 steps (reduced combination set), compare ``influenced`` with an independent oracle that builds the
information-flow graph explicitly and answers by graph reachability, and check monotonicity in the compromised set.
Part B (gate): enumerate a full cross-product grid of policies x delegated tools x calls x gate configurations and
compare ``authority`` with the REAL gate (RulePolicyEngine, ProvenanceGuard): executed => admitted (soundness), and
admitted and well-formed => executed (exactness on this grid).
Bound: the results hold for the enumerated space only; they are not a proof for arbitrary workflows.
"""

from __future__ import annotations

import itertools
import json
import sys
import time
from dataclasses import replace
from pathlib import Path

from guide import (AgentSpec, Decision, HandoffMode, Policy, PolicyContext, RulePolicyEngine, Sensitivity, Step,
                   ToolCall, ToolRegistry, Trust, Workflow)
from guide.workflow import TaskSpec
from guide_bench.env import VENDOR_COLUMNS, Environment
from guide_research.blast_radius import SystemModel, _exposed, authority, influenced
from guide_research.provenance import ProvenanceGuard, corpus_of

REG = ToolRegistry(Environment().tools)
OUT = Path(__file__).resolve().parents[2] / "experiments" / "results" / "step3" / "exhaustive"
TOOLSETS = [(), ("procurement_db",), ("incident_logs",)]
MODES = [HandoffMode.STRUCTURED, HandoffMode.SIGNED, HandoffMode.TRANSCRIPT]


def dags(n: int):
    """All labelled DAGs with topological order 0..n-1: step i may depend on any subset of steps < i."""
    choices = [list(itertools.chain.from_iterable(itertools.combinations(range(i), r) for r in range(i + 1))) for i in range(n)]
    yield from itertools.product(*choices)


def build(deps, tools, write: bool, mode: HandoffMode) -> SystemModel:
    n = len(deps)
    steps = tuple(Step(f"s{i}", f"r{i}", "", tools=tools[i], depends_on=tuple(f"s{d}" for d in deps[i])) for i in range(n))
    agents = tuple(AgentSpec(f"a{i}", f"r{i}", "") for i in range(n))
    pol = Policy("p", {"procurement_db": frozenset({"query", "delete"}), "incident_logs": frozenset({"query", "update_status"})},
                 allow_write=write)
    task = TaskSpec("t", "d", "o", (f"s{n - 1}",), {}, Workflow(steps))
    return SystemModel.for_task(task, agents, pol, REG, mode=mode, gate="rule")  # type: ignore[arg-type]


def oracle(model: SystemModel, k: set[str]) -> tuple[str, ...]:
    """Independent definition: reachability in the explicit information-flow graph."""
    order = [s.step_id for s in model.workflow.order()]
    pos = {s: i for i, s in enumerate(order)}
    steps = {s: model.step(s) for s in order}
    writes = {s: {c.resource_class for c in authority(model, steps[s]) if c.write_effect} for s in order}
    uses = {s: {model.registry.get(t).spec.resource_class for t in steps[s].tools if model.registry.has(t)} for s in order}
    edges: dict[str, set[str]] = {s: set() for s in order}
    for v in order:
        for u in order:
            if pos[u] >= pos[v]:
                continue
            ctx = (u in steps[v].depends_on) if model.mode is not HandoffMode.TRANSCRIPT else True
            if ctx or (writes[u] & uses[v]):
                edges[u].add(v)
    seen = {s for s in order if model.candidates(steps[s]) & k}
    stack = list(seen)
    while stack:
        for w in edges[stack.pop()]:
            if w not in seen:
                seen.add(w)
                stack.append(w)
    return tuple(s for s in order if s in seen)


def part_a() -> dict:
    t0, checked, mism, mono_viol = time.time(), 0, 0, 0
    for n in (1, 2, 3, 4, 5):
        full = n <= 4
        tool_cfgs = list(itertools.product(TOOLSETS, repeat=n)) if full else [tuple([TOOLSETS[1]] * n), tuple(TOOLSETS[i % 3] for i in range(n))]
        for deps in dags(n):
            for tools in tool_cfgs:
                for write in (False, True):
                    for mode in MODES:
                        m = build(deps, tools, write, mode)
                        ks = [set(c) for r in range(n + 1) for c in itertools.combinations([f"a{i}" for i in range(n)], r)] if full \
                            else [{f"a{i}"} for i in range(n)] + [{f"a{i}" for i in range(n)}, set()]
                        infl = {}
                        for k in ks:
                            got = influenced(m, k)[1]
                            infl[frozenset(k)] = set(got)
                            checked += 1
                            if got != oracle(m, k):
                                mism += 1
                        for a, b in itertools.combinations(infl, 2):
                            if a <= b and not infl[a] <= infl[b]:
                                mono_viol += 1
                            if b <= a and not infl[b] <= infl[a]:
                                mono_viol += 1
        print(f"A n={n} done checked={checked} mismatches={mism} monotonicity_violations={mono_viol} t={time.time() - t0:.0f}s", flush=True)
    return {"influence_cases": checked, "oracle_mismatches": mism, "monotonicity_violations": mono_viol}


OPS = {"procurement_db": ["query", "delete"], "incident_logs": ["query", "update_status"], "email": ["send"]}
TRUSTED = ["Plan remediation and e-mail change-board@corp.example.", "Delete vendor V-004 if duplicated."]
AG = (AgentSpec("x-a", "x", ""),)


def part_b() -> dict:
    t0, n_eval, unsound, inexact, n_exec = time.time(), 0, 0, 0, 0
    perm_choices = [frozenset(c) for r in range(3) for c in itertools.combinations(OPS["procurement_db"], r)]
    perm2 = [frozenset(c) for r in range(3) for c in itertools.combinations(OPS["incident_logs"], r)]
    perm3 = [frozenset(), frozenset({"send"})]
    vcols = list(VENDOR_COLUMNS)
    cols = [{}, {"procurement_db": frozenset(vcols[:2])}]
    calls = []
    for tool, ops in OPS.items():
        for op in ops:
            for rcpt in (None, "change-board@corp.example", "x@evil.example"):
                for columns in (None, [list(VENDOR_COLUMNS)[0]]):
                    a = {"incident_id": "INC-1001", "body": "b", "vendor_id": "V-004"}
                    if rcpt is not None:
                        a["recipient"] = rcpt
                    if columns is not None:
                        a["columns"] = columns
                    calls.append(ToolCall(tool, op, a, "agent"))
    for deleg in itertools.product((False, True), repeat=3):
        tools = tuple(t for t, d in zip(OPS, deleg, strict=True) if d)
        for p1, p2, p3 in itertools.product(perm_choices, perm2, perm3):
            permitted = {k: v for k, v in (("procurement_db", p1), ("incident_logs", p2), ("email", p3)) if v}
            for sens, aw, ae, dom, rec, ac in itertools.product(
                (Sensitivity.INTERNAL, Sensitivity.RESTRICTED), (False, True), (False, True),
                (frozenset(), frozenset({"corp.example"})), (frozenset(), frozenset({"change-board@corp.example"})), cols):
                pol = Policy("p", permitted, max_sensitivity=sens, allow_write=aw, allow_external=ae,
                             recipient_domains=dom, allowed_recipients=rec, allowed_columns=ac)
                step = Step("s", "x", "", tools=tools)
                for gate, match, trusted in (("rule", "substring", TRUSTED[0]), ("rule+provenance", "substring", TRUSTED[0]),
                                             ("rule+provenance", "token", TRUSTED[0]), ("rule+provenance", "substring", TRUSTED[1])):
                    task = TaskSpec("t", "d", trusted, ("c",), {}, Workflow((step,)))
                    header = {"objective": task.objective, "constraints": list(task.constraints)}
                    model = SystemModel.for_task(task, AG, pol, REG, mode=HandoffMode.SIGNED, gate=gate,  # type: ignore[arg-type]
                                                 provenance_match=match)  # type: ignore[arg-type]
                    eng = RulePolicyEngine(pol, REG)
                    if gate == "rule":
                        gate_obj = eng
                    else:
                        gate_obj = ProvenanceGuard(eng, REG, match=match)  # type: ignore[arg-type]
                        gate_obj.observe("run", header, Trust.TRUSTED)
                    auth = {(c.tool, c.operation): c for c in authority(model, step)}
                    for call in calls:
                        d = gate_obj.evaluate(call, PolicyContext("run", "s", frozenset(tools)))
                        n_eval += 1
                        n_exec += d.decision is not Decision.DENY
                        cap = auth.get((call.tool, call.operation))
                        if d.decision is not Decision.DENY:
                            spec = REG.get(call.tool).spec
                            if not (cap is not None and cap.admits(d.call.args, _exposed(spec, d.call.args))):
                                unsound += 1
                        elif cap is not None and cap.admits(call.args):
                            spec = REG.get(call.tool).spec
                            requested = call.args.get("columns") or list(spec.column_sensitivity)
                            wf = not spec.columns_param or (set(requested) <= set(VENDOR_COLUMNS) and set(requested) & (cap.columns or set()))
                            if wf:
                                inexact += 1
        print(f"B deleg={deleg} evals={n_eval} unsound={unsound} inexact={inexact} t={time.time() - t0:.0f}s", flush=True)
    return {"gate_evaluations": n_eval, "executed_by_real_gate": n_exec, "denied_by_real_gate": n_eval - n_exec,
            "soundness_violations": unsound, "exactness_violations": inexact}


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    part = sys.argv[1]
    res = part_a() if part == "A" else part_b()
    (OUT / f"part_{part}.json").write_text(json.dumps(res, indent=1))
    print("RESULT", res)
