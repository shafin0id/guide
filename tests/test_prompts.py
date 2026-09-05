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
from guide_mas.prompts.templates import format_task_prompt, get_static_prefix_for_domain


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
