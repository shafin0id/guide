"""
Dynamic Critical-Path DAG Topology Engine.

Implements Kahn's algorithm for linear-time O(|V| + |E|) topological scheduling,
dependency cycle detection, and parallel execution stage partitioning.
"""

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class TaskNode:
    """Represents an atomic subtask node in the workflow dependency DAG."""
    task_id: str
    domain: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    estimated_latency: float = 2.4  # Default benchmark baseline node execution time in seconds
    metadata: Dict[str, Any] = field(default_factory=dict)


class DynamicTopologyEngine:
    """
    Constructs, validates, and partitions task dependency DAGs into concurrent execution stages.
    """

    def __init__(self):
        self.nodes: Dict[str, TaskNode] = {}
        self.edges: Dict[str, Set[str]] = defaultdict(set)  # u -> set of v where u precedes v
        self.in_degree: Dict[str, int] = defaultdict(int)

    def add_node(self, node: TaskNode) -> None:
        """Adds a task node to the graph and registers its dependencies."""
        self.nodes[node.task_id] = node
        if node.task_id not in self.in_degree:
            self.in_degree[node.task_id] = 0

        for dep_id in node.dependencies:
            self.edges[dep_id].add(node.task_id)
            self.in_degree[node.task_id] += 1

    def add_dependency(self, prerequisite_task_id: str, dependent_task_id: str) -> None:
        """Explicitly registers a directed causal edge: prerequisite -> dependent."""
        if dependent_task_id not in self.nodes:
            raise KeyError(f"Dependent task '{dependent_task_id}' not found in graph")
        if prerequisite_task_id not in self.nodes:
            raise KeyError(f"Prerequisite task '{prerequisite_task_id}' not found in graph")

        if dependent_task_id not in self.edges[prerequisite_task_id]:
            self.edges[prerequisite_task_id].add(dependent_task_id)
            self.in_degree[dependent_task_id] += 1
            if prerequisite_task_id not in self.nodes[dependent_task_id].dependencies:
                self.nodes[dependent_task_id].dependencies.append(prerequisite_task_id)

    def validate_acyclic(self) -> List[str]:
        """
        Executes Kahn's algorithm in O(|V| + |E|) time to verify acyclicity.

        Returns:
            Linear topological ordering of task IDs.

        Raises:
            KeyError: If a prerequisite node does not exist in graph.
            ValueError: If a directed dependency cycle is detected.
        """
        # Validate that all declared dependencies exist in nodes
        for node_id, node in self.nodes.items():
            for dep in node.dependencies:
                if dep not in self.nodes:
                    raise KeyError(
                        f"Prerequisite task '{dep}' referenced by '{node_id}' does not exist in graph"
                    )

        in_degrees = {k: self.in_degree[k] for k in self.nodes}
        queue = deque([node_id for node_id, deg in in_degrees.items() if deg == 0])
        topological_order: List[str] = []

        while queue:
            curr = queue.popleft()
            topological_order.append(curr)

            for neighbor in self.edges[curr]:
                in_degrees[neighbor] -= 1
                if in_degrees[neighbor] == 0:
                    queue.append(neighbor)

        if len(topological_order) != len(self.nodes):
            unresolved = [node_id for node_id, deg in in_degrees.items() if deg > 0]
            raise ValueError(
                f"Cycle detected in task DAG: Unresolved cyclic dependencies among {unresolved}"
            )

        return topological_order

    def get_parallel_execution_stages(self) -> List[List[TaskNode]]:
        """
        Partitions the DAG into discrete parallel execution levels (stages).
        All tasks in stage k can execute concurrently because all prerequisites exist in stages < k.

        Returns:
            List of stages, each containing a list of TaskNodes.
        """
        self.validate_acyclic()

        in_degrees = {k: self.in_degree[k] for k in self.nodes}
        current_stage_ids = [node_id for node_id, deg in in_degrees.items() if deg == 0]
        stages: List[List[TaskNode]] = []

        while current_stage_ids:
            stage_nodes = [self.nodes[tid] for tid in current_stage_ids]
            stages.append(stage_nodes)

            next_stage_ids: List[str] = []
            for tid in current_stage_ids:
                for neighbor in self.edges[tid]:
                    in_degrees[neighbor] -= 1
                    if in_degrees[neighbor] == 0:
                        next_stage_ids.append(neighbor)

            current_stage_ids = next_stage_ids

        return stages

    def compute_critical_path_latency(self) -> Dict[str, float]:
        """
        Calculates theoretical latency comparison between sequential execution and GUIDE parallel scheduling.

        Returns:
            Dictionary containing:
                - sequential_latency: Sum of all node latencies.
                - guide_latency: Sum of maximum latencies across partitioned stages.
                - latency_reduction_pct: Percentage speedup achieved.
        """
        stages = self.get_parallel_execution_stages()
        sequential_latency = sum(node.estimated_latency for node in self.nodes.values())

        guide_latency = sum(
            max((node.estimated_latency for node in stage), default=0.0)
            for stage in stages
        )

        if sequential_latency > 0:
            reduction_pct = ((sequential_latency - guide_latency) / sequential_latency) * 100.0
        else:
            reduction_pct = 0.0

        return {
            "sequential_latency_seconds": round(sequential_latency, 2),
            "guide_latency_seconds": round(guide_latency, 2),
            "latency_reduction_pct": round(reduction_pct, 2),
            "total_nodes": len(self.nodes),
            "total_stages": len(stages),
        }


