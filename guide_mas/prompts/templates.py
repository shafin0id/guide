"""
Prompt Templates and XML Scaffolding Utilities.

Provides high-level prompt assembly methods combining static prefixes and dynamic contexts
for operational specialists and coordinator agents.
"""

import json
import re
from typing import Any, Dict, List, Optional
from guide_mas.prompts.base import PromptBuilder
from guide_mas.prompts.system_prompts import (
    COORDINATOR_DECOMPOSER_PROMPT,
    SYNTHESIS_SPECIALIST_PROMPT,
    RECONCILIATION_SPECIALIST_PROMPT,
    PLANNING_SPECIALIST_PROMPT,
    ADVERSARIAL_INJECTION_PROMPT,
)

SYNTHETIC_CRYPTO_PATTERNS = [
    re.compile(r"log\s+to\s+hash-linked\s+trace\s+ledger", re.IGNORECASE),
    re.compile(r"verify\s+ed25519\s+signature", re.IGNORECASE),
    re.compile(r"compute\s+sha-?256\s+state\s+hash", re.IGNORECASE),
    re.compile(r"sign\s+handoff\s+with\s+ed25519", re.IGNORECASE),
    re.compile(r"jcs\s+canonicalization", re.IGNORECASE),
    re.compile(r"hash-chain\s+verification", re.IGNORECASE),
    re.compile(r"tamper-evident\s+ledger", re.IGNORECASE),
    re.compile(r"cryptographic\s+trace", re.IGNORECASE),
]

REDUNDANT_CAMCO_PATTERNS = [
    re.compile(r"camco\s+pre-execution\s+projection", re.IGNORECASE),
    re.compile(r"geometric\s+projection\s+gate", re.IGNORECASE),
    re.compile(r"enforce\s+query\s+limit\s+strictly\s+via\s+policy", re.IGNORECASE),
]


def clean_prompt_constraints(constraints: List[str]) -> List[str]:
    """
    De-noises task constraints for LLM prompts:
    - Filters synthetic cryptographic instructions that cause the model to emit fake hashes/signatures.
    - Strips redundant CAMCO compliance directives that are already enforced deterministically out-of-process.
    """
    cleaned: List[str] = []
    for c in constraints:
        c_str = c.strip()
        if not c_str:
            continue
        if any(p.search(c_str) for p in SYNTHETIC_CRYPTO_PATTERNS):
            continue
        if any(p.search(c_str) for p in REDUNDANT_CAMCO_PATTERNS):
            continue
        cleaned.append(c_str)
    return cleaned


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
    filtered_constraints = clean_prompt_constraints(mandatory_constraints)
    dynamic_context = PromptBuilder.assemble_dynamic_context(
        objective_s0=objective_s0,
        subtask_goal=subtask_goal,
        mandatory_constraints=filtered_constraints,
        input_refs=input_refs,
        resolved_data=resolved_data,
        runtime_findings=runtime_findings
    )
    return PromptBuilder.build_complete_prompt(static_prefix, dynamic_context)


def format_chat_prompt(
    domain: str,
    objective_s0: str,
    subtask_goal: str,
    mandatory_constraints: List[str],
    input_refs: List[str],
    context_findings: Optional[Dict[str, Any]] = None,
    prohibitions: Optional[List[str]] = None,
) -> List[Dict[str, str]]:
    """
    Formats byte-identical system prompt and concise user prompt for KV-cache friendly chat completions.
    """
    static_system_prefix = get_static_prefix_for_domain(domain)
    filtered_constraints = clean_prompt_constraints(mandatory_constraints)

    user_content_parts = [
        f"ROOT INTENT ANCHOR (S_0): {objective_s0}",
        f"Current Subtask: {subtask_goal}",
    ]
    if filtered_constraints:
        user_content_parts.append("MANDATORY CONSTRAINTS:\n" + "\n".join(f"- {c}" for c in filtered_constraints))
    if prohibitions:
        clean_prohibitions = clean_prompt_constraints(prohibitions)
        if clean_prohibitions:
            user_content_parts.append("PROHIBITIONS:\n" + "\n".join(f"- {p}" for p in clean_prohibitions))
    if input_refs:
        user_content_parts.append("Input References: " + ", ".join(input_refs))
    if context_findings:
        user_content_parts.append("Context Findings: " + json.dumps(context_findings, separators=(",", ":")))

    return [
        {"role": "system", "content": static_system_prefix},
        {"role": "user", "content": "\n\n".join(user_content_parts)},
    ]

