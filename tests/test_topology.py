"""
Unit tests for DynamicTopologyEngine and TaskNode.

Verifies:
1. DAG construction and acyclicity validation in O(|V| + |E|) using Kahn's algorithm.
2. Detection and exception raising on directed dependency cycles.
3. Proper handling and error reporting when dependent tasks reference non-existent prerequisites.
4. Partitioning of DAG into concurrent parallel execution stages.
5. Critical-path theoretical latency computation.
"""

import pytest
from guide_mas.core.topology import AdaptiveTopologyScheduler, DynamicTopologyEngine, TaskNode


def test_acyclic_topological_sort():
    """Verifies that a valid DAG resolves into a proper linear topological order."""
    engine = DynamicTopologyEngine()
    engine.add_node(TaskNode(task_id="A", domain="synthesis", description="Step A"))
    engine.add_node(TaskNode(task_id="B", domain="synthesis", description="Step B", dependencies=["A"]))
    engine.add_node(TaskNode(task_id="C", domain="planning", description="Step C", dependencies=["A"]))
    engine.add_node(TaskNode(task_id="D", domain="reconciliation", description="Step D", dependencies=["B", "C"]))

    order = engine.validate_acyclic()
    assert len(order) == 4
    assert order.index("A") < order.index("B")
    assert order.index("A") < order.index("C")
    assert order.index("B") < order.index("D")
    assert order.index("C") < order.index("D")


def test_cycle_detection():
    """Verifies that a circular dependency graph is detected and rejected."""
    engine = DynamicTopologyEngine()
    engine.add_node(TaskNode(task_id="T1", domain="synthesis", description="T1", dependencies=["T3"]))
    engine.add_node(TaskNode(task_id="T2", domain="synthesis", description="T2", dependencies=["T1"]))
    engine.add_node(TaskNode(task_id="T3", domain="synthesis", description="T3", dependencies=["T2"]))

    with pytest.raises(ValueError, match="Cycle detected in task DAG"):
        engine.validate_acyclic()


def test_missing_prerequisite_detection():
    """Verifies that referencing a non-existent task ID raises KeyError."""
    engine = DynamicTopologyEngine()
    engine.add_node(TaskNode(task_id="T1", domain="synthesis", description="T1", dependencies=["GHOST_TASK"]))

    with pytest.raises(KeyError, match="Prerequisite task 'GHOST_TASK' referenced by 'T1' does not exist"):
        engine.validate_acyclic()


def test_parallel_execution_stage_partitioning():
    """Verifies that independent tasks are grouped into concurrent parallel levels."""
    engine = DynamicTopologyEngine()
    # Level 1: T1, T2, T3 (no dependencies)
    engine.add_node(TaskNode(task_id="T1", domain="synthesis", description="T1"))
    engine.add_node(TaskNode(task_id="T2", domain="synthesis", description="T2"))
    engine.add_node(TaskNode(task_id="T3", domain="synthesis", description="T3"))
    # Level 2: T4 (depends on T1, T2, T3)
    engine.add_node(TaskNode(task_id="T4", domain="reconciliation", description="T4", dependencies=["T1", "T2", "T3"]))
    # Level 3: T5, T6 (depend on T4)
    engine.add_node(TaskNode(task_id="T5", domain="planning", description="T5", dependencies=["T4"]))
    engine.add_node(TaskNode(task_id="T6", domain="planning", description="T6", dependencies=["T4"]))

    stages = engine.get_parallel_execution_stages()
    assert len(stages) == 3

    stage_1_ids = {n.task_id for n in stages[0]}
    assert stage_1_ids == {"T1", "T2", "T3"}

    stage_2_ids = {n.task_id for n in stages[1]}
    assert stage_2_ids == {"T4"}

    stage_3_ids = {n.task_id for n in stages[2]}
    assert stage_3_ids == {"T5", "T6"}