class AdaptiveTopologyScheduler(DynamicTopologyEngine):
    """
    Adaptive Topology Scheduler with dynamic stage coalescing.
    Coalesces fine-grained subtask nodes into optimal execution stages to minimize
    LLM invocation overhead while preserving causal data dependencies.
    """

    def get_coalesced_stages(self, target_stages: Optional[int] = None) -> List[List[TaskNode]]:
        """
        Partitions the DAG into adaptive coalesced execution stages:
        - <= 4 subtasks: Coalesced into 2 stages (Exploration/Extraction -> Synthesis/Validation).
        - 5-7 subtasks: Coalesced into 3 stages.
        - >= 8 subtasks: Coalesced into 4 stages.

        Returns:
            List of stages, each containing coalesced TaskNode(s).
        """
        topological_order = self.validate_acyclic()
        n_nodes = len(topological_order)

        if n_nodes == 0:
            return []
        if n_nodes == 1:
            return [[self.nodes[topological_order[0]]]]

        if target_stages is None:
            if n_nodes <= 4:
                n_stages = 2
            elif n_nodes <= 7:
                n_stages = 3
            else:
                n_stages = 4
        else:
            n_stages = max(1, min(target_stages, n_nodes))

        coalesced_stages: List[List[TaskNode]] = []
        for stage_idx in range(n_stages):
            start = (stage_idx * n_nodes) // n_stages
            end = ((stage_idx + 1) * n_nodes) // n_stages
            chunk_task_ids = topological_order[start:end]
            chunk_nodes = [self.nodes[tid] for tid in chunk_task_ids]

            if not chunk_nodes:
                continue

            # Identify dominant domain or terminal stage persona
            domain = chunk_nodes[-1].domain
            combined_desc = "\n".join(
                f"- [{node.task_id}] {node.description}" for node in chunk_nodes
            )
            deps = [f"stage_{stage_idx}"] if stage_idx > 0 else []

            coalesced_node = TaskNode(
                task_id=f"stage_{stage_idx + 1}",
                domain=domain,
                description=combined_desc,
                dependencies=deps,
                estimated_latency=sum(n.estimated_latency for n in chunk_nodes),
                metadata={
                    "original_task_ids": chunk_task_ids,
                    "original_nodes": chunk_nodes,
                    "stage_index": stage_idx,
                }
            )
            coalesced_stages.append([coalesced_node])

        return coalesced_stages

    def schedule(self, target_stages: Optional[int] = None) -> List[List[TaskNode]]:
        """Convenience alias for get_coalesced_stages."""
        return self.get_coalesced_stages(target_stages=target_stages)

    def get_parallel_execution_stages(self, coalesce: bool = False) -> List[List[TaskNode]]:
        """
        Overrides DynamicTopologyEngine method to support optional coalesced scheduling.
        """
        if coalesce:
            return self.get_coalesced_stages()
        return super().get_parallel_execution_stages()

    @classmethod
    def from_subtasks(
        cls,
        subtasks: List[str],
        task_id: str = "task",
        default_domain: str = "constrained_synthesis"
    ) -> "AdaptiveTopologyScheduler":
        """Factory method to construct an AdaptiveTopologyScheduler directly from subtask strings."""
        scheduler = cls()
        for idx, st in enumerate(subtasks):
            scheduler.add_node(
                TaskNode(
                    task_id=f"{task_id}_step{idx + 1}",
                    domain=default_domain,
                    description=st,
                    dependencies=[f"{task_id}_step{idx}"] if idx > 0 else []
                )
            )
        return scheduler

