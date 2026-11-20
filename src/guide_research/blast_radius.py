"""Static worst-case blast-radius analysis and least-privilege synthesis.

Research mechanism (see ``docs/formal_model.md`` for definitions and the soundness proof).
Given a deterministic GUIDE deployment -- workflow DAG, agents and roles, policy, tool
metadata, hand-off mode, gate configuration and trusted task text -- and a set ``K`` of
compromised agents, compute:

* ``authority(model, s)`` -- Auth(s): every effect the runtime can execute at step ``s``,
  as a set of :class:`Capability` atoms. Each predicate mirrors one branch of
  ``RulePolicyEngine.evaluate`` / ``ProvenanceGuard.evaluate`` (exact w.r.t. the gate).
* ``influenced(model, K)`` -- Infl(K): the least set of steps whose context, executing
  agent or readable tool state can depend on the adversary (direct compromise, context
  flow, state flow, optional injectable tools and transport adversary).
* ``blast_radius(model, K)`` -- BR(K) = union of Auth(s) over s in Infl(K).
* ``synthesize_least_privilege(model, calls)`` -- the pointwise-least policy and step
  delegation (in GUIDE's policy language) that still permits every observed nominal call.

Core never imports this module (layer rule Core <- Research <- Bench).
"""

from __future__ import annotations

import math
import unicodedata
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Any, Literal

from guide.agent import AgentSpec
from guide.policy import (
    Policy,
    external_recipient_params,
    normalize_recipient,
    parse_single_recipient,
    recipient_values,
)
from guide.runtime import HandoffMode
from guide.tools import ToolRegistry, ToolSpec
from guide.types import Sensitivity
from guide.workflow import Step, TaskSpec, Workflow
from guide_research.provenance import Match, corpus_of, extract_control_values, normalize_text, supported, tokens_of

GateMode = Literal["none", "rule", "rule+provenance"]


# ----------------------------------------------------------------------------- value sets
@dataclass(frozen=True)
class ValueSet:
    """Admissible values of one argument: a conjunction of the constraints that apply to it.

    ``domains``            gate recipient-domain allow-list (external ops only)
    ``exact``              gate exact recipient allow-list (external ops only)
    ``provenance``         guard rule: every element, normalised, must be supported by ``corpus``
    ``require_nonempty``   whether missing/empty control argument is rejected directly on this parameter
    ``optional_recipient`` whether absent/empty recipient is allowed on this sibling (group checked on Capability)
    """

    domains: frozenset[str] | None = None
    exact: frozenset[str] | None = None
    provenance: Match | None = None
    corpus: str = ""
    require_nonempty: bool = False
    optional_recipient: bool = False

    @property
    def unconstrained(self) -> bool:
        return self.domains is None and self.exact is None and self.provenance is None

    def admits(self, args: Mapping[str, Any], param: str) -> bool:
        """Mirror of the gate + guard checks for ``param`` in ``args``."""
        if self.domains is not None or self.exact is not None:
            norm_domains = (
                frozenset(unicodedata.normalize("NFKC", d).strip().lower() for d in self.domains)
                if self.domains is not None
                else None
            )
            norm_exact = (
                frozenset(unicodedata.normalize("NFKC", a).strip().lower() for a in self.exact)
                if self.exact is not None
                else None
            )
            vals = recipient_values(args, param)
            if vals is None:
                if not self.optional_recipient:
                    return False
            else:
                for v in vals:
                    if norm_domains is not None:
                        parsed = parse_single_recipient(v)
                        if parsed is None:
                            return False
                        addr, domain = parsed
                        if domain not in norm_domains:
                            return False
                        if norm_exact is not None and addr not in norm_exact:
                            return False
                    elif norm_exact is not None:
                        norm_dest = normalize_recipient(v)
                        if norm_dest is None or norm_dest not in norm_exact:
                            return False
        if self.provenance is not None:
            values = extract_control_values(args.get(param))
            if not values:
                if self.require_nonempty:
                    return False
            for v in values:
                if not supported(v, self.corpus, self.provenance):
                    return False
        return True

    def enumerate(self) -> frozenset[str] | None:
        """Admissible values in normal form (NFKC, stripped, lower-case), or None if not finitely enumerable.

        Normal form suffices: case, NFKC compatibility, and surrounding whitespace do not change any decision.
        """
        norm_corpus = normalize_text(self.corpus)
        if self.exact is not None:
            candidates: set[str] = {unicodedata.normalize("NFKC", a).strip().lower() for a in self.exact}
        elif self.provenance == "token":
            candidates = set(tokens_of(norm_corpus))
        elif self.provenance == "substring" and self.domains is not None:
            candidates = set()
            for d in self.domains:
                needle = "@" + unicodedata.normalize("NFKC", d).strip().lower()
                start = norm_corpus.find(needle)
                while start != -1:
                    end = start + len(needle)
                    candidates.update(norm_corpus[i:end].strip() for i in range(start + 1))
                    start = norm_corpus.find(needle, start + 1)
        else:
            return None
        return frozenset(c for c in candidates if c and self.admits({"v": c}, "v"))


