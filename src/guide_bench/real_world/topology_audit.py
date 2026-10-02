"""Protocol v7c: blast-radius-minimal agent topology audit over the 19 real-world configs.

Runs `guide_research.topology.frontier` across every (config, mode, policy, k) combination
and writes the frontier table plus answers to the pre-registered questions Q1-Q4. See
docs/static-analysis-extensions-plan.md §2.4-2.5.

Run: python -m guide_bench.real_world.topology_audit
"""

from __future__ import annotations

import json
import statistics
import time
from dataclasses import replace
from pathlib import Path

from guide.runtime import HandoffMode
from guide_bench.real_world.configs import load_configs
from guide_bench.run import git_state
from guide_research.blast_radius import ObservedCall, SystemModel, synthesize_least_privilege
from guide_research.topology import FrontierRow, apply_partition, frontier, wbr

OUT_DIR = Path("experiments/results/topology-v7c")
MAX_STEPS = 10  # Bell(10) = 115,975; configs with more steps are skipped (none in this study)


def _nominal_model(cfg) -> SystemModel:  # type: ignore[no-untyped-def]
    return SystemModel.for_task(cfg.task, cfg.agents, cfg.policy, cfg.registry, mode=HandoffMode.TRANSCRIPT, gate="rule")


def _lp_model(cfg, base: SystemModel) -> SystemModel:  # type: ignore[no-untyped-def]
    calls = tuple(ObservedCall(s, t, o, a) for s, t, o, a in cfg.nominal_calls)
    lp = synthesize_least_privilege(base, calls)
    return replace(base, policy=lp.policy, workflow=lp.workflow)


