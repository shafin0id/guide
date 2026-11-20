"""Protocol v9 analysis: reads the frozen-protocol result files and writes summary.json / summary.md. Zero API cost."""

from __future__ import annotations

import glob
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parents[2]
S3 = ROOT / "experiments" / "results" / "v9"
GUIDE_CONDS = ["none", "strict", "cred", "flexI_cred"]
BASELINES = ["tool_filter", "spotlighting", "repeat_user_prompt", "pi_detector"]
SUITES = ["banking", "slack", "travel", "workspace"]


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def cohen_h(p1: float, p2: float) -> float:
    return 2 * math.asin(math.sqrt(p1)) - 2 * math.asin(math.sqrt(p2))


def mcnemar(a: dict[str, bool], b: dict[str, bool]) -> dict:
    keys = [k for k in a if k in b]
    n01 = sum((not a[k]) and b[k] for k in keys)
    n10 = sum(a[k] and (not b[k]) for k in keys)
    p = binomtest(min(n01, n10), n01 + n10, 0.5).pvalue if n01 + n10 else 1.0
    return {"n": len(keys), "a_only": n10, "b_only": n01, "p": p}


def fmt(k: int, n: int) -> str:
    lo, hi = wilson(k, n)
    return f"{100 * k / n:.1f}% ({k}/{n}) [{100 * lo:.1f}, {100 * hi:.1f}]" if n else "n/a"


def load(pattern: str) -> list[dict]:
    last: dict[str, dict] = {}
    for f in sorted(glob.glob(pattern)):
        for line in Path(f).read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                if r.get("condition") == "tool_filter" and "impl" not in r:
                    continue  # discarded first implementation (provider ignored tool schemas); disclosed
                last[r["key"]] = r
    return [r for r in last.values() if r["status"] == "completed"]


def short(task: str) -> str:
    return task


