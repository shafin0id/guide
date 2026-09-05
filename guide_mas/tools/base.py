"""
Base Tool Interface Module.

Defines the abstract contract for enterprise tools, including explicit mapping
to the 5-element ActionRecord tuple required for CAMCO pre-execution gate validation.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from guide_mas.core.policy_gate import ActionRecord


class BaseTool(ABC):
    """Abstract base class for all sandboxed tools in the GUIDE ecosystem."""

    def __init__(self, name: str, description: str, resource_class: str):
        self.name = name
        self.description = description
        self.resource_class = resource_class

    @abstractmethod
    def create_action_record(
        self,
        operation: str,
        data_sensitivity: str = "INTERNAL",
        write_effect: bool = False
    ) -> ActionRecord:
        """Constructs a standardized 5-element ActionRecord for CAMCO validation."""
        pass

    @abstractmethod
    def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Executes tool logic under sandboxed enterprise conditions.

        Args:
            **kwargs: Validated runtime parameters.

        Returns:
            Dictionary containing execution outcome, status, and payload.
        """
        pass
