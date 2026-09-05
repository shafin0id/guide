"""
Unit tests for BayesUCBCoordinator.

Verifies:
1. Warm-up phase invariant (N_warmup >= 1 per eligible agent).
2. (1 - 1/t) Beta quantile maximization routing via scipy.stats.beta.ppf.
3. Fallback routing with exclusions (exclude parameter).
4. Anomaly-Triggered Trust Freeze penalty (beta += 5.0) on high-confidence failures.
5. Posterior updates (alpha += 1, beta += 1) and stats calculation.
"""

import pytest
from guide_mas.core.coordinator import BayesUCBCoordinator


def test_warmup_phase_invariant():
    """Verifies that all available agents receive at least 1 observation before UCB activates."""
    agents = ["agent_1", "agent_2", "agent_3"]
    domain = "synthesis"
    coordinator = BayesUCBCoordinator(agent_ids=agents, domains=[domain], warmup_pulls=1)

    # First 3 pulls must cycle through all unpulled agents
    selected_1 = coordinator.route(domain=domain, total_system_steps=1)
    coordinator.update_evidence(agent_id=selected_1, domain=domain, success=1)

    selected_2 = coordinator.route(domain=domain, total_system_steps=2)
    coordinator.update_evidence(agent_id=selected_2, domain=domain, success=1)

    selected_3 = coordinator.route(domain=domain, total_system_steps=3)
    coordinator.update_evidence(agent_id=selected_3, domain=domain, success=1)

    pulled = {selected_1, selected_2, selected_3}
    assert pulled == set(agents), f"Warmup did not cover all agents: {pulled}"


def test_bayes_ucb_quantile_routing():
    """Verifies that agent with higher empirical success has higher Beta quantile and is routed."""
    agents = ["high_performer", "low_performer"]
    domain = "synthesis"
    coordinator = BayesUCBCoordinator(agent_ids=agents, domains=[domain], warmup_pulls=1)

    # Provide warmup
    coordinator.update_evidence("high_performer", domain, success=1)
    coordinator.update_evidence("low_performer", domain, success=0)

    # Accumulate evidence
    for _ in range(5):
        coordinator.update_evidence("high_performer", domain, success=1)
    for _ in range(5):
        coordinator.update_evidence("low_performer", domain, success=0)

    # High performer has alpha=7, beta=1; low performer has alpha=1, beta=7
    best_agent = coordinator.route(domain=domain, total_system_steps=15)
    assert best_agent == "high_performer"

    stats_high = coordinator.get_agent_stats("high_performer", domain)
    stats_low = coordinator.get_agent_stats("low_performer", domain)
    assert stats_high["posterior_mean"] > stats_low["posterior_mean"]


def test_fallback_exclusion_routing():
    """Verifies that excluding the top arm routes to the second-highest arm."""
    agents = ["agent_a", "agent_b", "agent_c"]
    domain = "reconciliation"
    coordinator = BayesUCBCoordinator(agent_ids=agents, domains=[domain], warmup_pulls=1)

    # Arm A: 10 successes
    for _ in range(10):
        coordinator.update_evidence("agent_a", domain, success=1)
    # Arm B: 5 successes
    for _ in range(5):
        coordinator.update_evidence("agent_b", domain, success=1)
    # Arm C: 1 success
    coordinator.update_evidence("agent_c", domain, success=1)

    # Normal routing chooses agent_a
    assert coordinator.route(domain, total_system_steps=20) == "agent_a"

    # Excluding agent_a must route to agent_b
    fallback = coordinator.route(domain, total_system_steps=20, exclude=["agent_a"])
    assert fallback == "agent_b"

    # Excluding agent_a and agent_b must route to agent_c
    fallback_c = coordinator.route(domain, total_system_steps=20, exclude=["agent_a", "agent_b"])
    assert fallback_c == "agent_c"


def test_anomaly_triggered_trust_freeze():
    """Verifies that high-confidence failure (kappa >= 0.80) triggers beta += 5.0 penalty and freezes arm."""
    agents = ["reliable_agent", "suspect_agent"]
    domain = "planning"
    coordinator = BayesUCBCoordinator(
        agent_ids=agents,
        domains=[domain],
        warmup_pulls=1,
        anomaly_threshold=0.80,
        anomaly_penalty=5.0
    )

    # Suspect agent starts with 1 success
    coordinator.update_evidence("suspect_agent", domain, success=1, confidence=1.0)
    coordinator.update_evidence("reliable_agent", domain, success=1, confidence=1.0)

    # Suspect agent experiences anomalous failure with confidence 0.95
    update_res = coordinator.update_evidence(
        agent_id="suspect_agent",
        domain=domain,
        success=0,
        confidence=0.95
    )

    assert update_res["is_anomaly"] is True
    assert update_res["new_beta"] == 6.0  # initial 1.0 + 5.0 penalty
    assert update_res["frozen"] is True

    # Next route must avoid frozen suspect agent and choose reliable_agent
    next_selected = coordinator.route(domain, total_system_steps=5)
    assert next_selected == "reliable_agent"

    # Verify stats
    stats = coordinator.get_agent_stats("suspect_agent", domain)
    assert stats["anomalies"] == 1
    assert stats["frozen"] is True


def test_route_with_trace():
    """Verifies that route_with_trace returns exact alpha, beta, and Q values."""
    agents = ["agent_1", "agent_2"]
    domain = "synthesis"
    coordinator = BayesUCBCoordinator(agent_ids=agents, domains=[domain], warmup_pulls=1)

    # Warmup both
    coordinator.update_evidence("agent_1", domain, success=1)
    coordinator.update_evidence("agent_2", domain, success=0)

    selected, trace = coordinator.route_with_trace(domain=domain, total_system_steps=10)
    assert selected == "agent_1"
    assert "candidate_arms" in trace
    assert "agent_1" in trace["candidate_arms"]
    assert "alpha" in trace["candidate_arms"]["agent_1"]
    assert "beta" in trace["candidate_arms"]["agent_1"]
    assert "ucb_quantile" in trace["candidate_arms"]["agent_1"]
    assert trace["candidate_arms"]["agent_1"]["alpha"] == 2.0
    assert trace["candidate_arms"]["agent_1"]["beta"] == 1.0


def test_all_frozen_agents_error():
    """Verifies that when all agents are frozen, coordinator raises ValueError."""
    agents = ["agent_x"]
    domain = "synthesis"
    coordinator = BayesUCBCoordinator(agent_ids=agents, domains=[domain])
    coordinator.update_evidence("agent_x", domain, success=0, confidence=0.95)

    with pytest.raises(ValueError, match="No eligible non-frozen agents available"):
        coordinator.route(domain=domain, total_system_steps=5)