# ------------------------------------------------------------------------------------------------ AgentDojo
def agentdojo(md: list[str], out: dict) -> None:
    ben = load(str(S3 / "runs/main/rows_none_default.jsonl"))
    md.append("## A. AgentDojo benign utility (default agent, deepseek-flash, all 97 tasks)\n")
    md.append("| Condition | Overall | Banking | Slack | Travel | Workspace |\n|---|---|---|---|---|---|")
    util: dict[str, dict[str, bool]] = defaultdict(dict)
    for r in ben:
        util[r["condition"]][f"{r['suite']}|{r['user_task']}"] = bool(r["utility"])
    reps = {}
    for t in ("rep2", "rep3"):
        for r in load(str(S3 / f"runs/{t}/rows_none_default.jsonl")):
            reps.setdefault(r["condition"], {}).setdefault(t, {})[f"{r['suite']}|{r['user_task']}"] = bool(r["utility"])
    out["benign"] = {}
    for c in GUIDE_CONDS + BASELINES:
        u = util.get(c, {})
        if not u:
            continue
        row = [fmt(sum(u.values()), len(u))]
        for s in SUITES:
            ks = [k for k in u if k.startswith(s + "|")]
            row.append(fmt(sum(u[k] for k in ks), len(ks)))
        md.append(f"| {c} | " + " | ".join(row) + " |")
        out["benign"][c] = {"k": sum(u.values()), "n": len(u)}
    md.append("")
    if reps:
        md.append(
            "Repetitions (same tasks, rerun): utility rate rep1 / rep2 / rep3, and per-task disagreement between runs.\n"
        )
        md.append("| Condition | rep1 | rep2 | rep3 | tasks with differing outcomes |\n|---|---|---|---|---|")
        for c in GUIDE_CONDS:
            r = [util.get(c, {})] + [reps.get(c, {}).get(t, {}) for t in ("rep2", "rep3")]
            common = set(r[0]) & set(r[1]) & set(r[2])
            if not common:
                continue
            diff = sum(len({x[k] for x in r}) > 1 for k in common)
            md.append(
                f"| {c} | "
                + " | ".join(f"{100 * sum(x[k] for k in common) / len(common):.1f}%" for x in r)
                + f" | {diff}/{len(common)} |"
            )
        md.append("")
    md.append("Paired tests on benign utility (exact McNemar, same tasks):\n")
    md.append("| Comparison | tasks | first only | second only | p | Cohen's h |\n|---|---|---|---|---|---|")
    for a, b in [
        ("none", "strict"),
        ("none", "cred"),
        ("none", "flexI_cred"),
        ("strict", "flexI_cred"),
        ("strict", "cred"),
    ] + [("none", x) for x in BASELINES]:
        if a in util and b in util:
            m = mcnemar(util[a], util[b])
            h = cohen_h(sum(util[a].values()) / len(util[a]), sum(util[b].values()) / len(util[b]))
            md.append(f"| {a} vs {b} | {m['n']} | {m['a_only']} | {m['b_only']} | {m['p']:.4f} | {h:.2f} |")
    md.append("")
    out["attacks"] = {}
    for atk in ("direct", "important_instructions", "guide_aware"):
        rows = load(str(S3 / f"runs/main/rows_{atk}_weak.jsonl"))
        if not rows:
            continue
        md.append(f"## A. AgentDojo attacks: `{atk}` (weak agent, stratified 200-pair sample)\n")
        md.append(
            "| Condition | Attack success (95% CI) | Utility under attack | Monitor denials/run |\n|---|---|---|---|"
        )
        sec: dict[str, dict[str, bool]] = defaultdict(dict)
        for r in rows:
            sec[r["condition"]][f"{r['suite']}|{r['user_task']}|{r['injection_task']}"] = bool(r["security"])
        ut: dict[str, list[bool]] = defaultdict(list)
        den: dict[str, list[int]] = defaultdict(list)
        for r in rows:
            ut[r["condition"]].append(bool(r["utility"]))
            den[r["condition"]].append(r.get("guide_denials", 0))
        out["attacks"][atk] = {}
        for c in GUIDE_CONDS + BASELINES:
            if c in sec:
                k, n = sum(sec[c].values()), len(sec[c])
                md.append(
                    f"| {c} | {fmt(k, n)} | {100 * sum(ut[c]) / len(ut[c]):.1f}% | {statistics.mean(den[c]):.2f} |"
                )
                out["attacks"][atk][c] = {"asr_k": k, "n": n}
        md.append("")
        if "none" in sec:
            for c in GUIDE_CONDS[1:] + BASELINES:
                if c in sec:
                    m = mcnemar(sec["none"], sec[c])
                    md.append(
                        f"- none vs {c}: attack only in none = {m['a_only']}, only in {c} = {m['b_only']}, exact McNemar p = {m['p']:.4f}, "
                        f"Cohen's h = {cohen_h(sum(sec['none'].values()) / len(sec['none']), sum(sec[c].values()) / len(sec[c])):.2f}"
                    )
            md.append("")
    # adaptive
    ad = load(str(S3 / "runs/main/rows_adaptive_weak.jsonl"))
    if ad:
        md.append("## A. Adaptive attacker loop (5 rounds, 30 pairs)\n")
        md.append("| Condition | Attacker success (95% CI) | Mean winning round | Utility at end |\n|---|---|---|---|")
        by: dict[str, list[dict]] = defaultdict(list)
        for r in ad:
            by[r["condition"]].append(r)
        out["adaptive"] = {}
        for c in GUIDE_CONDS:
            rs = by.get(c, [])
            if rs:
                k = sum(r["success"] for r in rs)
                rounds = [r["round"] for r in rs if r["success"]]
                md.append(
                    f"| {c} | {fmt(k, len(rs))} | {statistics.mean(rounds):.1f} | {100 * sum(bool(r['utility']) for r in rs) / len(rs):.1f}% |"
                    if rounds
                    else f"| {c} | {fmt(k, len(rs))} | - | {100 * sum(bool(r['utility']) for r in rs) / len(rs):.1f}% |"
                )
                out["adaptive"][c] = {"k": k, "n": len(rs)}
        md.append("")


