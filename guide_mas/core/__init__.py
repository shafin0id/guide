"""
GUIDE Core Orchestration Package.

Exports the four foundational architectural controls:
1. BayesUCBCoordinator (Adaptive Bayesian MAB Routing)
2. CryptographicHandoffManager & IntentPackage (RFC 8785 / Ed25519 State Transfer)
3. CAMCOPolicyGate & ActionRecord (Pre-Execution Convex Action Projection)
4. HashLinkedTraceLedger (SHA-256 Tamper-Evident Backward Lineage)
5. DynamicTopologyEngine & TaskNode (O(|V| + |E|) Kahn DAG Scheduling)
"""

from guide_mas.core.coordinator import BayesUCBCoordinator
from guide_mas.core.handoff import CryptographicHandoffManager, IntentPackage
from guide_mas.core.policy_gate import ActionRecord, CAMCOPolicyGate
from guide_mas.core.topology import DynamicTopologyEngine, TaskNode
from guide_mas.core.trace_ledger import HashLinkedTraceLedger
from guide_mas.core.model_client import ModelClient, ModelResponse

__all__ = [
    "BayesUCBCoordinator",
    "CryptographicHandoffManager",
    "IntentPackage",
    "CAMCOPolicyGate",
    "ActionRecord",
    "HashLinkedTraceLedger",
    "DynamicTopologyEngine",
    "TaskNode",
    "ModelClient",
    "ModelResponse",
]
