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
from guide_mas.core.topology import DynamicTopologyEngine, TaskNode


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