# ----------------------------------------------------------------------------- capabilities
@dataclass(frozen=True)
class Capability:
    """One executable (step, tool, operation) with the constraints on its arguments."""

    step: str
    tool: str
    operation: str
    write_effect: bool
    external: bool
    resource_class: str
    params: tuple[tuple[str, ValueSet], ...] = ()
    columns: frozenset[str] | None = None  # data the call can place into an agent context
    recipient_group: tuple[str, ...] = ()  # external recipient params where >=1 must be present
    nonempty_control_group: tuple[str, ...] = ()  # provenance control params where >=1 must be non-empty

    @property
    def is_sink(self) -> bool:
        return self.write_effect or self.external

    def admits(self, args: Mapping[str, Any], exposed_columns: Iterable[str] | None = None) -> bool:
        if any(not vs.admits(args, p) for p, vs in self.params):
            return False
        if self.recipient_group and not any(recipient_values(args, p) is not None for p in self.recipient_group):
            return False
        if self.nonempty_control_group and not any(
            extract_control_values(args.get(p)) for p in self.nonempty_control_group
        ):
            return False
        return exposed_columns is None or self.columns is None or set(exposed_columns) <= self.columns


@dataclass(frozen=True, eq=False)
class SystemModel:
    workflow: Workflow
    agents: tuple[AgentSpec, ...]
    policy: Policy
    registry: ToolRegistry
    trusted_corpus: str
    mode: HandoffMode
    gate: GateMode
    provenance_match: Match = "substring"
    require_nonempty_control: bool = False

    @classmethod
    def for_task(
        cls,
        task: TaskSpec,
        agents: Sequence[AgentSpec],
        policy: Policy,
        registry: ToolRegistry,
        *,
        mode: HandoffMode,
        gate: GateMode,
        provenance_match: Match = "substring",
        require_nonempty_control: bool = False,
    ) -> SystemModel:
        # identical to the TRUSTED header the runtime shows the guard (Runtime.run)
        corpus = corpus_of({"objective": task.objective, "constraints": list(task.constraints)})
        return cls(
            task.workflow,
            tuple(agents),
            policy,
            registry,
            corpus,
            mode,
            gate,
            provenance_match,
            require_nonempty_control,
        )

    def step(self, step_id: str) -> Step:
        return next(s for s in self.workflow.steps if s.step_id == step_id)

    def candidates(self, step: Step) -> frozenset[str]:
        return frozenset(a.agent_id for a in self.agents if a.role == step.role)


def _columns(spec: ToolSpec, policy: Policy | None) -> frozenset[str] | None:
    """Columns a permitted call can expose; None if the tool has no column metadata."""
    if not spec.column_sensitivity:
        return None
    if policy is None or not spec.columns_param:
        return frozenset(spec.column_sensitivity)  # ungated, or gate does not bound columns
    allow = policy.allowed_columns.get(spec.name)
    return frozenset(
        c
        for c, sens in spec.column_sensitivity.items()
        if sens <= policy.max_sensitivity and (allow is None or c in allow)
    )


def authority(model: SystemModel, step: Step) -> tuple[Capability, ...]:
    """Auth(s): exact set of effects the configured gate lets step ``s`` execute."""
    caps: list[Capability] = []
    p = model.policy
    for tool in step.tools:  # delegation: the gate only admits tools delegated to the step
        if not model.registry.has(tool):
            continue
        spec = model.registry.get(tool).spec
        for op in spec.operations.values():
            params: dict[str, ValueSet] = {}
            if model.gate == "none":
                caps.append(
                    Capability(
                        step.step_id,
                        tool,
                        op.name,
                        op.write_effect,
                        op.external,
                        spec.resource_class,
                        (),
                        _columns(spec, None),
                    )
                )
                continue
            if tool not in p.permitted or op.name not in p.permitted[tool]:
                continue
            if op.write_effect and not p.allow_write:
                continue
            recipient_group: tuple[str, ...] = ()
            nonempty_control_group: tuple[str, ...] = ()
            if op.external:
                if not p.allow_external:
                    continue
                if p.recipient_domains or p.allowed_recipients:
                    rcpt_params = external_recipient_params(op.control_params)
                    recipient_group = rcpt_params
                    multi_rcpt = len(rcpt_params) > 1
                    for rcpt_param in rcpt_params:
                        params[rcpt_param] = ValueSet(
                            domains=frozenset(p.recipient_domains) if p.recipient_domains else None,
                            exact=frozenset(p.allowed_recipients) if p.allowed_recipients else None,
                            optional_recipient=multi_rcpt,
                        )
            columns = _columns(spec, p)
            if spec.column_sensitivity and spec.columns_param:
                if not columns:
                    continue  # every request is denied (sensitivity.exceeded)
            elif spec.default_sensitivity > p.max_sensitivity:
                continue
            if model.gate == "rule+provenance" and (op.write_effect or op.external):
                if model.require_nonempty_control and op.control_params:
                    nonempty_control_group = op.control_params
                single_ctrl = len(op.control_params) == 1
                for cp in op.control_params:
                    base = params.get(cp, ValueSet())
                    params[cp] = replace(
                        base,
                        provenance=model.provenance_match,
                        corpus=model.trusted_corpus,
                        require_nonempty=(model.require_nonempty_control and single_ctrl),
                    )
            caps.append(
                Capability(
                    step.step_id,
                    tool,
                    op.name,
                    op.write_effect,
                    op.external,
                    spec.resource_class,
                    tuple(sorted(params.items())),
                    columns,
                    recipient_group=recipient_group,
                    nonempty_control_group=nonempty_control_group,
                )
            )
    return tuple(caps)


