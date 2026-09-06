"""
Unit tests for the Modular Frontier-Level System Prompting Engine.

Verifies:
1. Static-Prefix Invariant Pinning (byte-identical invariant prefixes across invocations for KV caching).
2. Semantic XML Scaffolding (<system_role>, <enterprise_invariants>, <output_schema_spec>, <anti_injection_shield>, <execution_context>).
3. Dynamic Execution Context Suffix injection (S_0 immutability, input_refs pointers, subtask goal).
4. Persona coverage across all 5 frontier specialist roles.
"""

from guide_mas.prompts.base import PromptBuilder
from guide_mas.prompts.system_prompts import (
    ADVERSARIAL_INJECTION_PROMPT,
    COORDINATOR_DECOMPOSER_PROMPT,
    PLANNING_SPECIALIST_PROMPT,
    RECONCILIATION_SPECIALIST_PROMPT,
    SYNTHESIS_SPECIALIST_PROMPT,
)
from guide_mas.prompts.templates import (
    clean_prompt_constraints,
    format_chat_prompt,
    format_task_prompt,
    get_static_prefix_for_domain,
)


def test_static_prefix_byte_invariance():
    """Verifies that static prefixes are 100% byte-deterministic across multiple calls."""
    prefix1 = get_static_prefix_for_domain("constrained_synthesis")
    prefix2 = get_static_prefix_for_domain("constrained_synthesis")

    assert prefix1 == prefix2
    assert prefix1.encode("utf-8") == prefix2.encode("utf-8")
    assert "<system_role>" in prefix1
    assert "<enterprise_invariants>" in prefix1
    assert "<output_schema_spec>" in prefix1
    assert "<anti_injection_shield>" in prefix1


def test_all_five_personas_defined():
    """Verifies all required frontier personas are non-empty and properly tagged."""
    personas = [
        COORDINATOR_DECOMPOSER_PROMPT,
        SYNTHESIS_SPECIALIST_PROMPT,
        RECONCILIATION_SPECIALIST_PROMPT,
        PLANNING_SPECIALIST_PROMPT,
        ADVERSARIAL_INJECTION_PROMPT,
    ]
    for p in personas:
        assert isinstance(p, str)
        assert len(p) > 100
        assert "<system_role>" in p
        assert "<enterprise_invariants>" in p
        assert "<output_schema_spec>" in p
        assert "<anti_injection_shield>" in p


def test_dynamic_execution_context_assembly():
    """Verifies that dynamic context properly encapsulates S_0, constraints, and CAS pointers."""
    obj_s0 = "Extract SLA guarantees for Apex Cloud Systems"
    goal = "Query procurement database for vendor V-001"
    constraints = ["Suppress unit pricing", "Bound query limit to 50"]
    refs = ["sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069"]

    prompt = format_task_prompt(
        domain="constrained_synthesis",
        objective_s0=obj_s0,
        subtask_goal=goal,
        mandatory_constraints=constraints,
        input_refs=refs
    )

    assert obj_s0 in prompt
    assert goal in prompt
    assert "Suppress unit pricing" in prompt
    assert refs[0] in prompt
    assert "<execution_context>" in prompt
    assert "</execution_context>" in prompt


def test_clean_prompt_constraints_filters_crypto_and_camco():
    """Verifies that synthetic crypto directives and redundant CAMCO text are filtered."""
    raw_constraints = [
        "Suppress unit pricing",
        "Log to hash-linked trace ledger",
        "Verify Ed25519 signature before execution",
        "Bound query limit strictly to 50",
        "CAMCO pre-execution projection must validate arguments",
        "Compute SHA-256 state hash for verification",
        "Ensure high uptime guarantee",
    ]

    cleaned = clean_prompt_constraints(raw_constraints)

    assert "Suppress unit pricing" in cleaned
    assert "Bound query limit strictly to 50" in cleaned
    assert "Ensure high uptime guarantee" in cleaned

    # Synthetic crypto filtered
    assert not any("trace ledger" in c.lower() for c in cleaned)
    assert not any("ed25519" in c.lower() for c in cleaned)
    assert not any("sha-256" in c.lower() for c in cleaned)

    # Redundant CAMCO filtered
    assert not any("camco pre-execution" in c.lower() for c in cleaned)


def test_format_chat_prompt_byte_identical_system_role():
    """Verifies that format_chat_prompt produces byte-invariant system prompts for KV cache reuse."""
    messages1 = format_chat_prompt(
        domain="constrained_synthesis",
        objective_s0="Task 1 Objective",
        subtask_goal="Task 1 Subtask",
        mandatory_constraints=["Constraint 1", "Log to hash-linked trace ledger"],
        input_refs=["sha256:1111"],
    )
    messages2 = format_chat_prompt(
        domain="constrained_synthesis",
        objective_s0="Task 2 Objective entirely different",
        subtask_goal="Task 2 Subtask entirely different",
        mandatory_constraints=["Constraint 2"],
        input_refs=["sha256:2222"],
    )

    # System role must be 100% byte identical across completely different tasks in the same domain
    assert messages1[0]["role"] == "system"
    assert messages2[0]["role"] == "system"
    assert messages1[0]["content"] == messages2[0]["content"]
    assert messages1[0]["content"].encode("utf-8") == messages2[0]["content"].encode("utf-8")

    # Dynamic parts in user prompt
    assert "Task 1 Objective" in messages1[1]["content"]
    assert "Task 2 Objective entirely different" in messages2[1]["content"]
    # Filtered crypto not in prompt
    assert "trace ledger" not in messages1[1]["content"]

