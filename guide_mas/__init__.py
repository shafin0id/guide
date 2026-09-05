"""
GUIDE: Policy-Aware Orchestration Framework for Enterprise LLM Multi-Agent Workflows.

A deterministic, policy-aware orchestration framework engineered for multi-agent LLM
systems in regulated enterprise environments, implementing:
1. Bayes-UCB Dynamic Routing
2. Cryptographically Signed Intent Handoffs
3. CAMCO Pre-Execution Convex Action Projection
4. Hash-Linked Tamper-Evident Trace Ledger
"""

from guide_mas.config import (
    ComplexityTier,
    GUIDEConfig,
    SensitivityLevel,
    TaskDomain,
    get_config,
    set_config,
)
from guide_mas.core.coordinator import BayesUCBCoordinator
from guide_mas.core.handoff import CryptographicHandoffManager, IntentPackage
from guide_mas.core.policy_gate import ActionRecord, CAMCOPolicyGate
from guide_mas.core.topology import DynamicTopologyEngine, TaskNode
from guide_mas.core.trace_ledger import HashLinkedTraceLedger
from guide_mas.storage.content_store import ContentAddressableStore

__version__ = "2.4.0"
__author__ = "Shafin Ahmad"

__all__ = [
    "__version__",
    "GUIDEConfig",
    "get_config",
    "set_config",
    "SensitivityLevel",
    "TaskDomain",
    "ComplexityTier",
    "BayesUCBCoordinator",
    "CryptographicHandoffManager",
    "IntentPackage",
    "CAMCOPolicyGate",
    "ActionRecord",
    "HashLinkedTraceLedger",
    "DynamicTopologyEngine",
    "TaskNode",
    "ContentAddressableStore",
]
