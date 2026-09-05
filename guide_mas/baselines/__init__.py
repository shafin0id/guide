"""
GUIDE Baselines Package.

Provides Condition B1 (Conversational Sequential) and Condition B2 (Static Graph)
experimental baseline implementations for comparative evaluation.
"""

from guide_mas.baselines.b1_sequential import (
    SequentialBaselineAgent,
    SequentialWorkflowOrchestrator,
)
from guide_mas.baselines.b2_static_graph import (
    StaticGraphNode,
    StaticGraphOrchestrator,
    StaticGraphState,
)

__all__ = [
    "SequentialBaselineAgent",
    "SequentialWorkflowOrchestrator",
    "StaticGraphNode",
    "StaticGraphOrchestrator",
    "StaticGraphState",
]
