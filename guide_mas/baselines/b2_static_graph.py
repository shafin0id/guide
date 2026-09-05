"""
Condition B2: Static Graph Baseline.

Implements structured state graph orchestration (analogous to standard LangGraph / StateGraph),
passing typed Pydantic state dictionaries over predetermined static edges.
Lacks adaptive Bayesian routing (Bayes-UCB), out-of-process CAMCO Euclidean action projection,
and Ed25519 cryptographic state verification between hops.
"""

import time
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field
from guide_mas.core.model_client import ModelClient, ModelResponse
from guide_mas.tools.base import BaseTool


class StaticGraphState(BaseModel):
    """Structured shared state dictionary passing through static graph nodes."""
    run_id: str
    objective: str
    current_node: str = "start"
    subtasks_remaining: List[str] = Field(default_factory=list)
    findings: Dict[str, Any] = Field(default_factory=dict)
    tool_history: List[Dict[str, Any]] = Field(default_factory=list)
    iteration_count: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0


class StaticGraphNode:
    """Represents a discrete computational node in the static graph."""

    def __init__(
        self,
        node_name: str,
        domain: str,
        tools: Dict[str, BaseTool],
        model_client: Optional[ModelClient] = None
    ):
        self.node_name = node_name
        self.domain = domain
        self.tools = tools
        self.model_client = model_client or ModelClient()

    def execute(self, state: StaticGraphState) -> StaticGraphState:
        """
        Executes node logic directly modifying state.
        Executes tools directly without CAMCO policy gate validation.
        """
        state.current_node = self.node_name
        state.iteration_count += 1

        current_task = state.subtasks_remaining.pop(0) if state.subtasks_remaining else state.objective

        prompt = (
            f"Domain: {self.domain}\n"
            f"Current Node: {self.node_name}\n"
            f"Objective: {state.objective}\n"
            f"Task: {current_task}\n"
            f"Prior State Findings: {state.findings}"
        )

        model_resp = self.model_client.generate(
            prompt=prompt,
            system_instruction=f"Static Graph Node {self.node_name} for domain {self.domain}"
        )
        state.prompt_tokens += model_resp.prompt_tokens
        state.completion_tokens += model_resp.completion_tokens

        # Direct un-gated tool execution in B2 (no Euclidean bounding, no policy gate)
        tool_data = None
        if "procurement" in self.domain and "procurement_db" in self.tools:
            # Without CAMCO gate: limits are not clamped, confidential columns not screened
            tool_data = self.tools["procurement_db"].execute(limit=100)
            state.tool_history.append({"node": self.node_name, "tool": "procurement_db", "result": tool_data})
        elif "reconciliation" in self.domain and "incident_log_store" in self.tools:
            tool_data = self.tools["incident_log_store"].execute(limit=100)
            state.tool_history.append({"node": self.node_name, "tool": "incident_log_store", "result": tool_data})

        state.findings[self.node_name] = {
            "completed_task": current_task,
            "status": "COMPLETED",
            "parsed_output": model_resp.parsed_json or {},
            "raw_output": model_resp.content,
            "tool_data": tool_data,
            "timestamp": time.time()
        }

        return state


class StaticGraphOrchestrator:
    """
    Executes workflows over fixed, predefined graph edges without dynamic Bayesian routing
    or out-of-process policy projection.
    """

    def __init__(self, tools: Dict[str, BaseTool], model_client: Optional[ModelClient] = None):
        self.tools = tools
        self.model_client = model_client or ModelClient()
        self.nodes: Dict[str, StaticGraphNode] = {
            "synthesis_node": StaticGraphNode("synthesis_node", "constrained_synthesis", tools, self.model_client),
            "reconciliation_node": StaticGraphNode("reconciliation_node", "evidence_reconciliation", tools, self.model_client),
            "planning_node": StaticGraphNode("planning_node", "policy_planning", tools, self.model_client)
        }
        # Predefined static transition edges (No Bayesian adaptation)
        self.static_transitions = {
            "start": "synthesis_node",
            "synthesis_node": "reconciliation_node",
            "reconciliation_node": "planning_node",
            "planning_node": "end"
        }

    def execute_workflow(
        self,
        run_id: str,
        initial_objective: str,
        subtasks: List[str]
    ) -> Dict[str, Any]:
        """
        Executes the static graph pipeline from start to end.
        """
        start_time = time.time()
        state = StaticGraphState(
            run_id=run_id,
            objective=initial_objective,
            current_node="start",
            subtasks_remaining=list(subtasks)
        )

        trace: List[Dict[str, Any]] = []

        curr = self.static_transitions.get("start", "end")
        while curr != "end" and curr in self.nodes:
            node = self.nodes[curr]
            step_start = time.time()
            state = node.execute(state)
            step_latency = time.time() - step_start

            trace.append({
                "node": curr,
                "domain": node.domain,
                "latency_seconds": step_latency,
                "state_snapshot": state.model_dump()
            })

            curr = self.static_transitions.get(curr, "end")

        total_latency = time.time() - start_time
        final_findings = state.findings.get("planning_node", {}).get("parsed_output") or state.findings.get("synthesis_node", {}).get("parsed_output") or {}

        return {
            "condition": "B2_STATIC_GRAPH",
            "run_id": run_id,
            "final_state": state.model_dump(),
            "final_output": final_findings,
            "prompt_tokens": state.prompt_tokens,
            "completion_tokens": state.completion_tokens,
            "execution_trace": trace,
            "total_latency_seconds": total_latency,
            "policy_interceptions": 0,  # No policy gate in B2
            "cryptographic_verifications": 0  # No Ed25519 verification in B2
        }
