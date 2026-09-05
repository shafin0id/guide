"""
Modular Frontier-Level Prompting Engine Base Module.

Implements Semantic XML Scaffolding and Static-Prefix Invariant Pinning for KV-cache optimization.
Partitions prompts into 100% deterministic invariant prefixes (system_role, enterprise_invariants,
output_schema_spec, anti_injection_shield) and dynamic trailing execution_context.
"""

from typing import Any, Dict, List, Optional
import json


class PromptBuilder:
    """
    Constructs cache-optimized enterprise prompts partitioned into invariant static prefixes
    and dynamic execution context suffixes.
    """

    @staticmethod
    def wrap_xml(tag: str, content: str) -> str:
        """Encloses content within clean XML tags."""
        stripped = content.strip()
        return f"<{tag}>\n{stripped}\n</{tag}>"

    @classmethod
    def assemble_static_prefix(
        cls,
        system_role: str,
        enterprise_invariants: str,
        output_schema_spec: str,
        anti_injection_shield: str
    ) -> str:
        """
        Assembles the byte-invariant static prefix.
        Guarantees identical byte output across all invocations for provider KV-cache hits.
        """
        components = [
            cls.wrap_xml("system_role", system_role),
            cls.wrap_xml("enterprise_invariants", enterprise_invariants),
            cls.wrap_xml("output_schema_spec", output_schema_spec),
            cls.wrap_xml("anti_injection_shield", anti_injection_shield),
        ]
        return "\n\n".join(components)

    @classmethod
    def assemble_dynamic_context(
        cls,
        objective_s0: str,
        subtask_goal: str,
        mandatory_constraints: List[str],
        input_refs: List[str],
        resolved_data: Optional[Dict[str, str]] = None,
        runtime_findings: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Assembles the dynamic execution context suffix.
        Injects immutable root intent S_0, subtask instructions, and CAS pointers.
        """
        constraints_formatted = "\n".join(f"- {c}" for c in mandatory_constraints) or "- None"
        refs_formatted = "\n".join(f"- {r}" for r in input_refs) or "- None"

        data_sections = []
        if resolved_data:
            for ref, content in sorted(resolved_data.items()):
                data_sections.append(f"<document_ref id='{ref}'>\n{content}\n</document_ref>")
        data_block = "\n".join(data_sections) if data_sections else "No external retrieved documents."

        findings_block = json.dumps(runtime_findings or {}, sort_keys=True, indent=2)

        context_body = (
            f"<immutable_root_objective_s0>\n{objective_s0.strip()}\n</immutable_root_objective_s0>\n\n"
            f"<subtask_goal>\n{subtask_goal.strip()}\n</subtask_goal>\n\n"
            f"<active_mandatory_constraints>\n{constraints_formatted}\n</active_mandatory_constraints>\n\n"
            f"<content_pointers_input_refs>\n{refs_formatted}\n</content_pointers_input_refs>\n\n"
            f"<retrieved_data>\n{data_block}\n</retrieved_data>\n\n"
            f"<transient_findings>\n{findings_block}\n</transient_findings>"
        )

        return cls.wrap_xml("execution_context", context_body)

    @classmethod
    def build_complete_prompt(
        cls,
        static_prefix: str,
        dynamic_context: str
    ) -> str:
        """Combines the invariant static prefix with the dynamic context suffix."""
        return f"{static_prefix.strip()}\n\n{dynamic_context.strip()}"
