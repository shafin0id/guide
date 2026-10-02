"""Protocol v8 (M2): Proposition 4 (topology floor) and absolute-reach reporting.

Formal proof in docs/formal_model.md.
Code implements closed-form floor, step reachability under finest partition,
chain/dominating-source structural checks, and writes:
- experiments/results/topology-v8/abs_reach.jsonl
- experiments/results/topology-v8/census.jsonl
- experiments/results/topology-v8/summary.json
- experiments/results/topology-v8/summary.md
"""

from __future__ import annotations

import json
import statistics
from collections.abc import Iterable
from dataclasses import replace
from pathlib import Path
from typing import Any

from guide.runtime import HandoffMode
from guide.workflow import Step, Workflow
from guide_bench.mining.audit import wilson_interval
from guide_bench.mining.common import ExtractedAgent, ExtractedConfig, ExtractedStep
from guide_bench.mining.to_model import build_model
from guide_bench.real_world.configs import load_configs
from guide_research import topology
from guide_research.blast_radius import ObservedCall, SystemModel, blast_radius, synthesize_least_privilege

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "experiments" / "results" / "topology-v8"


def step_reach(model: SystemModel, step_id: str) -> frozenset[tuple[str, str]]:
    """R(s): distinct (tool, operation) sinks reachable when step s is compromised
    under the finest partition Pi_bot (one agent per step).
    """
    steps = model.workflow.steps
    n = len(steps)
    fine_model = topology.apply_partition(model, tuple(range(n)))
    try:
        idx = next(i for i, s in enumerate(steps) if s.step_id == step_id)
    except StopIteration:
        raise KeyError(f"Step '{step_id}' not found in workflow")
    agent_id = fine_model.agents[idx].agent_id
    br = blast_radius(fine_model, frozenset([agent_id]))
    return topology._distinct_sinks(br.capabilities)


def closed_form_floor(model: SystemModel) -> float:
    """Proposition 4(a): min_Pi WBR_1(Pi) = max_s |R(s)| / |Sinks*|."""
    sinks_star = topology.total_sinks_star(model)
    denom = len(sinks_star)
    if denom == 0:
        return 0.0
    steps = model.workflow.steps
    if not steps:
        return 0.0
    max_reach = max(len(step_reach(model, s.step_id)) for s in steps)
    return max_reach / denom


def has_dominating_source(workflow: Workflow, sink_steps: Iterable[str | Step]) -> bool:
    """True iff some step r reaches every step in sink_steps along depends_on edges."""
    sink_ids = {s if isinstance(s, str) else s.step_id for s in sink_steps}
    if not sink_ids:
        return False

    adj: dict[str, set[str]] = {s.step_id: set() for s in workflow.steps}
    for s in workflow.steps:
        for p in s.depends_on:
            if p in adj:
                adj[p].add(s.step_id)

    for r in workflow.steps:
        visited: set[str] = set()
        queue = [r.step_id]
        while queue:
            curr = queue.pop(0)
            if curr not in visited:
                visited.add(curr)
                queue.extend(adj.get(curr, set()) - visited)
        if sink_ids.issubset(visited):
            return True
    return False


def is_chain(workflow: Workflow) -> bool:
    """True iff every non-first step has depends_on == (previous step id,) in list order."""
    steps = workflow.steps
    if not steps:
        return True
    if steps[0].depends_on != ():
        return False
    for i in range(1, len(steps)):
        if steps[i].depends_on != (steps[i - 1].step_id,):
            return False
    return True


