"""Statistical analysis (docs/evaluation.md §5).

    python -m guide_bench.stats experiments/results/main [--baseline B2]
Writes summary.md and summary.json next to results.jsonl.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

METRICS = ("task_success", "intent_fidelity", "violation")
COMPARISONS = (("P", "B1"), ("P", "B2"), ("GPLUS", "P"), ("GPLUS", "B2"))


def load(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = [json.loads(line) for line in (path / "results.jsonl").read_text().splitlines() if line.strip()]
    ok = [r for r in rows if r.get("status") != "harness_error"]
    return ok, [r for r in rows if r.get("status") == "harness_error"]


def _mean(xs: list[float]) -> float:
    return statistics.fmean(xs) if xs else float("nan")


def cluster_bootstrap(rows: list[dict], metric: str, n: int = 10_000, seed: int = 7) -> tuple[float, float]:
    by_task: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        by_task[r["task_id"]].append(float(r[metric]))
    tasks = sorted(by_task)
    rng = random.Random(seed)
    means = []
    for _ in range(n):
        sample = [x for t in (rng.choice(tasks) for _ in tasks) for x in by_task[t]]
        means.append(_mean(sample))
    means.sort()
    return means[int(0.025 * n)], means[int(0.975 * n) - 1]


def iqr(xs: list[float]) -> tuple[float, float, float]:
    q = statistics.quantiles(xs, n=4) if len(xs) > 1 else [xs[0]] * 3
    return q[0], statistics.median(xs), q[2]


def holm(pvalues: dict[str, float]) -> dict[str, float]:
    items = sorted((p, k) for k, p in pvalues.items() if p == p)
    m, adj, running = len(items), {}, 0.0
    for i, (p, k) in enumerate(items):
        running = max(running, min(1.0, (m - i) * p))
        adj[k] = running
    return adj


def paired(rows: list[dict], a: str, b: str, metric: str) -> dict[str, Any]:
    from scipy.stats import wilcoxon

    per: dict[tuple[str, str], list[float]] = defaultdict(list)
    for r in rows:
        per[(r["task_id"], r["condition"])].append(float(r[metric]))
    tasks = sorted({t for t, c in per if c == a} & {t for t, c in per if c == b})
    diffs = [_mean(per[(t, a)]) - _mean(per[(t, b)]) for t in tasks]
    res: dict[str, Any] = {"n_tasks": len(tasks), "mean_diff": _mean(diffs), "nonzero": sum(d != 0 for d in diffs)}
    if res["nonzero"] == 0:
        res.update(W=None, p=float("nan"), note="all paired differences are zero; test uninformative")
    else:
        w = wilcoxon(diffs, zero_method="pratt", alternative="two-sided")
        res.update(W=float(w.statistic), p=float(w.pvalue))
        if res["nonzero"] < 6:
            res["note"] = "fewer than 6 non-zero differences; low power"
    return res


def summarise(rows: list[dict], conditions: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for c in conditions:
        rs = [r for r in rows if r["condition"] == c]
        if not rs:
            continue
        wall = [r["wall_s"] for r in rs]
        toks = [r["prompt_tokens"] + r["completion_tokens"] for r in rs]
        d = {
            "runs": len(rs),
            "completed": _mean([r["status"] == "completed" for r in rs]),
            "halted_integrity": sum(r["status"] == "rejected_integrity" for r in rs),
            "trace_completeness": _mean([r["trace_completeness"] for r in rs]),
            "model_calls": _mean([r["model_calls"] for r in rs]),
            "tokens_iqr": iqr(toks),
            "wall_iqr": iqr(wall),
            "denials": sum(len(r["denied_rules"]) for r in rs),
            "false_denial_runs": sum(bool(r["denied_rules"]) and r["task_success"] == 0 for r in rs),
        }
        for m in METRICS:
            d[m] = _mean([float(r[m]) for r in rs])
            d[m + "_ci"] = cluster_bootstrap(rs, m)
        out[c] = d
    return out


def fmt_ci(d: dict, m: str) -> str:
    lo, hi = d[m + "_ci"]
    return f"{d[m]:.3f} [{lo:.3f}, {hi:.3f}]"


def report(path: Path) -> dict[str, Any]:
    rows, errors = load(path)
    conditions = sorted({r["condition"] for r in rows}, key=lambda c: (len(c), c))
    summ = summarise(rows, conditions)
    lines = [
        f"# Results: `{path}`\n",
        f"Runs analysed: {len(rows)}; harness errors: {len(errors)}.\n",
        "## Per condition (mean, 95% task-cluster bootstrap CI)\n",
        "| Condition | runs | task success | intent fidelity | violation rate | completed | trace compl. | "
        "median tokens [IQR] | median wall s [IQR] | model calls |",
        "|---" * 10 + "|",
    ]
    for c, d in summ.items():
        t, w = d["tokens_iqr"], d["wall_iqr"]
        lines.append(
            f"| {c} | {d['runs']} | {fmt_ci(d, 'task_success')} | {fmt_ci(d, 'intent_fidelity')} | "
            f"{fmt_ci(d, 'violation')} | {d['completed']:.3f} | {d['trace_completeness']:.3f} | "
            f"{t[1]:.0f} [{t[0]:.0f}, {t[2]:.0f}] | {w[1]:.1f} [{w[0]:.1f}, {w[2]:.1f}] | {d['model_calls']:.1f} |"
        )
    comps = [(a, b) for a, b in COMPARISONS if a in summ and b in summ]
    tests: dict[str, Any] = {}
    if comps:
        lines += [
            "\n## Paired task-level comparisons (Wilcoxon signed-rank, Pratt; Holm-adjusted per metric)\n",
            "| Comparison | metric | tasks | non-zero | mean diff | W | p | p (Holm) | note |",
            "|---" * 9 + "|",
        ]
        for m in METRICS:
            res = {f"{a} vs {b}": paired(rows, a, b, m) for a, b in comps}
            adj = holm({k: v["p"] for k, v in res.items()})
            for k, v in res.items():
                v["p_holm"] = adj.get(k, float("nan"))
                w = "–" if v["W"] is None else f"{v['W']:.1f}"
                p = "–" if v["p"] != v["p"] else f"{v['p']:.4f}"
                ph = "–" if v["p_holm"] != v["p_holm"] else f"{v['p_holm']:.4f}"
                lines.append(
                    f"| {k} | {m} | {v['n_tasks']} | {v['nonzero']} | {v['mean_diff']:+.3f} "
                    f"| {w} | {p} | {ph} | {v.get('note', '')} |"
                )
            tests[m] = res
    if "P" in summ and "B2" in summ:
        p, b = summ["P"], summ["B2"]
        ratio = p["wall_iqr"][1] / b["wall_iqr"][1]
        gain = max(p["task_success"] - b["task_success"], p["intent_fidelity"] - b["intent_fidelity"])
        fewer = (1 - p["violation"] / b["violation"]) if b["violation"] > 0 else float("nan")
        meaningful = (gain >= 0.10 or (fewer == fewer and fewer >= 0.5)) and ratio <= 1.3
        lines += [
            "\n## Proposal practical-significance criterion (P vs B2)\n",
            f"- best gain in success/fidelity: {gain:+.3f} (threshold +0.10)",
            f"- violation reduction: {'n/a (B2 has none)' if fewer != fewer else f'{fewer:.1%}'} (threshold 50%)",
            f"- median wall-time ratio P/B2: {ratio:.2f} (threshold 1.30)",
            f"- **criterion met: {meaningful}**",
        ]
    by_task: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        by_task[r["task_id"]][r["condition"]].append(r)
    lines += [
        "\n## Per task: success / violation rate\n",
        "| Task | " + " | ".join(conditions) + " |",
        "|---" * (len(conditions) + 1) + "|",
    ]
    for t in sorted(by_task):
        cells = []
        for c in conditions:
            rs = by_task[t].get(c, [])
            cells.append(
                "–"
                if not rs
                else f"{_mean([r['task_success'] for r in rs]):.1f} / {_mean([r['violation'] for r in rs]):.1f}"
            )
        lines.append(f"| {t} | " + " | ".join(cells) + " |")
    if errors:
        lines += ["\n## Harness errors\n"] + [f"- {e['key']}: {e.get('error')}" for e in errors]
    (path / "summary.md").write_text("\n".join(lines) + "\n")
    (path / "summary.json").write_text(json.dumps({"conditions": summ, "tests": tests}, indent=2, default=str))
    return {"conditions": summ, "tests": tests}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    args = ap.parse_args(argv)
    report(Path(args.path))
    print((Path(args.path) / "summary.md").read_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