# ------------------------------------------------------------------------------------------------ real world
EDGES = {  # flow graph per topology: (edges among agent names, shared_transcript)
    "sequential": ([("R", "W"), ("W", "A")], False),
    "supervisor": ([], True),
    "parallel": ([("R", "A"), ("N", "A")], False),
    "router": ([("R", "W"), ("W", "S"), ("W", "S2")], False),
    "cyclic": ([("D", "V"), ("V", "D"), ("V", "A")], False),
    "hierarchical": ([], True),
    "conditional": ([("R", "W"), ("W", "S"), ("W", "S2")], False),
    "iterative": ([("D", "D"), ("D", "A")], False),
    "roundrobin": ([], True),
    "selector": ([], True),
    "swarm": ([], True),
    "graphflow_seq": ([("R", "W"), ("W", "A")], False),
    "graphflow_par": ([("R", "A"), ("N", "A")], False),
}
HOLDS_SINK = {"A": True, "AW": True, "S": True, "S2": True}


def structural(apps: list[tuple[str, str, str, str]], md: list[str], out: dict) -> None:
    md.append("## B. Structural analysis of the 15 live applications (assumed-compromise, one agent at a time)\n")
    md.append(
        "| App | Topology class | Agents | Compromised reader reaches an agent holding a sink | WBR1 (share of sink-holding agents influenced, max over single agents) |\n|---|---|---|---|---|"
    )
    res = []
    for app, _fw, topo, _sid in apps:
        edges, shared = EDGES[topo]
        agents = {a for e in edges for a in e}
        agents |= {"R", "W", "A"} if shared or not agents else set()
        if topo in ("parallel", "graphflow_par"):
            agents = {"R", "N", "A"}
        if topo in ("router", "conditional"):
            agents = {"R", "W", "S", "S2"}
        if topo in ("cyclic", "iterative"):
            agents = {"D", "V", "A"} if topo == "cyclic" else {"D", "A"}
        sinks = {a for a in agents if a in HOLDS_SINK}

        def influenced(
            k: str,
            _shared: bool = shared,
            _agents: set[str] = agents,
            _edges: list[tuple[str, str]] = edges,
        ) -> set[str]:
            if _shared:
                return set(_agents)
            seen, stack = {k}, [k]
            while stack:
                for u, v in _edges:
                    if u == stack[-1] and v not in seen:
                        seen.add(v)
                        stack.append(v)
                stack.pop() if stack and all(v in seen for u, v in _edges if u == stack[-1]) else None
            return seen

        reader = "D" if topo in ("cyclic", "iterative") else "R"
        reaches = bool(influenced(reader) & sinks)
        wbr = max(len(influenced(k) & sinks) / len(sinks) for k in agents)
        res.append({"app": app, "topology": topo, "reaches": reaches, "wbr1": wbr, "shared_transcript": shared})
        md.append(
            f"| {app} | {'shared-context group' if shared else 'directed flow'} | {len(agents)} | {'yes' if reaches else 'no'} | {wbr:.2f} |"
        )
    md.append("")
    out["structural"] = res