@dataclass(frozen=True)
class BlastRadius:
    compromised: frozenset[str]
    direct: frozenset[str]
    influenced: tuple[str, ...]
    capabilities: tuple[Capability, ...]
    reasons: Mapping[str, str] = field(default_factory=dict)

    def capability(self, step: str, tool: str, operation: str) -> Capability | None:
        return next((c for c in self.capabilities if (c.step, c.tool, c.operation) == (step, tool, operation)), None)

    def admits(
        self,
        step: str,
        tool: str,
        operation: str,
        args: Mapping[str, Any],
        exposed_columns: Iterable[str] | None = None,
    ) -> bool:
        cap = self.capability(step, tool, operation)
        return cap is not None and cap.admits(args, exposed_columns)

    @property
    def sinks(self) -> tuple[Capability, ...]:
        return tuple(c for c in self.capabilities if c.is_sink)

    def exposures(self, registry: ToolRegistry, above: Sensitivity) -> frozenset[tuple[str, str, str]]:
        """(step, tool, column) triples above ``above`` that can enter an influenced agent's context."""
        out = set()
        for c in self.capabilities:
            spec = registry.get(c.tool).spec
            for col in c.columns or ():
                if spec.sensitivity_of(col) > above:
                    out.add((c.step, c.tool, col))
        return frozenset(out)


def influenced(
    model: SystemModel,
    compromised: Iterable[str],
    *,
    injectable_tools: Iterable[str] = (),
    transport_adversary: bool = False,
) -> tuple[frozenset[str], tuple[str, ...], dict[str, str]]:
    """Least fixpoint Infl(K). Returns (direct steps, influenced steps in execution order, reasons)."""
    k, j = frozenset(compromised), frozenset(injectable_tools)
    order = model.workflow.order()
    pos = {s.step_id: i for i, s in enumerate(order)}
    reasons: dict[str, str] = {}
    for s in order:
        if model.candidates(s) & k:
            reasons[s.step_id] = "direct"
        elif set(s.tools) & j:
            reasons[s.step_id] = "injectable-tool"
        elif transport_adversary and model.mode is not HandoffMode.SIGNED:
            reasons[s.step_id] = "transport"
    direct = frozenset(sid for sid, why in reasons.items() if why == "direct")
    auth = {s.step_id: authority(model, s) for s in order}
    resources = {
        s.step_id: {model.registry.get(t).spec.resource_class for t in s.tools if model.registry.has(t)} for s in order
    }
    changed = True
    while changed:
        changed = False
        for s in order:
            if s.step_id in reasons:
                continue
            earlier = [x for x in order if pos[x.step_id] < pos[s.step_id] and x.step_id in reasons]
            if model.mode is HandoffMode.TRANSCRIPT:
                ctx = earlier[0].step_id if earlier else None
            else:
                ctx = next((d for d in s.depends_on if d in reasons), None)
            if ctx is not None:
                reasons[s.step_id] = f"context:{ctx}"
                changed = True
                continue
            written = {c.resource_class for x in earlier for c in auth[x.step_id] if c.write_effect}
            if written & resources[s.step_id]:
                reasons[s.step_id] = f"state:{sorted(written & resources[s.step_id])[0]}"
                changed = True
    ordered = tuple(s.step_id for s in order if s.step_id in reasons)
    return direct, ordered, reasons