def test_critical_path_latency_speedup():
    """Verifies theoretical latency computation matching Section 2.5."""
    engine = DynamicTopologyEngine()
    # 6 nodes each with 2.4s latency
    engine.add_node(TaskNode(task_id="T1", domain="synthesis", description="T1", estimated_latency=2.4))
    engine.add_node(TaskNode(task_id="T2", domain="synthesis", description="T2", estimated_latency=2.4))
    engine.add_node(TaskNode(task_id="T3", domain="synthesis", description="T3", estimated_latency=2.4))
    engine.add_node(TaskNode(task_id="T4", domain="reconciliation", description="T4", dependencies=["T1", "T2", "T3"], estimated_latency=2.4))
    engine.add_node(TaskNode(task_id="T5", domain="planning", description="T5", dependencies=["T4"], estimated_latency=2.4))
    engine.add_node(TaskNode(task_id="T6", domain="planning", description="T6", dependencies=["T4"], estimated_latency=2.4))

    latency_report = engine.compute_critical_path_latency()
    # Sequential: 6 * 2.4 = 14.4s
    assert latency_report["sequential_latency_seconds"] == 14.4
    # Parallel: 3 stages * 2.4s = 7.2s (50.0% speedup)
    assert latency_report["guide_latency_seconds"] == 7.2
    assert latency_report["latency_reduction_pct"] == 50.0


def test_adaptive_topology_scheduler_coalesce_small_workflow():
    """Verifies that workflows with <= 4 subtasks coalesce into exactly 2 execution stages."""
    subtasks = [
        "Query vendor database for SLA terms",
        "Extract delivery timelines and warranty constraints",
        "Cross-reference compliance certification",
        "Synthesize final evaluation JSON report"
    ]
    scheduler = AdaptiveTopologyScheduler.from_subtasks(subtasks, task_id="T01")
    stages = scheduler.get_coalesced_stages()

    # 4 subtasks -> 2 coalesced stages
    assert len(stages) == 2
    stage_1_nodes = stages[0]
    stage_2_nodes = stages[1]
    assert len(stage_1_nodes) == 1
    assert len(stage_2_nodes) == 1

    # Check that descriptions combine subtasks
    assert "Query vendor database" in stage_1_nodes[0].description
    assert "Extract delivery timelines" in stage_1_nodes[0].description
    assert "Cross-reference compliance" in stage_2_nodes[0].description
    assert "Synthesize final evaluation" in stage_2_nodes[0].description

    # Check stage dependencies
    assert stage_1_nodes[0].dependencies == []
    assert stage_2_nodes[0].dependencies == ["stage_1"]


def test_adaptive_topology_scheduler_deep_multihop_workflow():
    """Verifies that deep multi-hop workflows (e.g. 8 subtasks) coalesce into 4 stages."""
    subtasks = [f"Step {i}: execute action {i}" for i in range(1, 9)]
    scheduler = AdaptiveTopologyScheduler.from_subtasks(subtasks, task_id="GAIA01")
    stages = scheduler.get_coalesced_stages()

    # 8 subtasks -> 4 coalesced stages
    assert len(stages) == 4
    for stage in stages:
        assert len(stage) == 1

    # 6 subtasks -> 3 coalesced stages
    subtasks_6 = [f"Step {i}: execute action {i}" for i in range(1, 7)]
    scheduler_6 = AdaptiveTopologyScheduler.from_subtasks(subtasks_6, task_id="GAIA02")
    stages_6 = scheduler_6.get_coalesced_stages()
    assert len(stages_6) == 3


def test_adaptive_topology_scheduler_single_or_empty():
    """Verifies edge cases for empty or single subtask DAGs."""
    empty_scheduler = AdaptiveTopologyScheduler()
    assert empty_scheduler.get_coalesced_stages() == []

    single_scheduler = AdaptiveTopologyScheduler.from_subtasks(["Single atomic task"])
    single_stages = single_scheduler.get_coalesced_stages()
    assert len(single_stages) == 1
    assert len(single_stages[0]) == 1