def realworld(md: list[str], out: dict) -> None:
    import sys

    sys.path.insert(0, str(ROOT / "src"))
    from guide.policy import PolicyContext  # noqa: PLC0415
    from guide.types import ToolCall  # noqa: PLC0415
    from guide_realworld.core import Runtime  # noqa: PLC0415
    from guide_realworld.scenarios import ATTACK_GT, SCENARIOS  # noqa: PLC0415

    rows = load(str(S3 / "realworld/main/rows.jsonl"))
    if not rows:
        return
    apps = sorted({(r["app"], r["framework"], r["topology"], r["scenario"]) for r in rows})
    md.append("## B. Real-world applications (LangGraph, CrewAI, AutoGen; DeepSeek non-thinking)\n")
    md.append(
        "Benign success (default prompt) and attack success (assumed-compromised reader relays the attacker's note; plus direct and important_instructions insertions).\n"
    )
    md.append(
        "| Condition | Benign success | Attack success: relay | Attack success: direct + important_instructions | Attacker sink attempts (relay) |\n|---|---|---|---|---|"
    )
    out["realworld"] = {}
    for c in GUIDE_CONDS:
        b = [r for r in rows if r["condition"] == c and r["kind"] == "benign"]
        rl = [r for r in rows if r["condition"] == c and r["kind"] == "inject" and r["template"] == "relay"]
        ot = [r for r in rows if r["condition"] == c and r["kind"] == "inject" and r["template"] != "relay"]
        if b:
            md.append(
                f"| {c} | {fmt(sum(bool(r['benign_ok']) for r in b), len(b))} | {fmt(sum(bool(r['attack_ok']) for r in rl), len(rl))} | "
                f"{fmt(sum(bool(r['attack_ok']) for r in ot), len(ot))} | {sum(r['attacker_sink_attempts'] > 0 for r in rl)}/{len(rl)} |"
            )
            out["realworld"][c] = {
                "benign": [sum(bool(r["benign_ok"]) for r in b), len(b)],
                "relay": [sum(bool(r["attack_ok"]) for r in rl), len(rl)],
                "other": [sum(bool(r["attack_ok"]) for r in ot), len(ot)],
            }
    md.append("")
    md.append(
        "Attack success under the relay template by framework and topology (undefended `none` vs `strict`/`cred`/`flexI_cred`):\n"
    )
    md.append("| App | Framework | Topology | none | strict | cred | flexI_cred |\n|---|---|---|---|---|---|---|")
    for app, fw, topo, _s in apps:
        cells = []
        for c in GUIDE_CONDS:
            rl = [
                r
                for r in rows
                if r["app"] == app and r["condition"] == c and r["kind"] == "inject" and r["template"] == "relay"
            ]
            cells.append(f"{sum(bool(r['attack_ok']) for r in rl)}/{len(rl)}")
        md.append(f"| {app} | {fw} | {topo} | " + " | ".join(cells) + " |")
    md.append("")
    # static prediction vs live decisions on attacker sink attempts
    sound = exact = admitted_exec = blocked_den = total = 0
    pred_cache: dict[tuple[str, int, str], bool] = {}
    for r in rows:
        if r["kind"] != "inject" or r["condition"] == "none":
            continue
        sc = SCENARIOS[r["scenario"]]
        variant = {"strict": "strict", "cred": "cred", "flexI_cred": "flexI_cred"}[r["condition"]]
        key = (r["scenario"], r["task"], variant)
        if key not in pred_cache:
            rt = Runtime(sc, r["condition"], variant, sc.benign[r["task"]].prompt, "")
            for n, td in sc.tools.items():
                if td.directory:
                    rt.guard.observe_directory(rt.run_id, n, list(sc.directory_ids))
            tool, args = ATTACK_GT[r["scenario"]][r["task"]]
            d = rt.guard.evaluate(
                ToolCall(tool=tool, operation=tool, args=args, principal="agent"),
                PolicyContext(run_id=rt.run_id, step_id="x", step_tools=rt.step_tools),
            )
            pred_cache[key] = d.decision.value != "DENY"
        predicted_admit = pred_cache[key]
        gt_tool = ATTACK_GT[r["scenario"]][r["task"]][0]
        for e in r["events"]:
            gt_args = ATTACK_GT[r["scenario"]][r["task"]][1]
            ctrl = sc.tools[gt_tool].control
            if e["tool"] == gt_tool and all(str(e["args"].get(k, "")).lower() == str(gt_args[k]).lower() for k in ctrl):
                total += 1
                live_exec = e["decision"] != "DENY"
                if live_exec and not predicted_admit:
                    sound += 1
                if (not live_exec) and predicted_admit:
                    exact += 1
                admitted_exec += live_exec and predicted_admit
                blocked_den += (not live_exec) and (not predicted_admit)
    md.append(
        f"Static prediction vs live monitor decisions on attacker sink calls (held-out apps, zero-cost prediction from the guard rule, trusted = user prompt, full directory): "
        f"{total} calls; predicted-blocked and denied {blocked_den}; predicted-admitted and executed {admitted_exec}; "
        f"soundness violations (executed although predicted blocked) {sound}; over-approximations (denied although predicted admitted, e.g. lookup not performed) {exact}. "
        f"Agreement {(blocked_den + admitted_exec) / total * 100 if total else float('nan'):.1f}%.\n"
    )
    out["realworld_prediction"] = {
        "calls": total,
        "blocked_denied": blocked_den,
        "admitted_executed": admitted_exec,
        "soundness_violations": sound,
        "overapprox": exact,
    }
    structural(apps, md, out)


