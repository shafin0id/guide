"""Agent routing (proposal: route()).

:class:`BayesUCBRouter` keeps Beta(alpha, beta) evidence per (domain, agent), gives each
candidate ``warmup`` pulls, then selects argmax of the (1 - 1/t) posterior quantile
(Kaufmann, Cappe & Garivier 2012). Two optional, experimentally-evaluated extensions:

* ``discount`` (gamma < 1): exponential forgetting for non-stationary agents.
* ``failure_penalty``: extra beta mass on failures reported with high confidence
  (the baseline-v0 "trust freeze" heuristic). Off by default; see docs/experiments.md.

No regret guarantee is claimed for this system: the asymptotic result assumes stationary
Bernoulli rewards, which LLM agents do not provide.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the incomplete beta function (Lentz's method)."""
    tiny, eps = 1e-300, 3e-14

    def nz(v: float) -> float:
        return v if abs(v) > tiny else tiny

    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 / nz(1.0 - qab * x / qap)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 / nz(1.0 + aa * d)
        c = nz(1.0 + aa / c)
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 / nz(1.0 + aa * d)
        c = nz(1.0 + aa / c)
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def beta_cdf(x: float, a: float, b: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    ln_front = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x)
    if x < (a + 1.0) / (a + b + 2.0):
        return math.exp(ln_front) * _betacf(a, b, x) / a
    return 1.0 - math.exp(ln_front) * _betacf(b, a, 1.0 - x) / b


try:  # optional fast path; equality with the pure-Python path is asserted in tests
    from scipy.special import betaincinv as _betaincinv  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover - depends on environment
    _betaincinv = None


def beta_ppf(q: float, a: float, b: float, tol: float = 1e-10, *, pure: bool = False) -> float:
    """Quantile of Beta(a, b). Uses scipy if installed, else bisection on the CDF."""
    if _betaincinv is not None and not pure:
        return float(_betaincinv(a, b, q))
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if beta_cdf(mid, a, b) < q:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    return 0.5 * (lo + hi)


@dataclass(frozen=True)
class RoutingDecision:
    agent: str
    rule: str
    basis: Mapping[str, float] = field(default_factory=dict)


@runtime_checkable
class Router(Protocol):
    def select(self, domain: str, candidates: Sequence[str]) -> RoutingDecision: ...

    def update(self, domain: str, agent: str, success: bool, confidence: float | None = None) -> None: ...


class StaticRouter:
    """Fixed-role assignment: always the first candidate (or an explicit mapping)."""

    def __init__(self, assignment: Mapping[str, str] | None = None) -> None:
        self.assignment = dict(assignment or {})

    def select(self, domain: str, candidates: Sequence[str]) -> RoutingDecision:
        agent = self.assignment.get(domain, candidates[0])
        return RoutingDecision(agent, "static")

    def update(self, domain: str, agent: str, success: bool, confidence: float | None = None) -> None:
        return None


class BayesUCBRouter:
    def __init__(
        self,
        *,
        prior: tuple[float, float] = (1.0, 1.0),
        warmup: int = 1,
        discount: float = 1.0,
        failure_penalty: float = 0.0,
        penalty_confidence: float = 0.8,
    ) -> None:
        if not 0.0 < discount <= 1.0:
            raise ValueError("discount must be in (0, 1]")
        self.prior = prior
        self.warmup = warmup
        self.discount = discount
        self.failure_penalty = failure_penalty
        self.penalty_confidence = penalty_confidence
        self._ab: dict[tuple[str, str], list[float]] = {}
        self._pulls: dict[tuple[str, str], int] = {}
        self._t: dict[str, int] = {}

    def _state(self, domain: str, agent: str) -> list[float]:
        return self._ab.setdefault((domain, agent), [self.prior[0], self.prior[1]])

    def posterior(self, domain: str, agent: str) -> tuple[float, float]:
        a, b = self._state(domain, agent)
        return a, b

    def select(self, domain: str, candidates: Sequence[str]) -> RoutingDecision:
        if not candidates:
            raise ValueError("no candidate agents")
        for agent in candidates:
            if self._pulls.get((domain, agent), 0) < self.warmup:
                return RoutingDecision(agent, "warmup", {"pulls": float(self._pulls.get((domain, agent), 0))})
        t = self._t.get(domain, 0) + 1
        q = 1.0 - 1.0 / max(t, 2)
        scores = {agent: beta_ppf(q, *self._state(domain, agent)) for agent in candidates}
        best = max(candidates, key=lambda c: (scores[c], -candidates.index(c)))
        return RoutingDecision(best, "bayes_ucb", {"quantile": q, **{f"ucb:{k}": v for k, v in scores.items()}})

    def update(self, domain: str, agent: str, success: bool, confidence: float | None = None) -> None:
        self._t[domain] = self._t.get(domain, 0) + 1
        self._pulls[(domain, agent)] = self._pulls.get((domain, agent), 0) + 1
        if self.discount < 1.0:
            for (d, _), ab in self._ab.items():
                if d == domain:
                    ab[0] = self.prior[0] + self.discount * (ab[0] - self.prior[0])
                    ab[1] = self.prior[1] + self.discount * (ab[1] - self.prior[1])
        ab = self._state(domain, agent)
        if success:
            ab[0] += 1.0
        else:
            ab[1] += 1.0
            if self.failure_penalty and confidence is not None and confidence >= self.penalty_confidence:
                ab[1] += self.failure_penalty
