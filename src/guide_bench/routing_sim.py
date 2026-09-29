"""Routing simulation (hypothesis H4). SIMULATION: Bernoulli agents, not LLM agents.

Exercises the production ``guide.routing`` classes. Scenarios:
  misassigned : stationary; the statically assigned agent is not the best
  drift       : the initially-best agent degrades from 0.90 to 0.20 at T/2
Confidence reports are uninformative (always 0.9), as for poorly calibrated LLM self-reports,
so the failure penalty (baseline-v0 'trust freeze') is applied to every failure.

    python -m guide_bench.routing_sim --seeds 100 --horizon 1000 --out experiments/results/routing
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from collections.abc import Callable
from pathlib import Path

from guide.routing import BayesUCBRouter, Router, RoutingDecision, StaticRouter

AGENTS = ["a0", "a1", "a2", "a3", "a4"]


class RoundRobin:
    def __init__(self) -> None:
        self.i = 0

    def select(self, domain: str, candidates: list[str]) -> RoutingDecision:
        self.i += 1
        return RoutingDecision(candidates[(self.i - 1) % len(candidates)], "round_robin")

    def update(self, *a, **k) -> None:
        return None


POLICIES: dict[str, Callable[[], Router]] = {
    "static(first)": lambda: StaticRouter(),
    "round_robin": RoundRobin,
    "bayes_ucb": lambda: BayesUCBRouter(),
    "bayes_ucb+penalty": lambda: BayesUCBRouter(failure_penalty=5.0),
    "bayes_ucb+discount0.99": lambda: BayesUCBRouter(discount=0.99),
    "bayes_ucb+discount0.95": lambda: BayesUCBRouter(discount=0.95),
}


def means(scenario: str, t: int, horizon: int) -> list[float]:
    if scenario == "misassigned":
        return [0.75, 0.75, 0.90, 0.75, 0.75]
    return [0.90 if t < horizon // 2 else 0.20, 0.75, 0.75, 0.75, 0.75]


def simulate(policy: str, scenario: str, seed: int, horizon: int) -> tuple[float, float]:
    rng = random.Random(seed)
    router = POLICIES[policy]()
    regret = post = 0.0
    for t in range(horizon):
        mu = means(scenario, t, horizon)
        agent = router.select("d", AGENTS).agent
        k = AGENTS.index(agent)
        r = max(mu) - mu[k]
        regret += r
        if t >= horizon // 2:
            post += r
        router.update("d", agent, rng.random() < mu[k], confidence=0.9)
    return regret, post


def ci95(xs: list[float]) -> tuple[float, float, float]:
    m = statistics.fmean(xs)
    half = 1.96 * statistics.stdev(xs) / len(xs) ** 0.5 if len(xs) > 1 else 0.0
    return m, m - half, m + half


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=100)
    ap.add_argument("--horizon", type=int, default=1000)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    res: dict = {"seeds": args.seeds, "horizon": args.horizon, "scenarios": {}}
    lines = []
    for scenario in ("misassigned", "drift"):
        lines += [
            f"\n### {scenario} (T={args.horizon}, {args.seeds} seeds; mean expected regret, 95% CI)\n",
            "| Policy | total regret | regret after T/2 |",
            "|---|---|---|",
        ]
        res["scenarios"][scenario] = {}
        for policy in POLICIES:
            runs = [simulate(policy, scenario, s, args.horizon) for s in range(args.seeds)]
            tot, post = ci95([r[0] for r in runs]), ci95([r[1] for r in runs])
            res["scenarios"][scenario][policy] = {"total": tot, "post_half": post}
            lines.append(
                f"| {policy} | {tot[0]:.1f} [{tot[1]:.1f}, {tot[2]:.1f}] "
                f"| {post[0]:.1f} [{post[1]:.1f}, {post[2]:.1f}] |"
            )
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "routing.json").write_text(json.dumps(res, indent=2))
    (out / "routing.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
