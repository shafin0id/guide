"""
Bayesian Upper Confidence Bound (Bayes-UCB) Dynamic Coordinator Module.

Implements optimal finite-time multi-armed bandit routing via exact (1 - 1/t) Beta quantile
maximization (Kaufmann et al., 2012). Guarantees sublinear regret O(ln T) asymptotic to the
Lai-Robbins bound and enforces anomaly-triggered trust freeze penalties.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy.stats import beta


class BayesUCBCoordinator:
    """
    Evidence-based coordinator dynamically routing tasks to specialist agents
    based on posterior Beta distributions over empirical historical success rates.
    """

    def __init__(
        self,
        agent_ids: List[str],
        domains: List[str],
        warmup_pulls: int = 1,
        anomaly_threshold: float = 0.80,
        anomaly_penalty: float = 5.0
    ):
        """
        Initializes coordinator with agent registry and domain prior distributions.

        Args:
            agent_ids: List of available operational specialist agent IDs.
            domains: List of supported task domains.
            warmup_pulls: Minimum observations required per eligible agent per domain.
            anomaly_threshold: Confidence threshold kappa above which failures trigger freeze.
            anomaly_penalty: Beta shape parameter penalty added on anomalous failure.
        """
        self.agent_ids = list(agent_ids)
        self.domains = list(domains)
        self.warmup_pulls = warmup_pulls
        self.anomaly_threshold = anomaly_threshold
        self.anomaly_penalty = anomaly_penalty

        # Registry tracks conjugate Beta(alpha, beta) parameters and pulls
        self.registry: Dict[str, Dict[str, Dict[str, Any]]] = {
            aid: {
                d: {
                    "alpha": 1.0,
                    "beta": 1.0,
                    "pulls": 0,
                    "frozen": False,
                    "anomalies": 0
                }
                for d in domains
            }
            for aid in self.agent_ids
        }

    def route_with_trace(
        self,
        domain: str,
        total_system_steps: int,
        exclude: Optional[List[str]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Selects optimal agent using exact (1 - 1/t) Beta quantile maximization
        and returns detailed mathematical trace (alpha, beta, Q values).

        Args:
            domain: Target task domain string.
            total_system_steps: Total system-wide orchestration steps t.
            exclude: Optional list of agent IDs to exclude (for fallback / rerouting).

        Returns:
            Tuple of (selected_agent_id, selection_trace_dict).
        """
        if domain not in self.domains:
            self._register_domain(domain)

        excluded_set = set(exclude or [])
        available_agents = [
            aid for aid in self.agent_ids
            if aid not in excluded_set and not self.registry[aid][domain]["frozen"]
        ]

        # If all non-excluded agents are frozen, check if any unfrozen agent exists among excluded set
        if not available_agents:
            unfrozen_fallback = [
                aid for aid in self.agent_ids
                if not self.registry[aid][domain]["frozen"]
            ]
            if unfrozen_fallback:
                available_agents = unfrozen_fallback
            else:
                raise ValueError(
                    f"No eligible non-frozen agents available for domain '{domain}' "
                    f"(all agents frozen or excluded: {excluded_set})"
                )

        t = max(2, total_system_steps)
        quantile_target = 1.0 - (1.0 / t)

        trace: Dict[str, Any] = {
            "domain": domain,
            "total_system_steps": total_system_steps,
            "effective_t": t,
            "quantile_target": round(quantile_target, 6),
            "candidate_arms": {},
            "phase": "ucb_quantile"
        }

        # 1. Warm-up Phase: ensure every eligible agent receives at least N_warmup observations
        for aid in available_agents:
            pulls = self.registry[aid][domain]["pulls"]
            if pulls < self.warmup_pulls:
                trace["phase"] = "warmup"
                trace["selected_agent"] = aid
                trace["warmup_agent"] = aid
                return aid, trace

        # 2. Bayes-UCB Quantile Maximization Phase
        best_agent: Optional[str] = None
        best_bound = -float("inf")

        for aid in available_agents:
            a = float(self.registry[aid][domain]["alpha"])
            b = float(self.registry[aid][domain]["beta"])

            # Compute inverse cumulative distribution function (PPF) of Beta(a, b)
            ucb_quantile = float(beta.ppf(quantile_target, a, b))

            # Numerical stability guard against NaN at boundary
            if np.isnan(ucb_quantile):
                ucb_quantile = a / (a + b)

            trace["candidate_arms"][aid] = {
                "alpha": a,
                "beta": b,
                "pulls": self.registry[aid][domain]["pulls"],
                "ucb_quantile": round(ucb_quantile, 6),
                "posterior_mean": round(a / (a + b), 6)
            }

            if ucb_quantile > best_bound:
                best_bound = ucb_quantile
                best_agent = aid

        if best_agent is None:
            best_agent = available_agents[0]

        trace["selected_agent"] = best_agent
        trace["winning_bound"] = round(best_bound, 6)
        return best_agent, trace

    def route(
        self,
        domain: str,
        total_system_steps: int,
        exclude: Optional[List[str]] = None
    ) -> str:
        """
        Selects optimal agent using exact (1 - 1/t) Beta quantile maximization.

        Args:
            domain: Target task domain string.
            total_system_steps: Total system-wide orchestration steps t.
            exclude: Optional list of agent IDs to exclude (for fallback / rerouting).

        Returns:
            Selected agent ID string.
        """
        best_agent, _ = self.route_with_trace(
            domain=domain,
            total_system_steps=total_system_steps,
            exclude=exclude
        )
        return best_agent

    def update_evidence(
        self,
        agent_id: str,
        domain: str,
        success: int,
        confidence: float = 1.0
    ) -> Dict[str, Any]:
        """
        Updates posterior Beta distributions and applies anomaly trust freeze if triggered.

        Args:
            agent_id: Operational agent ID.
            domain: Task domain.
            success: Binary outcome r_t in {0, 1}.
            confidence: Self-reported confidence score kappa in [0.0, 1.0].

        Returns:
            Dictionary recording update details and anomaly status.
        """
        if agent_id not in self.registry:
            raise KeyError(f"Unknown agent ID '{agent_id}'")

        if domain not in self.registry[agent_id]:
            self._register_domain(domain)

        stats = self.registry[agent_id][domain]
        stats["pulls"] += 1
        is_anomaly = False

        # Anomaly-Triggered Trust Freeze: Failed task (r_t=0) with high confidence (kappa >= 0.80)
        if success == 0 and confidence >= self.anomaly_threshold:
            stats["beta"] += self.anomaly_penalty
            stats["frozen"] = True
            stats["anomalies"] += 1
            is_anomaly = True
        elif success == 1:
            stats["alpha"] += 1.0
        else:
            stats["beta"] += 1.0

        return {
            "agent_id": agent_id,
            "domain": domain,
            "success": success,
            "confidence": confidence,
            "is_anomaly": is_anomaly,
            "new_alpha": stats["alpha"],
            "new_beta": stats["beta"],
            "pulls": stats["pulls"],
            "frozen": stats["frozen"]
        }

    def unfreeze_agent(self, agent_id: str, domain: Optional[str] = None) -> None:
        """Manually unfreezes an agent after administrative review."""
        if agent_id in self.registry:
            targets = [domain] if domain else self.domains
            for d in targets:
                if d in self.registry[agent_id]:
                    self.registry[agent_id][d]["frozen"] = False

    def get_agent_stats(self, agent_id: str, domain: str) -> Dict[str, Any]:
        """Retrieves statistical posterior metrics for a specific agent and domain."""
        if agent_id not in self.registry or domain not in self.registry[agent_id]:
            raise KeyError(f"Agent '{agent_id}' or domain '{domain}' not found in registry")

        stats = self.registry[agent_id][domain]
        a = stats["alpha"]
        b = stats["beta"]
        mean = a / (a + b)
        variance = (a * b) / (((a + b) ** 2) * (a + b + 1))
        return {
            "alpha": a,
            "beta": b,
            "pulls": stats["pulls"],
            "posterior_mean": mean,
            "posterior_variance": variance,
            "frozen": stats["frozen"],
            "anomalies": stats["anomalies"]
        }

    def _register_domain(self, domain: str) -> None:
        """Internal helper to dynamically register a new task domain."""
        if domain not in self.domains:
            self.domains.append(domain)
        for aid in self.agent_ids:
            if domain not in self.registry[aid]:
                self.registry[aid][domain] = {
                    "alpha": 1.0,
                    "beta": 1.0,
                    "pulls": 0,
                    "frozen": False,
                    "anomalies": 0
                }