def blast_radius(
    model: SystemModel,
    compromised: Iterable[str],
    *,
    injectable_tools: Iterable[str] = (),
    transport_adversary: bool = False,
) -> BlastRadius:
    k = frozenset(compromised)
    direct, infl, reasons = influenced(
        model, k, injectable_tools=injectable_tools, transport_adversary=transport_adversary
    )
    caps = tuple(c for sid in infl for c in authority(model, model.step(sid)))
    return BlastRadius(k, direct, infl, caps, reasons)


# ----------------------------------------------------------------------------- least privilege
@dataclass(frozen=True)
class ObservedCall:
    """An executed call from a nominal trace (``args`` = executed, i.e. post-bounding, arguments)."""

    step: str
    tool: str
    operation: str
    args: Mapping[str, Any]


@dataclass(frozen=True)
class LeastPrivilege:
    policy: Policy
    workflow: Workflow


def synthesize_least_privilege(model: SystemModel, calls: Iterable[ObservedCall]) -> LeastPrivilege:
    """Pointwise-least policy + delegation (in GUIDE's policy language) permitting every observed call.

    Raises ValueError if an observed call is outside the original authority: least privilege
    only ever removes permissions.
    """
    observed = list(calls)
    p = model.policy
    used_tools: dict[str, set[str]] = {s.step_id: set() for s in model.workflow.steps}
    ops: dict[str, set[str]] = {}
    columns: dict[str, set[str]] = {}
    recipients: set[str] = set()
    numeric_max: dict[str, float] = {}
    sens = Sensitivity.PUBLIC
    write = external = False
    for c in observed:
        cap = next(
            (x for x in authority(model, model.step(c.step)) if (x.tool, x.operation) == (c.tool, c.operation)), None
        )
        if cap is None or not cap.admits(c.args, _exposed(model.registry.get(c.tool).spec, c.args)):
            raise ValueError(f"observed call outside original authority: {c}")
        spec = model.registry.get(c.tool).spec
        op = spec.operations[c.operation]
        used_tools[c.step].add(c.tool)
        ops.setdefault(c.tool, set()).add(c.operation)
        write |= op.write_effect
        external |= op.external
        if op.external:
            for rparam in external_recipient_params(op.control_params):
                vals = recipient_values(c.args, rparam)
                if vals:
                    for v in vals:
                        parsed = parse_single_recipient(v)
                        if parsed is not None:
                            recipients.add(parsed[0])
                        else:
                            norm = normalize_recipient(v)
                            if norm is not None:
                                recipients.add(norm)
        exposed = _exposed(spec, c.args)
        if spec.column_sensitivity and spec.columns_param:
            columns.setdefault(c.tool, set()).update(exposed or ())
            sens = max([sens, *(spec.sensitivity_of(x) for x in exposed or ())])
        else:
            sens = max(sens, spec.default_sensitivity)
        for name in p.numeric_bounds:
            if name in c.args:
                raw_n = c.args[name]
                if isinstance(raw_n, bool):
                    raise ValueError(f"observed numeric arg '{name}' cannot be bool")
                val_n = float(raw_n)
                if not math.isfinite(val_n):
                    raise ValueError(f"observed numeric arg '{name}' must be finite")
                numeric_max[name] = max(numeric_max.get(name, float("-inf")), val_n)
    domains = frozenset(r.rsplit("@", 1)[-1] for r in recipients if "@" in r)
    synthesized_domains = domains if domains else (p.recipient_domains if external else frozenset())
    synthesized_recipients = (
        frozenset(recipients) if recipients else (p.allowed_recipients if external else frozenset())
    )
    policy = replace(
        p,
        policy_id=f"{p.policy_id}-least-privilege",
        permitted={t: frozenset(o) for t, o in sorted(ops.items())},
        max_sensitivity=sens if observed else Sensitivity.PUBLIC,
        allow_write=write,
        allow_external=external,
        recipient_domains=synthesized_domains,
        allowed_recipients=synthesized_recipients,
        allowed_columns={t: frozenset(cs) for t, cs in sorted(columns.items())},
        numeric_bounds={
            n: (lo, min(hi, numeric_max[n])) if n in numeric_max else (lo, hi)
            for n, (lo, hi) in p.numeric_bounds.items()
        },
    )
    steps = tuple(
        replace(s, tools=tuple(t for t in s.tools if t in used_tools[s.step_id])) for s in model.workflow.steps
    )
    return LeastPrivilege(policy, Workflow(steps))


def _exposed(spec: ToolSpec, args: Mapping[str, Any]) -> list[str] | None:
    if not spec.column_sensitivity:
        return None
    if spec.columns_param and isinstance(args.get(spec.columns_param), list | tuple) and args[spec.columns_param]:
        return [str(x) for x in args[spec.columns_param]]
    return list(spec.column_sensitivity)