def run_topology_v8(progress: Any | None = None) -> dict[str, Any]:
    if progress:
        progress.set_total("M2", 1)
        progress.start_stage("M2", 1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Absolute reach analysis on 19 own configs
    configs = load_configs()
    abs_records: list[dict[str, Any]] = []

    for cfg in configs:
        nominal_base = SystemModel.for_task(
            cfg.task, cfg.agents, cfg.policy, cfg.registry, mode=HandoffMode.TRANSCRIPT, gate="rule"
        )
        calls = tuple(ObservedCall(s, t, o, a) for s, t, o, a in cfg.nominal_calls)
        lp = synthesize_least_privilege(nominal_base, calls)
        lp_base = replace(nominal_base, policy=lp.policy, workflow=lp.workflow)
        n_steps = len(cfg.task.workflow.steps)
        orig_identity = tuple(range(n_steps))

        m_i = topology.apply_partition(replace(nominal_base, mode=HandoffMode.TRANSCRIPT), orig_identity)
        sinks_star_nom = topology.total_sinks_star(m_i)
        denom_nom = len(sinks_star_nom)

        r_i = max(len(topology._distinct_sinks(blast_radius(m_i, frozenset([a.agent_id])).capabilities)) for a in m_i.agents)

        m_ii = topology.apply_partition(replace(lp_base, mode=HandoffMode.TRANSCRIPT), orig_identity)
        r_ii = max(len(topology._distinct_sinks(blast_radius(m_ii, frozenset([a.agent_id])).capabilities)) for a in m_ii.agents)

        m_iii = topology.apply_partition(replace(lp_base, mode=HandoffMode.SIGNED), orig_identity)
        r_iii = max(len(topology._distinct_sinks(blast_radius(m_iii, frozenset([a.agent_id])).capabilities)) for a in m_iii.agents)

        all_rgs = topology.set_partitions(n_steps)
        r_iv = min(
            max(
                len(topology._distinct_sinks(blast_radius(topology.apply_partition(replace(lp_base, mode=HandoffMode.SIGNED), rgs), frozenset([a.agent_id])).capabilities))
                for a in topology.apply_partition(replace(lp_base, mode=HandoffMode.SIGNED), rgs).agents
            )
            for rgs in all_rgs
        )

        nom_norm_i = (r_i / denom_nom) if denom_nom > 0 else 0.0
        nom_norm_ii = (r_ii / denom_nom) if denom_nom > 0 else 0.0
        nom_norm_iii = (r_iii / denom_nom) if denom_nom > 0 else 0.0
        nom_norm_iv = (r_iv / denom_nom) if denom_nom > 0 else 0.0

        abs_records.append({
            "config_id": cfg.config_id,
            "nominal_sinks_star": denom_nom,
            "abs_wbr1_i": r_i,
            "nom_wbr1_i": nom_norm_i,
            "abs_wbr1_ii": r_ii,
            "nom_wbr1_ii": nom_norm_ii,
            "abs_wbr1_iii": r_iii,
            "nom_wbr1_iii": nom_norm_iii,
            "abs_wbr1_iv": r_iv,
            "nom_wbr1_iv": nom_norm_iv,
            "reduction_abs_ii": r_i - r_ii,
            "reduction_abs_iv": r_i - r_iv,
        })

    with open(OUTPUT_DIR / "abs_reach.jsonl", "w", encoding="utf-8") as f:
        for r in abs_records:
            f.write(json.dumps(r) + "\n")

    med_abs_i = statistics.median(r["abs_wbr1_i"] for r in abs_records)
    med_nom_i = statistics.median(r["nom_wbr1_i"] for r in abs_records)

    med_abs_ii = statistics.median(r["abs_wbr1_ii"] for r in abs_records)
    med_nom_ii = statistics.median(r["nom_wbr1_ii"] for r in abs_records)

    med_abs_iii = statistics.median(r["abs_wbr1_iii"] for r in abs_records)
    med_nom_iii = statistics.median(r["nom_wbr1_iii"] for r in abs_records)

    med_abs_iv = statistics.median(r["abs_wbr1_iv"] for r in abs_records)
    med_nom_iv = statistics.median(r["nom_wbr1_iv"] for r in abs_records)

    med_red_abs = statistics.median(r["reduction_abs_ii"] for r in abs_records)

    # 2. Structural census over all 56 configs
    # (19 own configs + 36 mined scored acyclic + 1 mined cyclic listed separately)
    census_records: list[dict[str, Any]] = []

    # Own configs (19)
    for cfg in configs:
        wf = cfg.task.workflow
        chain = is_chain(wf)
        all_steps = [s.step_id for s in wf.steps]
        dom_all = has_dominating_source(wf, all_steps)

        # Sink steps: steps holding authority over sink operations
        m = SystemModel.for_task(cfg.task, cfg.agents, cfg.policy, cfg.registry, mode=HandoffMode.SIGNED, gate="rule")
        sink_steps = [s.step_id for s in wf.steps if any(c.is_sink for c in topology.authority(m, s))]
        has_sinks = len(sink_steps) > 0
        dom_sinks = has_dominating_source(wf, sink_steps) if has_sinks else False
        floor_1_signed = dom_sinks and has_sinks

        census_records.append({
            "set": "own",
            "config_id": cfg.config_id,
            "n_steps": len(wf.steps),
            "is_chain": chain,
            "dominating_source_all": dom_all,
            "has_sinks": has_sinks,
            "dominating_source_sinks": dom_sinks,
            "prop4_floor_1_signed": floor_1_signed,
            "cyclic": False,
        })

    # Mined configs (37)
    mined_file = REPO_ROOT / "experiments" / "mining" / "configs.jsonl"
    cyclic_records: list[dict[str, Any]] = []

    with open(mined_file, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            d = json.loads(line)
            cfg_id = f"{d['repo']}:{d['file']}"
            agents = [ExtractedAgent(name=a["name"], role=a.get("role", ""), tools=a.get("tools", [])) for a in d["agents"]]
            steps = [ExtractedStep(step_id=s["id"], agent=s["agent"], tools=s.get("tools", []), depends_on=s.get("depends_on", [])) for s in d["steps"]]
            ext_cfg = ExtractedConfig(
                framework=d["framework"],
                repo=d["repo"],
                sha=d["sha"],
                file=d["file"],
                agents=agents,
                steps=steps,
                process=d.get("process", ""),
                unresolved=d.get("unresolved", []),
            )

            step_objs = [
                Step(step_id=s.step_id, role=s.agent, instruction="", tools=tuple(s.tools), depends_on=tuple(s.depends_on))
                for s in ext_cfg.steps
            ]
            wf = Workflow(tuple(step_objs))

            is_cyclic = False
            try:
                wf.stages()
            except Exception:
                is_cyclic = True

            if is_cyclic:
                rec = {
                    "set": "mined",
                    "config_id": cfg_id,
                    "n_steps": len(wf.steps),
                    "is_chain": False,
                    "dominating_source_all": False,
                    "has_sinks": None,
                    "dominating_source_sinks": None,
                    "prop4_floor_1_signed": None,
                    "cyclic": True,
                }
                cyclic_records.append(rec)
                continue

            model, _ = build_model(ext_cfg, mode=HandoffMode.SIGNED)
            chain = is_chain(wf)
            all_steps = [s.step_id for s in wf.steps]
            dom_all = has_dominating_source(wf, all_steps)

            sink_steps = [s.step_id for s in wf.steps if any(c.is_sink for c in topology.authority(model, s))]
            has_sinks = len(sink_steps) > 0
            dom_sinks = has_dominating_source(wf, sink_steps) if has_sinks else False
            floor_1_signed = dom_sinks and has_sinks

            census_records.append({
                "set": "mined",
                "config_id": cfg_id,
                "n_steps": len(wf.steps),
                "is_chain": chain,
                "dominating_source_all": dom_all,
                "has_sinks": has_sinks,
                "dominating_source_sinks": dom_sinks,
                "prop4_floor_1_signed": floor_1_signed,
                "cyclic": False,
            })

    with open(OUTPUT_DIR / "census.jsonl", "w", encoding="utf-8") as f:
        for r in census_records:
            f.write(json.dumps(r) + "\n")
        for r in cyclic_records:
            f.write(json.dumps(r) + "\n")

    # Census aggregation
    def agg_census(records: list[dict[str, Any]]) -> dict[str, Any]:
        n = len(records)
        chains = sum(1 for r in records if r["is_chain"])
        dom_all = sum(1 for r in records if r["dominating_source_all"])
        sink_recs = [r for r in records if r["has_sinks"]]
        n_sinks = len(sink_recs)
        dom_sinks = sum(1 for r in sink_recs if r["dominating_source_sinks"])
        prop4_floor1 = sum(1 for r in records if r["prop4_floor_1_signed"])

        return {
            "n": n,
            "chain_count": chains,
            "chain_pct": chains / n if n > 0 else 0.0,
            "chain_ci": wilson_interval(chains, n) if n > 0 else (0.0, 0.0),
            "dom_all_count": dom_all,
            "dom_all_pct": dom_all / n if n > 0 else 0.0,
            "dom_all_ci": wilson_interval(dom_all, n) if n > 0 else (0.0, 0.0),
            "n_with_sinks": n_sinks,
            "dom_sinks_count": dom_sinks,
            "dom_sinks_pct": dom_sinks / n_sinks if n_sinks > 0 else 0.0,
            "dom_sinks_ci": wilson_interval(dom_sinks, n_sinks) if n_sinks > 0 else (0.0, 0.0),
            "prop4_floor1_count": prop4_floor1,
            "prop4_floor1_pct": prop4_floor1 / n if n > 0 else 0.0,
            "prop4_floor1_ci": wilson_interval(prop4_floor1, n) if n > 0 else (0.0, 0.0),
        }

    own_census = agg_census([r for r in census_records if r["set"] == "own"])
    mined_census = agg_census([r for r in census_records if r["set"] == "mined"])
    total_census = agg_census(census_records)

    summary: dict[str, Any] = {
        "abs_reach_medians": {
            "nominal_transcript": {"median_abs": med_abs_i, "median_nom_norm": med_nom_i},
            "least_privilege_transcript": {"median_abs": med_abs_ii, "median_nom_norm": med_nom_ii, "reduction_from_i": med_abs_i - med_abs_ii},
            "least_privilege_signed": {"median_abs": med_abs_iii, "median_nom_norm": med_nom_iii, "reduction_from_i": med_abs_i - med_abs_iii},
            "least_privilege_signed_best_partition": {"median_abs": med_abs_iv, "median_nom_norm": med_nom_iv, "reduction_from_i": med_abs_i - med_abs_iv},
        },
        "census": {
            "own": own_census,
            "mined_scored": mined_census,
            "total_acyclic": total_census,
            "cyclic_count": len(cyclic_records),
            "cyclic_configs": [r["config_id"] for r in cyclic_records],
        },
    }

    with open(OUTPUT_DIR / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Markdown summary
    md_content = f"""# Protocol v8 (M2): Proposition 4 and Absolute Reach

## Absolute Reach Across 19 Own Configs

| Condition | Median Abs WBR₁ | Median Nom-Normalised WBR₁ | Reduction from (i) |
|---|---|---|---|
| (i) Nominal, TRANSCRIPT | {med_abs_i:.1f} | {med_nom_i:.3f} | — |
| (ii) Least privilege | {med_abs_ii:.1f} | {med_nom_ii:.3f} | {med_abs_i - med_abs_ii:.1f} sinks ({(med_abs_i - med_abs_ii)/med_abs_i*100:.1f}%) |
| (iii) + SIGNED hand-off | {med_abs_iii:.1f} | {med_nom_iii:.3f} | {med_abs_i - med_abs_iii:.1f} sinks ({(med_abs_i - med_abs_iii)/med_abs_i*100:.1f}%) |
| (iv) + Best partition | {med_abs_iv:.1f} | {med_nom_iv:.3f} | {med_abs_i - med_abs_iv:.1f} sinks ({(med_abs_i - med_abs_iv)/med_abs_i*100:.1f}%) |

## Structural Census (55 Acyclic Configs)

*Note: 1 mined config (`zhongyu09/openchatbi:openchatbi/text2sql/sql_graph.py`) is cyclic and excluded from DAG blast-radius scoring.*

| Set | N | is_chain | Dominating Source (all steps) | Floor = 1 under SIGNED (Prop 4) |
|---|---|---|---|---|
| Own | {own_census['n']} | {own_census['chain_count']}/{own_census['n']} ({own_census['chain_pct']*100:.1f}%) | {own_census['dom_all_count']}/{own_census['n']} ({own_census['dom_all_pct']*100:.1f}%) | {own_census['prop4_floor1_count']}/{own_census['n']} ({own_census['prop4_floor1_pct']*100:.1f}%) |
| Mined (scored) | {mined_census['n']} | {mined_census['chain_count']}/{mined_census['n']} ({mined_census['chain_pct']*100:.1f}%) | {mined_census['dom_all_count']}/{mined_census['n']} ({mined_census['dom_all_pct']*100:.1f}%) | {mined_census['prop4_floor1_count']}/{mined_census['n']} ({mined_census['prop4_floor1_pct']*100:.1f}%) |
| **Total** | **{total_census['n']}** | **{total_census['chain_count']}/{total_census['n']} ({total_census['chain_pct']*100:.1f}%)** | **{total_census['dom_all_count']}/{total_census['n']} ({total_census['dom_all_pct']*100:.1f}%)** | **{total_census['prop4_floor1_count']}/{total_census['n']} ({total_census['prop4_floor1_pct']*100:.1f}%)** |
"""

    with open(OUTPUT_DIR / "summary.md", "w", encoding="utf-8") as f:
        f.write(md_content)

    if progress:
        progress.mark("M2", f"M2 completed: median abs reach reduction={med_abs_i - med_abs_iv:.1f} sinks, census={total_census['n']} acyclic")
        progress.finish_stage("M2")

    return summary


def main() -> None:
    run_topology_v8()


if __name__ == "__main__":
    main()
