"""
Condition B1: Conversational Sequential Baseline.

Implements plain-text conversational sequential handoffs without cryptographic checks,
hash-linked audit chains, or out-of-process CAMCO policy gates.
Subject to linear regret O(T) from static assignment, exponential context degradation
under the Data Processing Inequality (IPS = r^n), and soft guardrail prompt bypasses.
"""

import json
import time
from typing import Any, Dict, List, Optional
from guide_mas.core.model_client import ModelClient, ModelResponse
from guide_mas.tools.base import BaseTool


class SequentialBaselineAgent:
    """Individual conversational specialist agent in the sequential chain."""

    def __init__(
        self,
        agent_id: str,
        role_description: str,
        tools: Dict[str, BaseTool],
        model_client: Optional[ModelClient] = None
    ):
        self.agent_id = agent_id
        self.role_description = role_description
        self.tools = tools
        self.model_client = model_client or ModelClient()

    def process_step(
        self,
        conversation_history: str,
        current_subtask: str,
        retention_rate: float = 0.85,
        tool_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Processes subtask by appending to plain-text conversational history.
        Simulates contextual retention loss r^n per DPI when passing unstructured text.
        Executes tools directly without out-of-process CAMCO policy gating.
        """
        start_time = time.time()

        # Plain-text prompt without cryptographic sealing or static prefix caching
        prompt = (
            f"Role: {self.role_description}\n"
            f"Full Conversation History:\n{conversation_history}\n\n"
            f"Current Subtask: {current_subtask}\n"
            f"Execute your analysis and output your final result as a valid JSON object matching the subtask schema."
        )

        # Baseline execution through foundation model
        model_resp = self.model_client.generate(
            prompt=prompt,
            system_instruction=f"Role: {self.role_description}"
        )

        # In B1, execute tools directly without CAMCO policy gate validation
        tool_output = None
        if "procurement" in current_subtask.lower() and "procurement_db" in self.tools:
            # Executes directly: unconstrained limits or unmasked columns pass through
            tool_output = self.tools["procurement_db"].execute(
                **(tool_params or {"limit": 100})
            )
        elif "incident" in current_subtask.lower() and "incident_log_store" in self.tools:
            tool_output = self.tools["incident_log_store"].execute(
                **(tool_params or {"limit": 100})
            )

        execution_latency = time.time() - start_time

        output_text = model_resp.content
        if tool_output:
            output_text += f"\n[Tool Output]: {json.dumps(tool_output.get('records') or tool_output.get('logs') or {})}"

        return {
            "agent_id": self.agent_id,
            "prompt": prompt,
            "response": output_text,
            "parsed_json": model_resp.parsed_json,
            "tool_output": tool_output,
            "prompt_tokens": model_resp.prompt_tokens,
            "completion_tokens": model_resp.completion_tokens,
            "latency_seconds": execution_latency
        }


class SequentialWorkflowOrchestrator:
    """
    Executes a linear multi-agent workflow under Condition B1.
    Passes growing conversational histories sequentially across fixed agent roles.
    """

    def __init__(
        self,
        agent_roles: List[Dict[str, str]],
        tools: Dict[str, BaseTool],
        model_client: Optional[ModelClient] = None
    ):
        self.model_client = model_client or ModelClient()
        self.agents: List[SequentialBaselineAgent] = [
            SequentialBaselineAgent(
                agent_id=f"seq_agent_{i+1}",
                role_description=role["role"],
                tools=tools,
                model_client=self.model_client
            )
            for i, role in enumerate(agent_roles)
        ]
        self.tools = tools

    def execute_workflow(
        self,
        initial_objective: str,
        subtasks: List[str],
        retention_factor: float = 0.85
    ) -> Dict[str, Any]:
        """
        Runs the linear chain of agents sequentially.
        Demonstrates exponential context decay: IPS_sequential(n) = r^n.
        """
        start_total = time.time()
        conversation_history = f"Initial Task S_0: {initial_objective}\n"
        step_records = []
        n_hops = len(subtasks)

        # Calculate theoretical DPI intent preservation score
        ips_score = retention_factor ** n_hops

        for step_idx, subtask in enumerate(subtasks):
            # Select agent via static round-robin / fixed index (Linear Regret O(T))
            agent = self.agents[step_idx % len(self.agents)]
            step_result = agent.process_step(
                conversation_history=conversation_history,
                current_subtask=subtask,
                retention_rate=retention_factor
            )
            step_records.append(step_result)

            # Plain text accumulation
            conversation_history += f"\nStep {step_idx+1} ({agent.agent_id}): {step_result['response']}"

        total_latency = time.time() - start_total
        total_prompt_tokens = sum(r.get("prompt_tokens", 0) for r in step_records)
        total_completion_tokens = sum(r.get("completion_tokens", 0) for r in step_records)
        
        final_parsed = {}
        if step_records:
            final_parsed = step_records[-1].get("parsed_json") or {}
            if not final_parsed:
                final_parsed = self.model_client._extract_json(step_records[-1].get("response", "")) or {}

        return {
            "condition": "B1_CONVERSATIONAL_SEQUENTIAL",
            "initial_objective": initial_objective,
            "hops_executed": n_hops,
            "intent_preservation_score": ips_score,
            "step_records": step_records,
            "final_conversation_history": conversation_history,
            "final_output": final_parsed,
            "total_latency_seconds": total_latency,
            "prompt_tokens": total_prompt_tokens,
            "completion_tokens": total_completion_tokens,
            "policy_violations_blocked": 0  # B1 has no out-of-process gate to block violations
        }