def exhaustive(md: list[str], out: dict) -> None:
    pa, pb = S3 / "exhaustive/part_A.json", S3 / "exhaustive/part_B.json"
    if pa.exists() and pb.exists():
        a, b = json.loads(pa.read_text()), json.loads(pb.read_text())
        md.append("## C. Bounded exhaustive verification of the blast-radius model\n")
        md.append(
            f"- Influence analysis: {a['influence_cases']:,} (DAG, handoff mode, tool assignment, write policy, compromised set) cases on up to 5 steps; "
            f"{a['oracle_mismatches']} disagreements with an independent graph-reachability oracle; {a['monotonicity_violations']} monotonicity violations."
        )
        md.append(
            f"- Gate agreement: {b['gate_evaluations']:,} (policy, delegation, gate configuration, call) evaluations; real gate executed {b['executed_by_real_gate']:,} "
            f"and denied {b['denied_by_real_gate']:,}; {b['soundness_violations']} soundness and {b['exactness_violations']} exactness violations.\n"
        )
        out["exhaustive"] = {"A": a, "B": b}


def variants(md: list[str], out: dict) -> None:
    f = S3 / "w2/variants.json"
    if not f.exists():
        return
    v = json.loads(f.read_text())
    md.append(
        "## D. Offline variant study (zero cost): containment on 949 pairs' in-scope subset and estimated benign utility\n"
    )
    md.append(
        "| Variant | Dev containment | Held-out containment | Dev benign estimate | Held-out benign estimate |\n|---|---|---|---|---|"
    )
    for k, x in v.items():
        if k.startswith("_"):
            continue
        c, b = x["containment"], x["benign_est"]
        md.append(f"| {k} | {fmt(*c['dev'])} | {fmt(*c['heldout'])} | {fmt(*b['dev'])} | {fmt(*b['heldout'])} |")
    md.append(
        f"\nSelection rule outcome: {v['_selection']['chosen']} "
        f"(eligible: {', '.join(v['_selection']['eligible'])}). See scripts/v9/w2_variants.py.\n"
    )


def spend_summary(md: list[str], out: dict) -> None:
    led = S3 / "ledger.jsonl"
    if led.exists():
        tot: dict[str, float] = defaultdict(float)
        for line in led.read_text().splitlines():
            r = json.loads(line)
            tot[r["provider"]] += r["usd"]
        md.append("## E. Spend (ledger, list-price estimate)\n")
        md.append(", ".join(f"{k}: ${v:.2f}" for k, v in tot.items()) + "\n")
        out["spend_usd"] = dict(tot)


def main() -> None:
    md = ["# Protocol v9 results summary (auto-generated by scripts/v9/analyze.py)\n"]
    out: dict = {}
    for fn in (agentdojo, realworld, exhaustive, variants, spend_summary):
        fn(md, out)
    (S3 / "summary.md").write_text("\n".join(md))
    (S3 / "summary.json").write_text(json.dumps(out, indent=1))
    print("\n".join(md))


if __name__ == "__main__":
    main()
