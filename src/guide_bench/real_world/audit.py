"""Blast-radius audit over the 18 real-world-pattern configurations (Task 5 / protocol-v4).

Static analysis only -- no live model calls, no framework code executed. For each configuration
and each worker/writer agent A_i, computes BR({A_i}) under the nominal policy and under the
least-privilege policy synthesised from that configuration's own `nominal_calls`, and records:

  * whether A_i's blast radius reaches a destructive sink (write_effect) or an exfiltration sink
    (external) that ISN'T needed for the nominal calls (i.e. genuine over-privilege, not the
    agent's own job);
  * the sink-capability count under nominal vs least-privilege policy (privilege reduction);
  * whether every nominal call still executes under the synthesised least-privilege policy
    (nominal-workflow preservation).

Run: python -m guide_bench.real_world.audit
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from guide_bench.real_world.configs import RealWorldConfig, load_configs
from guide_bench.run import git_state
from guide_research.blast_radius import (
    LeastPrivilege,
    ObservedCall,
    SystemModel,
    blast_radius,
    synthesize_least_privilege,
)

OUT = Path("experiments/real_world_blast_radius/results.jsonl")


def _model(cfg: RealWorldConfig, policy=None) -> SystemModel:  # type: ignore[no-untyped-def]
    from guide.runtime import HandoffMode

    return SystemModel.for_task(
        cfg.task, cfg.agents, policy or cfg.policy, cfg.registry, mode=HandoffMode.TRANSCRIPT, gate="rule"
    )


def _sink_needed(cfg: RealWorldConfig, tool: str, op: str) -> bool:
    return any(t == tool and o == op for _, t, o, _ in cfg.nominal_calls)


def audit_one(cfg: RealWorldConfig) -> dict[str, object]:
    model = _model(cfg)
    calls = tuple(ObservedCall(s, t, o, a) for s, t, o, a in cfg.nominal_calls)
    lp: LeastPrivilege = synthesize_least_privilege(model, calls)
    lp_model = _model(cfg, policy=lp.policy)

    per_agent: list[dict[str, object]] = []
    any_unconstrained = False
    for agent in cfg.agents:
        k = frozenset({agent.agent_id})
        br_nominal = blast_radius(model, k)
        br_lp = blast_radius(lp_model, k)

        nominal_sinks = br_nominal.sinks
        lp_sinks = br_lp.sinks
        over_priv = [
            c for c in nominal_sinks if not _sink_needed(cfg, c.tool, c.operation)
        ]  # sinks this agent's compromise reaches that its own job never uses
        unconstrained = len(over_priv) > 0
        any_unconstrained = any_unconstrained or unconstrained

        per_agent.append(
            {
                "agent_id": agent.agent_id,
                "role": agent.role,
                "influenced_steps": list(br_nominal.influenced),
                "nominal_sink_capabilities": len(nominal_sinks),
                "lp_sink_capabilities": len(lp_sinks),
                "over_privileged_sinks": [f"{c.step}.{c.tool}.{c.operation}" for c in over_priv],
                "unconstrained_reachability": unconstrained,
            }
        )

    from guide.policy import PolicyContext, RulePolicyEngine
    from guide.types import ToolCall

    engine = RulePolicyEngine(lp.policy, cfg.registry)
    lp_denied = 0
    for s, t, o, a in cfg.nominal_calls:
        step = next(x for x in lp_model.workflow.steps if x.step_id == s)
        d = engine.evaluate(ToolCall(t, o, a, "nominal"), PolicyContext("audit", s, frozenset(step.tools)))
        lp_denied += int(d.decision.value == "DENY")

    total_nominal_sinks = sum(a["nominal_sink_capabilities"] for a in per_agent)  # type: ignore[misc]
    total_lp_sinks = sum(a["lp_sink_capabilities"] for a in per_agent)  # type: ignore[misc]
    reduction = 1.0 - (total_lp_sinks / total_nominal_sinks) if total_nominal_sinks else 0.0

    return {
        "config_id": cfg.config_id,
        "domain": cfg.domain,
        "pattern": cfg.pattern,
        "num_agents": len(cfg.agents),
        "unconstrained_reachability": any_unconstrained,
        "nominal_sink_total": total_nominal_sinks,
        "lp_sink_total": total_lp_sinks,
        "sink_reduction_fraction": round(reduction, 4),
        "nominal_calls_denied_under_lp": lp_denied,
        "nominal_calls_total": len(cfg.nominal_calls),
        "nominal_preserved": lp_denied == 0,
        "per_agent": per_agent,
    }


def run() -> dict[str, object]:
    configs = load_configs()
    rows = [audit_one(c) for c in configs]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    n = len(rows)
    unconstrained_pct = 100.0 * sum(r["unconstrained_reachability"] for r in rows) / n  # type: ignore[misc]
    preserved_pct = 100.0 * sum(r["nominal_preserved"] for r in rows) / n  # type: ignore[misc]
    total_nominal = sum(r["nominal_sink_total"] for r in rows)  # type: ignore[misc]
    total_lp = sum(r["lp_sink_total"] for r in rows)  # type: ignore[misc]
    mean_reduction = sum(r["sink_reduction_fraction"] for r in rows) / n  # type: ignore[misc]
    by_pattern: dict[str, dict[str, float]] = {}
    for pat in ("langgraph", "crewai", "autogen"):
        sub = [r for r in rows if r["pattern"] == pat]
        if sub:
            by_pattern[pat] = {
                "n": len(sub),
                "unconstrained_pct": 100.0 * sum(r["unconstrained_reachability"] for r in sub) / len(sub),  # type: ignore[misc]
            }

    summary = {
        "n_configs": n,
        "unconstrained_reachability_pct": round(unconstrained_pct, 1),
        "nominal_workflow_preserved_pct": round(preserved_pct, 1),
        "total_sink_capabilities_nominal": total_nominal,
        "total_sink_capabilities_least_privilege": total_lp,
        "mean_per_config_sink_reduction_pct": round(mean_reduction * 100, 1),
        "aggregate_sink_reduction_pct": round((1 - total_lp / total_nominal) * 100, 1) if total_nominal else 0.0,
        "by_pattern": by_pattern,
        "git": git_state(),
        "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scope_note": (
            "Configurations are hand-authored in GUIDE's own types reproducing documented "
            "LangGraph/CrewAI/AutoGen structural patterns; no external framework code was executed."
        ),
    }
    (OUT.parent / "summary.json").write_text(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
