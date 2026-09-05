"""
Prompt Templates and XML Scaffolding Utilities.

Provides high-level prompt assembly methods combining static prefixes and dynamic contexts
for operational specialists and coordinator agents.
"""

from typing import Any, Dict, List, Optional
from guide_mas.prompts.base import PromptBuilder
from guide_mas.prompts.system_prompts import (
    COORDINATOR_DECOMPOSER_PROMPT,
    SYNTHESIS_SPECIALIST_PROMPT,
    RECONCILIATION_SPECIALIST_PROMPT,
    PLANNING_SPECIALIST_PROMPT,
    ADVERSARIAL_INJECTION_PROMPT,
)


def get_static_prefix_for_domain(domain: str) -> str:
    """Returns the invariant static prefix corresponding to a task domain or persona."""
    normalized = domain.lower().strip()
    if normalized in ("constrained_synthesis", "synthesis"):
        return SYNTHESIS_SPECIALIST_PROMPT
    elif normalized in ("evidence_reconciliation", "reconciliation"):
        return RECONCILIATION_SPECIALIST_PROMPT
    elif normalized in ("policy_planning", "planning"):
        return PLANNING_SPECIALIST_PROMPT
    elif normalized in ("coordinator", "decomposer"):
        return COORDINATOR_DECOMPOSER_PROMPT
    elif normalized in ("adversarial", "red_team"):
        return ADVERSARIAL_INJECTION_PROMPT
    else:
        # Default fallback to coordinator persona
        return COORDINATOR_DECOMPOSER_PROMPT


def format_task_prompt(
    domain: str,
    objective_s0: str,
    subtask_goal: str,
    mandatory_constraints: List[str],
    input_refs: List[str],
    resolved_data: Optional[Dict[str, str]] = None,
    runtime_findings: Optional[Dict[str, Any]] = None
) -> str:
    """
    Constructs a complete, byte-cached prompt for an operational agent.
    Combines domain-specific invariant static prefix with dynamic runtime execution context.
    """
    static_prefix = get_static_prefix_for_domain(domain)
    dynamic_context = PromptBuilder.assemble_dynamic_context(
        objective_s0=objective_s0,
        subtask_goal=subtask_goal,
        mandatory_constraints=mandatory_constraints,
        input_refs=input_refs,
        resolved_data=resolved_data,
        runtime_findings=runtime_findings
    )
    return PromptBuilder.build_complete_prompt(static_prefix, dynamic_context)
