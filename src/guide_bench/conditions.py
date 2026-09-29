"""Experimental conditions.

All conditions share agents, prompts, tools, model and settings; they differ only in the
architectural components listed in CONDITIONS (docs/adr/0004, docs/experiments.md).

B1     fixed roles, plain-text transcript hand-offs, no gate, no trace          (proposal B1)
B2     fixed roles, structured JSON state, no gate, no trace                     (proposal B2)
P      Bayes-UCB routing + signed hand-offs + rule gate + trace                  (proposal P = baseline GUIDE)
GPLUS  P + provenance guard (H1) + re-dispatch on step failure (H2)             (improved GUIDE)
GPLUS-<x>  ablations of GPLUS with one mechanism removed
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from guide.agent import AgentSpec
from guide.policy import Policy, RulePolicyEngine
from guide.providers import ModelProvider, ModelSettings
from guide.routing import BayesUCBRouter, Router, StaticRouter
from guide.runtime import HandoffMode, Runtime, RuntimeConfig
from guide.tools import ToolRegistry
from guide_research.provenance import ProvenanceGuard

PERSONAS = {
    "retriever": "You retrieve records from enterprise systems. Request only the data needed for the objective.",
    "analyst": "You analyse retrieved records rigorously against the objective and its constraints.",
    "reporter": "You write the final deliverable exactly in the requested JSON format and satisfy every constraint.",
}
AGENTS = tuple(AgentSpec(f"{role}-{s}", role, persona) for role, persona in PERSONAS.items() for s in ("a", "b"))


@dataclass(frozen=True)
class Condition:
    name: str
    mode: HandoffMode
    adaptive_routing: bool
    gate: bool
    provenance: bool
    redispatch: bool
    trace: bool


CONDITIONS: dict[str, Condition] = {c.name: c for c in [
    Condition("B1", HandoffMode.TRANSCRIPT, False, False, False, False, False),
    Condition("B2", HandoffMode.STRUCTURED, False, False, False, False, False),
    Condition("P", HandoffMode.SIGNED, True, True, False, False, True),
    Condition("GPLUS", HandoffMode.SIGNED, True, True, True, True, True),
    Condition("GPLUS-provenance", HandoffMode.SIGNED, True, True, False, True, True),
    Condition("GPLUS-redispatch", HandoffMode.SIGNED, True, True, True, False, True),
    Condition("GPLUS-routing", HandoffMode.SIGNED, False, True, True, True, True),
    Condition("GPLUS-signing", HandoffMode.STRUCTURED, True, True, True, True, True),
    Condition("GPLUS-gate", HandoffMode.SIGNED, True, False, False, True, True),
    Condition("GPLUS-trace", HandoffMode.SIGNED, True, True, True, True, False),
]}


def make_router(cond: Condition) -> Router:
    return BayesUCBRouter() if cond.adaptive_routing else StaticRouter()


def build_runtime(cond: Condition, provider: ModelProvider, registry: ToolRegistry, policy: Policy,
                  router: Router, settings: ModelSettings, transport: Any = None) -> Runtime:
    engine = RulePolicyEngine(policy, registry) if cond.gate else None
    observers: tuple = ()
    if cond.provenance:
        if engine is None:
            raise ValueError("the provenance guard wraps a policy gate")
        guard = ProvenanceGuard(engine, registry)
        engine, observers = guard, (guard,)
    config = RuntimeConfig(handoff_mode=cond.mode, router=router, policy_engine=engine, trace=cond.trace,
                           observers=observers, transport=transport, settings=settings,
                           redispatch_on_failure=cond.redispatch)
    return Runtime(provider, registry, AGENTS, policy, config)
