"""
GUIDE Modular Prompting Engine Package.
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
    format_task_prompt,
    get_static_prefix_for_domain,
)

__all__ = [
    "PromptBuilder",
    "COORDINATOR_DECOMPOSER_PROMPT",
    "SYNTHESIS_SPECIALIST_PROMPT",
    "RECONCILIATION_SPECIALIST_PROMPT",
    "PLANNING_SPECIALIST_PROMPT",
    "ADVERSARIAL_INJECTION_PROMPT",
    "get_static_prefix_for_domain",
    "format_task_prompt",
]