def run() -> dict[str, object]:
    configs = load_configs()
    all_rows: list[FrontierRow] = []
    skipped: list[str] = []
    q4_records: list[dict[str, float]] = []  # per-config WBR_1 under the 4 §2.4 Q4 conditions

    for cfg in configs:
        n_steps = len(cfg.task.workflow.steps)
        if n_steps > MAX_STEPS:
            skipped.append(cfg.config_id)
            continue

        nominal_base = _nominal_model(cfg)
        lp_base = _lp_model(cfg, nominal_base)

        for mode in (HandoffMode.TRANSCRIPT, HandoffMode.SIGNED):
            for policy_kind, base in (("nominal", nominal_base), ("least_privilege", lp_base)):
                rows = frontier(cfg.config_id, base, mode, policy_kind, (1, 2))
                all_rows.extend(rows)

        # Q4: original structure/nominal/TRANSCRIPT vs LP-only vs LP+SIGNED vs LP+SIGNED+best-partition
        orig_identity = tuple(range(n_steps))
        m_i = apply_partition(replace(nominal_base, mode=HandoffMode.TRANSCRIPT), orig_identity)
        wbr_i = wbr(m_i, 1)

        m_ii = apply_partition(replace(lp_base, mode=HandoffMode.TRANSCRIPT), orig_identity)
        wbr_ii = wbr(m_ii, 1)

        m_iii = apply_partition(replace(lp_base, mode=HandoffMode.SIGNED), orig_identity)
        wbr_iii = wbr(m_iii, 1)

        best_rows = [r for r in all_rows if r.config_id == cfg.config_id and r.mode == "signed" and r.policy_kind == "least_privilege" and r.k == 1]
        wbr_iv = min((r.min_wbr for r in best_rows), default=wbr_iii)

        q4_records.append(
            {"config_id": cfg.config_id, "i_original": wbr_i, "ii_lp_only": wbr_ii, "iii_lp_signed": wbr_iii, "iv_lp_signed_best_partition": wbr_iv}
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with (OUT_DIR / "frontier.jsonl").open("w") as f:
        for r in all_rows:
            f.write(json.dumps(r.__dict__) + "\n")

    # Q1: transcript wash-out — median reduction (original -> best partition) under TRANSCRIPT, k=1
    q1_reductions = []
    for cfg in configs:
        if cfg.config_id in skipped:
            continue
        n_steps = len(cfg.task.workflow.steps)
        orig = next((r for r in all_rows if r.config_id == cfg.config_id and r.mode == "transcript" and r.policy_kind == "nominal" and r.k == 1 and r.m_blocks == 1), None)
        best = min(
            (r for r in all_rows if r.config_id == cfg.config_id and r.mode == "transcript" and r.policy_kind == "nominal" and r.k == 1),
            key=lambda r: r.min_wbr,
            default=None,
        )
        if orig and best and orig.min_wbr > 0:
            q1_reductions.append(1 - best.min_wbr / orig.min_wbr)
    q1_median_reduction = statistics.median(q1_reductions) if q1_reductions else float("nan")

    # Q2: least agents for the floor — under SIGNED + least-privilege, k=1
    q2_records = []
    for cfg in configs:
        if cfg.config_id in skipped:
            continue
        n_steps = len(cfg.task.workflow.steps)
        sub = [r for r in all_rows if r.config_id == cfg.config_id and r.mode == "signed" and r.policy_kind == "least_privilege" and r.k == 1]
        if not sub:
            continue
        floor = min(r.min_wbr for r in sub)
        m_at_floor = min(r.m_blocks for r in sub if abs(r.min_wbr - floor) < 1e-9)
        q2_records.append({"config_id": cfg.config_id, "n_steps": n_steps, "m_at_floor": m_at_floor, "floor_wbr": floor})

    # Q3: irreducible floor — configs where no partition/mode/policy pushes WBR_1 below a positive floor
    q3_irreducible = []
    for cfg in configs:
        if cfg.config_id in skipped:
            continue
        sub = [r for r in all_rows if r.config_id == cfg.config_id and r.k == 1]
        min_wbr_any = min((r.min_wbr for r in sub), default=0.0)
        if min_wbr_any > 1e-9:
            q3_irreducible.append({"config_id": cfg.config_id, "min_wbr_achievable": min_wbr_any})

    summary = {
        "n_configs_total": len(configs),
        "n_configs_skipped_too_large": len(skipped),
        "skipped_config_ids": skipped,
        "q1_transcript_washout": {
            "median_reduction_fraction": q1_median_reduction,
            "n_configs": len(q1_reductions),
            "interpretation": "fraction by which the best TRANSCRIPT partition reduces WBR_1 vs. the original (unpartitioned) structure",
        },
        "q2_least_agents_for_floor": q2_records,
        "q3_irreducible_floor": q3_irreducible,
        "q4_decomposition_median_wbr1": {
            "i_original_nominal_transcript": statistics.median([r["i_original"] for r in q4_records]) if q4_records else float("nan"),
            "ii_least_privilege_only": statistics.median([r["ii_lp_only"] for r in q4_records]) if q4_records else float("nan"),
            "iii_least_privilege_plus_signed": statistics.median([r["iii_lp_signed"] for r in q4_records]) if q4_records else float("nan"),
            "iv_least_privilege_plus_signed_plus_best_partition": statistics.median([r["iv_lp_signed_best_partition"] for r in q4_records]) if q4_records else float("nan"),
            "per_config": q4_records,
        },
        "git": git_state(),
        "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2))
    (OUT_DIR / "summary.md").write_text(_render_markdown(summary))
    return summary


def _render_markdown(summary: dict) -> str:  # type: ignore[type-arg]
    lines = ["# Protocol v7c: blast-radius-minimal agent topology — summary", ""]
    lines.append(f"Configs analysed: {summary['n_configs_total'] - summary['n_configs_skipped_too_large']} of {summary['n_configs_total']} "
                 f"({summary['n_configs_skipped_too_large']} skipped: too large for exhaustive partition enumeration)")
    lines.append("")
    lines.append("## Q1 — transcript wash-out")
    q1 = summary["q1_transcript_washout"]
    lines.append(f"Median WBR_1 reduction from best TRANSCRIPT partition vs. original structure: "
                 f"**{q1['median_reduction_fraction']:.3f}** (n={q1['n_configs']}).")
    lines.append("Hypothesis was 'little reduction' — under TRANSCRIPT, compromising one agent influences every later step regardless of topology.")
    lines.append("")
    lines.append("## Q2 — least agents for the floor (SIGNED + least-privilege, k=1)")
    lines.append("| config | n_steps | m at floor | floor WBR_1 |")
    lines.append("|---|---|---|---|")
    for r in summary["q2_least_agents_for_floor"]:
        lines.append(f"| {r['config_id']} | {r['n_steps']} | {r['m_at_floor']} | {r['floor_wbr']:.3f} |")
    lines.append("")
    lines.append("## Q3 — irreducible floor (no partition/mode/policy reaches WBR_1 = 0)")
    if not summary["q3_irreducible_floor"]:
        lines.append("None — every config reaches WBR_1 = 0 under some combination.")
    else:
        lines.append("| config | min achievable WBR_1 |")
        lines.append("|---|---|")
        for r in summary["q3_irreducible_floor"]:
            lines.append(f"| {r['config_id']} | {r['min_wbr_achievable']:.3f} |")
    lines.append("")
    lines.append("## Q4 — decomposition (median WBR_1 across configs)")
    q4 = summary["q4_decomposition_median_wbr1"]
    lines.append("| condition | median WBR_1 |")
    lines.append("|---|---|")
    lines.append(f"| (i) original structure, nominal policy, TRANSCRIPT | {q4['i_original_nominal_transcript']:.3f} |")
    lines.append(f"| (ii) least-privilege policy only | {q4['ii_least_privilege_only']:.3f} |")
    lines.append(f"| (iii) + SIGNED hand-off | {q4['iii_least_privilege_plus_signed']:.3f} |")
    lines.append(f"| (iv) + best partition | {q4['iv_least_privilege_plus_signed_plus_best_partition']:.3f} |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
